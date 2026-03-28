# ------------------------------------------------------------
# Import Required Libraries
# ------------------------------------------------------------

# requests → used to call external API (CoinGecko)
import requests

# sqlite3 → used to create and manage SQLite database
import sqlite3

# csv → used to write data into CSV files
import csv
import os
import time


# ------------------------------------------------------------
# CONFIGURATION SECTION
# ------------------------------------------------------------

# CoinGecko API endpoint for fetching market data
API_URL = "https://api.coingecko.com/api/v3/coins/markets"

# SQLite database file name
DB_NAME = os.path.join(os.path.dirname(__file__), "../data/crypto.db")

# Dataset A: Full market snapshot
SNAPSHOT_CSV = os.path.join(os.path.dirname(__file__), "../data/market_snapshot.csv")

# Dataset B: Shortlisted EDA coins
EDA_CSV = os.path.join(os.path.dirname(__file__), "../data/eda_coins.csv")


# Set of coins supported by Yahoo Finance
# We filter based on these IDs for historical data compatibility
YAHOO_SUPPORTED_COINS = {
    "bitcoin",
    "ethereum",
    "binancecoin",
    "solana",
    "ripple",
    "cardano",
    "dogecoin",
    "polkadot",
    "litecoin",
    "tron"
}


# ------------------------------------------------------------
# STEP 1: FETCH MARKET SNAPSHOT FROM API
# ------------------------------------------------------------

def fetch_market_snapshot():
    """
    Fetches top 250 cryptocurrencies by market capitalization
    from CoinGecko API.

    Returns:
        list of dictionaries (JSON response)
    """

    print("Step 1: Fetching market snapshot data...")

    # API parameters
    params = {
        "vs_currency": "usd",           # Prices in USD
        "order": "market_cap_desc",     # Sort by market cap descending
        "per_page": 250,                # Fetch top 250 coins
        "page": 1,
        "sparkline": "false"
    }

    # Send GET request to API
    response = requests.get(API_URL, params=params)

    # Raise error if request failed
    response.raise_for_status()

    # Convert JSON response into Python list
    data = response.json()

    print(f"Fetched {len(data)} coins.")

    return data


# ------------------------------------------------------------
# STEP 2: SAVE FULL SNAPSHOT TO CSV (Dataset A)
# ------------------------------------------------------------

def save_snapshot_csv(data):
    """
    Saves complete market snapshot into CSV file.
    """

    print(f"Step 2: Saving market snapshot to {SNAPSHOT_CSV}...")

    with open(SNAPSHOT_CSV, mode="w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        # Write header row
        writer.writerow([
            "coin_id",
            "symbol",
            "name",
            "current_price",
            "market_cap",
            "last_updated"
        ])

        # Write each coin's data
        for coin in data:
            writer.writerow([
                coin["id"],
                coin["symbol"],
                coin["name"],
                coin.get("current_price", 0),
                coin.get("market_cap", 0),
                coin.get("last_updated", "")
            ])

    print("Market snapshot CSV saved.")


# ------------------------------------------------------------
# STEP 3: SELECT EDA COINS (Yahoo Compatible)
# ------------------------------------------------------------

def select_eda_coins(data):
    """
    Filters coins that are compatible with Yahoo Finance.

    Criteria:
        Coin ID must exist in predefined set.
    """

    print("Step 3: Selecting EDA coins (Yahoo Finance compatible)...")

    selected = []

    # Loop through fetched coins
    for coin in data:

        # If coin is Yahoo supported, add to shortlist
        if coin["id"] in YAHOO_SUPPORTED_COINS:
            selected.append(coin)

    print(f"Selected {len(selected)} EDA coins:")

    for coin in selected:
        print(f"- {coin['name']} ({coin['symbol']})")

    return selected


# ------------------------------------------------------------
# STEP 4: SAVE EDA DATASET TO CSV (Dataset B)
# ------------------------------------------------------------

def save_eda_csv(selected_coins):
    """
    Saves shortlisted EDA coins to CSV file.
    """

    print(f"Step 4: Saving EDA dataset to {EDA_CSV}...")

    with open(EDA_CSV, mode="w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow([
            "coin_id",
            "symbol",
            "name",
            "current_price",
            "market_cap"
        ])

        for coin in selected_coins:
            writer.writerow([
                coin["id"],
                coin["symbol"],
                coin["name"],
                coin.get("current_price", 0),
                coin.get("market_cap", 0)
            ])

    print("EDA CSV saved.")


# ------------------------------------------------------------
# STEP 5: SAVE FULL SNAPSHOT TO SQLITE DATABASE
# ------------------------------------------------------------

def save_snapshot_to_db(data):
    """
    Stores market snapshot inside SQLite database using retries and UPSERT.
    """

    print(f"Step 5: Saving market snapshot to database ({DB_NAME})...")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with sqlite3.connect(DB_NAME, timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                cursor = conn.cursor()

                # Create table safely if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_snapshot (
                        coin_id TEXT PRIMARY KEY,
                        symbol TEXT,
                        name TEXT,
                        current_price REAL,
                        market_cap INTEGER,
                        last_updated TEXT
                    )
                """)

                # UPSERT strategy: Replace conflicting rows atomically
                for coin in data:
                    cursor.execute("""
                        REPLACE INTO market_snapshot (coin_id, symbol, name, current_price, market_cap, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        coin["id"], coin["symbol"], coin["name"],
                        coin.get("current_price", 0), coin.get("market_cap", 0),
                        coin.get("last_updated", "")
                    ))
            # Close the connection successfully outside context
            conn.close()
            print("Database updated successfully.")
            break
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print(f"Database locked, retrying {attempt+1}/{max_retries} in 0.5s...")
                time.sleep(0.5)
                if attempt == max_retries - 1:
                    print("Max retries reached. Failed to write to DB.")
            else:
                raise e


# ------------------------------------------------------------
# MAIN PIPELINE EXECUTION
# ------------------------------------------------------------

def fetch_latest_prices():
    """
    Controls the full data ingestion pipeline.
    """

    print("----- STARTING DATA PIPELINE -----")

    # Step 1: Fetch data from API
    snapshot_data = fetch_market_snapshot()

    # Step 2: Save full snapshot
    save_snapshot_csv(snapshot_data)

    # Step 3: Filter EDA coins
    eda_coins = select_eda_coins(snapshot_data)

    # Step 4: Save EDA dataset
    save_eda_csv(eda_coins)

    # Step 5: Save to database
    save_snapshot_to_db(snapshot_data)

    print("----- PIPELINE COMPLETE -----")


# Entry point protection
if __name__ == "__main__":
    fetch_latest_prices()
