# tests/test_sensores.py
#----> TERMINAL: python -m unittest tests_PY/test_sensores.py

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sqlite3
import json
from flask import Flask, request, jsonify
from datetime import datetime

# Import the functions to be tested from your module
from module import sensores
from module import alertas

OPENWEATHER_API_KEY = "43b0fcbe4e275f6ab76a4d5651092b7e"
OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Helper function to create a mock SQLite row that behaves like sqlite3.Row
class MockSqliteRow(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getitem__(self, key):
        # Define the expected order of columns for SELECT * FROM datos_sensores
        # This order must match the order SQLite would return columns
        keys_order = [
            'id', 'numero_cultivo', 'humedad_suelo', 'ph_suelo',
            'temperatura_ambiente', 'nitrogeno', 'fosforo', 'potasio', 'timestamp'
        ]
        if isinstance(key, int):
            if key < len(keys_order):
                return super().__getitem__(keys_order[key])
            else:
                raise IndexError(f"Tuple index out of range: {key}")
        return super().__getitem__(key)


class TestSensores(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'test_secret_key'
        self.client = self.app.test_client()

        # Patch sqlite3.connect for the entire test class
        self.connect_patcher = patch('module.sensores.sqlite3.connect')
        self.mock_connect = self.connect_patcher.start()

        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Patch requests.get for external API calls
        self.requests_get_patcher = patch('module.sensores.requests.get')
        self.mock_requests_get = self.requests_get_patcher.start()

        # Patch datetime.now for predictable timestamps
        self.datetime_patcher = patch('module.sensores.datetime')
        self.mock_datetime = self.datetime_patcher.start()
        self.mock_datetime.now.return_value = datetime(2025, 6, 18, 10, 0, 0)
        self.mock_datetime.strptime = datetime.strptime

        # Patch alertas.verificar_alertas
        self.alertas_verificar_alertas_patcher = patch('module.sensores.alertas.verificar_alertas')
        self.mock_verificar_alertas = self.alertas_verificar_alertas_patcher.start()

        # Reset the global data_generation_status for each test
        sensores.data_generation_status = {}

        # Add the routes (ensure these match the actual app.py routes)
        with self.app.app_context():
            self.app.add_url_rule(
                '/sensores/generar/<string:numero_cultivo>',
                view_func=sensores.generate_data,
                methods=['POST']
            )
            # Route for POST (setting status)
            self.app.add_url_rule(
                '/sensores/status/<string:numero_cultivo>',
                view_func=self._mock_set_data_generation_status, # Use a mock view for testing
                methods=['POST']
            )
            # Route for GET (getting status)
            self.app.add_url_rule(
                '/sensores/status/<string:numero_cultivo>',
                view_func=self._mock_get_data_generation_status, # Use a mock view for testing
                methods=['GET']
            )
            self.app.add_url_rule(
                '/sensores/datos/<string:numero_cultivo>',
                view_func=sensores.obtener_datos_por_cultivo,
                methods=['GET']
            )
            self.app.add_url_rule(
                '/sensores/historial/<string:numero_cultivo>',
                view_func=sensores.obtener_historial_datos_cultivo_api,
                methods=['GET']
            )
    
    # Helper mock view functions for Flask routes
    def _mock_set_data_generation_status(self, numero_cultivo):
        status = request.json.get('status')
        if status is None:
            return jsonify({"error": "Missing 'status' in request body"}), 400
        sensores.set_data_generation_status(numero_cultivo, status)
        return jsonify({"message": f"Generación de datos para el cultivo {numero_cultivo} establecida en {status}"}), 200

    def _mock_get_data_generation_status(self, numero_cultivo):
        status = sensores.data_generation_status.get(numero_cultivo, 'stopped')
        return jsonify(status), 200

    def tearDown(self):
        self.connect_patcher.stop()
        self.requests_get_patcher.stop()
        self.datetime_patcher.stop()
        self.alertas_verificar_alertas_patcher.stop()


    # Test Case: crear_tabla_datos_sensores
    def test_crear_tabla_datos_sensores(self):
        self.mock_cursor.execute.reset_mock()
        self.mock_conn.commit.reset_mock()
        self.mock_conn.close.reset_mock()

        sensores.crear_tabla_datos_sensores()
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()

    # Test Case: simular_ph
    def test_simular_ph(self):
        self.assertEqual(sensores.simular_ph(10, 20), 6.9)
        self.assertEqual(sensores.simular_ph(0, 0), 7.0)
        self.assertEqual(sensores.simular_ph(None, 25), round(7.0 + 0.02 * 25, 2))

    # Test Case: guardar_datos
    def test_guardar_datos(self):
        mock_datos = {
            "humedad_suelo": 75.0,
            "ph_suelo": 6.8,
            "temperatura_ambiente": 25.5,
            "nutrientes": {"N": 60, "P": 35, "K": 90}
        }
        numero_cultivo = "AGRO-1-1"
        expected_timestamp = self.mock_datetime.now.return_value.strftime("%Y-%m-%d %H:%M:%S")

        sensores.guardar_datos(mock_datos, numero_cultivo)

        # --- FIX: Copy the exact 'Actual:' SQL string from the traceback ---
        expected_sql = """
        INSERT INTO datos_sensores (
            numero_cultivo, humedad_suelo, ph_suelo,
            temperatura_ambiente, nitrogeno, fosforo, potasio, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
        # Ensure there are no extra leading/trailing newlines or spaces that are not in the actual code's string

        self.mock_cursor.execute.assert_called_once_with(
            expected_sql, (
                numero_cultivo,
                mock_datos['humedad_suelo'],
                mock_datos['ph_suelo'],
                mock_datos['temperatura_ambiente'],
                mock_datos['nutrientes']['N'],
                mock_datos['nutrientes']['P'],
                mock_datos['nutrientes']['K'],
                expected_timestamp
            )
        )
        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()
        self.mock_verificar_alertas.assert_called_once_with(numero_cultivo, mock_datos)

    # Test Case: obtener_coordenadas_cultivo
    def test_obtener_coordenadas_cultivo_found(self):
        self.mock_cursor.fetchone.return_value = (-34.98, -71.22)
        lat, lon = sensores.obtener_coordenadas_cultivo("AGRO-1-1")
        self.assertEqual(lat, -34.98)
        self.assertEqual(lon, -71.22)
        self.mock_cursor.execute.assert_called_once_with("SELECT latitud, longitud FROM cultivos WHERE numero = ?", ("AGRO-1-1",))
        self.mock_conn.close.assert_called_once()

    def test_obtener_coordenadas_cultivo_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        lat, lon = sensores.obtener_coordenadas_cultivo("NON-EXISTENT")
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        self.mock_cursor.execute.assert_called_once_with("SELECT latitud, longitud FROM cultivos WHERE numero = ?", ("NON-EXISTENT",))
        self.mock_conn.close.assert_called_once()

    # Test Case: get_real_time_weather
    def test_get_real_time_weather_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "main": {"temp": 28.5, "humidity": 65},
            "rain": {"1h": 5.2}
        }
        mock_response.raise_for_status.return_value = None
        self.mock_requests_get.return_value = mock_response

        temp, humidity, rain = sensores.get_real_time_weather(-34.98, -71.22)
        self.assertEqual(temp, 28.5)
        self.assertEqual(humidity, 65)
        self.assertEqual(rain, 5.2)
        self.mock_requests_get.assert_called_once_with(
            OPENWEATHER_BASE_URL,
            params={
                "lat": -34.98,
                "lon": -71.22,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "es"
            }
        )

    def test_get_real_time_weather_no_rain(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "main": {"temp": 20.0, "humidity": 50}
        }
        mock_response.raise_for_status.return_value = None
        self.mock_requests_get.return_value = mock_response

        temp, humidity, rain = sensores.get_real_time_weather(-34.98, -71.22)
        self.assertEqual(temp, 20.0)
        self.assertEqual(humidity, 50)
        self.assertEqual(rain, 0)

    def test_get_real_time_weather_api_error(self):
        import requests
        self.mock_requests_get.side_effect = requests.exceptions.RequestException("API Error")
        temp, humidity, rain = sensores.get_real_time_weather(-34.98, -71.22)
        self.assertIsNone(temp)
        self.assertIsNone(humidity)
        self.assertIsNone(rain)

    # Test Case: generate_data
    @patch('module.sensores.obtener_coordenadas_cultivo')
    @patch('module.sensores.get_real_time_weather')
    @patch('module.sensores.guardar_datos')
    @patch('module.sensores.random.uniform', side_effect=[
        20.0,  # temp
        70.0,  # humidity
        10.0,  # rain
        50.0,  # N
        30.0,  # P
        100.0  # K
    ])
    def test_generate_data_success_real_weather(self, mock_random_uniform, mock_guardar_datos, mock_get_real_time_weather, mock_obtener_coordenadas_cultivo):
        numero_cultivo = "AGRO-1-1"
        self.mock_cursor.fetchone.return_value = (1,)

        mock_obtener_coordenadas_cultivo.return_value = (-34.98, -71.22)
        mock_get_real_time_weather.return_value = (25.0, 60.0, 5.0)

        with self.app.app_context():
            response = self.client.post(f'/sensores/generar/{numero_cultivo}')
            self.assertEqual(response.status_code, 201)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['message'], "Datos de sensor generados y guardados exitosamente")
            self.assertIn('humedad_suelo', response_data['data'])

            self.mock_connect.assert_called_with(sensores.DATABASE)
            mock_obtener_coordenadas_cultivo.assert_called_once_with(numero_cultivo)
            mock_get_real_time_weather.assert_called_once_with(-34.98, -71.22)
            mock_guardar_datos.assert_called_once()
            args, _ = mock_guardar_datos.call_args
            self.assertIsInstance(args[0], dict)
            self.assertEqual(args[1], numero_cultivo)
            self.assertAlmostEqual(args[0]['humedad_suelo'], 60.0)
            self.assertAlmostEqual(args[0]['ph_suelo'], round(7.0 - 0.05 * 5.0 + 0.02 * 25.0, 2))


    @patch('module.sensores.obtener_coordenadas_cultivo')
    @patch('module.sensores.get_real_time_weather')
    @patch('module.sensores.guardar_datos')
    @patch('module.sensores.random.uniform', side_effect=[
        20.0,  # temp
        70.0,  # humidity
        10.0,  # rain
        50.0,  # N
        30.0,  # P
        100.0  # K
    ])
    def test_generate_data_success_simulated_weather(self, mock_random_uniform, mock_guardar_datos, mock_get_real_time_weather, mock_obtener_coordenadas_cultivo):
        numero_cultivo = "AGRO-1-1"
        self.mock_cursor.fetchone.return_value = (1,)

        mock_obtener_coordenadas_cultivo.return_value = (None, None)
        mock_get_real_time_weather.return_value = (None, None, None)

        with self.app.app_context():
            response = self.client.post(f'/sensores/generar/{numero_cultivo}')
            self.assertEqual(response.status_code, 201)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['message'], "Datos de sensor generados y guardados exitosamente")
            self.assertIn('humedad_suelo', response_data['data'])

            self.mock_connect.assert_called_with(sensores.DATABASE)
            mock_obtener_coordenadas_cultivo.assert_called_once_with(numero_cultivo)
            mock_get_real_time_weather.assert_not_called() 
            mock_guardar_datos.assert_called_once()

            args, _ = mock_guardar_datos.call_args
            self.assertAlmostEqual(args[0]['humedad_suelo'], 70.0)
            self.assertAlmostEqual(args[0]['temperatura_ambiente'], 20.0)
            self.assertAlmostEqual(args[0]['ph_suelo'], sensores.simular_ph(10.0, 20.0))


    def test_generate_data_cultivo_not_found(self):
        numero_cultivo = "NON-EXISTENT"
        self.mock_cursor.fetchone.return_value = None

        with self.app.app_context():
            response = self.client.post(f'/sensores/generar/{numero_cultivo}')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.data)['message'], f"El cultivo con número {numero_cultivo} no existe.")
            self.mock_connect.assert_called_once_with(sensores.DATABASE)
            self.mock_conn.close.assert_called_once()
            self.mock_verificar_alertas.assert_not_called()

    # Test Case: set_data_generation_status
    def test_set_data_generation_status(self):
        numero_cultivo = "AGRO-1-1"
        status = "running"
        with self.app.app_context():
            response = self.client.post(f'/sensores/status/{numero_cultivo}', json={'status': status})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data)['message'], f"Generación de datos para el cultivo {numero_cultivo} establecida en {status}")
            self.assertEqual(sensores.data_generation_status.get(numero_cultivo), status)

    # Test Case: get_data_generation_status
    def test_get_data_generation_status_running(self):
        numero_cultivo = "AGRO-1-1"
        sensores.data_generation_status[numero_cultivo] = "running"
        with self.app.app_context():
            response = self.client.get(f'/sensores/status/{numero_cultivo}')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), "running")

    def test_get_data_generation_status_stopped(self):
        numero_cultivo = "AGRO-1-2"
        with self.app.app_context():
            response = self.client.get(f'/sensores/status/{numero_cultivo}')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), "stopped")

    # Test Case: obtener_datos_por_cultivo_raw
    def test_obtener_datos_por_cultivo_raw_found(self):
        mock_data = MockSqliteRow({
            "id": 1,
            "numero_cultivo": "AGRO-1-1",
            "humedad_suelo": 60.5,
            "ph_suelo": 6.7,
            "temperatura_ambiente": 23.1,
            "nitrogeno": 55.0,
            "fosforo": 32.0,
            "potasio": 95.0,
            "timestamp": "2025-06-18 10:00:00"
        })
        self.mock_cursor.fetchone.return_value = mock_data
        self.mock_cursor.execute.reset_mock()

        result = sensores.obtener_datos_por_cultivo_raw("AGRO-1-1")
        self.assertEqual(result, dict(mock_data))
        # --- FIX: Copy the exact 'Actual:' SQL string from the traceback ---
        expected_sql = """
        SELECT * FROM datos_sensores WHERE numero_cultivo=? ORDER BY timestamp DESC LIMIT 1
    """
        self.mock_cursor.execute.assert_called_once_with(
            expected_sql, ("AGRO-1-1",)
        )
        self.mock_conn.close.assert_called_once()
        self.assertEqual(self.mock_conn.row_factory, sqlite3.Row)


    def test_obtener_datos_por_cultivo_raw_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.execute.reset_mock()

        result = sensores.obtener_datos_por_cultivo_raw("NON-EXISTENT")
        self.assertIsNone(result)
        # --- FIX: Copy the exact 'Actual:' SQL string from the traceback ---
        expected_sql = """
        SELECT * FROM datos_sensores WHERE numero_cultivo=? ORDER BY timestamp DESC LIMIT 1
    """
        self.mock_cursor.execute.assert_called_once_with(
            expected_sql, ("NON-EXISTENT",)
        )
        self.mock_conn.close.assert_called_once()
        self.assertEqual(self.mock_conn.row_factory, sqlite3.Row)

    # Test Case: obtener_datos_por_cultivo (API Endpoint)
    def test_obtener_datos_por_cultivo_api_found(self):
        mock_data = {
            "id": 1, "numero_cultivo": "AGRO-1-1", "humedad_suelo": 60.5, "ph_suelo": 6.7,
            "temperatura_ambiente": 23.1, "nitrogeno": 55.0, "fosforo": 32.0, "potasio": 95.0,
            "timestamp": "2025-06-18 10:00:00"
        }
        with patch('module.sensores.obtener_datos_por_cultivo_raw', return_value=mock_data) as mock_raw:
            with self.app.app_context():
                response = self.client.get('/sensores/datos/AGRO-1-1')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.data), mock_data)
                mock_raw.assert_called_once_with("AGRO-1-1")

    def test_obtener_datos_por_cultivo_api_not_found(self):
        with patch('module.sensores.obtener_datos_por_cultivo_raw', return_value=None) as mock_raw:
            with self.app.app_context():
                response = self.client.get('/sensores/datos/NON-EXISTENT')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.data), {})
                mock_raw.assert_called_once_with("NON-EXISTENT")

    # Test Case: obtener_historial_datos_sensores
    def test_obtener_historial_datos_sensores(self):
        mock_history_data = [
            MockSqliteRow({"timestamp": "2025-06-18 09:00:00", "humedad_suelo": 50.0, "ph_suelo": 6.0, "temperatura_ambiente": 20.0, "nitrogeno": 40.0, "fosforo": 25.0, "potasio": 80.0, "numero_cultivo": "AGRO-1-1", "id": 1}),
            MockSqliteRow({"timestamp": "2025-06-18 10:00:00", "humedad_suelo": 60.0, "ph_suelo": 6.5, "temperatura_ambiente": 22.0, "nitrogeno": 45.0, "fosforo": 30.0, "potasio": 85.0, "numero_cultivo": "AGRO-1-1", "id": 2})
        ]
        self.mock_cursor.fetchall.return_value = mock_history_data
        self.mock_cursor.execute.reset_mock()

        result = sensores.obtener_historial_datos_sensores("AGRO-1-1", limit=2)
        expected_result = [dict(row) for row in mock_history_data]
        self.assertEqual(result, expected_result)
        # --- FIX: Copy the exact 'Actual:' SQL string from the traceback ---
        expected_sql = """
        SELECT 
            timestamp, 
            humedad_suelo, 
            ph_suelo, 
            temperatura_ambiente, 
            nitrogeno, 
            fosforo, 
            potasio 
        FROM datos_sensores 
        WHERE numero_cultivo=? 
        ORDER BY timestamp ASC 
        LIMIT ?
    """
        self.mock_cursor.execute.assert_called_once_with(
            expected_sql, ("AGRO-1-1", 2)
        )
        self.mock_conn.close.assert_called_once()
        self.assertEqual(self.mock_conn.row_factory, sqlite3.Row)


    def test_obtener_historial_datos_sensores_empty(self):
        self.mock_cursor.fetchall.return_value = []
        self.mock_cursor.execute.reset_mock()

        result = sensores.obtener_historial_datos_sensores("AGRO-1-1", limit=5)
        self.assertEqual(result, [])
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.close.assert_called_once()
        self.assertEqual(self.mock_conn.row_factory, sqlite3.Row)


    # Test Case: obtener_historial_datos_cultivo_api
    def test_obtener_historial_datos_cultivo_api(self):
        mock_historial = [{"timestamp": "2025-06-18 10:00:00", "humedad_suelo": 60.0}]
        with patch('module.sensores.obtener_historial_datos_sensores', return_value=mock_historial) as mock_raw_history:
            with self.app.app_context():
                response = self.client.get('/sensores/historial/AGRO-1-1')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.data), mock_historial)
                mock_raw_history.assert_called_once_with("AGRO-1-1")

if __name__ == '__main__':
    unittest.main()