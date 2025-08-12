import requests
from datetime import datetime, timedelta
import pytz

API_KEY = "apikey from openweathermap"
URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_weather(city):
    """
    Obtiene el pronóstico del tiempo para una ciudad dada.
    Retorna los datos actuales y el pronóstico para los próximos 3 días.
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es"
    }
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if "list" in data and len(data["list"]) > 0:
            chile_tz = pytz.timezone('America/Santiago')
            forecast_by_day = {}

            for item in data["list"]:
                dt_chile = datetime.fromtimestamp(item["dt"], chile_tz)
                date_str = dt_chile.strftime("%Y-%m-%d")
                hour_str = dt_chile.strftime("%H:%M")

                if date_str not in forecast_by_day:
                    forecast_by_day[date_str] = []

                forecast_by_day[date_str].append({
                    "hour": hour_str,
                    "temp": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "rain_prob": item.get("pop", 0) * 100,
                    "wind": item["wind"]["speed"],
                    "description": item["weather"][0]["description"]
                })

            def find_closest_to_noon(forecasts):
                target_hour = 12
                return min(forecasts, key=lambda f: abs(int(f["hour"].split(":")[0]) - target_hour))

            now_chile = datetime.now(chile_tz)
            today = now_chile.date()
            result_list = []

            for i in range(3):
                day = today + timedelta(days=i)
                day_str = day.isoformat()

                if day_str in forecast_by_day:
                    forecast = find_closest_to_noon(forecast_by_day[day_str])
                    result_list.append({
                        "date": day_str,
                        "hour": forecast["hour"],
                        "prediction": forecast
                    })
                else:
                    result_list.append({
                        "date": day_str,
                        "hour": "N/A",
                        "prediction": {
                            "hour": "N/A", "temp": "N/A", "humidity": "N/A", 
                            "rain_prob": "N/A", "wind": "N/A", "description": "No data"
                        }
                    })

            # Datos actuales (primer pronóstico)
            current_data = data["list"][0]
            current_hour_chile = datetime.fromtimestamp(current_data["dt"], chile_tz).strftime("%H:%M")

            current = {
                "time": current_hour_chile,
                "temp": current_data["main"]["temp"],
                "humidity": current_data["main"]["humidity"],
                "rain_prob": current_data.get("pop", 0) * 100,
                "wind": current_data["wind"]["speed"],
                "description": current_data["weather"][0]["description"]
            }

            return {
                "city": data.get("city", {}).get("name", "Desconocido"),
                "forecast": result_list,
                "current": current
            }

    return {"city": "Error", "forecast": [], "current": {}}
