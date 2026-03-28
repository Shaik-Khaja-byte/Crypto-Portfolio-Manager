# Import time module to measure execution duration
import time

# Import risk_engine module
# This contains functions to load data and compute risk metrics
from core import risk_engine

# Import parallel_risk module
# This enables multithreaded risk computation
from core import parallel_risk

# Import InvestmentMixCalculator class
# This handles allocation and portfolio calculations
from core.investment_mix_calculator import InvestmentMixCalculator


def main():
    """
    Main execution function.

    This function orchestrates the entire Crypto Portfolio Manager system.

    Workflow:
        1. Load historical data
        2. Compute risk metrics (parallel execution)
        3. Generate allocation plan
        4. Compute portfolio statistics
        5. Display results
    """

    print("=== Crypto Portfolio Manager: Investment Mix Calculator ===\n")

    # ----------------------------------------------------------
    # 1. LOAD DATA
    # ----------------------------------------------------------

    print("1. Loading Data...")

    # Start timer to measure performance
    start_time = time.time()

    # Load historical price data from CSV
    # Returns dictionary:
    # {coin_id: [price1, price2, ...]}
    market_data = risk_engine.load_data()

    # Calculate duration
    load_duration = time.time() - start_time

    # Print number of coins loaded and execution time
    print(f"   Loaded data for {len(market_data)} coins in {load_duration:.4f} seconds.")

    # If no data loaded, stop execution
    if not market_data:
        print("   [ERROR] No data loaded. Check ../data/historical_prices.csv.")
        return


    # ----------------------------------------------------------
    # 2. PARALLEL RISK COMPUTATION
    # ----------------------------------------------------------

    print("\n2. Computing Risk Metrics (Parallel)...")

    # Start performance timer
    start_time = time.time()

    # Compute risk metrics using multithreading
    # This internally calls:
    # risk_engine.get_coin_metrics()
    risk_metrics = parallel_risk.compute_risk_metrics_parallel(market_data)

    # Calculate execution duration
    duration = time.time() - start_time

    print(f"   Processed {len(market_data)} coins in {duration:.4f} seconds.")

    # Display risk results in table format
    print("\n   [Risk Analysis Results]")
    print(f"   {'Coin ID':<15} {'Volatility':<12} {'Risk Category':<15}")
    print("-" * 45)

    for m in risk_metrics:
        print(f"   {m['coin_id']:<15} {m['volatility']:.4f}       {m['risk_category']:<15}")


    # ----------------------------------------------------------
    # 3. INVESTMENT ALLOCATION
    # ----------------------------------------------------------

    # Define total capital
    total_investment = 100000

    # Possible risk profiles
    risk_profiles = ["Medium", "High", "Low"]

    # Choose one profile (can be dynamic later)
    risk_profile = "Medium"

    print(f"\n3. Generating Allocation (Investment: ${total_investment}, Profile: {risk_profile})...")

    # Create InvestmentMixCalculator object
    calculator = InvestmentMixCalculator(
        risk_metrics,
        total_investment,
        risk_profile
    )

    # Calculate allocation per coin
    allocation = calculator.calculate_allocation()

    # Calculate portfolio statistics
    portfolio_stats = calculator.calculate_portfolio_stats(allocation)

    print("\n   [Allocation Plan]")
    print(f"   {'Coin ID':<15} {'Category':<10} {'Allocation ($)':<15} {'% of Portfolio':<15}")
    print("-" * 60)

    total_alloc = 0

    # Sort allocation by risk category for clean display
    allocation.sort(key=lambda x: x['risk_category'])

    for item in allocation:

        amount = item['allocated_amount']

        # Percentage calculation:
        # % = (allocated_amount / total_investment) × 100
        pct = (amount / total_investment) * 100

        print(f"   {item['coin_id']:<15} {item['risk_category']:<10} ${amount:<14,.2f} {pct:.1f}%")

        total_alloc += amount

    print("-" * 60)
    print(f"   Total Allocated: ${total_alloc:,.2f}")


    # ----------------------------------------------------------
    # 4. PORTFOLIO FORECAST
    # ----------------------------------------------------------

    print("\n   [Portfolio Forecast]")

    # Expected annual return:
    # Annual Return ≈ Daily Return × 365
    print(f"   Expected Annual Return: {portfolio_stats['expected_annual_return']*100:.2f}%")

    # Portfolio volatility (weighted risk approximation)
    print(f"   Portfolio Volatility:   {portfolio_stats['portfolio_volatility']*100:.4f}")

    print("\n=== Calculation Complete ===")


# ----------------------------------------------------------
# Entry Point Protection
# ----------------------------------------------------------

# This ensures:
# The main() function runs only if this file
# is executed directly.
# If imported as module, main() will not run automatically.

if __name__ == "__main__":
    main()
