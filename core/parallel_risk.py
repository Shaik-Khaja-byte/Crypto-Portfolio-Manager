# Import Python's concurrent futures module
# This allows parallel execution using threads
import concurrent.futures

# Import risk_engine module
# We will reuse get_coin_metrics() function
from core import risk_engine


def compute_risk_metrics_parallel(market_data):
    """
    Computes risk metrics for all coins using multithreading.

    Parameters:
        market_data (dict):
            Dictionary in format:
            {
                coin_id: [list_of_prices]
            }

    Returns:
        list:
            List of dictionaries containing:
            - coin_id
            - avg_daily_return
            - volatility
            - risk_category
    """

    # Store computed results
    results = []

    # Create a Thread Pool with maximum 5 worker threads
    # max_workers=5 means at most 5 coins processed simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        # Submit tasks to thread pool
        # Each task runs:
        # risk_engine.get_coin_metrics(coin_id, prices)

        # We map each future object to its coin_id
        # This helps us track which result belongs to which coin
        future_to_coin = {
            executor.submit(risk_engine.get_coin_metrics, coin_id, prices): coin_id
            for coin_id, prices in market_data.items()
        }

        # as_completed() returns futures as soon as they finish
        for future in concurrent.futures.as_completed(future_to_coin):

            # Identify which coin this future belongs to
            coin_id = future_to_coin[future]

            try:
                # Retrieve result from completed thread
                metrics = future.result()

                # Append computed metrics to results list
                results.append(metrics)

            except Exception as exc:
                # If any thread raises error,
                # print which coin failed
                print(f"Risk computation for {coin_id} generated an exception: {exc}")

    return results
