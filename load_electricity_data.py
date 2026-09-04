"""
Loads electricity_sample.csv into the electricity_usage table.
Uses pandas .to_sql() - a bulk-load method, different from the
row-by-row parameterized INSERT used in fetch_weather.py / fetch_aqi.py.
"""

import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# Step 1: Read the CSV
df = pd.read_csv("electricity_sample.csv")

# Step 2: Add city_id - all rows belong to Gwalior (city_id = 1)
df["city_id"] = 1

# Step 3: Bulk load into Postgres
engine = create_engine(DB_URL)
df.to_sql("electricity_usage", engine, if_exists="append", index=False)

print(f"Loaded {len(df)} rows into electricity_usage table.")