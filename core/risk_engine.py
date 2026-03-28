# Import built-in CSV module to read CSV files
import csv

# Import statistics module to calculate mean and standard deviation
import statistics

# Import math module (used conceptually for sqrt in volatility formula)
import math
import os

# Define the file name that contains historical price data
HISTORICAL_FILE = os.path.join(os.path.dirname(__file__), "../data/historical_prices.csv")


def parse_price(cell_value):
    """
    This function extracts a numeric price from a CSV cell.

    Sometimes yfinance exports messy multi-line strings.
    This function ensures we extract a valid float price.
    """

    try:
        # Case 1:
        # If the value is already a clean number like "96499.46"
        # Convert directly to float
        return float(cell_value)

    except ValueError:
        # If conversion fails, it means the value is messy text
        pass

    try:
        # Case 2:
        # If the value is multi-line text,
        # split it by newline
        lines = cell_value.strip().split('\n')

        # We expect price to be in second line
        # Example format:
        # Line 0: "Ticker"
        # Line 1: "BTC-USD 96499.460938"
        if len(lines) >= 2:

            # Split second line by spaces
            parts = lines[1].split()

            # Extract last element which should be the numeric price
            if len(parts) >= 2:
                return float(parts[-1])

    except Exception:
        # If anything unexpected happens,
        # return None
        pass

    return None


def load_data():
    """
    Loads historical price data from CSV.

    Returns:
        Dictionary in format:
        {
            coin_id: [list_of_prices]
        }
    """

    market_data = {}

    try:
        # Open CSV file
        with open(HISTORICAL_FILE, "r", encoding="utf-8") as f:

            # Read CSV as dictionary rows
            reader = csv.DictReader(f)

            # Iterate over each row
            for row in reader:

                coin_id = row['coin_id']
                raw_close = row['close']

                # Clean price using parse_price()
                price = parse_price(raw_close)

                # Only store valid numeric prices
                if price is not None:

                    # If coin not yet in dictionary,
                    # initialize empty list
                    if coin_id not in market_data:
                        market_data[coin_id] = []

                    # Append price to that coin's list
                    market_data[coin_id].append(price)

    except FileNotFoundError:
        print(f"Error: {HISTORICAL_FILE} not found.")
        return {}

    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

    return market_data


def calculate_daily_returns(prices):
    """
    Calculates percentage daily returns.

    Main Financial Formula Used:

    Return_t = (P_t − P_(t-1)) / P_(t-1)

    Where:
        P_t     = Current day's price
        P_(t-1) = Previous day's price
    """

    # If fewer than 2 prices,
    # we cannot compute return
    if len(prices) < 2:
        return []

    returns = []

    # Start from second element
    for i in range(1, len(prices)):

        prev = prices[i-1]   # Previous day price
        curr = prices[i]     # Current day price

        # Prevent division by zero
        if prev > 0:

            # Apply daily return formula
            ret = (curr - prev) / prev

            # Store calculated return
            returns.append(ret)

    return returns


def calculate_volatility(daily_returns):
    """
    Calculates volatility.

    Formula Used (Sample Standard Deviation):

    Volatility = sqrt( (1 / (n - 1)) × Σ (r_i − mean)^2 )

    statistics.stdev() automatically applies this formula.
    """

    # If insufficient data,
    # volatility is zero
    if len(daily_returns) < 2:
        return 0.0

    # Calculate standard deviation
    return statistics.stdev(daily_returns)


def determine_risk_category(volatility, thresholds=(0.02, 0.04)):
    """
    Categorizes coin risk level based on volatility.

    thresholds:
        low_cut  = boundary between Low and Medium
        high_cut = boundary between Medium and High
    """

    low_cut, high_cut = thresholds

    # If volatility is below low_cut
    # classify as Low risk
    if volatility < low_cut:
        return "Low"

    # If volatility between low_cut and high_cut
    # classify as Medium risk
    elif volatility < high_cut:
        return "Medium"

    # Otherwise classify as High risk
    else:
        return "High"


def get_coin_metrics(coin_id, prices):
    """
    Computes all metrics for a single coin.

    Returns:
        {
            coin_id,
            avg_daily_return,
            volatility,
            risk_category
        }
    """

    # Step 1: Compute daily returns
    daily_returns = calculate_daily_returns(prices)

    # If no returns available,
    # return default values
    if not daily_returns:
        return {
            "coin_id": coin_id,
            "avg_daily_return": 0.0,
            "volatility": 0.0,
            "risk_category": "Unknown"
        }

    # Step 2: Compute average daily return
    # Formula:
    # Mean = (r1 + r2 + ... + rn) / n
    avg_return = statistics.mean(daily_returns)

    # Step 3: Compute volatility (standard deviation)
    volatility = calculate_volatility(daily_returns)

    # Step 4: Categorize risk
    metrics = {
        "coin_id": coin_id,
        "avg_daily_return": avg_return,
        "volatility": volatility,
        "risk_category": determine_risk_category(volatility, thresholds=(0.03, 0.05))
    }

    return metrics
