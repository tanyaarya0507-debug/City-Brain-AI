"""
Trains three secondary models for City Brain AI, extending the project
beyond weather/AQI into traffic, electricity, and accident data:

1. Energy demand model  — predicts daily electricity consumption from
   average daily temperature (daily granularity; small sample size).
2. Accident risk model  — predicts expected daily accident count from
   weather + traffic conditions (daily granularity; small sample size).
3. Commute speed model  — predicts average traffic speed from hour of
   day, weekday, and weather (hourly granularity; same rich sample size
   as the weather/AQI data, so this one is the most reliable of the three).

NOTE ON DATA SIZE: accidents and electricity_usage are daily tables,
so these two models train on far fewer rows than the AQI model. This
is disclosed here and should be disclosed in the report — treat these
as illustrative/proof-of-concept models, not production-grade.
"""

import os
import numpy as np
import pandas as pd
import joblib
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
CITY_ID = 1


def load_raw_tables(engine):
    weather = pd.read_sql(
        f"SELECT recorded_at, temperature, humidity, wind_speed, weather_condition "
        f"FROM weather WHERE city_id = {CITY_ID} ORDER BY recorded_at", engine)
    aqi = pd.read_sql(
        f"SELECT recorded_at, aqi_value, pm25 FROM air_quality WHERE city_id = {CITY_ID} ORDER BY recorded_at", engine)
    traffic = pd.read_sql(
        f"SELECT recorded_at, vehicle_count, avg_speed_kmph, congestion_level "
        f"FROM traffic WHERE city_id = {CITY_ID} ORDER BY recorded_at", engine)
    electricity = pd.read_sql(
        f"SELECT usage_date, consumption_kwh FROM electricity_usage WHERE city_id = {CITY_ID} ORDER BY usage_date", engine)
    accidents = pd.read_sql(
        f"SELECT accident_date, minor_count, major_count, fatal_count, total_count "
        f"FROM accidents WHERE city_id = {CITY_ID} ORDER BY accident_date", engine)
    return weather, aqi, traffic, electricity, accidents


def build_daily_dataset(weather, aqi, traffic, electricity, accidents):
    weather = weather.copy()
    weather["recorded_at"] = pd.to_datetime(weather["recorded_at"])
    weather["is_rain"] = weather["weather_condition"].str.contains("rain|drizzle|storm", case=False, na=False).astype(int)
    weather["date"] = weather["recorded_at"].dt.date

    daily_weather = weather.groupby("date").agg(
        avg_temp=("temperature", "mean"),
        avg_humidity=("humidity", "mean"),
        avg_wind=("wind_speed", "mean"),
        rain_hours=("is_rain", "sum")
    ).reset_index()
    daily_weather["is_rain_day"] = (daily_weather["rain_hours"] > 0).astype(int)

    traffic = traffic.copy()
    traffic["recorded_at"] = pd.to_datetime(traffic["recorded_at"])
    traffic["date"] = traffic["recorded_at"].dt.date
    traffic["is_high_congestion"] = (traffic["congestion_level"] == "High").astype(int)
    daily_traffic = traffic.groupby("date").agg(
        avg_vehicle_count=("vehicle_count", "mean"),
        avg_speed=("avg_speed_kmph", "mean"),
        high_congestion_hours=("is_high_congestion", "sum")
    ).reset_index()

    electricity = electricity.copy()
    electricity["date"] = pd.to_datetime(electricity["usage_date"]).dt.date

    accidents = accidents.copy()
    accidents["date"] = pd.to_datetime(accidents["accident_date"]).dt.date

    daily = daily_weather.merge(daily_traffic, on="date", how="inner") \
                          .merge(electricity[["date", "consumption_kwh"]], on="date", how="inner") \
                          .merge(accidents[["date", "total_count"]], on="date", how="inner")

    daily["date"] = pd.to_datetime(daily["date"])
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)

    return daily


def build_hourly_commute_dataset(weather, traffic):
    weather = weather.copy()
    weather["recorded_at"] = pd.to_datetime(weather["recorded_at"]).dt.floor("h")
    weather["is_rain"] = weather["weather_condition"].str.contains("rain|drizzle|storm", case=False, na=False).astype(int)

    traffic = traffic.copy()
    traffic["recorded_at"] = pd.to_datetime(traffic["recorded_at"]).dt.floor("h")

    merged = traffic.merge(weather[["recorded_at", "temperature", "is_rain"]], on="recorded_at", how="inner")
    merged = merged.set_index("recorded_at")
    merged["hour"] = merged.index.hour
    merged["day_of_week"] = merged.index.dayofweek
    merged["is_weekend"] = merged["day_of_week"].isin([5, 6]).astype(int)
    merged["hour_sin"] = np.sin(2 * np.pi * merged["hour"] / 24)
    merged["hour_cos"] = np.cos(2 * np.pi * merged["hour"] / 24)
    return merged.dropna()


def train_and_report(X, y, name, model_type="rf"):
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    if model_type == "rf":
        model = RandomForestRegressor(n_estimators=150, max_depth=5, random_state=42)
    else:
        model = LinearRegression()

    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"[{name}] n={len(X)}, train={len(X_train)}, test={len(X_test)} -> MAE={mae:.2f}, R2={r2:.3f}")
    return model, mae, r2


def main():
    engine = create_engine(DB_URL)
    weather, aqi, traffic, electricity, accidents = load_raw_tables(engine)

    daily = build_daily_dataset(weather, aqi, traffic, electricity, accidents)
    print(f"Daily joined dataset: {len(daily)} rows (limited by electricity/accidents daily granularity)")

    # --- 1. Energy demand model ---
    energy_features = ["avg_temp", "day_of_week", "is_weekend"]
    energy_model, e_mae, e_r2 = train_and_report(
        daily[energy_features], daily["consumption_kwh"], "Energy demand", model_type="linear")
    joblib.dump({"model": energy_model, "features": energy_features, "mae": e_mae, "r2": e_r2},
                "energy_model.pkl")

    # --- 2. Accident risk model ---
    accident_features = ["avg_temp", "avg_humidity", "is_rain_day", "avg_vehicle_count", "high_congestion_hours"]
    accident_model, a_mae, a_r2 = train_and_report(
        daily[accident_features], daily["total_count"], "Accident risk", model_type="rf")
    joblib.dump({"model": accident_model, "features": accident_features, "mae": a_mae, "r2": a_r2,
                 "training_totals": daily["total_count"].tolist()},
                "accident_model.pkl")

    # --- 3. Commute speed model (hourly — much larger sample) ---
    commute_df = build_hourly_commute_dataset(weather, traffic)
    commute_features = ["hour_sin", "hour_cos", "day_of_week", "is_weekend", "temperature", "is_rain"]
    commute_model, c_mae, c_r2 = train_and_report(
        commute_df[commute_features], commute_df["avg_speed_kmph"], "Commute speed", model_type="rf")
    joblib.dump({"model": commute_model, "features": commute_features, "mae": c_mae, "r2": c_r2},
                "commute_model.pkl")

    print("\nAll three secondary models saved: energy_model.pkl, accident_model.pkl, commute_model.pkl")


if __name__ == "__main__":
    main()