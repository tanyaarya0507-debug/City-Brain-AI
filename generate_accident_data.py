"""
Generates a sample daily accident dataset for Gwalior, with high-risk days
tied to REAL rain conditions pulled from the weather table — so a genuine,
learnable weather -> accident relationship exists for the accident risk
model to find (previously "high-risk day" was a pure 15% random chance,
completely disconnected from any feature the model could see, which made
the relationship fundamentally unlearnable regardless of dataset size).
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

    weather = pd.read_sql(
        f"SELECT recorded_at, weather_condition FROM weather WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    weather["date"] = pd.to_datetime(weather["recorded_at"]).dt.date
    weather["is_rain"] = weather["weather_condition"].str.contains(
        "rain|drizzle|storm|fog", case=False, na=False
    ).astype(int)
    daily_rain = weather.groupby("date")["is_rain"].max().reset_index()
    daily_rain.columns = ["date", "is_rain_day"]

    records = []
    for _, row in daily_rain.iterrows():
        date = pd.to_datetime(row["date"])
        is_weekend = date.weekday() >= 5
        is_rain_day = row["is_rain_day"] == 1

        base = 3 if not is_weekend else 2

        # High-risk boost now tied to REAL rain/fog conditions that day,
        # not a disconnected random coin flip
        if is_rain_day:
            base += np.random.randint(3, 6)

        total_count = max(int(base + np.random.normal(0, 1)), 0)

        fatal_count = np.random.binomial(total_count, 0.05) if total_count > 0 else 0
        remaining = total_count - fatal_count
        major_count = np.random.binomial(remaining, 0.3) if remaining > 0 else 0
        minor_count = remaining - major_count

        records.append({
            "accident_date": date.strftime("%Y-%m-%d"),
            "minor_count": minor_count,
            "major_count": major_count,
            "fatal_count": fatal_count,
            "total_count": total_count
        })

    df = pd.DataFrame(records)
    df.to_csv("accidents_sample.csv", index=False)
    print(f"Generated {len(df)} rows -> accidents_sample.csv (high-risk days driven by real rain/fog conditions)")
    print(df.head())


if __name__ == "__main__":
    main()