"""
Generates a realistic sample electricity consumption dataset for Gwalior
(90 days), since this is explicitly sample/static data per project scope
- not a live feed.

Pattern built in on purpose (so EDA later finds something real to show):
- Higher consumption in summer (AC usage)
- Slightly higher on weekends
- Random day-to-day noise, like real usage data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)  # makes results reproducible - same "random" data every run

start_date = datetime(2026, 6, 1)
num_days = 90

records = []
for i in range(num_days):
    date = start_date + timedelta(days=i)

    # Base consumption
    base = 250

    # Summer months (June-July) have higher AC usage
    if date.month in [6, 7]:
        seasonal_boost = 60
    else:
        seasonal_boost = 20

    # Weekends slightly higher (more people home)
    weekend_boost = 15 if date.weekday() >= 5 else 0

    # Random daily noise
    noise = np.random.normal(0, 20)

    consumption = round(base + seasonal_boost + weekend_boost + noise, 2)
    consumption = max(consumption, 50)  # floor so we never get unrealistic negatives

    records.append({"usage_date": date.strftime("%Y-%m-%d"), "consumption_kwh": consumption})

df = pd.DataFrame(records)
df.to_csv("electricity_sample.csv", index=False)
print(f"Generated {len(df)} rows -> electricity_sample.csv")
print(df.head())