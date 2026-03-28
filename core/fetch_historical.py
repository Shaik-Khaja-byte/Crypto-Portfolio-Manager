# ------------------------------------------------------------
# Import Required Libraries
# ------------------------------------------------------------

# yfinance → Used to fetch historical price data from Yahoo Finance
import yfinance as yf

# csv → Used to write historical data into CSV file
import csv

# date → Used for handling date formatting
from datetime import date
import os


# ------------------------------------------------------------
# CONFIGURATION SECTION
# ------------------------------------------------------------

# Input file generated from previous pipeline
# Contains shortlisted coins compatible with Yahoo Finance
EDA_COINS_FILE = os.path.join(os.path.dirname(__file__), "../data/eda_coins.csv")

# Output file containing historical time-series data
HISTORICAL_CSV = os.path.join(os.path.dirname(__file__), "../data/historical_prices.csv")

# Time range configuration
PERIOD = "1y"      # Fetch 1 year of historical data
INTERVAL = "1d"    # Daily interval


# ------------------------------------------------------------
# Manual Mapping Between CoinGecko ID and Yahoo Finance Symbol
# ------------------------------------------------------------

# Important:
# CoinGecko uses IDs like "bitcoin"
# Yahoo Finance uses symbols like "BTC-USD"
# We must map them manually

YAHOO_SYMBOLS = {
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "binancecoin": "BNB-USD",
    "ripple": "XRP-USD",
    "solana": "SOL-USD",
    "cardano": "ADA-USD",
    "dogecoin": "DOGE-USD",
    "tron": "TRX-USD",
    "polkadot": "DOT-USD",
    "litecoin": "LTC-USD"
}


# ------------------------------------------------------------
# STEP 1: LOAD EDA COINS
# ------------------------------------------------------------

def load_eda_coins():
    """
    Reads eda_coins.csv and prepares a list of coins
    that are supported by Yahoo Finance.

    Returns:
        List of tuples:
        [
            (coin_id, yahoo_symbol),
            ...
        ]
    """

    coins = []

    # Open EDA CSV file
    with open(EDA_COINS_FILE, newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        # Loop through each row
        for row in reader:

            coin_id = row["coin_id"]

            # Only select coins that exist in Yahoo mapping
            if coin_id in YAHOO_SYMBOLS:

                coins.append(
                    (coin_id, YAHOO_SYMBOLS[coin_id])
                )

    return coins


# ------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------

def main():
    """
    Main execution function.

    Workflow:
        1. Load EDA-compatible coins
        2. Fetch historical data from Yahoo Finance
        3. Save OHLCV data into CSV
    """

    # Load shortlisted coins
    coins = load_eda_coins()

    print(f"Fetching Yahoo Finance historical data for {len(coins)} coins...")

    # Open output CSV file
    with open(HISTORICAL_CSV, mode="w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        # Write header row
        writer.writerow([
            "coin_id",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ])

        # Loop through each coin
        for coin_id, symbol in coins:

            print(f"→ Fetching {coin_id} ({symbol})")

            # Fetch historical data from Yahoo Finance
            # period = 1 year
            # interval = daily
            data = yf.download(
                symbol,
                period=PERIOD,
                interval=INTERVAL,
                progress=False
            )

            # Iterate through time-series rows
            for index, row in data.iterrows():

                writer.writerow([
                    coin_id,
                    index.date(),       # Date
                    row["Open"],        # Opening price
                    row["High"],        # Highest price of day
                    row["Low"],         # Lowest price of day
                    row["Close"],       # Closing price
                    row["Volume"]       # Trading volume
                ])

    print("Historical dataset created successfully.")


# ------------------------------------------------------------
# ENTRY POINT PROTECTION
# ------------------------------------------------------------

if __name__ == "__main__":
    main()
