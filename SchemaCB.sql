-- CityBrain AI — Database Schema
-- Run this in Supabase SQL Editor to set up all tables

-- Core reference table
CREATE TABLE cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);

-- Weather data
CREATE TABLE weather (
    weather_id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities(city_id),
    recorded_at TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    wind_speed DECIMAL(5,2),
    weather_condition VARCHAR(50)
);

-- Air quality data
CREATE TABLE air_quality (
    aqi_id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities(city_id),
    recorded_at TIMESTAMP NOT NULL,
    aqi_value INT,
    pm25 DECIMAL(6,2),
    pm10 DECIMAL(6,2),
    co DECIMAL(6,2),
    no2 DECIMAL(6,2),
    so2 DECIMAL(6,2),
    o3 DECIMAL(6,2)
);

-- Indexes for the columns we'll join/filter on constantly
CREATE INDEX idx_weather_city_time ON weather (city_id, recorded_at);
CREATE INDEX idx_aqi_city_time ON air_quality (city_id, recorded_at);

-- Seed your city (edit as needed)
INSERT INTO cities (city_name, latitude, longitude)
VALUES ('Gwalior', 26.2183, 78.1828);
