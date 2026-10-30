"""
Fetches current air quality for Gwalior from OpenWeatherMap's Air Pollution API
and inserts it into the air_quality table in Supabase.
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def calculate_aqi_from_pm25(pm25):
    """EPA breakpoint formula — used since OpenWeatherMap's own AQI is on a
    1-5 scale, not the EPA 0-500 scale your DB/dashboard use."""
    if pm25 is None:
        return None
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ]
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return round((i_hi - i_lo) / (c_hi - c_lo) * (pm25 - c_lo) + i_lo)
    return None


def fetch_and_store_aqi():
    load_dotenv()
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    DB_URL = os.getenv("DATABASE_URL")

    # Step 1: Call the API
    lat = 26.2183
    lon = 78.1828
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")

    data = response.json()

    # Step 2: Extract fields
    reading = data["list"][0]
    components = reading["components"]

    pm25 = components.get("pm2_5")
    pm10 = components.get("pm10")
    co = components.get("co")
    no2 = components.get("no2")
    so2 = components.get("so2")
    o3 = components.get("o3")
    recorded_at = datetime.now()

    aqi_value = calculate_aqi_from_pm25(pm25)

    print(f"Fetched: AQI {aqi_value}, PM2.5 {pm25}, PM10 {pm10}, CO {co}, NO2 {no2}, SO2 {so2}, O3 {o3}")

    # Step 3: Insert into the database using a parameterized query
    engine = create_engine(DB_URL)

    # Before inserting, check the most recent row to avoid duplicate entries
    with engine.connect() as conn:
        last_row = conn.execute(
            text("SELECT pm25, pm10, co, no2, so2, o3 FROM air_quality WHERE city_id = 1 ORDER BY recorded_at DESC LIMIT 1")
        ).fetchone()

    if (last_row and last_row.pm25 == pm25 and last_row.pm10 == pm10
            and last_row.co == co and last_row.no2 == no2
            and last_row.so2 == so2 and last_row.o3 == o3):
        print("No new data since last fetch — skipping insert.")
        return

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


if __name__ == "__main__":
    fetch_and_store_aqi()