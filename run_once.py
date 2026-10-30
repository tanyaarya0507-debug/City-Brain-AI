"""
Runs a single round of data collection: fetches AQI and weather once,
inserts into Supabase, then exits. Intended to be triggered repeatedly
by Windows Task Scheduler rather than looping internally.
"""

from datetime import datetime
from fetch_aqi import fetch_and_store_aqi
from Fetch_weather_api import fetch_and_store_weather

if __name__ == "__main__":
    print(f"\n--- Run started at {datetime.now()} ---")
    try:
        fetch_and_store_aqi()
    except Exception as e:
        print(f"Error fetching AQI: {e}")

    try:
        fetch_and_store_weather()
    except Exception as e:
        print(f"Error fetching weather: {e}")

    print(f"--- Run finished at {datetime.now()} ---")