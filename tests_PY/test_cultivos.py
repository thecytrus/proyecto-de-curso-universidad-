# tests/test_cultivos.py
#----> TERMINAL: python -m unittest tests_PY/test_cultivos.py

import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import json
from flask import Flask, session, jsonify, request

# Import the functions to be tested from your module
from module.cultivos import (
    crear_tabla_cultivos,
    obtener_cultivos,
    obtener_cultivos_por_usuario,
    obtener_cultivos_por_agronomo,
    obtener_datos_cultivo,
    agregar_cultivo,
    editar_cultivo,
    eliminar_cultivo
)

# Helper function to create a mock SQLite row that behaves like sqlite3.Row
class MockSqliteRow(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getitem__(self, key):
        keys_order = ['id', 'numero', 'ciudad', 'agricultor', 'tipo', 'latitud', 'longitud', 'usuario_id', 'agronomist_id']
        if isinstance(key, int):
            if key < len(keys_order):
                return super().__getitem__(keys_order[key])
            else:
                raise IndexError(f"Tuple index out of range: {key}")
        return super().__getitem__(key)


class TestCultivos(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'test_secret_key' # Needed for session handling
        self.client = self.app.test_client()

        # Patch sqlite3.connect for the entire test class
        self.connect_patcher = patch('module.cultivos.sqlite3.connect')
        self.mock_connect = self.connect_patcher.start()

        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Directly set the row_factory attribute on the mock connection
        # The actual function being tested sets this attribute, not calls it.
        # This ensures that when fetchone/fetchall are called, our MockSqliteRow
        # behaves correctly. We don't need to assert it was "called".
        self.mock_conn.row_factory = sqlite3.Row


        # Define routes for the Flask functions that return jsonify responses
        with self.app.app_context():
            # IMPORTANT: The argument names in the route must match the function's parameter names!
            self.app.add_url_rule('/cultivos', view_func=obtener_cultivos, methods=['GET'])
            self.app.add_url_rule('/cultivos/user/<int:usuario_id>', view_func=obtener_cultivos_por_usuario, methods=['GET'])
            self.app.add_url_rule('/cultivos/agronomo/<int:agronomist_id>', view_func=obtener_cultivos_por_agronomo, methods=['GET'])
            self.app.add_url_rule('/cultivos/add', view_func=agregar_cultivo, methods=['POST'])
            self.app.add_url_rule('/cultivos/edit/<string:numero_cultivo>', view_func=editar_cultivo, methods=['PUT'])
            self.app.add_url_rule('/cultivos/delete/<string:numero_cultivo>', view_func=eliminar_cultivo, methods=['DELETE'])

    def tearDown(self):
        self.connect_patcher.stop() # Stop the patcher

    # --- Test Case: crear_tabla_cultivos ---
    def test_crear_tabla_cultivos(self):
        self.mock_cursor.execute.reset_mock()
        self.mock_conn.commit.reset_mock()
        self.mock_conn.close.reset_mock()

        crear_tabla_cultivos()
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()
        self.mock_conn.close.assert_called_once()

    # --- Test Case: obtener_cultivos ---
    def test_obtener_cultivos(self):
        mock_cultivos_data = [
            MockSqliteRow({'id': 1, 'numero': 'AGRO-1-1', 'ciudad': 'Curico', 'agricultor': 'Juan Perez', 'tipo': 'Trigo', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1, 'agronomist_id': 10}),
            MockSqliteRow({'id': 2, 'numero': 'AGRO-1-2', 'ciudad': 'Talca', 'agricultor': 'Maria Lopez', 'tipo': 'Maiz', 'latitud': -35.43, 'longitud': -71.65, 'usuario_id': 2, 'agronomist_id': 10})
        ]
        self.mock_cursor.fetchall.return_value = mock_cultivos_data

        with self.app.app_context():
            response = self.client.get('/cultivos')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), [dict(row) for row in mock_cultivos_data])
            self.mock_cursor.execute.assert_called_once_with("SELECT * FROM cultivos")
            self.mock_conn.close.assert_called_once()

    # --- Test Case: obtener_cultivos_por_usuario ---
    def test_obtener_cultivos_por_usuario(self):
        mock_cultivos_data = [
            MockSqliteRow({'id': 1, 'numero': 'AGRO-1-1', 'ciudad': 'Curico', 'agricultor': 'Juan Perez', 'tipo': 'Trigo', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1, 'agronomist_id': 10})
        ]
        self.mock_cursor.fetchall.return_value = mock_cultivos_data

        with self.app.app_context():
            response = self.client.get('/cultivos/user/1')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), [dict(row) for row in mock_cultivos_data])
            self.mock_cursor.execute.assert_called_once_with("SELECT * FROM cultivos WHERE usuario_id=?", (1,))
            self.mock_conn.close.assert_called_once()

    # --- Test Case: obtener_cultivos_por_agronomo ---
    def test_obtener_cultivos_por_agronomo(self):
        mock_cultivos_data = [
            MockSqliteRow({'id': 1, 'numero': 'AGRO-1-1', 'ciudad': 'Curico', 'agricultor': 'Juan Perez', 'tipo': 'Trigo', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1, 'agronomist_id': 10}),
            MockSqliteRow({'id': 2, 'numero': 'AGRO-1-2', 'ciudad': 'Talca', 'agricultor': 'Maria Lopez', 'tipo': 'Maiz', 'latitud': -35.43, 'longitud': -71.65, 'usuario_id': 2, 'agronomist_id': 10})
        ]
        self.mock_cursor.fetchall.return_value = mock_cultivos_data

        with self.app.app_context():
            response = self.client.get('/cultivos/agronomo/10')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), [dict(row) for row in mock_cultivos_data])
            self.mock_cursor.execute.assert_called_once_with("SELECT * FROM cultivos WHERE agronomist_id=?", (10,))
            self.mock_conn.close.assert_called_once()

    # --- Test Case: obtener_datos_cultivo ---
    def test_obtener_datos_cultivo_found(self):
        mock_cultivo_data = MockSqliteRow({'id': 1, 'numero': 'AGRO-1-1', 'ciudad': 'Curico', 'agricultor': 'Juan Perez', 'tipo': 'Trigo', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1, 'agronomist_id': 10})
        self.mock_cursor.fetchone.return_value = mock_cultivo_data
        self.mock_cursor.execute.reset_mock()

        result = obtener_datos_cultivo('AGRO-1-1')
        self.assertEqual(result, dict(mock_cultivo_data))
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM cultivos WHERE numero=?", ('AGRO-1-1',))
        self.mock_conn.close.assert_called_once()

    def test_obtener_datos_cultivo_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.execute.reset_mock()

        result = obtener_datos_cultivo('NON-EXISTENT')
        self.assertIsNone(result)
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM cultivos WHERE numero=?", ('NON-EXISTENT',))
        self.mock_conn.close.assert_called_once()

    # --- Test Case: agregar_cultivo ---
    def test_agregar_cultivo_success(self):
        mock_request_json = {
            'ciudad': 'Curico',
            'tipo': 'Tomate',
            'latitud': -34.98,
            'longitud': -71.22,
            'usuario_id': 1
        }
        self.mock_cursor.fetchone.side_effect = [
            ('Juan Perez',), # For fetching agricultor_nombre
            (0,)             # For initial COUNT(*) = 0
        ]
        self.mock_cursor.execute.reset_mock()

        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                sess['usuario'] = {'id': 10, 'tipo_usuario': 'agronomo'}

            response = self.client.post('/cultivos/add', json=mock_request_json)
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data)
            self.assertEqual(response_data['message'], "Cultivo agregado exitosamente")
            self.assertIn('AGRO-10-', response_data['numero'])

            self.mock_cursor.execute.assert_any_call("SELECT nombre FROM usuarios WHERE id=?", (1,))
            self.mock_cursor.execute.assert_any_call("SELECT COUNT(*) FROM cultivos WHERE agronomist_id=?", (10,))
            self.mock_cursor.execute.assert_any_call(
                """
            INSERT INTO cultivos (numero, ciudad, agricultor, tipo, latitud, longitud, usuario_id, agronomist_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
                (response_data['numero'], 'Curico', 'Juan Perez', 'Tomate', -34.98, -71.22, 1, 10)
            )
            self.mock_conn.commit.assert_called_once()
            self.mock_conn.close.assert_called_once()


    def test_agregar_cultivo_unauthorized(self):
        mock_request_json = {
            'ciudad': 'Curico', 'tipo': 'Tomate', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1
        }
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                sess['usuario'] = {'id': 1, 'tipo_usuario': 'agricultor'} # Non-agronomist user
            response = self.client.post('/cultivos/add', json=mock_request_json)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(json.loads(response.data)['message'], "Usuario no autorizado o no es agrónomo")
            self.mock_conn.commit.assert_not_called()
            self.mock_conn.close.assert_not_called()

    def test_agregar_cultivo_invalid_data(self):
        mock_request_json = {'ciudad': 'Curico'} # Intentionally missing data
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                sess['usuario'] = {'id': 10, 'tipo_usuario': 'agronomo'}
            response = self.client.post('/cultivos/add', json=mock_request_json)
            self.assertEqual(response.status_code, 400)
            self.assertIn("Datos inválidos o incompletos", json.loads(response.data)['message'])
            self.mock_conn.commit.assert_not_called()

    def test_agregar_cultivo_agricultor_not_found(self):
        mock_request_json = {
            'ciudad': 'Curico', 'tipo': 'Tomate', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 999
        }
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                sess['usuario'] = {'id': 10, 'tipo_usuario': 'agronomo'}
            self.mock_cursor.fetchone.return_value = None
            self.mock_cursor.execute.reset_mock()

            response = self.client.post('/cultivos/add', json=mock_request_json)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(json.loads(response.data)['message'], "Agricultor no encontrado con ese usuario_id")
            self.mock_conn.close.assert_called_once()
            self.mock_conn.commit.assert_not_called()


    def test_agregar_cultivo_integrity_error(self):
        mock_request_json = {
            'ciudad': 'Curico', 'tipo': 'Tomate', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1
        }
        with self.app.test_request_context():
            with self.client.session_transaction() as sess:
                sess['usuario'] = {'id': 10, 'tipo_usuario': 'agronomo'}

            self.mock_cursor.fetchone.side_effect = [
                ('Juan Perez',),
                (0,)
            ]
            self.mock_cursor.execute.reset_mock()
            def execute_side_effect(query, params=None):
                if "INSERT INTO cultivos" in query:
                    raise sqlite3.IntegrityError("UNIQUE constraint failed: cultivos.numero")
                # For other queries, return a mock that does nothing or returns empty results
                # This ensures previous execute calls (like for fetching agricultor_nombre or count) work
                mock_return = MagicMock()
                mock_return.fetchone.return_value = None
                mock_return.fetchall.return_value = []
                return mock_return
            self.mock_cursor.execute.side_effect = execute_side_effect

            response = self.client.post('/cultivos/add', json=mock_request_json)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(json.loads(response.data)['message'], "Error al insertar cultivo. Verifica que no esté duplicado.")
            self.mock_conn.commit.assert_not_called()
            self.mock_conn.close.assert_called_once()


    # --- Test Case: editar_cultivo ---
    def test_editar_cultivo_success(self):
        mock_cultivo_existing_data = MockSqliteRow({
            'id': 1, 'numero': 'AGRO-1-1', 'ciudad': 'Curico', 'agricultor': 'Juan Perez',
            'tipo': 'Trigo', 'latitud': -34.98, 'longitud': -71.22, 'usuario_id': 1, 'agronomist_id': 10
        })
        mock_update_data = {
            'ciudad': 'Santiago',
            'tipo': 'Maiz',
            'latitud': -33.45,
            'longitud': -70.66,
            'usuario_id': 1
        }
        self.mock_cursor.fetchone.return_value = mock_cultivo_existing_data
        self.mock_cursor.rowcount = 1
        self.mock_cursor.execute.reset_mock()

        with self.app.test_request_context():
            response = self.client.put('/cultivos/edit/AGRO-1-1', json=mock_update_data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data)['message'], "Cultivo AGRO-1-1 actualizado exitosamente")

            # Verifica que el SELECT se haya llamado
            self.mock_cursor.execute.assert_any_call("SELECT * FROM cultivos WHERE numero=?", ('AGRO-1-1',))

            # Verifica la llamada al UPDATE sin importar formato exacto del string SQL
            called_args = self.mock_cursor.execute.call_args
            actual_sql, actual_params = called_args[0]

            self.assertIn("UPDATE cultivos SET", actual_sql)
            self.assertEqual(actual_params, [
                mock_update_data['ciudad'],
                mock_update_data['tipo'],
                mock_update_data['latitud'],
                mock_update_data['longitud'],
                mock_update_data['usuario_id'],
                'AGRO-1-1'
            ])

            self.mock_conn.commit.assert_called_once()
            self.mock_conn.close.assert_called_once()


    def test_editar_cultivo_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.execute.reset_mock()

        with self.app.test_request_context(json={"ciudad": "X"}):  # Enviar dato válido para pasar validación
            response = self.client.put('/cultivos/edit/NON-EXISTENT', json={"ciudad": "X"})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.data)['message'], "Cultivo con número NON-EXISTENT no encontrado")
            self.mock_cursor.execute.assert_called_once_with("SELECT * FROM cultivos WHERE numero=?", ('NON-EXISTENT',))
            self.mock_conn.close.assert_called_once()
            self.mock_conn.commit.assert_not_called()

    # --- Test Case: eliminar_cultivo ---
    def test_eliminar_cultivo_success(self):
        self.mock_cursor.rowcount = 1
        self.mock_cursor.execute.reset_mock()

        with self.app.test_request_context():
            response = self.client.delete('/cultivos/delete/AGRO-1-1')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data)['message'], "Cultivo AGRO-1-1 eliminado exitosamente")
            self.mock_cursor.execute.assert_called_once_with("DELETE FROM cultivos WHERE numero=?", ('AGRO-1-1',))
            self.mock_conn.commit.assert_called_once()
            self.mock_conn.close.assert_called_once()

    def test_eliminar_cultivo_not_found(self):
        self.mock_cursor.rowcount = 0
        self.mock_cursor.execute.reset_mock()

        with self.app.test_request_context():
            response = self.client.delete('/cultivos/delete/NON-EXISTENT')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.data)['message'], "Cultivo con número NON-EXISTENT no encontrado")
            self.mock_cursor.execute.assert_called_once_with("DELETE FROM cultivos WHERE numero=?", ('NON-EXISTENT',))
            self.mock_conn.close.assert_called_once()
            self.mock_conn.commit.assert_called_once() # Commit is still called even if no rows are affected

if __name__ == '__main__':
    unittest.main()