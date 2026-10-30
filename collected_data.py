"""
Fills the historical data gap for Gwalior (city_id = 1) using entirely
REAL data from Open-Meteo — both weather and air quality:
- Weather: Open-Meteo Forecast API (past_days)
- Air quality: Open-Meteo Air Quality API (CAMS atmospheric composition
  model — model-based, not raw ground-station readings, but real modeled
  data, not synthetic/random values)

Skips any hour already present in the DB, so it's safe to re-run without
creating duplicates alongside your existing live-collected rows.
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

CITY_ID = 1
LAT = 26.2183
LON = 78.1828
PAST_DAYS = 30

WEATHER_CODE_MAP = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 80: "rain showers", 95: "thunderstorm"
}


def fetch_real_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}&past_days={PAST_DAYS}"
        f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Open-Meteo weather call failed: {response.status_code} - {response.text}")

    hourly = response.json()["hourly"]
    times = hourly["time"]
    temps = hourly["temperature_2m"]
    humidity = hourly["relative_humidity_2m"]
    wind = hourly["wind_speed_10m"]
    codes = hourly.get("weathercode", [None] * len(times))

    rows = {}
    for i in range(len(times)):
        dt = datetime.fromisoformat(times[i])
        if dt > datetime.now():
            continue
        rows[dt] = {
            "city_id": CITY_ID,
            "recorded_at": dt,
            "temperature": temps[i],
            "humidity": humidity[i],
            "wind_speed": round(wind[i] / 3.6, 2) if wind[i] is not None else None,  # km/h -> m/s
            "weather_condition": WEATHER_CODE_MAP.get(codes[i], "unknown")
        }
    return rows


def fetch_real_aqi():
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={LAT}&longitude={LON}&past_days={PAST_DAYS}"
        f"&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Open-Meteo air-quality call failed: {response.status_code} - {response.text}")

    hourly = response.json()["hourly"]
    times = hourly["time"]
    pm10 = hourly["pm10"]
    pm25 = hourly["pm2_5"]
    co = hourly["carbon_monoxide"]
    no2 = hourly["nitrogen_dioxide"]
    so2 = hourly["sulphur_dioxide"]
    o3 = hourly["ozone"]
    us_aqi = hourly["us_aqi"]

    rows = {}
    for i in range(len(times)):
        dt = datetime.fromisoformat(times[i])
        if dt > datetime.now():
            continue
        rows[dt] = {
            "city_id": CITY_ID,
            "recorded_at": dt,
            "aqi_value": us_aqi[i],
            "pm25": pm25[i],
            "pm10": pm10[i],
            "co": co[i],
            "no2": no2[i],
            "so2": so2[i],
            "o3": o3[i]
        }
    return rows


def get_existing_timestamps(engine, table):
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT recorded_at FROM {table} WHERE city_id = :city_id"), {"city_id": CITY_ID})
        return {row.recorded_at.replace(minute=0, second=0, microsecond=0) for row in result}


def main():
    engine = create_engine(DB_URL)

    print("Fetching real historical weather from Open-Meteo...")
    weather_rows = fetch_real_weather()
    print(f"Got {len(weather_rows)} real hourly weather rows.")

    print("Fetching real historical air quality from Open-Meteo...")
    aqi_rows = fetch_real_aqi()
    print(f"Got {len(aqi_rows)} real hourly air_quality rows.")

    existing_weather_hours = get_existing_timestamps(engine, "weather")
    existing_aqi_hours = get_existing_timestamps(engine, "air_quality")

    new_weather = [r for dt, r in weather_rows.items()
                   if dt.replace(minute=0, second=0, microsecond=0) not in existing_weather_hours]
    new_aqi = [r for dt, r in aqi_rows.items()
               if dt.replace(minute=0, second=0, microsecond=0) not in existing_aqi_hours]

    print(f"Inserting {len(new_weather)} new weather rows (skipping already-covered hours)...")
    print(f"Inserting {len(new_aqi)} new air_quality rows (skipping already-covered hours)...")

    with engine.connect() as conn:
        for row in new_weather:
            conn.execute(
                text("""
                    INSERT INTO weather (city_id, recorded_at, temperature, humidity, wind_speed, weather_condition)
                    VALUES (:city_id, :recorded_at, :temperature, :humidity, :wind_speed, :weather_condition)
                """),
                row
            )
        for row in new_aqi:
            conn.execute(
                text("""
                    INSERT INTO air_quality (city_id, recorded_at, aqi_value, pm25, pm10, co, no2, so2, o3)
                    VALUES (:city_id, :recorded_at, :aqi_value, :pm25, :pm10, :co, :no2, :so2, :o3)
                """),
                row
            )
        conn.commit()

    print("Done. Historical gap filled with real weather + real (model-based) AQI data.")


if __name__ == "__main__":
    main()