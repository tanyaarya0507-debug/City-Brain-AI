"""
City Brain AI — Streamlit Dashboard
Environmental Dark theme with a city-skyline hero banner, richer status
cards, and a more filled-out layout on top of the existing data pipeline,
correlation analysis, insight panel, and What-If AQI predictor.
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import joblib
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
CITY_ID = 1

st.set_page_config(page_title="City Brain AI — Gwalior", layout="wide", page_icon="🌆")

TEAL = "#1D9E75"
TEAL_LIGHT = "#5DCAA5"
AMBER = "#EF9F27"
RED = "#E24B4A"
BLUE_GRAY = "#7FB8C4"
NAVY = "#0B1220"
CARD = "#101B2D"
BORDER = "#1D3A4A"

# --- Global theme CSS ---
st.markdown(f"""
<style>
    div[data-testid="stMetric"] {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1rem 1.2rem;
    }}
    div[data-testid="stMetricLabel"] {{ color: {BLUE_GRAY}; }}
    div[data-testid="stMetricValue"] {{ color: {TEAL_LIGHT}; }}
    h2, h3 {{
        color: #E6F1FB !important;
        border-left: 3px solid {TEAL};
        padding-left: 10px;
    }}
    .stMarkdown p {{ color: #C7D9E0; }}
    .stCaption, [data-testid="stCaptionContainer"] {{ color: #6B8794 !important; }}
    .cb-badge {{
        display: inline-block;
        background: rgba(29,158,117,0.15);
        color: {TEAL_LIGHT};
        border: 1px solid {TEAL};
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 13px;
        margin-right: 8px;
    }}
    .cb-section-icon {{
        font-size: 22px;
        margin-right: 6px;
    }}
</style>
""", unsafe_allow_html=True)

# --- Skyline hero banner (self-contained SVG, no external assets) ---
skyline_svg = f"""
<div style="position:relative; border-radius:16px; overflow:hidden; margin-bottom:1.5rem;
            border:1px solid {BORDER}; background: linear-gradient(180deg, #0F2038 0%, {NAVY} 70%);">
  <svg viewBox="0 0 1200 220" preserveAspectRatio="none" style="width:100%; height:180px; display:block;">
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0F2038"/>
        <stop offset="100%" stop-color="#0B1220"/>
      </linearGradient>
    </defs>
    <rect width="1200" height="220" fill="url(#sky)"/>
    <circle cx="1040" cy="55" r="30" fill="#16324a" opacity="0.7"/>
    <g fill="#0E1B2E" opacity="0.95">
      <rect x="20" y="120" width="60" height="100"/>
      <rect x="90" y="90" width="45" height="130"/>
      <rect x="145" y="140" width="70" height="80"/>
      <rect x="225" y="70" width="50" height="150"/>
      <rect x="285" y="110" width="60" height="110"/>
      <rect x="355" y="60" width="40" height="160"/>
      <rect x="405" y="130" width="80" height="90"/>
      <rect x="495" y="95" width="55" height="125"/>
      <rect x="560" y="140" width="65" height="80"/>
      <rect x="635" y="75" width="45" height="145"/>
      <rect x="690" y="115" width="70" height="105"/>
      <rect x="770" y="55" width="50" height="165"/>
      <rect x="830" y="125" width="60" height="95"/>
      <rect x="900" y="90" width="45" height="130"/>
      <rect x="955" y="140" width="75" height="80"/>
      <rect x="1040" y="100" width="50" height="120"/>
      <rect x="1100" y="70" width="55" height="150"/>
      <rect x="1165" y="130" width="35" height="90"/>
    </g>
    <g fill="{TEAL_LIGHT}" opacity="0.85">
      <rect x="35" y="140" width="6" height="6"/><rect x="55" y="160" width="6" height="6"/>
      <rect x="100" y="110" width="6" height="6"/><rect x="115" y="150" width="6" height="6"/>
      <rect x="235" y="90" width="6" height="6"/><rect x="250" y="130" width="6" height="6"/>
      <rect x="365" y="80" width="6" height="6"/><rect x="378" y="120" width="6" height="6"/>
      <rect x="510" y="115" width="6" height="6"/><rect x="525" y="155" width="6" height="6"/>
      <rect x="645" y="95" width="6" height="6"/><rect x="658" y="135" width="6" height="6"/>
      <rect x="785" y="75" width="6" height="6"/><rect x="798" y="115" width="6" height="6"/>
      <rect x="915" y="110" width="6" height="6"/><rect x="928" y="150" width="6" height="6"/>
      <rect x="1055" y="120" width="6" height="6"/><rect x="1115" y="90" width="6" height="6"/>
    </g>
  </svg>
  <div style="position:absolute; bottom:0; left:0; right:0; padding:1.2rem 1.6rem 1.4rem;
              background: linear-gradient(180deg, rgba(11,18,32,0) 0%, rgba(11,18,32,0.92) 60%);">
    <div style="font-size:30px; font-weight:600; color:#E6F1FB;">🌆 City Brain AI</div>
    <div style="font-size:15px; color:{BLUE_GRAY}; margin-top:4px;">
      Live urban intelligence for Gwalior — weather, air quality &amp; ML-based AQI prediction
    </div>
  </div>
</div>
"""
st.markdown(skyline_svg, unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_data():
    engine = create_engine(DB_URL)
    weather = pd.read_sql(
        f"SELECT recorded_at, temperature, humidity, wind_speed, weather_condition "
        f"FROM weather WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    aqi = pd.read_sql(
        f"SELECT recorded_at, aqi_value, pm25, pm10, co, no2, so2, o3 "
        f"FROM air_quality WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    weather["hour"] = pd.to_datetime(weather["recorded_at"]).dt.floor("h")
    aqi["hour"] = pd.to_datetime(aqi["recorded_at"]).dt.floor("h")
    weather = weather.drop_duplicates(subset="hour", keep="first").set_index("hour")
    aqi = aqi.drop_duplicates(subset="hour", keep="first").set_index("hour")
    merged = weather.join(aqi, how="inner", lsuffix="_w").dropna()
    return merged


@st.cache_resource
def load_model():
    return joblib.load("aqi_model.pkl")


@st.cache_resource
def load_secondary_models():
    return {
        "energy": joblib.load("energy_model.pkl"),
        "accident": joblib.load("accident_model.pkl"),
        "commute": joblib.load("commute_model.pkl"),
    }


@st.cache_data(ttl=600)
def load_secondary_daily_data():
    """Loads traffic, electricity, and accident data and builds the same
    daily-aggregated view used to train the secondary models, so the
    dashboard's live values match what each model was actually trained on."""
    engine = create_engine(DB_URL)

    weather = pd.read_sql(
        f"SELECT recorded_at, temperature, weather_condition FROM weather WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    weather["recorded_at"] = pd.to_datetime(weather["recorded_at"])
    weather["is_rain"] = weather["weather_condition"].str.contains("rain|drizzle|storm|fog", case=False, na=False).astype(int)
    weather["date"] = weather["recorded_at"].dt.date
    daily_weather = weather.groupby("date").agg(
        avg_temp=("temperature", "mean"), rain_hours=("is_rain", "sum")
    ).reset_index()
    daily_weather["is_rain_day"] = (daily_weather["rain_hours"] > 0).astype(int)

    traffic = pd.read_sql(
        f"SELECT recorded_at, vehicle_count, avg_speed_kmph, congestion_level FROM traffic WHERE city_id = {CITY_ID} ORDER BY recorded_at",
        engine
    )
    traffic["recorded_at"] = pd.to_datetime(traffic["recorded_at"])
    traffic["date"] = traffic["recorded_at"].dt.date
    traffic["is_high_congestion"] = (traffic["congestion_level"] == "High").astype(int)
    daily_traffic = traffic.groupby("date").agg(
        avg_vehicle_count=("vehicle_count", "mean"),
        avg_speed=("avg_speed_kmph", "mean"),
        high_congestion_hours=("is_high_congestion", "sum")
    ).reset_index()

    electricity = pd.read_sql(
        f"SELECT usage_date, consumption_kwh FROM electricity_usage WHERE city_id = {CITY_ID} ORDER BY usage_date", engine)
    electricity["date"] = pd.to_datetime(electricity["usage_date"]).dt.date

    accidents = pd.read_sql(
        f"SELECT accident_date, total_count FROM accidents WHERE city_id = {CITY_ID} ORDER BY accident_date", engine)
    accidents["date"] = pd.to_datetime(accidents["accident_date"]).dt.date

    daily = daily_weather.merge(daily_traffic, on="date", how="inner") \
                          .merge(electricity[["date", "consumption_kwh"]], on="date", how="inner") \
                          .merge(accidents[["date", "total_count"]], on="date", how="inner")
    daily["date"] = pd.to_datetime(daily["date"])
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)
    return daily.sort_values("date").reset_index(drop=True)


def build_features(df):
    df = df.copy()
    df["hour_num"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["is_rush_hour"] = df["hour_num"].isin([7, 8, 9, 18, 19, 20]).astype(int)
    df["is_night"] = df["hour_num"].isin([0, 1, 2, 3, 4, 5]).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_num"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_num"] / 24)
    df['aqi_lag_1h'] = df['aqi_value'].shift(1)
    df['aqi_lag_3h'] = df['aqi_value'].shift(3)
    df['pm25_lag_1h'] = df['pm25'].shift(1)
    df['temp_rolling_3h'] = df['temperature'].rolling(3).mean()
    df['wind_rolling_3h'] = df['wind_speed'].rolling(3).mean()
    df['temp_change_1h'] = df['temperature'].diff(1)
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    return df


def get_health_advice(aqi, conditions=None, activity="general"):
    """
    conditions: list of strings from
        ["asthma", "heart_disease", "elderly", "children", "pregnant", "outdoor_worker"]
    activity: one of "general", "exercise", "commute"
    """
    conditions = conditions or []

    if aqi <= 50:
        band = "good"
        headline = "Air quality is good."
    elif aqi <= 100:
        band = "moderate"
        headline = "Moderate air quality — generally acceptable."
    elif aqi <= 150:
        band = "sensitive"
        headline = "Unhealthy for sensitive groups."
    elif aqi <= 200:
        band = "unhealthy"
        headline = "Unhealthy air quality."
    else:
        band = "hazardous"
        headline = "Hazardous air quality."

    tips = []

    # --- Activity-specific advice ---
    activity_advice = {
        "good":       {"exercise": "Great day for outdoor exercise or sport.",
                        "commute": "Safe to walk or cycle to work/school.",
                        "general": "No precautions needed."},
        "moderate":   {"exercise": "Outdoor exercise is fine; unusually sensitive individuals may notice mild symptoms.",
                        "commute": "Walking/cycling is fine for most people.",
                        "general": "No precautions needed for most people."},
        "sensitive":  {"exercise": "Reduce prolonged or intense outdoor exertion; consider indoor exercise instead.",
                        "commute": "Consider a mask (N95) if commuting outdoors for a long time.",
                        "general": "Limit prolonged outdoor exposure if you're in a sensitive group."},
        "unhealthy":  {"exercise": "Avoid outdoor exercise. Move workouts indoors.",
                        "commute": "Wear an N95 mask if you must go outside; minimize time outdoors.",
                        "general": "Everyone should reduce prolonged outdoor exertion."},
        "hazardous":  {"exercise": "Do not exercise outdoors under any circumstances.",
                        "commute": "Avoid going outside unless essential; wear an N95 mask if you must.",
                        "general": "Stay indoors with windows closed; use an air purifier if available."}
    }
    tips.append(activity_advice[band][activity])

    # --- Condition-specific advice ---
    if "asthma" in conditions and band in ("sensitive", "unhealthy", "hazardous"):
        tips.append("Keep rescue inhaler accessible; avoid outdoor triggers today.")
    if "heart_disease" in conditions and band in ("unhealthy", "hazardous"):
        tips.append("Avoid strenuous activity — poor air quality raises cardiovascular strain.")
    if "elderly" in conditions and band in ("sensitive", "unhealthy", "hazardous"):
        tips.append("Elderly individuals should minimize outdoor time and stay hydrated.")
    if "children" in conditions and band in ("sensitive", "unhealthy", "hazardous"):
        tips.append("Keep children indoors during peak pollution hours (typically morning/evening).")
    if "pregnant" in conditions and band in ("unhealthy", "hazardous"):
        tips.append("Pregnant individuals should avoid outdoor exposure — consult a doctor if symptoms occur.")
    if "outdoor_worker" in conditions and band in ("sensitive", "unhealthy", "hazardous"):
        tips.append("Take frequent indoor breaks; wear a mask rated for particulate filtration.")

    return headline, tips


def aqi_badge(aqi):
    if aqi <= 50:
        return "Good", TEAL_LIGHT
    elif aqi <= 100:
        return "Moderate", AMBER
    elif aqi <= 150:
        return "Unhealthy (Sensitive)", AMBER
    else:
        return "Unhealthy", RED


def generate_insights(df, correlations):
    insights = []
    if len(df) < 48:
        insights.append("Not enough data yet to compare recent trends — check back once more hours of data have been collected.")
        return insights

    recent = df.tail(24)
    previous = df.iloc[-48:-24]

    def pct_change(new, old):
        return 0 if old == 0 else ((new - old) / abs(old)) * 100

    aqi_change = pct_change(recent["aqi_value"].mean(), previous["aqi_value"].mean())
    temp_change = recent["temperature"].mean() - previous["temperature"].mean()
    wind_change = recent["wind_speed"].mean() - previous["wind_speed"].mean()
    humidity_change = recent["humidity"].mean() - previous["humidity"].mean()

    if abs(aqi_change) < 3:
        insights.append(f"AQI has stayed roughly stable over the last 24 hours "
                         f"(avg {recent['aqi_value'].mean():.0f}, previous 24h avg {previous['aqi_value'].mean():.0f}).")
    else:
        direction = "risen" if aqi_change > 0 else "fallen"
        insights.append(f"AQI has {direction} {abs(aqi_change):.0f}% compared to the previous 24-hour period "
                         f"(now averaging {recent['aqi_value'].mean():.0f}, was {previous['aqi_value'].mean():.0f}).")

    wind_corr = correlations.loc["wind_speed", "aqi_value"] if "wind_speed" in correlations.index else None
    temp_corr = correlations.loc["temperature", "aqi_value"] if "temperature" in correlations.index else None

    if abs(wind_change) > 0.5 and wind_corr is not None:
        direction = "increased" if wind_change > 0 else "decreased"
        expected_effect = "typically lowers AQI" if wind_corr < 0 else "typically raises AQI"
        insights.append(f"Wind speed has {direction} by {abs(wind_change):.1f} m/s — in this dataset, "
                         f"higher wind speed {expected_effect} (r={wind_corr:.2f}).")

    if abs(temp_change) > 1 and temp_corr is not None:
        direction = "risen" if temp_change > 0 else "dropped"
        expected_effect = "typically raises AQI" if temp_corr > 0 else "typically lowers AQI"
        insights.append(f"Temperature has {direction} by {abs(temp_change):.1f}°C — higher temperature "
                         f"{expected_effect} in this dataset (r={temp_corr:.2f}).")

    if abs(humidity_change) > 5:
        direction = "increased" if humidity_change > 0 else "decreased"
        insights.append(f"Humidity has {direction} by {abs(humidity_change):.0f} percentage points "
                         f"compared to the prior 24 hours.")

    worst_hour = recent["aqi_value"].idxmax()
    insights.append(f"The worst air quality in the last 24 hours was recorded around "
                     f"{worst_hour.strftime('%I %p on %b %d')}, with AQI reaching {recent['aqi_value'].max():.0f}.")

    return insights


df = load_data()
latest = df.iloc[-1]
badge_label, badge_color = aqi_badge(latest["aqi_value"])

# --- Status badges row ---
st.markdown(f"""
<div style="margin-bottom:1.2rem;">
  <span class="cb-badge">📍 Gwalior, MP</span>
  <span class="cb-badge" style="color:{badge_color}; border-color:{badge_color};">● {badge_label}</span>
  <span class="cb-badge">🕒 Updated {latest.name.strftime('%d %b, %I:%M %p')}</span>
  <span class="cb-badge">📊 {len(df)} hourly records</span>
</div>
""", unsafe_allow_html=True)

# --- Top-line current status ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest AQI", f"{latest['aqi_value']:.0f}")
col2.metric("PM2.5", f"{latest['pm25']:.1f} µg/m³")
col3.metric("Temperature", f"{latest['temperature']:.1f} °C")
col4.metric("Humidity", f"{latest['humidity']:.0f}%")

st.markdown("---")

# --- Live map ---
st.subheader("🗺️ Live Location")
st.caption("Marker color reflects current AQI severity")

GWALIOR_LAT, GWALIOR_LON = 26.2183, 78.1828
map_df = pd.DataFrame([{
    "lat": GWALIOR_LAT, "lon": GWALIOR_LON,
    "label": f"Gwalior — AQI {latest['aqi_value']:.0f} ({badge_label})"
}])
fig_map = px.scatter_map(
    map_df, lat="lat", lon="lon", hover_name="label",
    color_discrete_sequence=[badge_color], zoom=11, height=380,
    center={"lat": GWALIOR_LAT, "lon": GWALIOR_LON}
)
fig_map.update_traces(marker=dict(size=22))
fig_map.update_layout(map_style="dark", margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor=NAVY)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# --- Interactive trend charts ---
st.subheader("📈 Historical trends")
st.caption("Zoom by dragging, hover for exact values, double-click to reset")

date_range = st.select_slider(
    "Show data from",
    options=["Last 24h", "Last 3 days", "Last 7 days", "Full range"],
    value="Last 7 days"
)
range_map = {"Last 24h": 24, "Last 3 days": 72, "Last 7 days": 168, "Full range": len(df)}
plot_df = df.tail(range_map[date_range]).reset_index()
plot_df["temperature_smooth"] = plot_df["temperature"].rolling(window=3, center=True).mean()
plot_df["humidity_smooth"] = plot_df["humidity"].rolling(window=3, center=True).mean()

tab1, tab2 = st.tabs(["AQI & PM2.5", "Weather"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df["hour"], y=plot_df["aqi_value"],
                              mode="lines", name="AQI", line=dict(color=AMBER, width=2)))
    fig.add_trace(go.Scatter(x=plot_df["hour"], y=plot_df["pm25"],
                              mode="lines", name="PM2.5", line=dict(color=TEAL_LIGHT, width=2)))
    fig.update_layout(
        hovermode="x unified", height=420,
        xaxis_title="Time", yaxis_title="Value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        paper_bgcolor=NAVY, plot_bgcolor=NAVY,
        font=dict(color="#C7D9E0"),
        xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df["hour"], y=plot_df["temperature_smooth"],
                              mode="lines", name="Temperature (°C)", line=dict(color=AMBER, width=2)))
    fig.add_trace(go.Scatter(x=plot_df["hour"], y=plot_df["humidity_smooth"],
                              mode="lines", name="Humidity (%)", line=dict(color=TEAL_LIGHT, width=2),
                              yaxis="y2"))
    fig.update_layout(
        hovermode="x unified", height=420,
        xaxis_title="Time",
        yaxis=dict(title="Temperature (°C)", gridcolor=BORDER),
        yaxis2=dict(title="Humidity (%)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        paper_bgcolor=NAVY, plot_bgcolor=NAVY,
        font=dict(color="#C7D9E0")
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- AQI Forecast ---
st.subheader("🔭 6-Hour AQI Forecast")
st.caption("Recursive prediction using the model's own lag features. Assumes near-term weather "
           "stays close to current conditions — a short-term indicative trend, not a precise forecast.")

def forecast_aqi(df, model, features, hours_ahead=6):
    last_row = df.iloc[-1]
    last_temp, last_humidity, last_wind, last_pm25 = (
        last_row["temperature"], last_row["humidity"], last_row["wind_speed"], last_row["pm25"]
    )
    aqi_history = list(df["aqi_value"].tail(3))
    current_time = df.index[-1]
    forecasts = []
    for step in range(1, hours_ahead + 1):
        future_time = current_time + pd.Timedelta(hours=step)
        hour, dow = future_time.hour, future_time.dayofweek
        row = {
            "temperature": last_temp, "humidity": last_humidity, "wind_speed": last_wind,
            "hour_sin": np.sin(2 * np.pi * hour / 24), "hour_cos": np.cos(2 * np.pi * hour / 24),
            "is_rush_hour": 1 if hour in (7, 8, 9, 18, 19, 20) else 0,
            "is_night": 1 if hour in (0, 1, 2, 3, 4, 5) else 0,
            "day_of_week": dow, "is_weekend": 1 if dow in (5, 6) else 0,
            "aqi_lag_1h": aqi_history[-1],
            "aqi_lag_3h": aqi_history[-3] if len(aqi_history) >= 3 else aqi_history[0],
            "pm25_lag_1h": last_pm25, "temp_rolling_3h": last_temp, "wind_rolling_3h": last_wind,
            "temp_change_1h": 0
        }
        X_future = pd.DataFrame([row])[features]
        pred_aqi = model.predict(X_future)[0]
        forecasts.append({"time": future_time, "predicted_aqi": pred_aqi})
        aqi_history.append(pred_aqi)
        if len(aqi_history) > 3:
            aqi_history.pop(0)
    return pd.DataFrame(forecasts)

_model_bundle = load_model()
forecast_df = forecast_aqi(df, _model_bundle["model"], _model_bundle["features"], hours_ahead=6)

fig = go.Figure()
recent_actual = df.tail(12).reset_index()
fig.add_trace(go.Scatter(x=recent_actual["hour"], y=recent_actual["aqi_value"],
                          mode="lines+markers", name="Actual AQI", line=dict(color=TEAL_LIGHT, width=2)))
fig.add_trace(go.Scatter(x=forecast_df["time"], y=forecast_df["predicted_aqi"],
                          mode="lines+markers", name="Forecast", line=dict(color=AMBER, width=2, dash="dash")))
fig.update_layout(
    hovermode="x unified", height=380, xaxis_title="Time", yaxis_title="AQI",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    paper_bgcolor=NAVY, plot_bgcolor=NAVY, font=dict(color="#C7D9E0"),
    xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER)
)
st.plotly_chart(fig, use_container_width=True)

fcol1, fcol2, fcol3 = st.columns(3)
fcol1.metric("Next hour", f"{forecast_df['predicted_aqi'].iloc[0]:.0f}")
fcol2.metric("In 3 hours", f"{forecast_df['predicted_aqi'].iloc[2]:.0f}")
fcol3.metric("In 6 hours", f"{forecast_df['predicted_aqi'].iloc[5]:.0f}")

st.markdown("---")

# --- Interactive correlation heatmap ---
st.subheader("🔗 Correlation: weather vs air quality")
st.caption("Hover over any cell to see the exact correlation value")
numeric_cols = ["temperature", "humidity", "wind_speed", "aqi_value", "pm25", "pm10", "co", "no2", "so2", "o3"]
corr = df[numeric_cols].corr(method="pearson")

fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="Tealrose", zmin=-1, zmax=1, aspect="auto")
fig.update_layout(height=500, paper_bgcolor=NAVY, plot_bgcolor=NAVY, font=dict(color="#C7D9E0"))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Auto-Generated Insight Panel ---
st.subheader("🧠 Insights")
st.caption("Automatically generated from the last 24 hours vs. the prior 24 hours")

insight_lines = generate_insights(df, corr)
for line in insight_lines:
    st.markdown(f"<p style='color:#C7D9E0; padding:6px 0;'>▸ {line}</p>", unsafe_allow_html=True)

st.markdown("---")

# --- AQI Prediction tool (What-If Simulator) ---
st.subheader("🔮 What-if AQI predictor")
st.caption("Adjust weather conditions to see the model's predicted AQI")

model_bundle = load_model()
model = model_bundle["model"]
features = model_bundle["features"]

pcol1, pcol2, pcol3 = st.columns(3)
temp_input = pcol1.slider("Temperature (°C)", 15.0, 45.0, float(df["temperature"].mean()))
humidity_input = pcol2.slider("Humidity (%)", 0, 100, int(df["humidity"].mean()))
wind_input = pcol3.slider("Wind Speed (m/s)", 0.0, 15.0, float(df["wind_speed"].mean()))

pcol4, pcol5 = st.columns(2)
hour_input = pcol4.slider("Hour of Day", 0, 23, 12)
day_input = pcol5.selectbox("Day of Week", options=list(range(7)),
                             format_func=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][x])

hour_sin = np.sin(2 * np.pi * hour_input / 24)
hour_cos = np.cos(2 * np.pi * hour_input / 24)
is_rush_hour = 1 if hour_input in (7, 8, 9, 18, 19, 20) else 0
is_night = 1 if hour_input in (0, 1, 2, 3, 4, 5) else 0

# Pull the actual most recent AQI/PM2.5 values to use as lag context —
# a hypothetical scenario can't invent history, so we anchor to reality
latest_aqi = df["aqi_value"].iloc[-1]
latest_aqi_3h_ago = df["aqi_value"].iloc[-3] if len(df) >= 3 else latest_aqi
latest_pm25 = df["pm25"].iloc[-1]
is_weekend_input = 1 if day_input in (5, 6) else 0

input_row = pd.DataFrame([{
    "temperature": temp_input,
    "humidity": humidity_input,
    "wind_speed": wind_input,
    "hour_sin": hour_sin,
    "hour_cos": hour_cos,
    "is_rush_hour": is_rush_hour,
    "is_night": is_night,
    "day_of_week": day_input,
    "is_weekend": is_weekend_input,
    "aqi_lag_1h": latest_aqi,
    "aqi_lag_3h": latest_aqi_3h_ago,
    "pm25_lag_1h": latest_pm25,
    "temp_rolling_3h": temp_input,   # sliders represent a single hypothetical hour, so treat as flat
    "wind_rolling_3h": wind_input,
    "temp_change_1h": 0              # no meaningful "change" for a single hypothetical point
}])[features]

predicted_aqi = model.predict(input_row)[0]
st.caption(f"Using most recent AQI ({latest_aqi:.0f}) and PM2.5 ({latest_pm25:.1f}) as recent-history context for this prediction.")
st.metric("Predicted AQI", f"{predicted_aqi:.0f}")
acol1, acol2 = st.columns(2)
conditions = acol1.multiselect(
    "Any of these apply to you?",
    options=["asthma", "heart_disease", "elderly", "children", "pregnant", "outdoor_worker"],
    format_func=lambda x: x.replace("_", " ").title()
)
activity = acol2.selectbox("Planned activity", options=["general", "exercise", "commute"],
                            format_func=lambda x: x.title())

headline, tips = get_health_advice(predicted_aqi, conditions, activity)

if predicted_aqi <= 50:
    st.success(headline)
elif predicted_aqi <= 100:
    st.info(headline)
elif predicted_aqi <= 150:
    st.warning(headline)
else:
    st.error(headline)

for tip in tips:
    st.markdown(f"<p style='color:#C7D9E0; padding:4px 0;'>▸ {tip}</p>", unsafe_allow_html=True)

st.markdown("---")

# --- Load secondary data + models (traffic, electricity, accidents) ---
daily_df = load_secondary_daily_data()
secondary_models = load_secondary_models()
latest_daily = daily_df.iloc[-1]

# --- City Stress Index ---
st.subheader("🌆 City Stress Index")
st.caption("A single 0–100 score combining air quality, traffic, energy load, and accidents for the most recent day with complete data")

def normalize(value, series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return 50.0
    return float(np.clip((value - lo) / (hi - lo) * 100, 0, 100))

daily_aqi = df.resample("D").mean(numeric_only=True)["aqi_value"].reindex(daily_df["date"]).ffill()
latest_date = daily_df["date"].iloc[-1]
latest_aqi_for_day = daily_aqi.loc[latest_date] if latest_date in daily_aqi.index else df["aqi_value"].iloc[-1]

aqi_component = normalize(latest_aqi_for_day, daily_aqi.dropna())
traffic_component = normalize(latest_daily["avg_vehicle_count"], daily_df["avg_vehicle_count"])
energy_component = normalize(latest_daily["consumption_kwh"], daily_df["consumption_kwh"])
accident_component = normalize(latest_daily["total_count"], daily_df["total_count"])

stress_index = round(np.mean([aqi_component, traffic_component, energy_component, accident_component]))

if stress_index < 35:
    stress_color, stress_label = TEAL_LIGHT, "Low stress"
elif stress_index < 65:
    stress_color, stress_label = AMBER, "Moderate stress"
else:
    stress_color, stress_label = RED, "High stress"

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=stress_index,
    title={"text": f"{stress_label} — {latest_date.strftime('%d %b %Y')}", "font": {"color": "#E6F1FB"}},
    number={"font": {"color": stress_color}},
    gauge={
        "axis": {"range": [0, 100], "tickcolor": BLUE_GRAY},
        "bar": {"color": stress_color},
        "bgcolor": CARD,
        "steps": [
            {"range": [0, 35], "color": "#123529"},
            {"range": [35, 65], "color": "#3a2f16"},
            {"range": [65, 100], "color": "#3a1616"}
        ]
    }
))
fig_gauge.update_layout(paper_bgcolor=NAVY, font=dict(color="#C7D9E0"), height=320)
st.plotly_chart(fig_gauge, use_container_width=True)

scol1, scol2, scol3, scol4 = st.columns(4)
scol1.metric("Air Quality", f"{aqi_component:.0f}/100")
scol2.metric("Traffic", f"{traffic_component:.0f}/100")
scol3.metric("Energy Load", f"{energy_component:.0f}/100")
scol4.metric("Accidents", f"{accident_component:.0f}/100")

st.markdown("---")

# --- Energy Demand Predictor ---
st.subheader("⚡ Energy Demand Predictor")
st.caption(f"Predicts daily electricity consumption from temperature (Random Forest, R²={secondary_models['energy']['r2']:.2f})")

ecol1, ecol2 = st.columns(2)
energy_temp_input = ecol1.slider("Average daily temperature (°C)", 15.0, 45.0, float(daily_df["avg_temp"].mean()), key="energy_temp")
energy_day_input = ecol2.selectbox("Day of week", options=list(range(7)),
                                    format_func=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][x], key="energy_day")
energy_is_weekend = 1 if energy_day_input in (5, 6) else 0

energy_input_row = pd.DataFrame([{
    "avg_temp": energy_temp_input, "day_of_week": energy_day_input, "is_weekend": energy_is_weekend
}])[secondary_models["energy"]["features"]]
predicted_kwh = secondary_models["energy"]["model"].predict(energy_input_row)[0]
st.metric("Predicted consumption", f"{predicted_kwh:.0f} kWh")

st.markdown("---")

# --- Commute Time Advisor ---
st.subheader("🚗 Commute Time Advisor")
st.caption(f"Predicts average traffic speed by hour of day (Random Forest, R²={secondary_models['commute']['r2']:.2f}) "
           "and suggests the clearest window in the next 24 hours")

commute_is_rain = st.checkbox("Assume rain/fog conditions", key="commute_rain")
commute_temp = df["temperature"].iloc[-1]

hours_range = list(range(24))
commute_rows = []
dow = df.index[-1].dayofweek
for h in hours_range:
    commute_rows.append({
        "hour_sin": np.sin(2 * np.pi * h / 24), "hour_cos": np.cos(2 * np.pi * h / 24),
        "day_of_week": dow, "is_weekend": 1 if dow in (5, 6) else 0,
        "temperature": commute_temp, "is_rain": 1 if commute_is_rain else 0
    })
commute_X = pd.DataFrame(commute_rows)[secondary_models["commute"]["features"]]
predicted_speeds = secondary_models["commute"]["model"].predict(commute_X)

best_hour = int(np.argmax(predicted_speeds))
fig_commute = go.Figure()
fig_commute.add_trace(go.Bar(x=hours_range, y=predicted_speeds,
                              marker_color=[AMBER if h == best_hour else TEAL_LIGHT for h in hours_range]))
fig_commute.update_layout(
    height=340, xaxis_title="Hour of day", yaxis_title="Predicted avg speed (km/h)",
    paper_bgcolor=NAVY, plot_bgcolor=NAVY, font=dict(color="#C7D9E0"),
    xaxis=dict(gridcolor=BORDER, dtick=1), yaxis=dict(gridcolor=BORDER)
)
st.plotly_chart(fig_commute, use_container_width=True)
st.info(f"🕒 Clearest predicted commute window: **{best_hour}:00** "
        f"({predicted_speeds[best_hour]:.0f} km/h average speed)")

st.markdown("---")

# --- Accident Risk Simulator ---
st.subheader("🚨 Road Safety Risk Simulator")
st.caption(f"Estimates expected daily accident count from weather and traffic conditions "
           f"(Random Forest, R²={secondary_models['accident']['r2']:.2f})")

rcol1, rcol2, rcol3 = st.columns(3)
risk_temp = rcol1.slider("Average temperature (°C)", 15.0, 45.0, float(daily_df["avg_temp"].mean()), key="risk_temp")
risk_humidity = rcol2.slider("Average humidity (%)", 0, 100, int(df["humidity"].mean()), key="risk_humidity")
risk_is_rain = rcol3.checkbox("Rain/fog day", key="risk_rain")

rcol4, rcol5 = st.columns(2)
risk_vehicle_count = rcol4.slider("Average vehicle count", 0, int(daily_df["avg_vehicle_count"].max() * 1.5),
                                   int(daily_df["avg_vehicle_count"].mean()), key="risk_vehicles")
risk_congestion_hours = rcol5.slider("High-congestion hours that day", 0, 24,
                                      int(daily_df["high_congestion_hours"].mean()), key="risk_congestion")

risk_input_row = pd.DataFrame([{
    "avg_temp": risk_temp, "avg_humidity": risk_humidity, "is_rain_day": 1 if risk_is_rain else 0,
    "avg_vehicle_count": risk_vehicle_count, "high_congestion_hours": risk_congestion_hours
}])[secondary_models["accident"]["features"]]
predicted_accidents = max(0, secondary_models["accident"]["model"].predict(risk_input_row)[0])

if predicted_accidents < 2:
    st.success(f"Predicted accident count: {predicted_accidents:.1f} — Low risk")
elif predicted_accidents < 5:
    st.warning(f"Predicted accident count: {predicted_accidents:.1f} — Moderate risk")
else:
    st.error(f"Predicted accident count: {predicted_accidents:.1f} — High risk")

st.markdown("---")
st.caption("City Brain AI — Minor Project | Data: OpenWeatherMap (live) + Open-Meteo (historical) | "
           "Air quality figures are model-based estimates, not raw sensor readings. Traffic, electricity, "
           "and accident figures are synthetically generated, driven by real weather conditions.")