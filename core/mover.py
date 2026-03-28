import os
import shutil

base_dir = r"c:/Users/Asus/Downloads/crypto-portfolio-manager-20260315T081555Z-3-001/crypto-portfolio-manager"
core_dir = os.path.join(base_dir, "core")
data_dir = os.path.join(base_dir, "data")

os.makedirs(core_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

core_files = ["collect_data.py", "fetch_historical.py", "risk_engine.py", "parallel_risk.py", "investment_mix_calculator.py", "test_investment_mix.py"]
data_files = ["crypto.db", "market_snapshot.csv", "eda_coins.csv", "historical_prices.csv"]

for f in core_files:
    src = os.path.join(base_dir, f)
    dst = os.path.join(core_dir, f)
    if os.path.exists(src):
        shutil.move(src, dst)

for f in data_files:
    src = os.path.join(base_dir, f)
    dst = os.path.join(data_dir, f)
    if os.path.exists(src):
        shutil.move(src, dst)

print("Moved files successfully.")
