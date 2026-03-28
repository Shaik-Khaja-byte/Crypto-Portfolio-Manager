class InvestmentMixCalculator:
    
    def __init__(self, risk_metrics, total_investment, risk_profile):
        """
        Constructor of the InvestmentMixCalculator class.

        Parameters:
        risk_metrics (list):
            A list of dictionaries containing:
            - coin_id
            - risk_category
            - volatility
            - avg_daily_return

        total_investment (float):
            Total capital (in USD) to allocate.

        risk_profile (str):
            Investor preference level.
            Acceptable values:
            - 'Low'
            - 'Medium'
            - 'High'
        """

        # Store risk metrics from Risk Engine
        self.risk_metrics = risk_metrics

        # Store total investment amount
        self.total_investment = total_investment

        # Normalize risk profile (capitalize for consistency)
        self.risk_profile = risk_profile.capitalize()


    def get_allocation_rules(self):
        """
        Returns predefined allocation percentages
        based on investor risk profile.

        Output format:
        {
            "Low": percentage,
            "Medium": percentage,
            "High": percentage
        }

        The sum of percentages always equals 1.0 (100%).
        """

        # Conservative investor
        # Most money goes to Low risk assets
        if self.risk_profile == "Low":
            return {"Low": 0.60, "Medium": 0.30, "High": 0.10}

        # Balanced investor
        elif self.risk_profile == "Medium":
            return {"Low": 0.40, "Medium": 0.40, "High": 0.20}

        # Aggressive investor
        # More capital allocated to High risk assets
        elif self.risk_profile == "High":
            return {"Low": 0.20, "Medium": 0.40, "High": 0.40}

        # Default behavior if invalid input
        else:
            return {"Low": 0.40, "Medium": 0.40, "High": 0.20}


    def calculate_allocation(self):
        """
        Calculates how much money should be allocated to each coin.

        Strategy used:
        - Allocate total capital across risk categories
        - Within each category, distribute equally

        This follows a simple equal-weight bucket model.
        """

        # Step 1: Get allocation rules
        rules = self.get_allocation_rules()

        # Step 2: Group coins by risk category
        coins_by_risk = {"Low": [], "Medium": [], "High": []}

        for coin in self.risk_metrics:

            # If risk category missing, default to High
            category = coin.get('risk_category', 'High')

            if category in coins_by_risk:
                coins_by_risk[category].append(coin)
            else:
                coins_by_risk["High"].append(coin)

        allocation_result = []

        # Step 3: Allocate money per category
        for category, target_pct in rules.items():

            eligible_coins = coins_by_risk[category]

            # If no coins exist in category, skip
            if not eligible_coins:
                continue

            # Financial Formula:
            # Category Budget = Total Investment × Target Percentage
            category_budget = self.total_investment * target_pct

            # Equal weight rule:
            # Amount per coin = Category Budget / Number of coins
            amount_per_coin = category_budget / len(eligible_coins)

            for coin in eligible_coins:

                allocation_result.append({
                    "coin_id": coin['coin_id'],
                    "risk_category": category,
                    "allocated_amount": round(amount_per_coin, 2),
                    "target_percent": target_pct,
                    "expected_daily_return": coin['avg_daily_return'],
                    "volatility": coin['volatility']
                })

        return allocation_result


    def calculate_portfolio_stats(self, allocation):
        """
        Computes portfolio-level performance metrics.

        Uses weighted average formulas.
        """

        # If no allocation, return zeros
        if not allocation:
            return {
                "total_invested": 0,
                "expected_daily_return": 0,
                "expected_annual_return": 0,
                "portfolio_volatility": 0
            }

        # Step 1: Compute total invested
        total_invested = sum(item['allocated_amount'] for item in allocation)

        weighted_return = 0
        weighted_risk = 0

        # Step 2: Apply weighted formulas
        for item in allocation:

            # Weight formula:
            # w_i = invested_amount_i / total_portfolio_value
            weight = item['allocated_amount'] / total_invested

            # Portfolio Expected Return Formula:
            # E(Rp) = Σ (w_i × r_i)
            weighted_return += item['expected_daily_return'] * weight

            # Portfolio Risk Approximation:
            # σp ≈ Σ (w_i × σ_i)
            weighted_risk += item['volatility'] * weight

        return {
            "total_invested": total_invested,

            # Daily expected return
            "expected_daily_return": weighted_return,

            # Annualized return (simple approximation)
            # Annual Return ≈ Daily Return × 365
            "expected_annual_return": weighted_return * 365,

            # Weighted volatility
            "portfolio_volatility": weighted_risk
        }
