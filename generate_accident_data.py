"""
Generates realistic sample daily accident data for Gwalior (30 days).

Pattern built in on purpose:
- Slightly more accidents on weekdays (rush hour traffic)
- Occasional "high-risk days" (simulating rain/fog/festival traffic) with a spike
- Severity split: most accidents are minor, fatal ones are rare
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

    # Base accident count
    base = 3 if not is_weekend else 2

    # ~15% chance of a "high-risk day" (rain, fog, festival traffic etc.)
    is_high_risk_day = np.random.random() < 0.15
    if is_high_risk_day:
        base += np.random.randint(3, 6)

    total_count = max(int(base + np.random.normal(0, 1)), 0)

    # Severity split - most are minor, fatal ones are rare
    fatal_count = np.random.binomial(total_count, 0.05) if total_count > 0 else 0
    remaining = total_count - fatal_count
    major_count = np.random.binomial(remaining, 0.3) if remaining > 0 else 0
    minor_count = remaining - major_count

    records.append({
        "accident_date": current_date.strftime("%Y-%m-%d"),
        "minor_count": minor_count,
        "major_count": major_count,
        "fatal_count": fatal_count,
        "total_count": total_count
    })

df = pd.DataFrame(records)
df.to_csv("accidents_sample.csv", index=False)
print(f"Generated {len(df)} rows -> accidents_sample.csv")
print(df.head())