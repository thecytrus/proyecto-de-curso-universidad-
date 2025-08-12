# APP.PY
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, session, flash
from module import usuarios, chatbot, clima, sensores, cultivos, tecnicos, alertas, datos_avanzados
from module.clima import get_weather # Asegúrate de que esta función exista si la usas en otras partes.
from module.tecnicos import tecnicos_bp
import os
import sqlite3
from datetime import timedelta, datetime
import secrets
import requests
import json
import threading
import time
import pytz

DATABASE = "users.db"

# Configuración de la aplicación y sesiones
app = Flask(__name__)
# Genera una clave secreta aleatoria para asegurar las sesiones de Flask
app.secret_key = secrets.token_hex(16)

# Por defecto, las sesiones durarán 30 minutos
app.permanent_session_lifetime = timedelta(minutes=30)

# Registrar el blueprint para las rutas de gestión de usuarios comunes y técnicos
app.register_blueprint(tecnicos_bp)

# Crear la tabla 'usuarios' si no existe al iniciar la aplicación
usuarios.crear_base_datos()
# Crea la tabla de cultivos si no existe
cultivos.crear_tabla_cultivos()
# Crear tabla de sensores en la base de datos si no existe
sensores.crear_tabla_datos_sensores()
#se crea la tabla de datos del chat si no existe
chatbot.crear_tabla_chat()

# Crear la tabla de alertas si no existe
alertas.crear_tabla_alertas()
# Crear la tabla de historial de alertas si no existe
alertas.crear_tabla_historial_alertas()
#crea la tabla de datos avanzados si no existe
datos_avanzados.crear_tabla_datos_avanzados()

# Diccionario para almacenar los hilos de generación continua de datos
data_generation_threads = {}

# Antes de cada solicitud, se verifica si la sesión debe ser permanente
@app.before_request
def make_session_permanent_or_not():
    # Si el usuario está logueado, revisar si quiere sesión permanente
    # Esta lógica debe ser ajustada dependiendo de cómo envíes ese dato (ejemplo: en session o cookie)
    if 'usuario' in session:
        # Ejemplo: si en session hay 'sesion_permanente' y es True, entonces sesión permanente
        if session.get('sesion_permanente'):
            session.permanent = True
        else:
            session.permanent = False

# Ruta del index (página de inicio)
@app.route('/')
def index():
    return render_template('index.html')


# Endpoint para verificar el estado de la sesión
@app.route('/api/verificar_sesion')
def verificar_sesion():
    # Retorna un JSON indicando si la sesión está activa
    if 'usuario' in session:
        return jsonify({"sesion_activa": True})
    else:
        return jsonify({"sesion_activa": False}), 401

# Ruta del login (inicio de sesión)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form.get("nombre")
        contrasena = request.form.get("contrasena")
        # Verifica si el usuario desea que la sesión sea permanente
        sesion_permanente = request.form.get("sesion_permanente") == "on"

        if not nombre or not contrasena:
            return render_template('login.html', error="Debes ingresar nombre y contraseña.")

        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Consulta para verificar las credenciales del usuario (nombre o correo)
        query = """
            SELECT * FROM usuarios
            WHERE (nombre = ? OR correo = ?)
              AND contrasena = ?
        """
        cursor.execute(query, (nombre, nombre, contrasena))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Si las credenciales son correctas, guarda la información del usuario en la sesión
            session['usuario'] = {
                'id': user['id'],
                'nombre': user['nombre'],
                'correo': user['correo'],
                'tipo_usuario': user['tipo_usuario'].lower()
            }
            session['sesion_permanente'] = sesion_permanente
            session.permanent = sesion_permanente # Activa la duración permanente si es True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")

    return render_template('login.html')

# Endpoint API para el inicio de sesión (útil para clientes externos, como aplicaciones móviles)
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    nombre = data.get('nombre')
    contrasena = data.get('contrasena')
    sesion_permanente = data.get('sesion_permanente', False)

    if not nombre or not contrasena:
        return jsonify({"message": "Faltan datos"}), 400

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Consulta para verificar las credenciales del usuario (nombre o correo)
    query = """
        SELECT * FROM usuarios
        WHERE (nombre = ? OR correo = ?)
          AND contrasena = ?
    """
    cursor.execute(query, (nombre, nombre, contrasena))
    user = cursor.fetchone()
    conn.close()

    if user:
        # Si las credenciales son correctas, guarda la información del usuario en la sesión
        session['usuario'] = {
            'id': user['id'],
            'nombre': user['nombre'],
            'correo': user['correo'],
            'tipo_usuario': user['tipo_usuario'].lower()
        }
        session['sesion_permanente'] = sesion_permanente
        session.permanent = sesion_permanente
        return jsonify({"message": "Inicio de sesión exitoso"}), 200
    else:
        return jsonify({"message": "Usuario o contraseña incorrectos"}), 401


# Ruta para el registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombreRegistro')
        correo = request.form.get('correoRegistro')
        contrasena = request.form.get('contrasenaRegistro')
        tipo_usuario = request.form.get('tipo_usuario')
        email = correo
        notificaciones = 1

        if not nombre or not correo or not contrasena:
            return render_template('register.html', error="Todos los campos son obligatorios")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Verifica si el correo ya está registrado en la base de datos
        cursor.execute("SELECT * FROM usuarios WHERE correo=?", (correo,))
        if cursor.fetchone():
            conn.close()
            return render_template('register.html', error="El correo ya está registrado")

        # Inserta el nuevo usuario en la base de datos
        cursor.execute(
            "INSERT INTO usuarios (nombre, correo, contrasena, tipo_usuario, email, notificaciones) VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, correo, contrasena, tipo_usuario, email, notificaciones)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    # Elimina la información del usuario y la persistencia de la sesión
    session.pop('usuario', None)
    session.pop('sesion_permanente', None)
    return redirect(url_for('login'))

# Ruta principal para el chatbot
@app.route('/chatbot')
def chatbot_route():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    # Crear una conversación nueva si no existe
    if 'conversacion_id' not in session:
        session['conversacion_id'] = chatbot.nueva_conversacion()

    return render_template('chatbot.html')

# Endpoint para enviar un mensaje al chat
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if 'usuario' not in session:
        return jsonify({'error': 'No has iniciado sesión'}), 401

    data = request.get_json()
    mensaje_usuario = data.get('mensaje')
    user_id = session['usuario']['id']

    if not mensaje_usuario:
        return jsonify({'error': 'Mensaje vacío'}), 400

    # Usar el conversacion_id de la sesión
    if 'conversacion_id' not in session:
        session['conversacion_id'] = chatbot.nueva_conversacion()

    conversacion_id = session['conversacion_id']

    # La función chatbot.chat ahora maneja el guardado internamente
    respuesta_json = chatbot.chat(mensaje_usuario, user_id, conversacion_id)

    # chatbot.chat now returns a jsonify object, so we can directly return it
    return respuesta_json # <--- Removed the redundant save here

# Endpoint para obtener historial completo
@app.route('/chat/historial/todo', methods=['GET'])
def historial_todo():
    activa = 1
    if 'usuario' not in session:
        return jsonify({'error': 'No has iniciado sesión'}), 401

    user_id = session['usuario']['id']
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT conversacion_id, pregunta, respuesta, fecha, estado
        FROM historial_chat
        WHERE user_id = ? AND estado = ?
        ORDER BY conversacion_id, fecha ASC
    ''', (user_id, activa))
    rows = cursor.fetchall()
    conn.close()

    conversations = {}
    for conversacion_id, pregunta, respuesta, fecha, estado in rows:
        if conversacion_id not in conversations:
            conversations[conversacion_id] = []
        conversations[conversacion_id].append({
            'pregunta': pregunta,
            'respuesta': respuesta,
            'fecha': fecha,
            'estado': estado
        })

    return jsonify({'conversations': conversations})

# Endpoint para iniciar nueva conversación
@app.route('/chat/nueva_conversacion', methods=['POST'])
def nueva_conversacion_route():
    if 'usuario' not in session:
        return jsonify({'error': 'No has iniciado sesión'}), 401

    new_conv_id = chatbot.nueva_conversacion()
    session['conversacion_id'] = new_conv_id
    return jsonify({'conversacion_id': new_conv_id})
# ENDPOINT que devuelve el tipo de usuario actualmente en sesión
@app.route('/api/usuario_tipo', methods=['GET'])
def api_usuario_tipo():
    if 'usuario' not in session:
        return jsonify({"tipo_usuario": None}), 401
    tipo_usuario = session['usuario']['tipo_usuario'].lower()
    return jsonify({"tipo_usuario": tipo_usuario}), 200

# Ruta para la página del clima
@app.route('/clima', methods=['GET'])
def clima_route():
    # Redirige al login si no hay un usuario en la sesión
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('clima.html', active='clima_route')

# Endpoint API para obtener datos del clima
@app.route('/api/weather', methods=['POST'])
def api_weather():
    city = request.json.get("city")
    if city:
        weather_data = get_weather(city)
        
        if weather_data and weather_data.get("current") and weather_data.get("forecast") is not None:
            current_weather = weather_data["current"]

            # Obtener la fecha y hora actual en Chile
            chile_tz = pytz.timezone('America/Santiago')
            now_chile = datetime.now(chile_tz)
            fecha_hora_actual = now_chile.strftime("%Y-%m-%d %H:%M:%S")

            # Preparar la línea para guardar en el archivo
            line_to_save = (
                f"{city}, {fecha_hora_actual}, "
                f"{current_weather['temp']:.2f}, "
                f"{current_weather['humidity']}, "
                f"{current_weather['rain_prob']:.0f}, "
                f"{current_weather['wind']:.2f}, "
                f"{current_weather['description']}\n"
            )

            try:
                with open("clima.txt", "a", encoding="utf-8") as f:
                    f.write(line_to_save)
            except Exception as e:
                print(f"Error al escribir en clima.txt: {e}")

            return jsonify({
                "city": weather_data.get("city"),
                "current": current_weather,
                "forecast": weather_data["forecast"],
                "description": current_weather["description"]
            })
    return jsonify({"message": "Error o ciudad no proporcionada"}), 400

# Ruta para la página de gestión de cultivos
@app.route('/cultivos')
def cultivos_route():
    # Verifica que exista 'usuario' en la sesión para que se pueda acceder a la vista.
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user_info = session['usuario']
    tipo_usuario = user_info['tipo_usuario']
    user_id = user_info['id']
    
    cultivos_list = []
    has_cultivos = False

    # Dependiendo del tipo de usuario, obtenemos los cultivos específicos
    if tipo_usuario == 'agricultor':
        # Los agricultores solo ven sus propios cultivos
        cultivos_list = cultivos.obtener_cultivos_por_usuario(user_id).json
        has_cultivos = len(cultivos_list) > 0
    elif tipo_usuario == 'agronomo':
        # Los agrónomos solo ven los cultivos que ellos agregaron
        cultivos_list = cultivos.obtener_cultivos_por_agronomo(user_id).json
        has_cultivos = len(cultivos_list) > 0
    else: # admin o cualquier otro
        # Administradores o cualquier otro tipo de usuario ve todos los cultivos (o según su rol)
        cultivos_list = cultivos.obtener_cultivos().json
        has_cultivos = len(cultivos_list) > 0
    
    return render_template('cultivos.html', cultivos=cultivos_list, has_cultivos=has_cultivos, tipo_usuario=tipo_usuario)


# Endpoint para obtener cultivos. Opcionalmente se puede filtrar por usuario vía query string.
@app.route('/api/cultivos', methods=['GET'])
def obtener_cultivos_api():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_info = session['usuario']
    user_id = user_info['id']
    tipo_usuario = user_info['tipo_usuario']

    # Si es agricultor, solo puede ver sus cultivos
    if tipo_usuario == 'agricultor':
        return cultivos.obtener_cultivos_por_usuario(user_id)
    # Si es agrónomo, solo puede ver los cultivos que él agregó
    elif tipo_usuario == 'agronomo':
        return cultivos.obtener_cultivos_por_agronomo(user_id)
    else:
        # Administradores ven todos los cultivos
        return cultivos.obtener_cultivos()

# Endpoint para agregar un cultivo (se espera que el JSON tenga todos los campos).
@app.route('/api/cultivos', methods=['POST'])
def agregar_cultivo_api():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401
    
    # Asegúrate de que solo los agrónomos puedan agregar cultivos
    if session['usuario']['tipo_usuario'].lower() != 'agronomo':
        return jsonify({"message": "Solo los agrónomos pueden agregar cultivos."}), 403
    
    return cultivos.agregar_cultivo()

# Endpoint para editar un cultivo
@app.route('/api/cultivos/<numero_cultivo>', methods=['PUT']) # numero_cultivo ahora es string
def editar_cultivo_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401
    
    user_info = session['usuario']
    user_id = user_info['id']
    tipo_usuario = user_info['tipo_usuario']

    # Verificar si el usuario tiene permiso para editar este cultivo
    conn = sqlite3.connect(cultivos.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    authorized = False
    if tipo_usuario == 'agronomo':
        # Un agrónomo solo puede editar los cultivos que él añadió
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone():
            authorized = True
    elif tipo_usuario == 'admin':
        authorized = True # Los administradores pueden editar cualquier cultivo
    
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para editar este cultivo."}), 403
    
    return cultivos.editar_cultivo(numero_cultivo)

# Endpoint para eliminar un cultivo
@app.route('/api/cultivos/<numero_cultivo>', methods=['DELETE']) # numero_cultivo ahora es string
def eliminar_cultivo_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_info = session['usuario']
    user_id = user_info['id']
    tipo_usuario = user_info['tipo_usuario']

    # Verificar si el usuario tiene permiso para eliminar este cultivo
    conn = sqlite3.connect(cultivos.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    authorized = False
    if tipo_usuario == 'agronomo':
        # Un agrónomo solo puede eliminar los cultivos que él añadió
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone():
            authorized = True
    elif tipo_usuario == 'admin':
        authorized = True # Los administradores pueden eliminar cualquier cultivo
    
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para eliminar este cultivo."}), 403

    return cultivos.eliminar_cultivo(numero_cultivo)

# Endpoint para obtener los usuarios cuyo tipo_usuario sea "agricultor"
@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios_api():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401
    DATABASE = "users.db"
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Se filtra para obtener solo los usuarios con tipo_usuario "agricultor"
    cursor.execute("SELECT id, nombre FROM usuarios WHERE tipo_usuario='agricultor'")
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(usuarios)


# Función para ejecutar la generación de datos de forma continua
def run_continuous_generation(numero_cultivo, user_id, tipo_usuario):
    while sensores.get_data_generation_status(numero_cultivo) == 'running':
        with app.app_context(): # Esencial para el contexto de Flask
            # Volver a verificar la autorización dentro del bucle para asegurar que sigue siendo válida
            conn = sqlite3.connect(cultivos.DATABASE)
            cursor = conn.cursor()
            authorized = False
            if tipo_usuario == 'agronomo':
                cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
                if cursor.fetchone(): authorized = True
            elif tipo_usuario == 'agricultor':
                cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
                if cursor.fetchone(): authorized = True
            elif tipo_usuario == 'admin':
                authorized = True
            conn.close()

            if authorized:
                sensores.generate_data(numero_cultivo)
                print(f"Datos generados para el cultivo {numero_cultivo}")
            else:
                # Si se pierde la autorización, detener la generación
                sensores.set_data_generation_status(numero_cultivo, 'stopped')
                print(f"Generación de datos detenida para el cultivo {numero_cultivo} por pérdida de autorización.")
                break
        time.sleep(30) # Generar datos cada 30 segundos (AJUSTAR SI ES NECESARIO)


# Ruta principal para mostrar la vista de sensores (se pasa la lista de cultivos a la plantilla)
@app.route('/sensores')
def sensores_route():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user_info = session['usuario']
    user_id = user_info['id']
    tipo_usuario = user_info['tipo_usuario']
    
    cultivos_del_usuario = []
    has_cultivos = False

    if tipo_usuario == 'agricultor':
        # Obtener los cultivos asociados al agricultor
        cultivos_data = cultivos.obtener_cultivos_por_usuario(user_id).json
        cultivos_del_usuario = cultivos_data
        has_cultivos = len(cultivos_del_usuario) > 0
    elif tipo_usuario == 'agronomo':
        # Los agrónomos pueden ver los sensores de los cultivos que ellos agregaron.
        cultivos_data = cultivos.obtener_cultivos_por_agronomo(user_id).json
        cultivos_del_usuario = cultivos_data
        has_cultivos = len(cultivos_del_usuario) > 0
    elif tipo_usuario == 'admin':
        # Los administradores ven todos los cultivos.
        cultivos_data = cultivos.obtener_cultivos().json
        cultivos_del_usuario = cultivos_data
        has_cultivos = len(cultivos_del_usuario) > 0
    
    # Pasar el estado actual de la generación para cada cultivo a la plantilla
    for crop in cultivos_del_usuario:
        crop['generation_status'] = sensores.get_data_generation_status(crop['numero'])

    return render_template('sensores.html', cultivos=cultivos_del_usuario, has_cultivos=has_cultivos, tipo_usuario=tipo_usuario, active='sensores_route')

# Endpoint para controlar la generación de datos (iniciar/detener)
@app.route('/control_generacion_datos', methods=['POST'])
def control_generacion_datos():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_info = session['usuario']
    tipo_usuario = user_info.get('tipo_usuario', '').lower()
    user_id = user_info.get('id')

    if tipo_usuario not in ['agronomo', 'admin', 'agricultor']:
        return jsonify({
            "message": "Solo agrónomos, agricultores y administradores pueden controlar la generación de datos."
        }), 403

    params = request.get_json()
    numero_cultivo = params.get("numero_cultivo")
    action = params.get("action") # 'start' o 'stop'

    if not numero_cultivo or not action:
        return jsonify({"message": "Faltan parámetros: numero_cultivo y action"}), 400

    # Verificar la autorización del usuario para el cultivo dado
    authorized = False
    conn = sqlite3.connect(cultivos.DATABASE)
    cursor = conn.cursor()
    if tipo_usuario == 'agronomo':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'agricultor':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'admin':
        authorized = True
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para controlar la generación de datos para este cultivo."}), 403

    if action == 'start':
        if sensores.get_data_generation_status(numero_cultivo) == 'stopped':
            sensores.set_data_generation_status(numero_cultivo, 'running')
            # Iniciar un nuevo hilo para la generación continua
            thread = threading.Thread(target=run_continuous_generation, args=(numero_cultivo, user_id, tipo_usuario))
            thread.daemon = True # Permite que el programa principal se cierre incluso si los hilos están corriendo
            thread.start()
            data_generation_threads[numero_cultivo] = thread
            return jsonify({"message": f"Generación de datos iniciada para el cultivo {numero_cultivo}"}), 200
        else:
            return jsonify({"message": f"La generación de datos ya está en marcha para el cultivo {numero_cultivo}"}), 200
    elif action == 'stop':
        if sensores.get_data_generation_status(numero_cultivo) == 'running':
            sensores.set_data_generation_status(numero_cultivo, 'stopped')
            # El hilo se detendrá naturalmente después de la próxima iteración de su bucle
            return jsonify({"message": f"Generación de datos detenida para el cultivo {numero_cultivo}"}), 200
        else:
            return jsonify({"message": f"La generación de datos ya está detenida para el cultivo {numero_cultivo}"}), 200
    else:
        return jsonify({"message": "Acción no válida. Use 'start' o 'stop'."}), 400


# Endpoint para obtener el histórico de datos para un cultivo específico
# NOTA: Este endpoint originalmente devolvía solo el último dato.
# La función obtener_datos_sensores de app.py llama a sensores.obtener_datos_por_cultivo.
# Para el historial, necesitas un nuevo endpoint, como el que se añadió abajo.
@app.route('/api/sensores/<numero_cultivo>', methods=['GET'])
def obtener_datos_sensores(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_info = session['usuario']
    user_id = user_info['id']
    tipo_usuario = user_info['tipo_usuario']

    # Verificar permisos según el tipo de usuario
    conn = sqlite3.connect(cultivos.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    authorized = False
    if tipo_usuario == 'agricultor':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone():
            authorized = True
    elif tipo_usuario == 'agronomo':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone():
            authorized = True
    elif tipo_usuario == 'admin':
        authorized = True
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para ver los datos de este cultivo o el cultivo no existe."}), 403

    # Obtener datos del sensor
    sensor_response = sensores.obtener_datos_por_cultivo(numero_cultivo)
    sensor_data = sensor_response.get_json()

    # Verificar alertas y agregar bandera
    try:
        alert_triggered = alertas.verificar_alertas(numero_cultivo, sensor_data)
        print(f"Para cultivo {numero_cultivo}, alertTriggered: {alert_triggered}")  # Debug en el servidor
    except Exception as e:
        print(f"Error al verificar alertas para cultivo {numero_cultivo}: {e}")
        alert_triggered = False

    sensor_data['alertTriggered'] = alert_triggered
    return jsonify(sensor_data)



# --- NUEVA RUTA PARA OBTENER DATOS HISTÓRICOS DE SENSORES ---
@app.route('/api/sensores/<numero_cultivo>/historial', methods=['GET'])
def obtener_historial_sensores_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_info = session['usuario']
    user_id = user_info['id']
    tipo_usuario = user_info['tipo_usuario']

    # Verificar si el usuario tiene permiso para ver el historial de este cultivo
    conn = sqlite3.connect(cultivos.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    authorized = False
    if tipo_usuario == 'agricultor':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone():
            authorized = True
    elif tipo_usuario == 'agronomo':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone():
            authorized = True
    elif tipo_usuario == 'admin':
        authorized = True
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para ver el historial de este cultivo."}), 403

    # Llama a la nueva función de sensores.py para obtener el historial
    return sensores.obtener_historial_datos_cultivo_api(numero_cultivo)


# El endpoint /generar_datos ya no es estrictamente necesario para la generación continua,
# pero puedes mantenerlo para una generación manual única si lo deseas.
# Si lo mantienes, asegúrate de que verifique el estado de la generación y actúe en consecuencia
# (por ejemplo, solo genera si está detenido)
@app.route('/generar_datos', methods=['POST'])
def generar_datos():
    # Este endpoint es ahora principalmente para una generación de datos *manual y única*.
    # Para la generación continua, usa /control_generacion_datos con 'start'.
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_info = session['usuario']
    tipo_usuario = user_info.get('tipo_usuario', '').lower()
    user_id = user_info.get('id')

    if tipo_usuario not in ['agronomo', 'admin', 'agricultor']:
        return jsonify({
            "message": "Solo agrónomos, agricultores y administradores pueden generar datos de sensores."
        }), 403

    params = request.get_json()
    numero_cultivo = params.get("numero_cultivo")
    if not numero_cultivo:
        return jsonify({"message": "Falta el parámetro: numero_cultivo"}), 400

    # Evitar la generación manual si la generación continua ya está en ejecución
    if sensores.get_data_generation_status(numero_cultivo) == 'running':
        return jsonify({"message": f"La generación continua de datos ya está activa para el cultivo {numero_cultivo}. Deténgala para generar datos manualmente."}), 409


    # Verificar si el usuario tiene permiso para generar datos para este cultivo
    authorized = False
    conn = sqlite3.connect(cultivos.DATABASE)
    cursor = conn.cursor()
    if tipo_usuario == 'agronomo':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'agricultor':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'admin':
        authorized = True
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para generar datos para este cultivo."}), 403

    return sensores.generate_data(numero_cultivo)    

# Ruta de Login para Admin
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        nombre = request.form.get("nombreAdmin")
        contrasena = request.form.get("contrasenaAdmin")
        sesion_permanente = request.form.get("sesion_permanente") == "on"

        if not nombre or not contrasena:
            return render_template('login_admin.html', error="Debes ingresar nombre y contraseña.")

        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Se selecciona el usuario que tenga tipo 'ADMIN' y la contraseña se compara como texto plano
        query = """
            SELECT * FROM usuarios
            WHERE (nombre = ? OR correo = ?)
              AND contrasena = ?
              AND UPPER(TRIM(tipo_usuario)) = 'ADMIN'
        """
        cursor.execute(query, (nombre, nombre, contrasena))
        admin_user = cursor.fetchone()
        conn.close()

        if admin_user:
            # Si es un administrador, se guarda la información en la sesión
            session['usuario'] = {
                'id': admin_user['id'],
                'nombre': admin_user['nombre'],
                'correo': admin_user['correo'],
                'tipo_usuario': admin_user['tipo_usuario'].lower()
            }
            session['sesion_permanente'] = sesion_permanente
            session.permanent = sesion_permanente
            return redirect(url_for('tecnicos_bp.tecnicos_route'))

        else:
            error_msg = "Solo usuarios de tipo 'ADMIN' pueden iniciar sesión en Admin."
            return render_template('login_admin.html', error=error_msg)
    return render_template('login_admin.html')


# Ruta de Registro para Admin
@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        nombre = request.form.get("nombreRegistroAdmin")
        contrasena = request.form.get("contrasenaRegistroAdmin")
        correo = request.form.get("correoRegistroAdmin")
        # Se asigna el rol de Administrador de forma consistente
        tipo_usuario = "ADMIN"
        email = correo

        if not nombre or not contrasena or not correo:
            return render_template('register_admin.html', error="Faltan datos")

        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Se verifica que el correo no esté ya registrado
        cursor.execute("SELECT * FROM usuarios WHERE correo=?", (correo,))
        if cursor.fetchone():
            conn.close()
            return render_template('register_admin.html', error="El correo ya está registrado")

        # Se almacena la contraseña en texto plano (no recomendado para producción)
        cursor.execute(
            "INSERT INTO usuarios (nombre, contrasena, correo, tipo_usuario, email) VALUES (?, ?, ?, ?, ?)",
            (nombre, contrasena, correo, tipo_usuario, email)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('login_admin'))
    return render_template('register_admin.html')

# Ruta para la página de tecnicos
@app.route('/tecnicos')
def tecnicos_route():
    # Verifica que el usuario esté logueado y que sea un administrador
    if 'usuario' not in session or session['usuario']['tipo_usuario'].upper() != 'ADMIN':
        return redirect(url_for('login_admin')) # Redirige al login de administradores si no es un ADMIN
    return render_template('tecnicos.html')


# Ruta para la página de perfil del usuario
@app.route('/perfil')
def perfil():
    # Redirige al login si no hay un usuario en la sesión
    if 'usuario' not in session:
        return redirect(url_for('login'))
    usuario = session['usuario']
    return render_template('perfil.html', usuario=usuario)

@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():
    if 'usuario' not in session:
        return jsonify({"message": "Sesión expirada"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"message": "No se recibieron datos"}), 400

    usuario = session['usuario']
    nombre = data.get('nombre')
    correo = data.get('correo')
    contrasena_actual = data.get('password_actual')

    if not nombre or not correo or not contrasena_actual:
        return jsonify({"message": "Todos los campos son obligatorios"}), 400

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT contrasena FROM usuarios WHERE id = ?", (usuario['id'],))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"message": "Usuario no encontrado"}), 404

    stored_password = row[0]
    if contrasena_actual != stored_password:
        conn.close()
        return jsonify({"message": "Contraseña actual incorrecta"}), 400

    cursor.execute("""
        UPDATE usuarios
        SET nombre = ?, correo = ?
        WHERE id = ?
    """, (nombre, correo, usuario['id']))
    conn.commit()
    conn.close()

    session['usuario']['nombre'] = nombre
    session['usuario']['correo'] = correo

    return jsonify({
        "message": "Perfil actualizado correctamente",
        "usuario": {"nombre": nombre, "correo": correo}
    }), 200


@app.route('/cambiar_password', methods=['POST'])
def cambiar_password():
    if 'usuario' not in session:
        return jsonify({"message": "Sesión expirada"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"message": "No se recibieron datos"}), 400

    usuario = session['usuario']
    contrasena_actual = data.get('password_actual')
    nueva_contrasena = data.get('password_nueva')
    confirmar_contrasena = data.get('password_nueva_confirm')

    if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
        return jsonify({"message": "Todos los campos son obligatorios"}), 400

    if nueva_contrasena != confirmar_contrasena:
        return jsonify({"message": "Las contraseñas no coinciden"}), 400

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT contrasena FROM usuarios WHERE id = ?", (usuario['id'],))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"message": "Usuario no encontrado"}), 404

    stored_password = row[0]

    if contrasena_actual != stored_password:
        conn.close()
        return jsonify({"message": "Contraseña actual incorrecta"}), 400

    if nueva_contrasena == stored_password:
        conn.close()
        return jsonify({"message": "La nueva contraseña no puede ser igual a la actual"}), 400

    cursor.execute("""
        UPDATE usuarios
        SET contrasena = ?
        WHERE id = ?
    """, (nueva_contrasena, usuario['id']))
    conn.commit()
    conn.close()

    return jsonify({"message": "Contraseña actualizada correctamente"}), 200

# Ruta para gestionar alertas (globales, sin usuario_id)
@app.route('/alertas', methods=['GET', 'POST'])
def gestionar_alertas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    user_type = session['usuario'].get('tipo_usuario')
    if user_type not in ['ADMIN', 'admin', 'agronomo']:
        flash('Solo administradores y agrónomos pueden gestionar alertas.', 'error')
        return redirect(url_for('historial_alertas'))
    else :
        flash('Acceso permitido.', 'success')
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"message": "Datos JSON inválidos"}), 400

            tipo_alerta = data.get('tipo_alerta')
            umbral = data.get('umbral')
            condicion = data.get('condicion')

            # Validación básica para campos requeridos
            if not all([tipo_alerta, umbral, condicion]):
                return jsonify({"message": "Faltan datos requeridos para la alerta"}), 400

            try:
                # Asegurarse de que el umbral sea un número
                umbral = float(umbral)
            except ValueError:
                return jsonify({"message": "El umbral debe ser un número"}), 400

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            try:
                # Se elimina usuario_id ya que las alertas son globales
                cursor.execute('''
                    INSERT INTO alertas (tipo_alerta, umbral, condicion, activa)
                    VALUES (?, ?, ?, ?)
                ''', (tipo_alerta, umbral, condicion, True))
                conn.commit()
                return jsonify({"message": "Alerta agregada exitosamente"}), 201  # 201 Created
            except sqlite3.Error as e:
                conn.rollback()
                return jsonify({"message": f"Error en la base de datos: {e}"}), 500
            finally:
                conn.close()
        # Método GET: Se obtienen todas las alertas de forma global
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alertas')
        alertas = cursor.fetchall()
        conn.close()

        return render_template('alertas.html', alertas=alertas)


# Ruta para ver el historial de alertas (Jinja2 template)
@app.route('/historial_alertas')
def historial_alertas():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user_id = session['usuario']['id']
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    cursor = conn.cursor()
    # Se filtra el historial por usuario_id o agronomist_id
    cursor.execute('''
        SELECT ha.fecha, a.tipo_alerta, a.umbral
        FROM historial_alertas ha
        JOIN alertas a ON ha.alerta_id = a.id
        WHERE ha.usuario_id = ? OR ha.agronomist_id = ?
        ORDER BY ha.fecha DESC
    ''', (user_id, user_id))
    historial = cursor.fetchall()
    conn.close()

    return render_template('historial_alertas.html', historial=historial, active='historial_alertas')


# Ruta API para actualizar preferencias de notificación
@app.route('/api/preferencias_notificacion', methods=['POST'])
def preferencias_notificacion():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    data = request.get_json()
    email_preferencia = data.get('email')
    notificaciones_activas = data.get('notificaciones')
    DATABASE = "users.db"
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE usuarios
            SET email = ?, notificaciones = ?
            WHERE id = ?
        """, (email_preferencia, notificaciones_activas, session['usuario']['id']))
        conn.commit()
        return jsonify({"message": "Preferencias actualizadas"}), 200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"message": f"Error al actualizar preferencias: {e}"}), 500
    finally:
        conn.close()


# Endpoint para obtener notificaciones (para el centro de notificaciones JS)
@app.route('/api/notificaciones', methods=['GET'])
def obtener_notificaciones():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_id = session['usuario']['id']
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Se modificó para incluir la verificación tanto de usuario_id como de agronomist_id
    cursor.execute('''
        SELECT ha.fecha, a.tipo_alerta, a.umbral
        FROM historial_alertas ha
        JOIN alertas a ON ha.alerta_id = a.id
        WHERE ha.usuario_id = ? OR ha.agronomist_id = ?
        ORDER BY ha.fecha DESC
        LIMIT 10
    ''', (user_id, user_id))
    notificaciones = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in notificaciones]), 200


# Endpoint API para obtener historial de alertas en formato JSON (para la tabla JS)
# Endpoint API para obtener historial de alertas en formato JSON (para la tabla JS)
@app.route('/api/historial_alertas', methods=['GET'])
def api_historial_alertas():
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    user_id = session['usuario']['id']
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Depuración: Mostrar la estructura de la tabla 'alertas'
        cursor.execute("PRAGMA table_info(alertas)")
        columnas_alertas = [row["name"] for row in cursor.fetchall()]
        print("Columnas en 'alertas':", columnas_alertas)

        # Depuración: Mostrar la estructura de la tabla 'historial_alertas'
        cursor.execute("PRAGMA table_info(historial_alertas)")
        columnas_historial = [row["name"] for row in cursor.fetchall()]
        print("Columnas en 'historial_alertas':", columnas_historial)

        # Ejecutar la consulta SQL
        cursor.execute('''
            SELECT ha.fecha, a.tipo_alerta, a.umbral,a.condicion, ha.valor_sensor, ha.numero_cultivo
            FROM historial_alertas ha
            JOIN alertas a ON ha.alerta_id = a.id
            WHERE ha.usuario_id = ? OR ha.agronomist_id = ?
            ORDER BY ha.fecha DESC
        ''', (user_id, user_id))
        historial = cursor.fetchall()
    except Exception as e:
        print("Error en la consulta SQL:", e)
        conn.close()
        return jsonify({"message": "Error en la consulta SQL", "error": str(e)}), 500

    conn.close()
    historial_list = [dict(row) for row in historial]
    return jsonify(historial_list)

@app.route('/alertas/eliminar/<int:alerta_id>', methods=['POST'])
def eliminar_alerta(alerta_id):
    # Verificar si el usuario está autenticado
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401

    # Solo administradores y agrónomos pueden eliminar alertas
    user_type = session['usuario'].get('tipo_usuario')
    if user_type not in ['ADMIN', 'admin', 'agronomo']:
        return jsonify({"message": "Acceso denegado"}), 403
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alertas WHERE id = ?", (alerta_id,))
        if cursor.rowcount == 0:
            # Si no se encontró la alerta
            return jsonify({"message": "Alerta no encontrada"}), 404
        conn.commit()
        return jsonify({"message": "Alerta eliminada correctamente"}), 200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"message": f"Error en la eliminación de la alerta: {str(e)}"}), 500
    finally:
        conn.close()

# Ruta principal para mostrar datos avanzados
@app.route('/datos_avanzados', methods=['GET'])
def mostrar_datos_avanzados():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    user_info = session['usuario']
    tipo_usuario = user_info['tipo_usuario']

    #  Bloquear acceso a agricultores
    if tipo_usuario == 'agricultor':
        flash('Acceso denegado: Esta sección es exclusiva para agrónomos y administradores.', 'error')
        return redirect(url_for('sensores_route'))  # O cualquier otra página que tengas

    user_id = user_info['id']
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if tipo_usuario == 'agronomo':
        cursor.execute("SELECT numero, tipo, ciudad FROM cultivos WHERE agronomist_id = ?", (user_id,))
    else:  # admin
        cursor.execute("SELECT numero, tipo, ciudad FROM cultivos")
    
    cultivos_disponibles = cursor.fetchall()
    conn.close()

    selected_cultivo = request.args.get('cultivo') or (cultivos_disponibles[0]['numero'] if cultivos_disponibles else None)

    return render_template('datos_avanzados.html',
                         cultivos=cultivos_disponibles,
                         selected_cultivo=selected_cultivo)


# API para obtener datos avanzados
@app.route('/api/datos_avanzados/<numero_cultivo>', methods=['GET'])
def obtener_datos_avanzados_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    # Verificar permisos para el cultivo
    user_info = session['usuario']
    tipo_usuario = user_info['tipo_usuario']
    user_id = user_info['id']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    authorized = False
    if tipo_usuario == 'agricultor':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'agronomo':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'admin':
        authorized = True
    
    conn.close()

    if not authorized:
        return jsonify({"error": "No tiene permiso para ver estos datos"}), 403
    
    return datos_avanzados.obtener_datos_avanzados(numero_cultivo)

# API para obtener recomendaciones de IA
@app.route("/api/ia_recommendations/<numero_cultivo>", methods=["GET"])
def get_ia_recommendations_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    return datos_avanzados.obtener_recomendaciones_ia(numero_cultivo)

# API para obtener pronóstico meteorológico
@app.route("/api/pronostico/<numero_cultivo>", methods=["GET"])
def pronostico_cultivo_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    return datos_avanzados.obtener_pronostico_cultivo(numero_cultivo)

@app.route("/enviar_resumen_email/<numero_cultivo>", methods=["POST"])
def enviar_resumen_email(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        # Verificar si ya se envió un correo recientemente para este cultivo
        last_sent_key = f"last_email_sent_{numero_cultivo}"
        last_sent = session.get(last_sent_key)
        
        if last_sent and (datetime.now() - datetime.fromisoformat(last_sent)) < timedelta(hours=1):
            return jsonify({"error": "Ya se envió un resumen recientemente. Espere al menos 1 hora."}), 429
            
        # Obtener destinatarios y enviar correo (solo la versión V2)
        result = datos_avanzados.enviar_resumen_clima_email_V2(*datos_avanzados.obtener_destinatarios_cultivo(numero_cultivo))
        
        if not result:
            return jsonify({"error": "No se pudo enviar el resumen"}), 500
            
        # Actualizar el timestamp del último envío
        session[last_sent_key] = datetime.now().isoformat()
        
        return jsonify({"mensaje": "Resumen enviado con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#nueva ruta 
@app.route('/api/datos_avanzados/generar/<numero_cultivo>', methods=['POST'])
def generar_datos_avanzados_api(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"message": "No autorizado"}), 401
    
    # Verificar permisos para el cultivo
    user_info = session['usuario']
    tipo_usuario = user_info['tipo_usuario']
    user_id = user_info['id']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    authorized = False
    if tipo_usuario == 'agricultor':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND usuario_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'agronomo':
        cursor.execute("SELECT id FROM cultivos WHERE numero = ? AND agronomist_id = ?", (numero_cultivo, user_id))
        if cursor.fetchone(): authorized = True
    elif tipo_usuario == 'admin':
        authorized = True
    
    conn.close()

    if not authorized:
        return jsonify({"message": "No tiene permiso para generar datos para este cultivo"}), 403
    
    # Llamar a la función de generación de datos avanzados
    return datos_avanzados.generar_datos_avanzados(numero_cultivo)

# TENDENCIA HUMEDAD
@app.route('/api/datos_avanzados/historial_humedad/<numero_cultivo>', methods=['GET'])
def obtener_historial_humedad(numero_cultivo):
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT humedad_suelo, timestamp 
        FROM datos_sensores 
        WHERE numero_cultivo = ? 
        AND humedad_suelo IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 30
    """, (numero_cultivo,))
    
    historial = cursor.fetchall()
    conn.close()
    
    return jsonify([{"valor": row["humedad_suelo"], "fecha": row["timestamp"]} for row in historial])

# NUEVA RUTA PARA ELIMINAR CHAT 
@app.route('/chat/eliminar/<conversacion_id>', methods=['POST'])
def eliminar_conversacion(conversacion_id):
    chatbot.cambiar_estado(conversacion_id)
    return jsonify({"mensaje": "Conversación eliminada correctamente."})

# Inicia la aplicación Flask en modo depuración si el script se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)