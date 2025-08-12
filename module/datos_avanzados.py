import sqlite3
import math
from flask import jsonify
from datetime import datetime, timedelta
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import json
from email.mime.multipart import MIMEMultipart

# Configuración de la base de datos
DATABASE = "users.db"

# Configuración para OpenRouter
API_KEY = "apikey from openrouter"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324:free" # Modelo a utilizar

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ecosmart-app.com",  # Reemplaza con tu dominio real
    "X-Title": "EcoSmartBot"
}

# Configuración de correo electrónico
EMAIL_ADDRESS = 'ecos75396@gmail.com'
EMAIL_PASSWORD = 'jdai wnww gybb yzlx'#clave nueva 
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# OpenWeatherMap API Key 
OPENWEATHER_API_KEY = "apikey from openweathermap"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"

def crear_tabla_datos_avanzados():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos_avanzados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cultivo TEXT NOT NULL,
            humedad_ultimo REAL,
            humedad_maximo REAL,
            humedad_minimo REAL,
            humedad_promedio REAL,
            humedad_desviacion REAL,
            humedad_anomalia INTEGER DEFAULT 0,
            ph_ultimo REAL,
            ph_maximo REAL,
            ph_minimo REAL,
            ph_promedio REAL,
            ph_desviacion REAL,
            ph_anomalia INTEGER DEFAULT 0,
            temp_ultimo REAL,
            temp_maximo REAL,
            temp_minimo REAL,
            temp_promedio REAL,
            temp_desviacion REAL,
            temp_anomalia INTEGER DEFAULT 0,
            nitrogeno_ultimo REAL,
            nitrogeno_maximo REAL,
            nitrogeno_minimo REAL,
            nitrogeno_promedio REAL,
            nitrogeno_desviacion REAL,
            nitrogeno_anomalia INTEGER DEFAULT 0,
            fosforo_ultimo REAL,
            fosforo_maximo REAL,
            fosforo_minimo REAL,
            fosforo_promedio REAL,
            fosforo_desviacion REAL,
            fosforo_anomalia INTEGER DEFAULT 0,
            potasio_ultimo REAL,
            potasio_maximo REAL,
            potasio_minimo REAL,
            potasio_promedio REAL,
            potasio_desviacion REAL,
            potasio_anomalia INTEGER DEFAULT 0,
            probabilidad_lluvia REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (numero_cultivo) REFERENCES cultivos(numero)
        )
    """)
    conn.commit()
    conn.close()

def obtener_destinatarios_cultivo(numero_cultivo):
    """Obtiene los emails del agricultor y agrónomo asociados a un cultivo"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u1.email as agricultor_email, u2.email as agronomo_email
        FROM cultivos c
        LEFT JOIN usuarios u1 ON c.usuario_id = u1.id
        LEFT JOIN usuarios u2 ON c.agronomist_id = u2.id
        WHERE c.numero = ?
    """, (numero_cultivo,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise ValueError(f"No se encontró el cultivo {numero_cultivo}")
    
    agricultor_email = result[0]
    agronomo_email = result[1] if result[1] else None
    
    # Obtener coordenadas para el pronóstico
    lat, lon = obtener_coordenadas_cultivo(numero_cultivo)
    if not lat or not lon:
        raise ValueError("No se encontraron coordenadas para el cultivo")
    
    return lat, lon, numero_cultivo, agronomo_email, agricultor_email

def obtener_datos_avanzados(numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM datos_avanzados 
        WHERE numero_cultivo = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (numero_cultivo,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": "No hay datos avanzados para este cultivo"}, 404
    
    datos = {
        "humedad": {
            "ultimo": row["humedad_ultimo"],
            "maximo": row["humedad_maximo"],
            "minimo": row["humedad_minimo"],
            "promedio": row["humedad_promedio"],
            "desviacion": row["humedad_desviacion"],
            "anomalia": row["humedad_anomalia"]
        },
        "ph": {
            "ultimo": row["ph_ultimo"],
            "maximo": row["ph_maximo"],
            "minimo": row["ph_minimo"],
            "promedio": row["ph_promedio"],
            "desviacion": row["ph_desviacion"],
            "anomalia": row["ph_anomalia"]
        },
        "temp": {
            "ultimo": row["temp_ultimo"],
            "maximo": row["temp_maximo"],
            "minimo": row["temp_minimo"],
            "promedio": row["temp_promedio"],
            "desviacion": row["temp_desviacion"],
            "anomalia": row["temp_anomalia"]
        },
        "nitrogeno": {
            "ultimo": row["nitrogeno_ultimo"],
            "maximo": row["nitrogeno_maximo"],
            "minimo": row["nitrogeno_minimo"],
            "promedio": row["nitrogeno_promedio"],
            "desviacion": row["nitrogeno_desviacion"],
            "anomalia": row["nitrogeno_anomalia"]
        },
        "fosforo": {
            "ultimo": row["fosforo_ultimo"],
            "maximo": row["fosforo_maximo"],
            "minimo": row["fosforo_minimo"],
            "promedio": row["fosforo_promedio"],
            "desviacion": row["fosforo_desviacion"],
            "anomalia": row["fosforo_anomalia"]
        },
        "potasio": {
            "ultimo": row["potasio_ultimo"],
            "maximo": row["potasio_maximo"],
            "minimo": row["potasio_minimo"],
            "promedio": row["potasio_promedio"],
            "desviacion": row["potasio_desviacion"],
            "anomalia": row["potasio_anomalia"]
        },
        "probabilidad_lluvia": row["probabilidad_lluvia"],
        "timestamp": row["timestamp"]
    }
    
    return datos

def obtener_recomendaciones_ia(numero_cultivo):
    try:
        lat, lon = obtener_coordenadas_cultivo(numero_cultivo)
        if not lat or not lon:
            return {"error": "No se encontraron coordenadas para el cultivo"}, 404
            
        pronostico = obtener_pronostico_clima(lat, lon)
        if not pronostico:
            return {"error": "No se pudo obtener el pronóstico"}, 500
            
        recomendacion = obtener_recomendacion_clima(pronostico)
        
        return {
            "recommendation": recomendacion,
            "pronostico": pronostico
        }
        
    except Exception as e:
        return {"error": str(e)}, 500

def obtener_pronostico_cultivo(numero_cultivo):
    try:
        lat, lon = obtener_coordenadas_cultivo(numero_cultivo)
        if not lat or not lon:
            return {"error": "Coordenadas no disponibles"}, 404
            
        pronostico = obtener_pronostico_clima(lat, lon)
        if not pronostico:
            return {"error": "No se pudo obtener pronóstico"}, 500
            
        pronostico_formateado = []
        for dia in pronostico[:3]:
            pronostico_formateado.append({
                "fecha": dia.get("fecha", "N/A"),
                "temp": dia.get("temp", "N/A"),
                "probabilidad_lluvia": dia.get("probabilidad_lluvia", "N/A"),
                "description": dia.get("description", "N/A").capitalize()
            })
            
        return pronostico_formateado
        
    except Exception as e:
        return {"error": str(e)}, 500

def calcular_estadisticas(lista_valores):
    if not lista_valores:
        return None, None, None, None, None
    n = len(lista_valores)
    promedio = sum(lista_valores) / n
    varianza = sum((x - promedio) ** 2 for x in lista_valores) / n
    desviacion = math.sqrt(varianza)
    maximo = max(lista_valores)
    minimo = min(lista_valores)
    ultimo = lista_valores[-1]
    return ultimo, maximo, minimo, promedio, desviacion

def detectar_anomalia(current_value, historical_values, threshold_std_dev=2):
    if len(historical_values) < 5:
        return 0
    mean = sum(historical_values) / len(historical_values)
    variance = sum((x - mean) ** 2 for x in historical_values) / len(historical_values)
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return 0

    if abs(current_value - mean) > threshold_std_dev * std_dev:
        return 1
    return 0

def obtener_ultimos_valores_parametro(numero_cultivo, parametro, limit=30):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT {parametro}, timestamp FROM datos_sensores
        WHERE numero_cultivo = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (numero_cultivo, limit))
    
    filas = cursor.fetchall()
    conn.close()
    return [(fila[parametro], fila['timestamp']) for fila in reversed(filas) if fila[parametro] is not None]

def generar_datos_avanzados(numero_cultivo):
    parametros = {
        "humedad_suelo": "humedad",
        "ph_suelo": "ph",
        "temperatura_ambiente": "temp",
        "nitrogeno": "nitrogeno",
        "fosforo": "fosforo",
        "potasio": "potasio"
    }

    datos = {}

    for clave_sensor, prefijo_columna in parametros.items():
        valores_con_timestamp = obtener_ultimos_valores_parametro(numero_cultivo, clave_sensor)
        valores = [val for val, _ in valores_con_timestamp]

        if not valores:
            datos[f"{prefijo_columna}_ultimo"] = None
            datos[f"{prefijo_columna}_maximo"] = None
            datos[f"{prefijo_columna}_minimo"] = None
            datos[f"{prefijo_columna}_promedio"] = None
            datos[f"{prefijo_columna}_desviacion"] = None
            datos[f"{prefijo_columna}_anomalia"] = 0
            continue

        ultimo, maximo, minimo, promedio, desviacion = calcular_estadisticas(valores)
        anomalia = detectar_anomalia(ultimo, valores[:-1]) if len(valores) > 1 else 0

        datos[f"{prefijo_columna}_ultimo"] = ultimo
        datos[f"{prefijo_columna}_maximo"] = maximo
        datos[f"{prefijo_columna}_minimo"] = minimo
        datos[f"{prefijo_columna}_promedio"] = promedio
        datos[f"{prefijo_columna}_desviacion"] = desviacion
        datos[f"{prefijo_columna}_anomalia"] = anomalia

    # Obtener probabilidad de lluvia
    lat, lon = obtener_coordenadas_cultivo(numero_cultivo)
    prob_lluvia = None
    if lat and lon:
        pronosticos = obtener_pronostico_clima(lat, lon)
        if pronosticos:
            prob_lluvia = pronosticos[0].get("probabilidad_lluvia", 0)

    datos['probabilidad_lluvia'] = prob_lluvia

    # Insertar en la tabla datos_avanzados
    columnas = ', '.join(['numero_cultivo'] + list(datos.keys()))
    placeholders = ', '.join(['?'] * (len(datos) + 1))
    valores = [numero_cultivo] + list(datos.values())

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO datos_avanzados ({columnas})
        VALUES ({placeholders})
    """, valores)
    conn.commit()
    conn.close()

    return {"message": f"Datos avanzados generados para cultivo {numero_cultivo}"}, 201

def obtener_coordenadas_cultivo(numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT latitud, longitud FROM cultivos WHERE numero = ?", (numero_cultivo,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return resultado[0], resultado[1]
    return None, None

def obtener_pronostico_clima(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "es"
    }

    try:
        response = requests.get(OPENWEATHER_URL, params=params)
        response.raise_for_status()
        data = response.json()
        lista = data.get("list", [])

        pronosticos_diarios = {}
        for item in lista:
            fecha_txt = item.get("dt_txt")
            if not fecha_txt:
                continue
            dia = fecha_txt.split(" ")[0]
            pronosticos_diarios.setdefault(dia, []).append(item)

        pronosticos_ordenados = []
        fechas_ordenadas = sorted(pronosticos_diarios.keys())[:3]

        for dia in fechas_ordenadas:
            registros = pronosticos_diarios[dia]
            if not registros:
                continue

            temps = [r["main"]["temp"] for r in registros if "main" in r]
            pops = [r.get("pop", 0) for r in registros]
            descripciones = [r["weather"][0]["description"] for r in registros if "weather" in r and r["weather"]]

            resumen = {
                "fecha": dia,
                "temp": sum(temps) / len(temps) if temps else None,
                "probabilidad_lluvia": max(pops) * 100,
                "description": max(set(descripciones), key=descripciones.count) if descripciones else "Sin datos"
            }
            pronosticos_ordenados.append(resumen)

        return pronosticos_ordenados

    except requests.RequestException:
        return None

def obtener_recomendacion_clima(pronostico):
    prompt = (
        "Actúa como un asesor agrícola experto. "
        "A continuación se muestra un pronóstico climático obtenido del sistema. "
        "Proporciona una recomendación breve y práctica para la gestión del cultivo.\n\n"
        f"{json.dumps(pronostico, ensure_ascii=False, indent=2)}"
    )
    
    messages = [
        {"role": "system", "content": "Eres un experto en agricultura y agronomía."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return "No se pudo generar una recomendación en este momento."
    except Exception:
        return "No se pudo obtener recomendación del clima."

def enviar_resumen_clima_email_V2(lat, lon, numero_cultivo, agronomo_email, agricultor_email):
    if not agricultor_email and not agronomo_email:
        return False

    try:
        pronostico = obtener_pronostico_clima(lat, lon)
        if not pronostico:
            return False

        recomendacion = obtener_recomendacion_clima(pronostico)
        
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM datos_avanzados 
            WHERE numero_cultivo = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (numero_cultivo,))
        datos = cursor.fetchone()
        conn.close()

        if not datos:
            return False

        asunto = f"🌱 Resumen EcoSmart - Cultivo {numero_cultivo}"

        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #2e7d32;">Resumen de tu Cultivo {numero_cultivo}</h2>
            
            <h3 style="color: #388e3c;">📊 Datos Actuales</h3>
            <ul>
                <li><strong>Humedad del suelo:</strong> {datos['humedad_ultimo']}% (Prom: {datos['humedad_promedio']}%)</li>
                <li><strong>pH del suelo:</strong> {datos['ph_ultimo']} (Prom: {datos['ph_promedio']})</li>
                <li><strong>Temperatura:</strong> {datos['temp_ultimo']}°C (Prom: {datos['temp_promedio']}°C)</li>
                <li><strong>Nutrientes (N-P-K):</strong> {datos['nitrogeno_ultimo']}-{datos['fosforo_ultimo']}-{datos['potasio_ultimo']} ppm</li>
            </ul>
            
            <h3 style="color: #388e3c;">🌦 Pronóstico del Clima</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #81c784; color: white;">
                    <th style="padding: 8px; text-align: left;">Fecha</th>
                    <th style="padding: 8px; text-align: left;">Temperatura</th>
                    <th style="padding: 8px; text-align: left;">Lluvia</th>
                    <th style="padding: 8px; text-align: left;">Condición</th>
                </tr>
        """

        for dia in pronostico[:3]:
            mensaje_html += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 8px;">{dia['fecha']}</td>
                    <td style="padding: 8px;">{dia['temp']}°C</td>
                    <td style="padding: 8px;">{dia['probabilidad_lluvia']}%</td>
                    <td style="padding: 8px;">{dia['description'].capitalize()}</td>
                </tr>
            """

        mensaje_html += f"""
            </table>
            
            <h3 style="color: #388e3c;">💡 Recomendaciones Inteligentes</h3>
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px;">
                {recomendacion.replace('\n', '<br>')}
            </div>
            
            <p style="margin-top: 20px; font-size: 0.9em; color: #666;">
                Este es un mensaje automático generado por el sistema EcoSmart.
                <br>Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </p>
        </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['Subject'] = Header(asunto, 'utf-8')
        msg.attach(MIMEText(mensaje_html, 'html', 'utf-8'))

        destinatarios = []
        if agricultor_email:
            destinatarios.append(agricultor_email)
        if agronomo_email:
            destinatarios.append(agronomo_email)

        if not destinatarios:
            return False

        msg['To'] = ", ".join(destinatarios)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, destinatarios, msg.as_string())

        return True

    except Exception:
        return False