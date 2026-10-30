"""
Loads weather + air_quality data from Supabase, merges them on hourly
timestamp, and performs EDA / correlation analysis for the City Brain AI
minor project.

Gap handling: the raw DB tables are NOT modified. This script reindexes
to a complete hourly timeline IN MEMORY only, so missing hours show up
explicitly as NaN rather than being silently skipped or invented. Short
gaps (<=3 hours) are linearly interpolated for analysis purposes; longer
gaps are left as missing and excluded from correlation/model steps.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sqlalchemy import create_engine
from scipy import stats

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
CITY_ID = 1

INTERPOLATION_LIMIT_HOURS = 3


def load_data(engine):
    weather_df = pd.read_sql(
        f"SELECT recorded_at, temperature, humidity, wind_speed, weather_condition "
        f"FROM weather WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    aqi_df = pd.read_sql(
        f"SELECT recorded_at, aqi_value, pm25, pm10, co, no2, so2, o3 "
        f"FROM air_quality WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    return weather_df, aqi_df


def dedupe_by_hour(df):
    """If any hour has multiple rows (leftover duplicates), keep only the first."""
    df = df.copy()
    df["hour"] = pd.to_datetime(df["recorded_at"]).dt.floor("h")
    df = df.drop_duplicates(subset="hour", keep="first")
    df = df.set_index("hour").drop(columns=["recorded_at"])
    return df


def reindex_and_interpolate(df, full_range):
    df = df.reindex(full_range)
    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].interpolate(
        method="linear", limit=INTERPOLATION_LIMIT_HOURS
    )
    return df


def main():
    engine = create_engine(DB_URL)

    print("Loading data from Supabase...")
    weather_df, aqi_df = load_data(engine)
    print(f"Raw rows — weather: {len(weather_df)}, air_quality: {len(aqi_df)}")

    weather_hourly = dedupe_by_hour(weather_df)
    aqi_hourly = dedupe_by_hour(aqi_df)
    print(f"After hourly de-dup — weather: {len(weather_hourly)}, air_quality: {len(aqi_hourly)}")

    # Build one complete hourly timeline spanning the full data range
    start = min(weather_hourly.index.min(), aqi_hourly.index.min())
    end = max(weather_hourly.index.max(), aqi_hourly.index.max())
    full_range = pd.date_range(start=start, end=end, freq="h")
    print(f"Full expected hourly range: {len(full_range)} hours ({start} to {end})")

    weather_full = reindex_and_interpolate(weather_hourly, full_range)
    aqi_full = reindex_and_interpolate(aqi_hourly, full_range)

    # Merge into one analysis-ready DataFrame
    merged = weather_full.join(aqi_full, how="inner")
    before_drop = len(merged)
    merged_clean = merged.dropna()
    print(f"Merged rows: {before_drop}, usable after dropping remaining NaN gaps: {len(merged_clean)}")

    # Save the analysis-ready dataset for reuse (does NOT touch the DB)
    merged_clean.to_csv("weather_aqi_merged.csv")
    print("Saved merged dataset to weather_aqi_merged.csv")

    # --- EDA ---
    numeric_cols = ["temperature", "humidity", "wind_speed",
                     "aqi_value", "pm25", "pm10", "co", "no2", "so2", "o3"]
    numeric_cols = [c for c in numeric_cols if c in merged_clean.columns]

    print("\nSummary statistics:")
    print(merged_clean[numeric_cols].describe())

    # Correlation matrix + heatmap
    corr = merged_clean[numeric_cols].corr(method="pearson")
    print("\nPearson correlation matrix:")
    print(corr.round(2))

    plt.figure(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Correlation: Weather vs Air Quality (Gwalior)")
    plt.tight_layout()
    plt.savefig("correlation_heatmap.png")
    print("Saved correlation_heatmap.png")

    # Key scatter plots: weather variables vs PM2.5 (and AQI)
    weather_vars = ["temperature", "humidity", "wind_speed"]
    for var in weather_vars:
        if var not in merged_clean.columns:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        sns.scatterplot(data=merged_clean, x=var, y="pm25", ax=axes[0])
        r, p = stats.pearsonr(merged_clean[var], merged_clean["pm25"])
        axes[0].set_title(f"{var} vs PM2.5 (r={r:.2f}, p={p:.3f})")

        sns.scatterplot(data=merged_clean, x=var, y="aqi_value", ax=axes[1])
        r2, p2 = stats.pearsonr(merged_clean[var], merged_clean["aqi_value"])
        axes[1].set_title(f"{var} vs AQI (r={r2:.2f}, p={p2:.3f})")

        plt.tight_layout()
        filename = f"scatter_{var}.png"
        plt.savefig(filename)
        print(f"Saved {filename}")

    print("\nDone. Review the printed correlation matrix and saved PNGs.")


if __name__ == "__main__":
    main()