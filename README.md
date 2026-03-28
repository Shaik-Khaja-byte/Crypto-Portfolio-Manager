# Crypto Portfolio Manager

A complete end-to-end cryptocurrency analytics pipeline and professional web dashboard built in Python (Streamlit).

This project implements a structured financial data workflow and UI:

API Data Ingestion -> Database Storage -> Historical Data Processing -> Risk Engine -> Parallel Computation -> Portfolio Allocation -> AI Forecast -> UI Visualization & PDF Output

It simulates a robust backend architecture and dynamic frontend used in real-world quantitative investment systems.

---

# System Architecture

The project is divided into major layers:

1. **Presentation & Application Layer** (Streamlit Dashboard, Auth, Notifications)
2. **AI & Risk Analytics Layer** (Machine Learning, Parallel Math Engine)
3. **Data Ingestion Layer** (REST APIs via CoinGecko & Yahoo Finance)
4. **Storage Layer** (SQLite, CSVs)

Each module is cleanly separated to follow modular design principles.

---

# Project Structure

```text
CRYPTO-PORTFOLIO-MANAGER/
│
├── app.py                           # Main Streamlit dashboard application
├── database_manager.py              # SQLite database interactions (WAL mode, thread-safe)
├── notifications.py                 # Email (SMTP) and PDF reporting engine
├── predictor.py                     # Scikit-Learn ML script for 7-day price forecasting
├── styles.py                        # Custom CSS styling for the web interface
├── requirements.txt                 # Library dependencies
├── .env.example                     # Environment variable template (copy to .env)
├── .gitignore                       # Git ignore rules
├── README.md                        # Project documentation (this file)
├── audit_report.pdf                 # Generated sample compliance report
│
├── core/
│   ├── __init__.py                  # Package initialization file
│   ├── collect_data.py              # Fetches live CoinGecko API data
│   ├── fetch_historical.py          # Downloads Yahoo Finance 1-year bulk data
│   ├── investment_mix_calculator.py # Risk-based portfolio allocation math
│   ├── mover.py                     # Script used for internal file migration
│   ├── parallel_risk.py             # Multithreaded risk computation wrapper
│   ├── risk_engine.py               # Math engine for returns, volatility, risk scoring
│   └── test_investment_mix.py       # CLI execution tool for testing the math engine
│
├── data/
│   ├── crypto.db                    # Main SQLite database (WAL mode) storing users and portfolios
│   ├── crypto_eda.ipynb             # Jupyter Notebook for exploratory data analysis
│   ├── eda_coins.csv                # Shortlisted coins compatible with Yahoo Finance
│   ├── historical_prices.csv        # Downloaded 1-year OHLCV pricing bulk data
│   └── market_snapshot.csv          # Snapshot array of the top 250 crypto assets
│
└── docs/                            # Contains project diagrams, logic texts, and milestone reports
    ├── Charts Explanation - milestone 1.docx
    ├── Formulas and concept learning.docx
    ├── chart 1.png
    ├── chart 2.png
    ├── chart 3.png
    ├── chart 4.png
    ├── chart 5.png
    ├── crypto_types_plan.txt
    ├── math_logic.txt
    ├── milestone 1 - presentation.docx
    └── parallel_tasks_explanation.txt
```

---

# File-Level Breakdown

## 1. Data Ingestion Layer

### `core/collect_data.py`
**Purpose**: Fetches live cryptocurrency market data from CoinGecko API and builds initial datasets.
- `fetch_market_snapshot()`: Calls CoinGecko API for top 250 coins based on market cap.
- `save_snapshot_csv()`: Writes the full API response to `market_snapshot.csv`.
- `select_eda_coins()`: Filters Yahoo-Finance compatible coins for historical mapping.
- `save_eda_csv()`: Writes the filtered compatible coins to `eda_coins.csv`.
- `save_snapshot_to_db()`: Saves the tabular market data to the `crypto.db` SQLite database.
- `fetch_latest_prices()`: Main pipeline trigger executing the ingestion steps linearly.

---

## 2. Historical Data Layer

### `core/fetch_historical.py`
**Purpose**: Fetches 1-year daily OHLCV data using Yahoo Finance mapping.
- `load_eda_coins()`: Maps the short-listed coins to valid Yahoo Finance ticker symbols.
- `main()`: Iterates through tickers, downloads 1-year of yfinance data, and exports it to `historical_prices.csv`.

---

## 3. Risk Analytics Layer

### `core/risk_engine.py`
**Purpose**: The central quantitative financial mathematics engine.
- `parse_price()`: Cleans raw string arrays and parses numeric prices from CSV representations.
- `load_data()`: Reads historical CSV data into memory mapping.
- `calculate_daily_returns()`: Uses price differences to calculate daily percentage returns.
- `calculate_volatility()`: Calculates sample standard deviations from daily return arrays.
- `determine_risk_category()`: Classifies assets into risk buckets based on standard deviation limits.
- `get_coin_metrics()`: Aggregates return, volatility, and profile categorization for a given asset.

---

## 4. Parallel Risk Computation

### `core/parallel_risk.py`
**Purpose**: Uses Multithreading for rapid calculations across large datasets.
- `compute_risk_metrics_parallel()`: Uses thread pools to speed up metric algorithms across multiple assets.

---

## 5. Portfolio Allocation Engine

### `core/investment_mix_calculator.py`
**Purpose**: Calculates targeted portfolio allocations.
- `__init__()`: Initializes object with risk metrics, total capital, and risk profile classification.
- `get_allocation_rules()`: Maps risk profile configurations to predefined percentage groupings.
- `calculate_allocation()`: Spreads capital within risk buckets equally based on target rules.
- `calculate_portfolio_stats()`: Processes weighted returns and predicted portfolio volatilities.

---

## 6. Main Execution Orchestrator

### `core/test_investment_mix.py`
**Purpose**: CLI testing playground orchestrating risk flows setup.
- `main()`: Triggers loaders, runs parallel threads, and outputs calculations direct to the terminal out.

### `core/mover.py`
**Purpose**: Internal utility script.
- (Script Block): Automates migration of core logic and data files into the core and data subdirectory structure.

---

## 7. Exploratory Data Analysis

### `data/crypto_eda.ipynb`
**Purpose**: Used for data visualization, correlation analysis, pattern observation, and statistical exploration.

---

## 8. Presentation & Application Layer

### `app.py`
**Purpose**: Main Streamlit web application orchestrating the UI, routing, and pulling data from core modules.
- `auth_view()`: Renders the login and registration UI tabs.
- `load_market_data()`: Cached helper to load and format live CSV market prices.
- `get_current_price()`: Helper to retrieve precise live prices for calculation workflows.
- `page_dashboard()`: Renders the main portfolio view, Risk Sentinel tracking, and investment console.
- `page_market()`: Displays the global market tracker in a dynamic tabular format.
- `page_risk()`: Renders multithreaded volatility analysis and Plotly gauge charts.
- `page_prediction()`: Renders the AI Machine Learning linear regression forecasts.
- `page_settings()`: Allows risk threshold configurations and PDF report downloads.

### `styles.py`
**Purpose**: Injects custom CSS for the application interface.
- `get_css()`: Returns a multi-line CSS string providing the dark-mode aesthetic and customized widgets.

---

## 9. Database & Authentication Core

### `database_manager.py`
**Purpose**: Handles all SQLite database transactions for users, settings, and portfolios. Uses **WAL (Write-Ahead Logging)** mode and a global `threading.Lock` for thread-safe, serialized writes.
- `_get_conn()`: Creates a WAL-mode SQLite connection with timeout and cross-thread safety.
- `_execute_write()`: Decorator that serializes all write operations through `db_lock` with retry logic.
- `_execute_read()`: Decorator for safe read-only operations without lock contention.
- `init_db()`: Initializes schema tables (users, portfolio, settings, alert_log).
- `hash_password()`: Secures user passwords using SHA-256 formatting.
- `create_user()`: Registers a new user and sets default risk settings.
- `verify_user()`: Verifies the 4-digit OTP code to activate the account.
- `authenticate_user()`: Validates credentials and limits access securely.
- `add_to_portfolio()`: Records a new purchase in the user's portfolio.
- `remove_asset()`: Liquidates an asset by removing its row from the database.
- `get_live_portfolio()`: Joins the personal portfolio with the global market snapshot to calculate live ROI.
- `get_settings()`: Fetches the user's custom risk alert threshold.
- `update_settings()`: Updates the custom risk alert threshold.
- `process_all_risk_alerts()`: Event-driven alert engine with deduplication—sends email only on first breach or re-breach after recovery.
- `get_latest_active_alert()`: Returns the most recent active alert for UI display.

---

## 10. Notifications & Reporting Engine

### `notifications.py`
**Purpose**: Handles automated SMTP email alerts and generates FPDF compliance reports. All credentials are loaded securely from a `.env` file using `python-dotenv` — no secrets are hardcoded.
- `_send_email()`: Private handler for establishing secure TLS SMTP connections.
- `send_otp()`: Sends registration verification codes to users.
- `send_risk_alert()`: Sends automated warnings when assets drop below customized thresholds.
- `generate_pdf_report()`: Dynamically writes and formats a professional PDF audit report using fpdf.

---

## 11. AI & Machine Learning Layer

### `predictor.py`
**Purpose**: Scikit-Learn logic to forecast future cryptocurrency prices.
- `get_7day_prediction()`: Cleans historical data, trains a Linear Regression model, and infers prices for 7 days.

---

# Data Flow

How data moves across files:
1. **Ingestion Flow**: Data runs via `core/collect_data.py` and `core/fetch_historical.py` -> JSON API transforms to persistent CSVs and `crypto.db` in `data/`.
2. **Session and DB Flow**: `app.py` triggers authentication -> Uses `database_manager.py` to establish state in `crypto.db` -> Generates Email OTP via `notifications.py`.
3. **Analytics Flow**: User selects strategy in UI -> Calls `core.parallel_risk` -> Fetches Math from `core.risk_engine` -> Divides capital via `core.investment_mix_calculator` -> Saves portfolio to DB.
4. **AI Flow**: User queries prediction -> `app.py` triggers `predictor.py` -> Sklearn Linear regression runs on historical CSV -> Output pushed to Plotly Graph.
5. **Reporting Flow**: User requests Audit -> `database_manager.py` fetches live allocation -> `notifications.py` compiles PDF -> UI provides download bytes.

---

# Execution Flow

Exact pipeline configuration:
API Data Collection -> CSV and SQLite Storage -> Historical Extraction -> Multithreaded Risk Processing -> Rule-based Capital Allocation -> Output Dashboard, AI Forecast, and PDF Report

---

# How to Run

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/crypto-portfolio-manager.git
cd crypto-portfolio-manager
```

### Step 2: Create a Virtual Environment
```bash
python -m venv venv
```
Activate the virtual environment:
- **Windows**: `venv\Scripts\activate`
- **macOS/Linux**: `source venv/bin/activate`

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the provided template and fill in your credentials:
```bash
cp .env.example .env
```
Edit the `.env` file and add your SMTP credentials (see [Environment Variables](#environment-variables) below).

### Step 5: Extract & Process Data
Build the local database and historical cache mappings by running:
```bash
python core/collect_data.py
python core/fetch_historical.py
```

### Step 6: Launch the Application
Start the Streamlit Web Server Dashboard:
```bash
streamlit run app.py
```

---

# Environment Variables

This project requires a `.env` file in the root directory to securely store SMTP credentials for email notifications (OTP verification and risk alerts).

A template is provided in `.env.example`. Copy it and fill in your values:

```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

| Variable | Description |
|---|---|
| `EMAIL_USER` | The email address used to send OTP and risk alert emails |
| `EMAIL_PASS` | App-specific password (e.g., Gmail App Password — not your regular password) |
| `SMTP_SERVER` | SMTP server hostname (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP server port (default: `587` for TLS) |

> **⚠️ Important**: The `.env` file contains sensitive credentials and is excluded from version control via `.gitignore`. Never commit it to the repository.

---

# Dependencies

Extracting from `requirements.txt` and python file imports:
- `streamlit`: Web dashboard framework.
- `numpy`: Array manipulation.
- `pandas`: Data structuring.
- `plotly`: Interactive UI charts.
- `requests`: Fetching CoinGecko REST APIs.
- `yfinance`: Yahoo Finance history extraction.
- `fpdf`: Generation of automated PDF reports.
- `scikit-learn`: Linear Regression logic.
- `python-dotenv`: Secure loading of environment variables from `.env`.

(Additional pure-Python libraries used: `os`, `time`, `datetime`, `sqlite3`, `hashlib`, `csv`, `statistics`, `math`, `concurrent.futures`, `smtplib`, `threading`)

---

# Features Implemented

- Complete Auth Flow (Login, OTP Email Registration, Encrypted Passwords)
- Secure Credential Handling via `.env` (no hardcoded secrets)
- Live CoinGecko API Integration  
- CSV & SQLite Persistent Tracking (WAL mode, thread-safe writes)
- 1-year Historical Time-Series Processing via Yahoo Finance 
- Multithreaded Volatility Modelling & Risk Categorization
- Risk-based Automated Portfolio Allocation Strategies
- Live Tracking Portfolio Dashboard & Profit/Loss Calculation
- Event-driven "Risk Sentinel" SMTP Email Alerts with Deduplication
- Sklearn Machine Learning 7-Day Asset Forecasting
- Full PDF Audit Report Generation
- Glassmorphism Dark Mode UI via CSS

---

# Project Scope

This project demonstrates:

- Backend data pipeline engineering
- Financial mathematics implementation
- Volatility modeling
- Risk classification systems
- Parallel computing in Python
- Portfolio optimization logic
- Modular system design
- Persistent database integration
- Web Dashboard engineering with Streamlit
- Applied AI/ML Forecasting

It can serve as a foundation for:

- Algorithmic trading systems
- Quantitative finance research
- Financial dashboard applications
- Investment advisory systems

---

# Future Enhancements

- Sharpe Ratio and Sortino Ratio
- Correlation matrix modeling
- Covariance-based portfolio volatility
- Monte Carlo simulation
- REST API layer
- Deployment to cloud
- Real-time streaming WebSocket data

---

# License

This project is licensed under the MIT License.

---

**Crypto Portfolio Manager**  
End-to-End Financial Analytics System in Python
