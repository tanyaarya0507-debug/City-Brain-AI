"""
Loads all CityBrain AI tables into pandas DataFrames and does a first-pass
inspection of each - shape, data types, and missing values.
This is the starting point for EDA (Week 3).
"""

import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

# Load each table into its own DataFrame
weather_df = pd.read_sql("SELECT * FROM weather WHERE city_id = 1", engine)
aqi_df = pd.read_sql("SELECT * FROM air_quality WHERE city_id = 1", engine)
aqi_df["o3"] = pd.to_numeric(aqi_df["o3"], errors="coerce")
traffic_df = pd.read_sql("SELECT * FROM traffic WHERE city_id = 1", engine)
electricity_df = pd.read_sql("SELECT * FROM electricity_usage WHERE city_id = 1", engine)
accidents_df = pd.read_sql("SELECT * FROM accidents WHERE city_id = 1", engine)

tables = {
    "Weather": weather_df,
    "Air Quality": aqi_df,
    "Traffic": traffic_df,
    "Electricity": electricity_df,
    "Accidents": accidents_df
}

for name, df in tables.items():
    print(f"\n{'='*50}")
    print(f"{name} — {len(df)} rows")
    print(f"{'='*50}")
    print(df.dtypes)
    print("\nMissing values per column:")
    print(df.isnull().sum())
    
# --- Correlation check: does vehicle count actually relate to speed? ---
print(f"\n{'='*50}")
print("Traffic: correlation between vehicle_count and avg_speed_kmph")
print(f"{'='*50}")
correlation = traffic_df["vehicle_count"].corr(traffic_df["avg_speed_kmph"])
print(f"Correlation coefficient: {correlation:.3f}")

# --- Electricity: weekday vs weekend average consumption ---
print(f"\n{'='*50}")
print("Electricity: average consumption by day type")
print(f"{'='*50}")
electricity_df["usage_date"] = pd.to_datetime(electricity_df["usage_date"])
electricity_df["is_weekend"] = electricity_df["usage_date"].dt.weekday >= 5
avg_by_day_type = electricity_df.groupby("is_weekend")["consumption_kwh"].mean()
print(avg_by_day_type)
 
# --- Accidents: how much worse are high-risk days? ---
print(f"\n{'='*50}")
print("Accidents: distribution of daily totals")
print(f"{'='*50}")
print(accidents_df["total_count"].describe())