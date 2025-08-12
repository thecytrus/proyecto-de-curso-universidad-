import random
import sqlite3
from flask import jsonify
from datetime import datetime
import requests
import json # Import json to handle dictionary properly
from module import alertas # Importado para llamar a verificar_alertas

DATABASE = "users.db"
# Tu clave API para OpenWeatherMap (consíguela en https://openweathermap.org/)
OPENWEATHER_API_KEY = "apikey from openweathermap "
OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Diccionario global para almacenar el estado de la generación de datos por cultivo.
data_generation_status = {}

def crear_tabla_datos_sensores():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos_sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cultivo TEXT NOT NULL,
            humedad_suelo REAL,
            ph_suelo REAL,
            temperatura_ambiente REAL,
            nitrogeno REAL,
            fosforo REAL,
            potasio REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (numero_cultivo) REFERENCES cultivos(numero)
        );
    """)
    conn.commit()
    conn.close()

def simular_ph(rain, temperature):
    return round(7.0 - 0.05 * (rain or 0) + 0.02 * temperature, 2)

def guardar_datos(datos, numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO datos_sensores (
            numero_cultivo, humedad_suelo, ph_suelo,
            temperatura_ambiente, nitrogeno, fosforo, potasio, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero_cultivo,
        datos['humedad_suelo'],
        datos['ph_suelo'],
        datos['temperatura_ambiente'],
        datos['nutrientes']['N'],
        datos['nutrientes']['P'],
        datos['nutrientes']['K'],
        fecha_hora
    ))
    conn.commit()
    conn.close()
    # Esta línea es crucial y ya estaba bien para el sistema de alertas.
    alertas.verificar_alertas(numero_cultivo, datos)

# Función para obtener las coordenadas (latitud y longitud) del cultivo desde la tabla cultivos.
def obtener_coordenadas_cultivo(numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT latitud, longitud FROM cultivos WHERE numero = ?", (numero_cultivo,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        lat, lon = resultado
        return lat, lon
    return None, None

# Función modificada para obtener datos meteorológicos usando solamente latitud y longitud.
def get_real_time_weather(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",   # Temperatura en grados Celsius
        "lang": "es"         # Respuesta en español
    }
    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params)
        response.raise_for_status()   # Lanza error si ocurre algún problema en la petición.
        data = response.json()
        
        # Obtener temperatura y humedad desde la respuesta.
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        # La precipitación puede no estar siempre presente
        rain = data.get("rain",{}).get("1h",0) # Obtiene la lluvia en 1h, si no existe, por defecto 0
        return temperature, humidity, rain
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos meteorológicos: {e}")
        return None, None, None

def generate_data(numero_cultivo):
    # Validamos que el cultivo existe.
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM cultivos WHERE numero = ?", (numero_cultivo,))
    if not cursor.fetchone():
        conn.close()
        # Devuelve un jsonify para ser compatible con la ruta Flask que lo llama
        return jsonify({"message": f"El cultivo con número {numero_cultivo} no existe."}), 404
    conn.close()

    # Obtenemos las coordenadas del cultivo.
    lat, lon = obtener_coordenadas_cultivo(numero_cultivo)
    
    # Si se tienen coordenadas, se consultan los datos reales.
    if lat is not None and lon is not None:
        temperature, humidity, rain = get_real_time_weather(lat, lon)
    else:
        temperature, humidity, rain = None, None, None

    # En caso de falla en la API o ausencia de coordenadas, se utilizan valores simulados.
    if temperature is None:
        temperature = round(random.uniform(15.0, 35.0), 2)
        print("Usando temperatura simulada (no se obtuvieron datos reales).")
    if humidity is None:
        humidity = round(random.uniform(30.0, 80.0), 2)
        print("Usando humedad simulada (no se obtuvieron datos reales).")
    if rain is None:
        rain = round(random.uniform(0.0, 50.0), 2)
        print("Usando precipitación simulada (no se obtuvieron datos reales).")

    datos = {
        "humedad_suelo": humidity,
        "ph_suelo": simular_ph(rain, temperature),
        "temperatura_ambiente": temperature,
        "nutrientes": {
            "N": round(50 + 0.5 * humidity - 0.3 * temperature, 1),
            "P": round(30 + 0.2 * temperature - 0.1 * (rain or 0), 1),
            "K": round(100 - 0.4 * (rain or 0) + 0.2 * humidity, 1)
        }
    }

    guardar_datos(datos, numero_cultivo)
    return jsonify({
        "message": "Datos de sensor generados y guardados exitosamente",
        "data": datos
    }), 201

# Funciones para administrar el estado de la generación de datos.
def set_data_generation_status(numero_cultivo, status):
    data_generation_status[numero_cultivo] = status
    return jsonify({"message": f"Generación de datos para el cultivo {numero_cultivo} establecida en {status}"}), 200

def get_data_generation_status(numero_cultivo):
    return data_generation_status.get(numero_cultivo, 'stopped')

def obtener_datos_por_cultivo_raw(numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM datos_sensores WHERE numero_cultivo=? ORDER BY timestamp DESC LIMIT 1
    """, (numero_cultivo,))
    fila = cursor.fetchone()
    conn.close()

    if fila:
        return {
            "id": fila["id"],
            "numero_cultivo": fila["numero_cultivo"],
            "humedad_suelo": fila["humedad_suelo"],
            "ph_suelo": fila["ph_suelo"],
            "temperatura_ambiente": fila["temperatura_ambiente"],
            "nitrogeno": fila["nitrogeno"],
            "fosforo": fila["fosforo"],
            "potasio": fila["potasio"],
            "timestamp": fila["timestamp"]
        }
    return None

def obtener_datos_por_cultivo(numero_cultivo):
    datos = obtener_datos_por_cultivo_raw(numero_cultivo)
    return jsonify(datos if datos else {})

# --- NUEVA FUNCIÓN PARA OBTENER DATOS HISTÓRICOS ---
def obtener_historial_datos_sensores(numero_cultivo, limit=20):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
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
    """, (numero_cultivo, limit))
    filas = cursor.fetchall()
    conn.close()

    # Convertir las filas a una lista de diccionarios
    historial = []
    for fila in filas:
        historial.append(dict(fila))
    return historial

# Actualiza esta función para manejar las solicitudes de historial
def obtener_historial_datos_cultivo_api(numero_cultivo):
    historial_datos = obtener_historial_datos_sensores(numero_cultivo)
    return jsonify(historial_datos)
