import requests
import sqlite3
from flask import jsonify, session, request, redirect, url_for, render_template
import uuid
import json
import re  # Importar módulo de expresiones regulares

# Importar módulos de cultivo y sensores
from module import cultivos, sensores

# Configuración para OpenRouter
API_KEY = "apikey from openrouter"  # CLAVE de OpenRouter
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324:free"  # Modelo a utilizar

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ecosmart-app.com",  # Reemplaza con tu dominio real
    "X-Title": "EcoSmartBot"
}

# --- Funciones de Base de Datos y Conversación ---

def crear_tabla_chat():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            conversacion_id TEXT,
            pregunta TEXT,
            respuesta TEXT,
            estado INTEGER, -- 1 para activa, 0 para inactiva
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def cambiar_estado(conversacion_id):
    # Cambiar el estado de la conversación a 0
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE historial_chat
        SET estado = 0
        WHERE conversacion_id = ?
    ''', (conversacion_id,))
    conn.commit()
    conn.close()

def nueva_conversacion():
    return str(uuid.uuid4())

def guardar_interaccion(user_id, conversacion_id, pregunta, respuesta, activa=1):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historial_chat (user_id, conversacion_id, pregunta, respuesta, estado)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, conversacion_id, pregunta, respuesta, activa))
    conn.commit()
    conn.close()

def obtener_historial(conversacion_id, max_mensajes=10):
    activa = 1
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pregunta, respuesta, fecha, estado FROM historial_chat
        WHERE conversacion_id = ? AND estado = ?
        ORDER BY fecha ASC
    ''', (conversacion_id, activa))
    historial = cursor.fetchall()
    conn.close()
    # Limitar historial a últimos max_mensajes
    if len(historial) > max_mensajes:
        historial = historial[-max_mensajes:]
    return historial

def cargar_contexto_conversacion(conversacion_id, max_mensajes=10):
    """
    Carga el historial completo desde la base de datos y lo formatea
    para la estructura esperada del modelo.
    """
    historial = obtener_historial(conversacion_id, max_mensajes)
    mensajes = []
    for entry in historial:
        pregunta, respuesta, fecha, estado = entry  # Asegúrate de que hay cuatro valores
        if pregunta:
            mensajes.append({"role": "user", "content": pregunta})
        if respuesta:
            mensajes.append({"role": "assistant", "content": respuesta})
    return mensajes

# --- Funciones para Acceder a Datos de Cultivos y Sensores (Herramientas/Tools) ---

def get_cultivo_data_for_user(numero_cultivo: str, user_id: int):
    cultivo_data = cultivos.obtener_datos_cultivo(numero_cultivo)  # Devuelve un diccionario
    if cultivo_data:
        if cultivo_data['usuario_id'] == user_id or \
           (session.get('usuario') and session['usuario']['tipo_usuario'] == 'agronomo' and cultivo_data['agronomist_id'] == user_id):
            return {
                "numero": cultivo_data.get('numero'),
                "ciudad": cultivo_data.get('ciudad'),
                "tipo": cultivo_data.get('tipo'),
                "latitud": cultivo_data.get('latitud'),
                "longitud": cultivo_data.get('longitud')
            }
    return {"error": "Cultivo no encontrado o no autorizado para este usuario."}

def get_sensor_data_for_user_cultivo(numero_cultivo: str, user_id: int):
    cultivo_data = cultivos.obtener_datos_cultivo(numero_cultivo)
    if not cultivo_data or not (cultivo_data['usuario_id'] == user_id or \
                                (session.get('usuario') and session['usuario']['tipo_usuario'] == 'agronomo' and cultivo_data['agronomist_id'] == user_id)):
        return {"error": "Cultivo no encontrado o no autorizado para este usuario."}

    sensor_data = sensores.obtener_datos_por_cultivo_raw(numero_cultivo)  # Usar la función RAW
    if sensor_data:
        return {
            "humedad_suelo": sensor_data.get('humedad_suelo'),
            "ph_suelo": sensor_data.get('ph_suelo'),
            "temperatura_ambiente": sensor_data.get('temperatura_ambiente'),
            "nitrogeno": sensor_data.get('nitrogeno'),
            "fosforo": sensor_data.get('fosforo'),
            "potasio": sensor_data.get('potasio'),
            "timestamp": sensor_data.get('timestamp')
        }
    return {"message": "No se encontraron datos de sensores recientes para este cultivo."}

# --- Plantillas Predefinidas (gestionadas en el frontend) ---
plantillas = {
    "agricultor": [
        "¿Cuál es la mejor época para sembrar {cultivo} en {ubicacion}?",
        "¿Qué tipo de suelo es ideal para {cultivo}?",
        "¿Cada cuánto debería regar mis plantas?",
        "Dime la humedad de mi cultivo",
        "¿Qué pH tiene el suelo de mi cultivo?"
    ],
    "agronomo": [
        "¿Cuáles son los principales problemas de un cultivo de {cultivo}?",
        "¿Cómo afecta la temperatura o humedad al crecimiento?",
        "Dame los datos de mi cultivo",
        "Necesito la información de sensores del cultivo"
    ],
    "admin": [
        "¿Qué datos tengo sobre los cultivos?",
        "¿Cuáles son los sensores disponibles?"
    ]
}

def obtener_respuesta_predefinida(tipo_usuario, consulta):
    """
    Actualmente no forzamos respuestas fijas.
    Devuelve None para que la IA genere respuestas dinámicas.
    """
    consulta_lower = consulta.lower()
    if re.search(r'(AGRO-\d+-\d+)', consulta, re.IGNORECASE):
        return None
    return None


# --- Función Principal del Chatbot ---

def chat(user_input, user_id, conversacion_id):
    # Cargar últimos 10 mensajes para contexto
    messages = cargar_contexto_conversacion(conversacion_id, max_mensajes=10)

    # Consulta predefinida
    respuesta_predefinida = obtener_respuesta_predefinida(
        session.get('usuario', {}).get('tipo_usuario', 'agricultor').lower(), user_input
    )
    if respuesta_predefinida:
        messages.append({"role": "assistant", "content": respuesta_predefinida})
        guardar_interaccion(user_id, conversacion_id, user_input, respuesta_predefinida)
        return jsonify({"respuesta": respuesta_predefinida})

    # Preparar mensajes para el modelo
    messages.append({"role": "user", "content": user_input})
    system_prompt = {
    "role": "system",
    "content": (
        "Eres EcoSmart, un asistente especializado únicamente en temas de agricultura y agronomía. "
        "Solo debes responder preguntas relacionadas con cultivos, suelos, sensores agrícolas, fertilización, riego, clima, y salud de las plantas. "
        "Si la consulta está fuera de ese ámbito, responde amablemente diciendo que no es un tema que dominas."
    )
}

    messages_for_api = [system_prompt] + messages

    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": messages_for_api,
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )

        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()

            final_bot_response = reply

            # Analiza si hay un código de cultivo
            match = re.search(r'(AGRO-\d+-\d+)', user_input, re.IGNORECASE)
            numero_cultivo = match.group(1) if match else None

            if numero_cultivo:
                lower_input = user_input.lower()
                sensor_keywords = ["dame los datos", "sensores", "temperatura", "ph", "humedad", "nitrógeno", "fosforo", "fósforo", "potasio", "datos sensores"]
                general_keywords = ["latitud", "longitud", "ciudad", "tipo de cultivo", "datos cultivo"]
                sensor_match = any(keyword in lower_input for keyword in sensor_keywords)
                general_match = any(keyword in lower_input for keyword in general_keywords)

                if sensor_match and not general_match:
                    sensor_info = get_sensor_data_for_user_cultivo(numero_cultivo, user_id)
                    if "error" not in sensor_info and "message" not in sensor_info:
                        final_bot_response = (
                            f"Datos de sensores para el cultivo {numero_cultivo} ({sensor_info.get('timestamp', 'sin fecha')}): "
                            f"Humedad: {sensor_info.get('humedad_suelo', 'N/A')}%, "
                            f"pH: {sensor_info.get('ph_suelo', 'N/A')}, "
                            f"Temperatura: {sensor_info.get('temperatura_ambiente', 'N/A')}°C, "
                            f"Nitrógeno: {sensor_info.get('nitrogeno', 'N/A')}, "
                            f"Fósforo: {sensor_info.get('fosforo', 'N/A')}, "
                            f"Potasio: {sensor_info.get('potasio', 'N/A')}."
                        )
                    elif "message" in sensor_info:
                        final_bot_response = sensor_info["message"]
                    else:
                        final_bot_response = sensor_info["error"]

                elif general_match and not sensor_match:
                    cultivo_info = get_cultivo_data_for_user(numero_cultivo, user_id)
                    if "error" not in cultivo_info:
                        final_bot_response = (
                            f"El cultivo {numero_cultivo} es de tipo {cultivo_info.get('tipo', 'desconocido')} "
                            f"en {cultivo_info.get('ciudad', 'desconocido')}, ubicado en "
                            f"Latitud: {cultivo_info.get('latitud', 'N/A')} y Longitud: {cultivo_info.get('longitud', 'N/A')}."
                        )
                    else:
                        final_bot_response = cultivo_info["error"]

            # Guardar en base de datos y contexto
            messages.append({"role": "assistant", "content": final_bot_response})
            guardar_interaccion(user_id, conversacion_id, user_input, final_bot_response)
            return jsonify({"respuesta": final_bot_response})

        else:
            error_msg = f"Error al contactar OpenRouter: {response.status_code}"
            return jsonify({"error": error_msg})

    except Exception as e:
        return jsonify({"error": f"Excepción en el servidor: {str(e)}"})
