import time
from datetime import datetime
from fetch_aqi import fetch_and_store_aqi
from Fetch_weather_api import fetch_and_store_weather 

INTERVAL_SECONDS = 60 * 60  # every 1 hour

def run_forever():
    while True:
        try:
            print(f"\n--- Run started at {datetime.now()} ---")
            fetch_and_store_aqi()
            fetch_and_store_weather()
        except Exception as e:
            print(f"Error during collection: {e}")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_forever()