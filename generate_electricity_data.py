"""
Generates a sample electricity consumption dataset for Gwalior, driven by
REAL daily average temperature pulled from the weather table — so a
genuine, learnable temperature -> consumption relationship exists for
the energy demand model to find (previously this used calendar month as
a proxy for season, which had no connection to the model's actual
`avg_temp` feature, causing the model to fail no matter how much data
was added).
"""

import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
CITY_ID = 1

np.random.seed(42)


def main():
    engine = create_engine(DB_URL)

    # Pull real daily average temperature from the weather table
    weather = pd.read_sql(
        f"SELECT recorded_at, temperature FROM weather WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    weather["date"] = pd.to_datetime(weather["recorded_at"]).dt.date
    daily_temp = weather.groupby("date")["temperature"].mean().reset_index()
    daily_temp.columns = ["date", "avg_temp"]

    records = []
    for _, row in daily_temp.iterrows():
        date = pd.to_datetime(row["date"])
        avg_temp = row["avg_temp"]

        base = 250

        # Real temperature-driven AC load: every degree above 25C adds usage
        temp_boost = max(0, (avg_temp - 25) * 8)

        # Weekends slightly higher (more people home)
        weekend_boost = 15 if date.weekday() >= 5 else 0

        # Random daily noise, smaller now since temp_boost carries real signal
        noise = np.random.normal(0, 12)

        consumption = round(base + temp_boost + weekend_boost + noise, 2)
        consumption = max(consumption, 50)

        records.append({"usage_date": date.strftime("%Y-%m-%d"), "consumption_kwh": consumption})

    df = pd.DataFrame(records)
    df.to_csv("electricity_sample.csv", index=False)
    print(f"Generated {len(df)} rows -> electricity_sample.csv (driven by real daily avg temperature)")
    print(df.head())


if __name__ == "__main__":
    main()