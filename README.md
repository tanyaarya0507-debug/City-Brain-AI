&#x20;CityBrain AI



Unified urban intelligence dashboard — Weather, AQI, Traffic, and Emergency data with ML-based AQI prediction.



\## Status

Week 1: database foundation — schema and connection working.



\## Setup



1\. Create a free Postgres project at \[supabase.com](https://supabase.com)

2\. In the Supabase SQL Editor, run `sql/schema.sql` to create all tables

3\. Copy `.env.example` to `.env` and fill in your real Supabase connection string

4\. Install dependencies:

&#x20;  ```bash

&#x20;  pip install -r requirements.txt

&#x20;  ```

5\. Test the connection:

&#x20;  ```bash

&#x20;  python scripts/test\_connection.py

&#x20;  ```

&#x20;  You should see your `cities` table printed and a "Connection test passed" message.



\## Roadmap (Major Project — Future Scope)

Live IoT sensors, hospital integration, smart parking, waste management,

disease analytics, Spark/Kafka/Airflow pipeline, Explainable AI, multi-city support.



