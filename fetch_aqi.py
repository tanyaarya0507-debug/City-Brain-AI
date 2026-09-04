"""
Fetches current air quality for Gwalior from WAQI (World Air Quality Index)
and inserts it into the air_quality table in Supabase.
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
API_KEY = os.getenv("WAQI_API_KEY")
DB_URL = os.getenv("DATABASE_URL")

# Step 1: Call the API
url = f"https://api.waqi.info/feed/Gwalior/?token={API_KEY}"
response = requests.get(url)

if response.status_code != 200:
    raise Exception(f"API call failed: {response.status_code} - {response.text}")

data = response.json()

if data["status"] != "ok":
    raise Exception(f"WAQI returned an error: {data}")

# Step 2: Extract fields — using .get() with defaults since not every
# pollutant is always reported by every station
result = data["data"]
raw_aqi = result["aqi"]
# WAQI sometimes returns "-" instead of a number when the aggregate
# AQI isn't computed yet — store None in that case rather than crashing
aqi_value = raw_aqi if isinstance(raw_aqi, int) else None
iaqi = result.get("iaqi", {})

pm25 = iaqi.get("pm25", {}).get("v")
pm10 = iaqi.get("pm10", {}).get("v")
co = iaqi.get("co", {}).get("v")
no2 = iaqi.get("no2", {}).get("v")
so2 = iaqi.get("so2", {}).get("v")
o3 = iaqi.get("o3", {}).get("v")
recorded_at = datetime.now()

print(f"Fetched: AQI {aqi_value}, PM2.5 {pm25}, PM10 {pm10}, CO {co}, NO2 {no2}, SO2 {so2}, O3 {o3}")

# Step 3: Insert into the database using a parameterized query
engine = create_engine(DB_URL)

with engine.connect() as conn:
    conn.execute(
        text("""
            INSERT INTO air_quality (city_id, recorded_at, aqi_value, pm25, pm10, co, no2, so2, o3)
            VALUES (:city_id, :recorded_at, :aqi_value, :pm25, :pm10, :co, :no2, :so2, :o3)
        """),
        {
            "city_id": 1,
            "recorded_at": recorded_at,
            "aqi_value": aqi_value,
            "pm25": pm25,
            "pm10": pm10,
            "co": co,
            "no2": no2,
            "so2": so2,
            "o3": o3
        }
    )
    conn.commit()

print("Inserted successfully into air_quality table.")