import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import timedelta
# Reusing the existing price-cleaning logic to ensure data consistency
from core.risk_engine import parse_price

def get_7day_prediction(coin_id):
    """
    AI ENGINE: Uses Scikit-Learn to perform a time-series forecast.
    It treats dates as the independent variable (X) and price as the dependent variable (y).
    """
    
    # --- 1. DATA ACQUISITION ---
    # Locating the historical dataset stored in the /data folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_csv = os.path.join(base_dir, "data", "historical_prices.csv")
    
    if not os.path.exists(historical_csv):
        historical_csv = "data/historical_prices.csv"
        
    try:
        df = pd.read_csv(historical_csv)
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None
        
    # Filtering the dataset to only include the coin the user wants to predict
    df_coin = df[df['coin_id'] == coin_id].copy()
    
    if df_coin.empty:
        return None, None
    
    # --- 2. DATA PREPROCESSING (Cleaning) ---
    # Financial data from APIs often includes headers or text strings.
    # We apply parse_price to convert "messy" strings into pure floats.
    df_coin['close'] = df_coin['close'].apply(parse_price)
    
    # Machine Learning models cannot handle 'NaN' (Not a Number) values.
    # We drop any rows that failed the cleaning process.
    df_coin = df_coin.dropna(subset=['close'])
    
    # We need at least 2 data points to draw a trendline.
    if len(df_coin) < 2:
        return None, None

    # Standardizing the date format and ensuring the timeline is chronological.
    df_coin['date'] = pd.to_datetime(df_coin['date'])
    df_coin = df_coin.sort_values('date')
    
    # --- 3. FEATURE ENGINEERING ---
    # Scikit-Learn cannot "read" dates. We convert dates into 'Ordinals' 
    # (integers representing the number of days since Year 1).
    # X must be a 2D array (reshaped) for the LinearRegression model.
    X = df_coin['date'].map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    y = df_coin['close'].values

    # --- 4. MODEL TRAINING ---
    # We initialize the Linear Regression algorithm.
    # This finds the 'line of best fit' (y = mx + b) for the historical data.
    try:
        model = LinearRegression()
        model.fit(X, y)
    except Exception as e:
        print(f"Model training error: {e}")
        return None, None

    # --- 5. INFERENCE (Prediction) ---
    # We generate a list of the next 7 calendar dates.
    last_date = df_coin['date'].iloc[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, 8)]
    
    # We convert these future dates to Ordinals so the model can process them.
    future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    
    # The model predicts the price based on the historical trendline it learned.
    predictions = model.predict(future_ordinals)
    
    # Return the forecast dates and predicted prices to the UI for plotting.
    return future_dates, predictions