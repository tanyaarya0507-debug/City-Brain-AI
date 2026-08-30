"""
Quick test: confirms Python can talk to your Supabase Postgres database.
Run this after setting up .env with your real DATABASE_URL.
"""

from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise ValueError("DATABASE_URL not found — did you create a .env file from .env.example?")

engine = create_engine(DB_URL)

# Read the cities table
df = pd.read_sql("SELECT * FROM cities", engine)
print("Cities table:")
print(df)

# Confirm write access works too
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO weather (city_id, recorded_at, temperature, humidity, wind_speed, weather_condition)
        VALUES (1, NOW(), 33.0, 46.0, 9.5, 'Clear')
    """))
    conn.commit()

print("\nConnection test passed — read and write both work.")
