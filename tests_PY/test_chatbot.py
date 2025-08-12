# tests/test_chatbot.py
#----> TERMINAL: python -m unittest tests_PY/test_chatbot.py

import unittest
from unittest.mock import patch, MagicMock
from module.chatbot import (
    crear_tabla_chat,
    cambiar_estado,
    nueva_conversacion,
    guardar_interaccion,
    obtener_historial,
    cargar_contexto_conversacion,
    chat # Only import chat, as it's the main function being tested
)
from flask import session, Flask

app = Flask(__name__)
app.secret_key = 'test_secret_key'  # Necessary for using session

class TestChatbot(unittest.TestCase):

    @patch('module.chatbot.sqlite3.connect')
    def test_crear_tabla_chat(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        crear_tabla_chat()
        mock_conn.cursor().execute.assert_called_once()

    @patch('module.chatbot.sqlite3.connect')
    def test_cambiar_estado(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        cambiar_estado('test_id')
        # This string must EXACTLY match what's executed.
        # Based on your traceback, it starts with a newline and 8 spaces.
        mock_conn.cursor().execute.assert_called_once_with(
            '\n        UPDATE historial_chat\n        SET estado = 0\n        WHERE conversacion_id = ?\n    ',
            ('test_id',)
        )

    def test_nueva_conversacion(self):
        conversacion_id = nueva_conversacion()
        self.assertIsInstance(conversacion_id, str)

    @patch('module.chatbot.sqlite3.connect')
    def test_guardar_interaccion(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        guardar_interaccion(1, 'test_id', 'pregunta', 'respuesta')
        mock_conn.cursor().execute.assert_called_once()

    @patch('module.chatbot.sqlite3.connect')
    def test_obtener_historial(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor().fetchall.return_value = [('pregunta', 'respuesta', 'fecha', 1)]
        historial = obtener_historial('test_id')
        self.assertEqual(len(historial), 1)

    @patch('module.chatbot.obtener_historial')
    def test_cargar_contexto_conversacion(self, mock_obtener_historial):
        mock_obtener_historial.return_value = [('pregunta', 'respuesta', 'fecha', 1)]
        contexto = cargar_contexto_conversacion('test_id')
        self.assertEqual(len(contexto), 2)

    @patch('module.cultivos.obtener_datos_cultivo') # Patch the dependency directly
    def test_get_cultivo_data_for_user(self, mock_obtener_datos_cultivo):
        mock_obtener_datos_cultivo.return_value = {
            'usuario_id': 1,
            'agronomist_id': None,
            'numero': 'AGRO-123-456',
            'ciudad': 'Santiago',
            'tipo': 'Tomate',
            'latitud': '-33.456',
            'longitud': '-70.648'
        }
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor', 'id': 1}
            # Import and call the actual function you're testing here
            from module.chatbot import get_cultivo_data_for_user as actual_get_cultivo_data_for_user
            data = actual_get_cultivo_data_for_user('AGRO-123-456', 1)
            self.assertIn('numero', data)
            self.assertEqual(data['numero'], 'AGRO-123-456')
            self.assertEqual(data['ciudad'], 'Santiago')


    @patch('module.sensores.obtener_datos_por_cultivo_raw') # Patch the dependency directly
    @patch('module.cultivos.obtener_datos_cultivo') # Patch this dependency as well
    def test_get_sensor_data_for_user_cultivo(self, mock_obtener_datos_cultivo, mock_obtener_datos_por_cultivo_raw):
        mock_obtener_datos_cultivo.return_value = {'usuario_id': 1, 'agronomist_id': None, 'numero': 'AGRO-123-456'}
        mock_obtener_datos_por_cultivo_raw.return_value = {
            'humedad_suelo': 30,
            'ph_suelo': 6.5,
            'temperatura_ambiente': 25,
            'nitrogeno': 100,
            'fosforo': 50,
            'potasio': 75,
            'timestamp': '2025-06-18 10:00:00'
        }
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor', 'id': 1}
            # Import and call the actual function you're testing here
            from module.chatbot import get_sensor_data_for_user_cultivo as actual_get_sensor_data_for_user_cultivo
            data = actual_get_sensor_data_for_user_cultivo('AGRO-123-456', 1)
            self.assertIn('humedad_suelo', data)
            self.assertEqual(data['humedad_suelo'], 30)
            self.assertEqual(data['ph_suelo'], 6.5)

    @patch('module.chatbot.requests.post')
    @patch('module.chatbot.guardar_interaccion')
    @patch('module.chatbot.cargar_contexto_conversacion')
    def test_chat_general_question(self, mock_cargar_contexto, mock_guardar_interaccion, mock_post):
        mock_cargar_contexto.return_value = []
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Esta es una respuesta general de la IA."}}]
        }
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor'}
            response = chat("¿Cuál es la mejor época para sembrar maíz?", 1, "test_id_general")
            self.assertEqual(response.json['respuesta'], "Esta es una respuesta general de la IA.")
            mock_guardar_interaccion.assert_called_once_with(
                1, "test_id_general", "¿Cuál es la mejor época para sembrar maíz?", "Esta es una respuesta general de la IA."
            )

    @patch('module.chatbot.requests.post')
    @patch('module.chatbot.guardar_interaccion')
    @patch('module.chatbot.cargar_contexto_conversacion')
    @patch('module.cultivos.obtener_datos_cultivo')
    def test_chat_cultivo_info_request(self, mock_obtener_datos_cultivo, mock_cargar_contexto, mock_guardar_interaccion, mock_post):
        mock_cargar_contexto.return_value = []
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Respuesta LLM base."}}]
        }
        mock_obtener_datos_cultivo.return_value = {
            'usuario_id': 1,
            'agronomist_id': None,
            'numero': 'AGRO-123-456',
            'ciudad': 'Curicó',
            'tipo': 'Trigo',
            'latitud': 'Lat-A',
            'longitud': 'Long-B'
        }
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor', 'id': 1}
            # Adjusted input to specifically trigger general_match (using 'latitud' as a keyword)
            user_input = "Cuál es la latitud de mi cultivo AGRO-123-456?"
            response = chat(user_input, 1, "test_id_cultivo")

            expected_response_text = (
                f"El cultivo AGRO-123-456 es de tipo Trigo "
                f"en Curicó, ubicado en "
                f"Latitud: Lat-A y Longitud: Long-B."
            )
            self.assertEqual(response.json['respuesta'], expected_response_text)
            mock_obtener_datos_cultivo.assert_called_once_with("AGRO-123-456")
            mock_guardar_interaccion.assert_called_once_with(
                1, "test_id_cultivo", user_input, expected_response_text
            )

    @patch('module.chatbot.requests.post')
    @patch('module.chatbot.guardar_interaccion')
    @patch('module.chatbot.cargar_contexto_conversacion')
    @patch('module.sensores.obtener_datos_por_cultivo_raw')
    @patch('module.cultivos.obtener_datos_cultivo')
    def test_chat_sensor_info_request(self, mock_obtener_datos_cultivo, mock_obtener_datos_por_cultivo_raw, mock_cargar_contexto, mock_guardar_interaccion, mock_post):
        mock_cargar_contexto.return_value = []
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Respuesta LLM base."}}]
        }
        mock_obtener_datos_cultivo.return_value = {'usuario_id': 1, 'agronomist_id': None, 'numero': 'AGRO-789-012'}
        mock_obtener_datos_por_cultivo_raw.return_value = {
            "humedad_suelo": 45,
            "ph_suelo": 7.0,
            "temperatura_ambiente": 22.5,
            "nitrogeno": 80,
            "fosforo": 40,
            "potasio": 60,
            "timestamp": "2025-06-18 15:30:00"
        }
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor', 'id': 1}
            # Adjusted input to specifically trigger sensor_match (using 'humedad' as a keyword)
            user_input = "Dime la humedad de AGRO-789-012."
            response = chat(user_input, 1, "test_id_sensor")

            expected_response_text = (
                "Datos de sensores para el cultivo AGRO-789-012 (2025-06-18 15:30:00): "
                "Humedad: 45%, pH: 7.0, Temperatura: 22.5°C, Nitrógeno: 80, Fósforo: 40, Potasio: 60."
            )
            self.assertEqual(response.json['respuesta'], expected_response_text)
            mock_obtener_datos_cultivo.assert_called_once_with("AGRO-789-012")
            mock_obtener_datos_por_cultivo_raw.assert_called_once_with("AGRO-789-012")
            mock_guardar_interaccion.assert_called_once_with(
                1, "test_id_sensor", user_input, expected_response_text
            )

    @patch('module.chatbot.requests.post')
    @patch('module.chatbot.guardar_interaccion')
    @patch('module.chatbot.cargar_contexto_conversacion')
    @patch('module.cultivos.obtener_datos_cultivo')
    def test_chat_cultivo_not_found(self, mock_obtener_datos_cultivo, mock_cargar_contexto, mock_guardar_interaccion, mock_post):
        mock_cargar_contexto.return_value = []
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Respuesta LLM base."}}]
        }
        mock_obtener_datos_cultivo.return_value = None
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor', 'id': 1}
            # Adjusted input to specifically trigger general_match (using 'latitud' as a keyword)
            user_input = "Cuál es la latitud de mi cultivo AGRO-999-999?"
            response = chat(user_input, 1, "test_id_not_found")
            self.assertEqual(response.json['respuesta'], "Cultivo no encontrado o no autorizado para este usuario.")
            mock_obtener_datos_cultivo.assert_called_once_with("AGRO-999-999")
            mock_guardar_interaccion.assert_called_once_with(
                1, "test_id_not_found", user_input, "Cultivo no encontrado o no autorizado para este usuario."
            )

    @patch('module.chatbot.requests.post')
    @patch('module.chatbot.guardar_interaccion')
    @patch('module.chatbot.cargar_contexto_conversacion')
    @patch('module.sensores.obtener_datos_por_cultivo_raw')
    @patch('module.cultivos.obtener_datos_cultivo')
    def test_chat_sensor_no_data(self, mock_obtener_datos_cultivo, mock_obtener_datos_por_cultivo_raw, mock_cargar_contexto, mock_guardar_interaccion, mock_post):
        mock_cargar_contexto.return_value = []
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Respuesta LLM base."}}]
        }
        mock_obtener_datos_cultivo.return_value = {'usuario_id': 1, 'agronomist_id': None, 'numero': 'AGRO-000-000'}
        mock_obtener_datos_por_cultivo_raw.return_value = None
        with app.test_request_context():
            session['usuario'] = {'tipo_usuario': 'agricultor', 'id': 1}
            # Adjusted input to specifically trigger sensor_match (using 'humedad' as a keyword)
            user_input = "Dime la humedad de AGRO-000-000."
            response = chat(user_input, 1, "test_id_no_sensor_data")
            self.assertEqual(response.json['respuesta'], "No se encontraron datos de sensores recientes para este cultivo.")
            mock_obtener_datos_cultivo.assert_called_once_with("AGRO-000-000")
            mock_obtener_datos_por_cultivo_raw.assert_called_once_with("AGRO-000-000")
            mock_guardar_interaccion.assert_called_once_with(
                1, "test_id_no_sensor_data", user_input, "No se encontraron datos de sensores recientes para este cultivo."
            )

if __name__ == '__main__':
    unittest.main()