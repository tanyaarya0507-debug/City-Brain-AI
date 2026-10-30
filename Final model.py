"""
Trains the final Random Forest model (AQI prediction) on the full cleaned
dataset and saves it to disk so the Streamlit dashboard can load it
instantly without retraining every time it starts.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

DATA_PATH = "weather_aqi_merged.csv"
MODEL_PATH = "aqi_model.pkl"

FEATURES = ['temperature', 'humidity', 'wind_speed', 'hour_sin', 'hour_cos',
            'is_rush_hour', 'is_night', 'day_of_week', 'is_weekend',
            'aqi_lag_1h', 'aqi_lag_3h', 'pm25_lag_1h',
            'temp_rolling_3h', 'wind_rolling_3h', 'temp_change_1h']
TARGET = 'aqi_value'


def build_features(df):
    df = df.copy()
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    df['is_rush_hour'] = df['hour'].isin([7, 8, 9, 18, 19, 20]).astype(int)
    df['is_night'] = df['hour'].isin([0, 1, 2, 3, 4, 5]).astype(int)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['aqi_lag_1h'] = df['aqi_value'].shift(1)
    df['aqi_lag_3h'] = df['aqi_value'].shift(3)
    df['pm25_lag_1h'] = df['pm25'].shift(1)
    df['temp_rolling_3h'] = df['temperature'].rolling(3).mean()
    df['wind_rolling_3h'] = df['wind_speed'].rolling(3).mean()
    df['temp_change_1h'] = df['temperature'].diff(1)
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    df = df.dropna()  # lag/rolling features create NaN in the first few rows — drop them
    return df


def main():
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df = build_features(df)

    X = df[FEATURES]
    y = df[TARGET]
    split_idx = int(len(X) * 0.8)
    X_in, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_in, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)
    model.fit(X_in, y_in)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Final model — MAE: {mae:.2f}, R2: {r2:.3f}")

    joblib.dump({
        "model": model,
        "features": FEATURES,
        "mae": mae,
        "r2": r2
    }, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()