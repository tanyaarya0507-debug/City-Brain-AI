"""
Generates realistic sample hourly traffic data for Gwalior (30 days),
since this is explicitly sample/static data per project scope.

Pattern built in on purpose:
- Morning rush hour: 8-10 AM
- Evening rush hour: 5-8 PM
- Lower traffic on weekends
- Congestion level derived from vehicle count (not random - it's a
  real relationship: more vehicles = slower speed = more congestion)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

start_date = datetime(2026, 8, 5)
num_days = 30

records = []
for day in range(num_days):
    current_date = start_date + timedelta(days=day)
    is_weekend = current_date.weekday() >= 5

    for hour in range(24):
        # Base vehicle count depends on time of day
        if hour in [8, 9]:  # morning rush
            base_count = 850
        elif hour in [17, 18, 19]:  # evening rush
            base_count = 900
        elif 22 <= hour or hour <= 5:  # late night
            base_count = 100
        else:  # regular daytime
            base_count = 400

        # Weekends have less traffic overall
        if is_weekend:
            base_count = int(base_count * 0.6)

        # Random noise
        vehicle_count = max(int(base_count + np.random.normal(0, 40)), 20)

        # Speed decreases as vehicle count increases (real relationship,
        # not independent random data)
        avg_speed = round(max(60 - (vehicle_count / 25), 8) + np.random.normal(0, 2), 1)

        # Congestion level derived from vehicle count thresholds
        if vehicle_count > 700:
            congestion = "High"
        elif vehicle_count > 350:
            congestion = "Medium"
        else:
            congestion = "Low"

        recorded_at = current_date.replace(hour=hour, minute=0, second=0)

        records.append({
            "recorded_at": recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "vehicle_count": vehicle_count,
            "avg_speed_kmph": avg_speed,
            "congestion_level": congestion
        })

df = pd.DataFrame(records)
df.to_csv("traffic_sample.csv", index=False)
print(f"Generated {len(df)} rows -> traffic_sample.csv")
print(df.head())