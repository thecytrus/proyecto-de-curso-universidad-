# tests/test_clima.py
#----> TERMINAL: python -m unittest tests_PY/test_clima.py

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

# Import the function to be tested
from module.clima import get_weather

class TestClima(unittest.TestCase):

    # --- Helper to create a mock OpenWeatherMap response ---
    def _create_mock_response(self, status_code, json_data=None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        if json_data:
            mock_resp.json.return_value = json_data
        return mock_resp

    # --- Test Case 1: Successful API Call and Data Parsing ---
    @patch('module.clima.requests.get')
    def test_get_weather_success(self, mock_get):
        # Define a mock API response that simulates OpenWeatherMap's forecast structure
        # We'll create data for today, tomorrow, and the day after.
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)
        day_after_tomorrow = today + timedelta(days=2)

        mock_json_data = {
            "city": {"name": "Curico"},
            "list": [
                # Today's data (first entry for current and first day forecast)
                {"dt_txt": f"{today} 09:00:00", "main": {"temp": 15.0, "humidity": 80}, "weather": [{"description": "cielo claro"}], "wind": {"speed": 5.0}, "pop": 0.1},
                {"dt_txt": f"{today} 12:00:00", "main": {"temp": 18.0, "humidity": 70}, "weather": [{"description": "nublado"}], "wind": {"speed": 6.0}, "pop": 0.2},
                # Tomorrow's data (first entry for second day forecast)
                {"dt_txt": f"{tomorrow} 09:00:00", "main": {"temp": 10.0, "humidity": 90}, "weather": [{"description": "lluvia ligera"}], "wind": {"speed": 7.0}, "pop": 0.7},
                {"dt_txt": f"{tomorrow} 12:00:00", "main": {"temp": 12.0, "humidity": 85}, "weather": [{"description": "lluvia"}], "wind": {"speed": 8.0}, "pop": 0.8},
                # Day after tomorrow's data (first entry for third day forecast)
                {"dt_txt": f"{day_after_tomorrow} 09:00:00", "main": {"temp": 20.0, "humidity": 60}, "weather": [{"description": "soleado"}], "wind": {"speed": 4.0}, "pop": 0.05},
                {"dt_txt": f"{day_after_tomorrow} 12:00:00", "main": {"temp": 22.0, "humidity": 55}, "weather": [{"description": "parcialmente nublado"}], "wind": {"speed": 4.5}, "pop": 0.1},
            ]
        }

        mock_get.return_value = self._create_mock_response(200, mock_json_data)

        # Call the function under test
        weather_data = get_weather("Curico")

        # Assertions
        self.assertIn("city", weather_data)
        self.assertEqual(weather_data["city"], "Curico")

        self.assertIn("current", weather_data)
        self.assertEqual(weather_data["current"]["temp"], 15.0)
        self.assertEqual(weather_data["current"]["humidity"], 80)
        self.assertEqual(weather_data["current"]["rain_prob"], 10.0) # 0.1 * 100
        self.assertEqual(weather_data["current"]["wind"], 5.0)
        self.assertEqual(weather_data["current"]["description"], "cielo claro")

        self.assertIn("forecast", weather_data)
        self.assertEqual(len(weather_data["forecast"]), 3)

        # Check today's forecast summary
        self.assertEqual(weather_data["forecast"][0]["date"], today.isoformat())
        self.assertEqual(weather_data["forecast"][0]["prediction"]["temp"], 15.0)

        # Check tomorrow's forecast summary
        self.assertEqual(weather_data["forecast"][1]["date"], tomorrow.isoformat())
        self.assertEqual(weather_data["forecast"][1]["prediction"]["temp"], 10.0)

        # Check day after tomorrow's forecast summary
        self.assertEqual(weather_data["forecast"][2]["date"], day_after_tomorrow.isoformat())
        self.assertEqual(weather_data["forecast"][2]["prediction"]["temp"], 20.0)

        # Verify requests.get was called with correct parameters
        mock_get.assert_called_once_with(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "q": "Curico",
                "appid": "43b0fcbe4e275f6ab76a4d5651092b7e", # API_KEY
                "units": "metric",
                "lang": "es"
            }
        )

    # --- Test Case 2: API Call Failure (Non-200 Status Code) ---
    @patch('module.clima.requests.get')
    def test_get_weather_api_failure(self, mock_get):
        mock_get.return_value = self._create_mock_response(404) # Simulate "City not found"

        weather_data = get_weather("NonExistentCity")

        self.assertEqual(weather_data["city"], "Error")
        self.assertEqual(weather_data["forecast"], [])
        self.assertEqual(weather_data["current"], {})

    # --- Test Case 3: Empty 'list' in API Response ---
    @patch('module.clima.requests.get')
    def test_get_weather_empty_list(self, mock_get):
        mock_json_data = {
            "city": {"name": "EmptyListCity"},
            "list": [] # Empty list
        }
        mock_get.return_value = self._create_mock_response(200, mock_json_data)

        weather_data = get_weather("EmptyListCity")

        self.assertEqual(weather_data["city"], "Error") # Your code defaults to "Error" if list is empty
        self.assertEqual(weather_data["forecast"], [])
        self.assertEqual(weather_data["current"], {})

    # --- Test Case 4: Missing 'pop' (Probability of Precipitation) ---
    @patch('module.clima.requests.get')
    def test_get_weather_missing_pop(self, mock_get):
        today = datetime.today().date()
        mock_json_data = {
            "city": {"name": "NoPopCity"},
            "list": [
                # Missing 'pop' key
                {"dt_txt": f"{today} 09:00:00", "main": {"temp": 15.0, "humidity": 80}, "weather": [{"description": "cielo claro"}], "wind": {"speed": 5.0}},
            ]
        }
        mock_get.return_value = self._create_mock_response(200, mock_json_data)

        weather_data = get_weather("NoPopCity")

        self.assertIn("current", weather_data)
        # Should default to 0 if 'pop' is missing
        self.assertEqual(weather_data["current"]["rain_prob"], 0.0) 
        self.assertIn("forecast", weather_data)
        # Check the first day's prediction for pop
        self.assertEqual(weather_data["forecast"][0]["prediction"]["rain_prob"], 0.0)


if __name__ == '__main__':
    unittest.main()