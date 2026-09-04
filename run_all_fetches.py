"""
Runs both weather and AQI fetch scripts together.
Meant to be triggered on a schedule (e.g. every 3-4 hours) via
Windows Task Scheduler, so real historical data accumulates over time.
"""

import subprocess
import sys
from datetime import datetime

print(f"\n=== Running scheduled fetch at {datetime.now()} ===")

print("\n-- Fetching weather --")
subprocess.run([sys.executable, "scripts/fetch_weather.py"])

print("\n-- Fetching AQI --")
subprocess.run([sys.executable, "scripts/fetch_aqi.py"])

print("\n=== Done ===\n")