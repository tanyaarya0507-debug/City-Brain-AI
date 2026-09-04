"""
Loads traffic_sample.csv into the traffic table.
"""

import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

df = pd.read_csv("traffic_sample.csv")
df["city_id"] = 1

engine = create_engine(DB_URL)
df.to_sql("traffic", engine, if_exists="append", index=False)

print(f"Loaded {len(df)} rows into traffic table.")