"""
Loads accidents_sample.csv into the accidents table.
"""

import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

df = pd.read_csv("accidents_sample.csv")
df["city_id"] = 1

engine = create_engine(DB_URL)
df.to_sql("accidents", engine, if_exists="append", index=False)

print(f"Loaded {len(df)} rows into accidents table.")