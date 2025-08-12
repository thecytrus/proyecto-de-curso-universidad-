# tests/test_alertas.py
#----> TERMINAL: python -m unittest tests_PY/test_alertas.py

import unittest
from unittest.mock import patch, MagicMock
import sqlite3
from datetime import datetime, timedelta
import os
import builtins # Import builtins for patching print
from module.alertas import (
    enviar_notificacion_email,
    crear_tabla_alertas,
    crear_tabla_historial_alertas,
    activar_alerta,
    get_user_email,
    verificar_alertas,
    DATABASE # Import DATABASE from alertas to use it for testing
)
from flask import session, Flask

app = Flask(__name__)
app.secret_key = 'test_secret_key'

class TestAlertas(unittest.TestCase):

    def setUp(self):
        """Set up for each test: create a temporary database."""
        self.test_db = 'test_users.db'
        # Temporarily change the DATABASE path for testing
        self.original_database = DATABASE
        # We need to patch the DATABASE global variable in the alertas module
        # This is a bit tricky as global variables aren't easily mocked directly like functions
        # For simplicity in this test, we'll ensure the functions themselves connect to self.test_db
        # Or, a more robust way would be to pass the db path to functions or use a class-based system.
        # For now, let's just make sure the test functions use a temporary DB.

        # Ensure the DATABASE constant in alertas.py points to the test DB during tests
        # This requires modifying the module's global state, which can be risky.
        # A better design would be to pass the database path to functions, or use a dependency injection.
        # For this example, we'll use a patch for simplicity.
        self.db_patcher = patch('module.alertas.DATABASE', self.test_db)
        self.db_patcher.start()

        self.conn = sqlite3.connect(self.test_db)
        self.cursor = self.conn.cursor()

        # Create necessary tables for testing
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cultivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER,
                usuario_id INTEGER,
                agronomist_id INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (agronomist_id) REFERENCES usuarios (id)
            )
        ''')
        self.conn.commit()
        self.conn.close()

        crear_tabla_alertas()
        crear_tabla_historial_alertas()

    def tearDown(self):
        """Clean up after each test: remove the temporary database."""
        self.db_patcher.stop()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    @patch('module.alertas.smtplib.SMTP')
    def test_enviar_notificacion_email_success(self, mock_smtp):
        """Test successful email notification sending."""
        mock_instance = mock_smtp.return_value.__enter__.return_value
        destinatario = "test@example.com"
        asunto = "Test Subject"
        mensaje = "Test Message"

        with patch('builtins.print') as mock_print: # Patch print for this test
            enviar_notificacion_email(destinatario, asunto, mensaje)

            mock_smtp.assert_called_once_with('smtp.gmail.com', 587)
            mock_instance.starttls.assert_called_once()
            mock_instance.login.assert_called_once_with('ecos75396@gmail.com', 'jdai wnww gybb yzlx')
            mock_instance.send_message.assert_called_once()

            # Inspect the message object directly
            sent_message = mock_instance.send_message.call_args[0][0]
            self.assertIn(destinatario, sent_message['To'])
            self.assertEqual(sent_message['Subject'], asunto)
            self.assertEqual(sent_message.get_payload(decode=True).decode('utf-8'), mensaje)
            
            mock_print.assert_called_once_with(f"[INFO] Correo de alerta enviado a {destinatario}: '{asunto}'")


    @patch('module.alertas.smtplib.SMTP', side_effect=Exception("SMTP Error"))
    def test_enviar_notificacion_email_failure(self, mock_smtp):
        """Test email notification sending failure."""
        destinatario = "test@example.com"
        asunto = "Test Subject"
        mensaje = "Test Message"

        with patch('builtins.print') as mock_print: # Patch print for this test
            enviar_notificacion_email(destinatario, asunto, mensaje)
            mock_print.assert_called_once()
            self.assertIn("[ERROR] Error al enviar correo de alerta", mock_print.call_args[0][0])

    def test_crear_tabla_alertas(self):
        """Test if the 'alertas' table is created correctly."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(alertas)")
        columns = [column[1] for column in cursor.fetchall()]
        conn.close()
        self.assertIn('id', columns)
        self.assertIn('tipo_alerta', columns)
        self.assertIn('umbral', columns)
        self.assertIn('condicion', columns)
        self.assertIn('activa', columns)

    def test_crear_tabla_historial_alertas(self):
        """Test if the 'historial_alertas' table is created correctly."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(historial_alertas)")
        columns = [column[1] for column in cursor.fetchall()]
        conn.close()
        self.assertIn('id', columns)
        self.assertIn('alerta_id', columns)
        self.assertIn('usuario_id', columns)
        self.assertIn('agronomist_id', columns)
        self.assertIn('fecha', columns)
        self.assertIn('numero_cultivo', columns)
        self.assertIn('valor_sensor', columns)

    def test_activar_alerta(self):
        """Test logging an alert activation to the history."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy user data
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("user1@example.com",))
        usuario_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist1@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy alert
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 1))
        alerta_id = cursor.lastrowid
        conn.commit()

        numero_cultivo = 101
        valor_sensor = 26.5
        
        with patch('builtins.print') as mock_print:
            activar_alerta(alerta_id, usuario_id, agronomist_id, numero_cultivo, valor_sensor)
            mock_print.assert_called_once_with(f"[INFO] Alerta ID {alerta_id} registrada para cultivo {numero_cultivo}, usuario {usuario_id}, valor sensor {valor_sensor}")


        cursor.execute("SELECT * FROM historial_alertas WHERE alerta_id = ? AND usuario_id = ?",
                       (alerta_id, usuario_id))
        record = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(record)
        self.assertEqual(record[1], alerta_id)  # alerta_id
        self.assertEqual(record[2], usuario_id)  # usuario_id
        self.assertEqual(record[3], agronomist_id)  # agronomist_id
        self.assertEqual(record[5], numero_cultivo) # numero_cultivo
        self.assertEqual(record[6], valor_sensor) # valor_sensor

    def test_get_user_email(self):
        """Test retrieving user email by ID."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("test_user@example.com",))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        email = get_user_email(user_id)
        self.assertEqual(email, "test_user@example.com")

        email_not_found = get_user_email(999) # Non-existent ID
        self.assertIsNone(email_not_found)

    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_trigger(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test that an alert triggers and sends email when conditions are met."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy users
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("farmer@example.com",))
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy crop linked to the users
        numero_cultivo = 123
        cursor.execute("INSERT INTO cultivos (numero, usuario_id, agronomist_id) VALUES (?, ?, ?)",
                       (numero_cultivo, farmer_id, agronomist_id))
        conn.commit()

        # Insert an active alert
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 1))
        alerta_id = cursor.lastrowid
        conn.commit()
        conn.close()

        datos_sensor = {"temperatura": 26.0, "humedad": 70.0, "unidad": "°C"}

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            # You can add assertions for print calls if needed, e.g., for DEBUG messages
            # For simplicity, we'll just check if triggered is True and emails were sent

        self.assertTrue(triggered)
        mock_activar_alerta.assert_called_once_with(alerta_id, farmer_id, agronomist_id, numero_cultivo, 26.0)
        self.assertEqual(mock_enviar_notificacion_email.call_count, 2) # Farmer and Agronomist

        # Check farmer's email
        args_farmer, kwargs_farmer = mock_enviar_notificacion_email.call_args_list[0]
        self.assertEqual(args_farmer[0], "farmer@example.com")
        self.assertIn("¡Alerta EcoSmart - Cultivo 123!", args_farmer[1])
        self.assertIn("Temperatura", args_farmer[2])

        # Check agronomist's email
        args_agronomist, kwargs_agronomist = mock_enviar_notificacion_email.call_args_list[1]
        self.assertEqual(args_agronomist[0], "agronomist@example.com")
        self.assertIn("¡Alerta EcoSmart - Cultivo 123!", args_agronomist[1])
        self.assertIn("Alerta del cultivo asignado #123", args_agronomist[2])


    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_no_trigger_condition_not_met(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test that no alert triggers if conditions are not met."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy users
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("farmer@example.com",))
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy crop linked to the users
        numero_cultivo = 123
        cursor.execute("INSERT INTO cultivos (numero, usuario_id, agronomist_id) VALUES (?, ?, ?)",
                       (numero_cultivo, farmer_id, agronomist_id))
        conn.commit()

        # Insert an active alert (temp > 25)
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 1))
        alerta_id = cursor.lastrowid
        conn.commit()
        conn.close()

        datos_sensor = {"temperatura": 24.0, "humedad": 70.0, "unidad": "°C"} # Temperature below threshold

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            # Assert that the print for 'Condición no cumplida' was called
            # We can check specific calls if needed, or just that it was printed
            mock_print.assert_any_call(f"[DEBUG] Condición no cumplida para alerta ID {alerta_id}.")


        self.assertFalse(triggered)
        mock_activar_alerta.assert_not_called()
        mock_enviar_notificacion_email.assert_not_called()

    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_no_trigger_recent_alert(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test that an alert does not re-trigger if sent recently."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy users
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("farmer@example.com",))
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy crop linked to the users
        numero_cultivo = 123
        cursor.execute("INSERT INTO cultivos (numero, usuario_id, agronomist_id) VALUES (?, ?, ?)",
                       (numero_cultivo, farmer_id, agronomist_id))
        conn.commit()

        # Insert an active alert
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 1))
        alerta_id = cursor.lastrowid
        conn.commit()

        # Insert a recent alert into history (within 15 minutes)
        recent_time = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO historial_alertas (alerta_id, usuario_id, agronomist_id, fecha, numero_cultivo, valor_sensor) VALUES (?, ?, ?, ?, ?, ?)",
            (alerta_id, farmer_id, agronomist_id, recent_time, numero_cultivo, 26.0)
        )
        conn.commit()
        conn.close()

        datos_sensor = {"temperatura": 26.0, "humedad": 70.0, "unidad": "°C"}

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            mock_print.assert_any_call(f"[DEBUG] Alerta ID {alerta_id} ya enviada recientemente.")

        self.assertFalse(triggered)
        mock_activar_alerta.assert_not_called()
        mock_enviar_notificacion_email.assert_not_called()

    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_trigger_after_cooldown(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test that an alert triggers if enough time has passed since the last notification."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy users
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("farmer@example.com",))
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy crop linked to the users
        numero_cultivo = 123
        cursor.execute("INSERT INTO cultivos (numero, usuario_id, agronomist_id) VALUES (?, ?, ?)",
                       (numero_cultivo, farmer_id, agronomist_id))
        conn.commit()

        # Insert an active alert
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 1))
        alerta_id = cursor.lastrowid
        conn.commit()

        # Insert an old alert into history (more than 15 minutes ago)
        old_time = (datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO historial_alertas (alerta_id, usuario_id, agronomist_id, fecha, numero_cultivo, valor_sensor) VALUES (?, ?, ?, ?, ?, ?)",
            (alerta_id, farmer_id, agronomist_id, old_time, numero_cultivo, 26.0)
        )
        conn.commit()
        conn.close()

        datos_sensor = {"temperatura": 26.0, "humedad": 70.0, "unidad": "°C"}

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            # The exact print statement for successful logging is inside activar_alerta, which is mocked.
            # We can assert on other debug prints or just the overall outcome.

        self.assertTrue(triggered)
        mock_activar_alerta.assert_called_once_with(alerta_id, farmer_id, agronomist_id, numero_cultivo, 26.0)
        self.assertEqual(mock_enviar_notificacion_email.call_count, 2)

    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_no_crop_found(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test that no alert triggers if the crop is not found."""
        numero_cultivo = 999
        datos_sensor = {"temperatura": 26.0}

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            mock_print.assert_called_once()
            self.assertIn(f"[WARN] No se encontró el cultivo número {numero_cultivo}.", mock_print.call_args[0][0])

        self.assertFalse(triggered)
        mock_activar_alerta.assert_not_called()
        mock_enviar_notificacion_email.assert_not_called()

    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_inactive_alert(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test that an inactive alert does not trigger."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy users
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("farmer@example.com",))
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy crop linked to the users
        numero_cultivo = 123
        cursor.execute("INSERT INTO cultivos (numero, usuario_id, agronomist_id) VALUES (?, ?, ?)",
                       (numero_cultivo, farmer_id, agronomist_id))
        conn.commit()

        # Insert an inactive alert
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 0)) # activa = 0
        conn.commit()
        conn.close()

        datos_sensor = {"temperatura": 26.0, "humedad": 70.0, "unidad": "°C"}

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            # Check for DEBUG prints related to alert evaluation but no trigger
            mock_print.assert_any_call(f"[DEBUG] 0 alerta(s) activa(s) encontrada(s).")


        self.assertFalse(triggered)
        mock_activar_alerta.assert_not_called()
        mock_enviar_notificacion_email.assert_not_called()

    @patch('module.alertas.enviar_notificacion_email')
    @patch('module.alertas.activar_alerta')
    def test_verificar_alertas_no_email_for_farmer(self, mock_activar_alerta, mock_enviar_notificacion_email):
        """Test alert triggers but no email sent if farmer email is missing."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Insert dummy user without email for farmer
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", (None,))
        farmer_id = cursor.lastrowid
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", ("agronomist@example.com",))
        agronomist_id = cursor.lastrowid
        conn.commit()

        # Insert a dummy crop linked to the users
        numero_cultivo = 123
        cursor.execute("INSERT INTO cultivos (numero, usuario_id, agronomist_id) VALUES (?, ?, ?)",
                       (numero_cultivo, farmer_id, agronomist_id))
        conn.commit()

        # Insert an active alert
        cursor.execute("INSERT INTO alertas (tipo_alerta, umbral, condicion, activa) VALUES (?, ?, ?, ?)",
                       ("temperatura", 25.0, ">", 1))
        alerta_id = cursor.lastrowid
        conn.commit()
        conn.close()

        datos_sensor = {"temperatura": 26.0, "humedad": 70.0, "unidad": "°C"}

        with patch('builtins.print') as mock_print:
            triggered = verificar_alertas(numero_cultivo, datos_sensor)
            mock_print.assert_any_call(f"[WARN] No se encontró email para agricultor {farmer_id}.")


        self.assertTrue(triggered) # The alert still technically triggered and was logged
        mock_activar_alerta.assert_called_once()
        mock_enviar_notificacion_email.assert_called_once() # Only agronomist email should be sent

        args, kwargs = mock_enviar_notificacion_email.call_args_list[0]
        self.assertEqual(args[0], "agronomist@example.com")


if __name__ == '__main__':
    unittest.main()