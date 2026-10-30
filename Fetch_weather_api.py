"""
Fetches current weather for Gwalior from OpenWeatherMap and inserts it
into the weather table in Supabase.
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def fetch_and_store_weather():
    load_dotenv()
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    DB_URL = os.getenv("DATABASE_URL")

    # Step 1: Call the API
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Gwalior&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")

    data = response.json()

    # Step 2: Extract just the fields we need from the nested JSON
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    weather_condition = data["weather"][0]["description"]
    recorded_at = datetime.now()

    print(f"Fetched: {temperature}°C, {humidity}% humidity, wind {wind_speed} m/s, {weather_condition}")

    # Step 3: Insert into the database using a PARAMETERIZED query
    engine = create_engine(DB_URL)

    # Before inserting, check the most recent row to avoid duplicate entries
    with engine.connect() as conn:
        last_row = conn.execute(
            text("SELECT temperature, humidity, wind_speed, weather_condition FROM weather WHERE city_id = 1 ORDER BY recorded_at DESC LIMIT 1")
        ).fetchone()

    if (last_row and last_row.temperature == temperature and last_row.humidity == humidity
            and last_row.wind_speed == wind_speed and last_row.weather_condition == weather_condition):
        print("No new data since last fetch — skipping insert.")
        return

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO weather (city_id, recorded_at, temperature, humidity, wind_speed, weather_condition)
                VALUES (:city_id, :recorded_at, :temperature, :humidity, :wind_speed, :weather_condition)
            """),
            {
                "city_id": 1,
                "recorded_at": recorded_at,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "weather_condition": weather_condition
            }
        )
        conn.commit()

    print("Inserted successfully into weather table.")


if __name__ == "__main__":
    fetch_and_store_weather()