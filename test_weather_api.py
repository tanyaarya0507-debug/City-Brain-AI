import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
print("Key loaded:", API_KEY)
url = f"https://api.openweathermap.org/data/2.5/weather?q=Gwalior&appid={API_KEY}&units=metric"
response = requests.get(url)

print("Status code:", response.status_code)
print(response.json())