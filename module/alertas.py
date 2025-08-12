import sqlite3
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header  # Para manejar caracteres especiales en el asunto

DATABASE = "users.db"

def enviar_notificacion_email(destinatario, asunto, mensaje):
    EMAIL_ADDRESS = 'ecos75396@gmail.com'
    EMAIL_PASSWORD = 'jdai wnww gybb yzlx' #NUEVA
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587

    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER]):
        print("[WARN] Configuración de correo electrónico incompleta. No se puede enviar el correo.")
        return

    msg = MIMEText(mensaje, 'plain', 'utf-8')
    msg['Subject'] = Header(asunto, 'utf-8')
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = destinatario

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"[INFO] Correo de alerta enviado a {destinatario}: '{asunto}'")
    except Exception as e:
        print(f"[ERROR] Error al enviar correo de alerta a {destinatario}: {e}")

def crear_tabla_alertas():
    """Crea la tabla 'alertas' si no existe."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_alerta TEXT,
            umbral REAL,
            condicion TEXT,
            activa BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def crear_tabla_historial_alertas():
    """Crea la tabla 'historial_alertas' si no existe."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alerta_id INTEGER,
            usuario_id INTEGER NOT NULL,
            agronomist_id INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            numero_cultivo INTEGER,
            valor_sensor REAL,
            FOREIGN KEY (alerta_id) REFERENCES alertas (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (agronomist_id) REFERENCES usuarios (id)
        )
    ''')
    conn.commit()
    conn.close()


def activar_alerta(alerta_id, usuario_id, agronomist_id, numero_cultivo, valor_sensor):
    """Registra una activación de alerta en el historial."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO historial_alertas (alerta_id, usuario_id, agronomist_id, fecha, numero_cultivo, valor_sensor) VALUES (?, ?, ?, ?, ?, ?)",
            (alerta_id, usuario_id, agronomist_id, timestamp_actual, numero_cultivo, valor_sensor)
        )
        conn.commit()
        print(f"[INFO] Alerta ID {alerta_id} registrada para cultivo {numero_cultivo}, usuario {usuario_id}, valor sensor {valor_sensor}")
    except Exception as e:
        print(f"[ERROR] Error al insertar en historial_alertas: {e}")
    finally:
        conn.close()

def get_user_email(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM usuarios WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def verificar_alertas(numero_cultivo, datos):
    triggered = False
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT usuario_id, agronomist_id FROM cultivos WHERE numero = ?", (numero_cultivo,))
    row = cursor.fetchone()
    if not row:
        print(f"[WARN] No se encontró el cultivo número {numero_cultivo}.")
        conn.close()
        return False

    usuario_id = row["usuario_id"]
    agronomist_id = row["agronomist_id"]
    print(f"[DEBUG] Cultivo {numero_cultivo}: usuario_id={usuario_id}, agronomist_id={agronomist_id}")
    print("[DEBUG] Datos recibidos del sensor:", datos)

    agricultor_email = get_user_email(usuario_id)
    agronomo_email = get_user_email(agronomist_id) if agronomist_id else None

    cursor.execute("SELECT * FROM alertas WHERE activa = 1")
    alertas = cursor.fetchall()
    print(f"[DEBUG] {len(alertas)} alerta(s) activa(s) encontrada(s).")

    for alerta in alertas:
        tipo_alerta = alerta["tipo_alerta"]
        condicion = alerta["condicion"]
        umbral = alerta["umbral"]
        alerta_id = alerta["id"]

        valor_sensor = datos.get(tipo_alerta)
        if valor_sensor is None:
            print(f"[DEBUG] No se encontró '{tipo_alerta}' en los datos. Se omite la alerta.")
            continue

        try:
            valor_sensor = float(valor_sensor)
            umbral = float(umbral)
        except Exception as e:
            print(f"[ERROR] Fallo conversión numérica para alerta ID {alerta_id}: {e}")
            continue

        cumple = False
        if condicion == '>' and valor_sensor > umbral:
            cumple = True
        elif condicion == '<' and valor_sensor < umbral:
            cumple = True
        elif condicion == '>=' and valor_sensor >= umbral:
            cumple = True
        elif condicion == '<=' and valor_sensor <= umbral:
            cumple = True
        elif condicion == '==' and valor_sensor == umbral:
            cumple = True

        print(f"[DEBUG] Evaluando alerta ID {alerta_id}: {valor_sensor} {condicion} {umbral} => {cumple}")

        if cumple:
            cursor.execute("""
                SELECT fecha FROM historial_alertas 
                WHERE alerta_id = ? AND usuario_id = ?
                ORDER BY fecha DESC LIMIT 1
            """, (alerta_id, usuario_id))
            last = cursor.fetchone()

            should_send = True
            if last:
                try:
                    last_time = datetime.strptime(last["fecha"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - last_time).total_seconds() < 15 * 60: # 15 minutos
                        print(f"[DEBUG] Alerta ID {alerta_id} ya enviada recientemente.")
                        should_send = False
                except Exception as e:
                    print(f"[ERROR] Error parseando fecha: {e}")

            if should_send:
                activar_alerta(alerta_id, usuario_id, agronomist_id, numero_cultivo, valor_sensor)
                triggered = True

                asunto = f"¡Alerta EcoSmart - Cultivo {numero_cultivo}!"
                mensaje_base = (
                    f"Se ha detectado una condición inusual en el cultivo número {numero_cultivo}.\n\n"
                    f"Tipo de Alerta: {tipo_alerta.replace('_', ' ').title()}\n"
                    f"Condición: {valor_sensor} {condicion} {umbral} {datos.get('unidad', '')}\n"
                    f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "Por favor, revisa el panel de EcoSmart."
                )

                if agricultor_email:
                    enviar_notificacion_email(agricultor_email, asunto, mensaje_base)
                else:
                    print(f"[WARN] No se encontró email para agricultor {usuario_id}.")

                if agronomo_email:
                    mensaje_agronomo = (
                        f"Alerta del cultivo asignado #{numero_cultivo}.\n\n{mensaje_base}"
                    )
                    enviar_notificacion_email(agronomo_email, asunto, mensaje_agronomo)
                elif agronomist_id:
                    print(f"[WARN] No se encontró email para agrónomo {agronomist_id}.")
        else:
            print(f"[DEBUG] Condición no cumplida para alerta ID {alerta_id}.")

    conn.close()
    return triggered
