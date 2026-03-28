import sqlite3
import os
import hashlib
import threading
import time
from datetime import datetime
import notifications

# --- DATABASE CONFIGURATION ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "crypto.db")

# --- GLOBAL WRITE LOCK ---
# Ensures only ONE thread can write to the database at any time.
db_lock = threading.Lock()


def _get_conn():
    """Creates a new SQLite connection with WAL mode, timeout, and cross-thread safety."""
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _execute_write(func):
    """Decorator: serializes all write operations through db_lock with retry logic."""
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            with db_lock:
                try:
                    with _get_conn() as conn:
                        cursor = conn.cursor()
                        result = func(cursor, *args, **kwargs)
                        return result
                except sqlite3.OperationalError as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        print(f"DB locked, retry {attempt+1}/{max_retries}...")
                        time.sleep(0.5)
                    else:
                        raise
        return None
    return wrapper


def _execute_read(func):
    """Decorator: reads do not need the lock, but still use safe connection handling."""
    def wrapper(*args, **kwargs):
        with _get_conn() as conn:
            cursor = conn.cursor()
            return func(cursor, *args, **kwargs)
    return wrapper


# ------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------
def init_db():
    """Creates all required tables if they don't exist."""
    with db_lock:
        with _get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password_hash TEXT,
                    is_verified INTEGER DEFAULT 0,
                    otp_code TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT,
                    coin_id TEXT,
                    quantity REAL,
                    purchase_price REAL,
                    timestamp TEXT,
                    FOREIGN KEY (user_email) REFERENCES users (email)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_email TEXT PRIMARY KEY,
                    alert_threshold_pct REAL DEFAULT 10.0,
                    FOREIGN KEY (user_email) REFERENCES users (email)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_log (
                    portfolio_id INTEGER PRIMARY KEY,
                    user_email TEXT,
                    coin_id TEXT,
                    last_alert_price REAL,
                    drop_pct REAL,
                    last_alert_timestamp TEXT,
                    alert_sent INTEGER DEFAULT 0,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolio (id) ON DELETE CASCADE
                )
            """)


# ------------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ------------------------------------------------------------------
# USER CRUD
# ------------------------------------------------------------------
def create_user(email, password, otp_code):
    """Registers a new user and sets default risk settings."""
    try:
        with db_lock:
            with _get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, password_hash, otp_code) VALUES (?, ?, ?)",
                    (email, hash_password(password), otp_code),
                )
                cursor.execute(
                    "INSERT INTO settings (user_email, alert_threshold_pct) VALUES (?, ?)",
                    (email, 10.0),
                )
        return True
    except sqlite3.IntegrityError:
        return False


@_execute_read
def verify_user(cursor, email, otp_code):
    """Verifies OTP — read first, then conditionally write."""
    cursor.execute("SELECT otp_code FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    if result and str(result[0]) == str(otp_code):
        # Need a write — acquire lock manually
        with db_lock:
            with _get_conn() as wconn:
                wconn.cursor().execute(
                    "UPDATE users SET is_verified = 1 WHERE email = ?", (email,)
                )
        return True
    return False


@_execute_read
def authenticate_user(cursor, email, password):
    """Checks credentials during login (READ-ONLY)."""
    cursor.execute(
        "SELECT password_hash, is_verified FROM users WHERE email = ?", (email,)
    )
    result = cursor.fetchone()
    if result:
        stored_hash, is_verified = result
        if stored_hash == hash_password(password):
            return {"authenticated": True, "is_verified": bool(is_verified)}
    return {"authenticated": False, "is_verified": False}


# ------------------------------------------------------------------
# PORTFOLIO CRUD
# ------------------------------------------------------------------
@_execute_write
def add_to_portfolio(cursor, email, coin, qty, price, timestamp):
    """CREATE: Records a new purchase."""
    cursor.execute(
        "INSERT INTO portfolio (user_email, coin_id, quantity, purchase_price, timestamp) VALUES (?, ?, ?, ?, ?)",
        (email, coin, qty, price, timestamp),
    )


@_execute_write
def remove_asset(cursor, asset_id, email):
    """DELETE: Liquidates an asset."""
    cursor.execute(
        "DELETE FROM portfolio WHERE id = ? AND user_email = ?", (asset_id, email)
    )


@_execute_read
def get_live_portfolio(cursor, email):
    """READ: JOINs portfolio with market snapshot for live ROI."""
    cursor.execute(
        """
        SELECT p.id, p.coin_id, p.quantity, p.purchase_price, p.timestamp,
               m.current_price, m.name, m.symbol
        FROM portfolio p
        LEFT JOIN market_snapshot m ON p.coin_id = m.coin_id
        WHERE p.user_email = ?
        """,
        (email,),
    )
    items = cursor.fetchall()

    result = []
    for r in items:
        result.append(
            {
                "id": r[0],
                "coin_id": r[1],
                "quantity": r[2],
                "purchase_price": r[3],
                "timestamp": r[4],
                "current_price": r[5] if r[5] is not None else r[3],
                "name": r[6] if r[6] is not None else r[1],
                "symbol": r[7] if r[7] is not None else r[1],
            }
        )
    return result


# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
@_execute_read
def get_settings(cursor, email):
    """Fetches the user's custom risk alert threshold (READ-ONLY)."""
    cursor.execute(
        "SELECT alert_threshold_pct FROM settings WHERE user_email = ?", (email,)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    return 10.0


@_execute_write
def update_settings(cursor, email, threshold):
    """Updates the risk threshold."""
    cursor.execute(
        "UPDATE settings SET alert_threshold_pct = ? WHERE user_email = ?",
        (threshold, email),
    )


# ------------------------------------------------------------------
# ALERT ENGINE (EVENT-DRIVEN, DEDUPLICATED)
# ------------------------------------------------------------------
def process_all_risk_alerts(user_email):
    """
    Backend task: checks every holding against the user's threshold.
    Sends email ONLY on first breach or re-breach after recovery.
    """
    portfolio = get_live_portfolio(user_email)
    threshold = get_settings(user_email)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_lock:
        with _get_conn() as conn:
            cursor = conn.cursor()

            for item in portfolio:
                purch = item["purchase_price"]
                curr = item["current_price"]
                drop_pct = ((purch - curr) / purch * 100) if purch > 0 else 0
                port_id = item["id"]
                coin = item["coin_id"]

                # CHECK before writing — prevents duplicate inserts
                cursor.execute(
                    "SELECT alert_sent FROM alert_log WHERE portfolio_id = ?",
                    (port_id,),
                )
                result = cursor.fetchone()

                if drop_pct >= threshold:
                    if not result:
                        # FIRST BREACH — send + insert
                        notifications.send_risk_alert(user_email, coin, curr, drop_pct)
                        cursor.execute(
                            """INSERT INTO alert_log
                               (portfolio_id, user_email, coin_id, last_alert_price, drop_pct, last_alert_timestamp, alert_sent)
                               VALUES (?, ?, ?, ?, ?, ?, 1)""",
                            (port_id, user_email, coin, curr, drop_pct, now),
                        )
                    elif result[0] == 0:
                        # RE-BREACH after recovery — send + update
                        notifications.send_risk_alert(user_email, coin, curr, drop_pct)
                        cursor.execute(
                            """UPDATE alert_log
                               SET last_alert_price=?, drop_pct=?, last_alert_timestamp=?, alert_sent=1
                               WHERE portfolio_id=?""",
                            (curr, drop_pct, now, port_id),
                        )
                    elif result[0] == 1:
                        # Already alerted — silent tracking update only
                        cursor.execute(
                            "UPDATE alert_log SET drop_pct=?, last_alert_price=? WHERE portfolio_id=?",
                            (drop_pct, curr, port_id),
                        )
                else:
                    # Price recovered — reset so future drops trigger again
                    if result and result[0] == 1:
                        cursor.execute(
                            "UPDATE alert_log SET alert_sent=0 WHERE portfolio_id=?",
                            (port_id,),
                        )


@_execute_read
def get_latest_active_alert(cursor, user_email):
    """UI FETCH: returns the single most recent active alert (READ-ONLY)."""
    cursor.execute(
        """SELECT coin_id, drop_pct, last_alert_timestamp
           FROM alert_log
           WHERE user_email = ? AND alert_sent = 1
           ORDER BY last_alert_timestamp DESC LIMIT 1""",
        (user_email,),
    )
    row = cursor.fetchone()
    if row:
        return {"coin_id": row[0], "drop_pct": row[1], "timestamp": row[2]}
    return None


if __name__ == "__main__":
    init_db()
    print("Database manager initialized successfully.")