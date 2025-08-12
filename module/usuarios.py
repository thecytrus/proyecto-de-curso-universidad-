from flask import request, jsonify
import sqlite3

def crear_base_datos():
    base = sqlite3.connect("users.db")
    cursor = base.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        contrasena TEXT,
        correo TEXT,
        tipo_usuario TEXT,
        email TEXT, -- Agregada columna para el email de notificación (redundante con 'correo' si este es el email principal, pero mantenida para tu estructura)
        notificaciones BOOLEAN DEFAULT 1 -- Agregada columna para la preferencia de notificación
    );
    """)
    base.commit()
    base.close()

def login_post():
    # Si la petición tiene JSON, lo procesa; de lo contrario usa request.form
    if request.is_json:
        datos = request.get_json()
    else:
        datos = request.form

    nombre = datos.get("nombre")
    contrasena = datos.get("contrasena")

    base = sqlite3.connect("users.db")
    cursor = base.cursor()
    # Cambiado para seleccionar todas las columnas necesarias si el usuario se autentica
    cursor.execute(
        "SELECT id, nombre, correo, tipo_usuario, email, notificaciones FROM usuarios WHERE (nombre=? OR correo=?) AND contrasena=?",
        (nombre, nombre, contrasena)
    )
    usuario_data = cursor.fetchone() # Fetchone devuelve una tupla por defecto
    base.close()

    if usuario_data:
        # Convertir a diccionario para la sesión si es necesario
        # En app.py, se esperaría que session['usuario'] sea un diccionario o un objeto accesible
        # Para que session['usuario']['id'] funcione, necesitaríamos convertirlo.
        # Si no se usa en app.py, no es estrictamente necesario aquí.
        # Pero para consistencia con app.py que usa session['usuario']['id']
        usuario = {
            "id": usuario_data[0],
            "nombre": usuario_data[1],
            "correo": usuario_data[2],
            "tipo_usuario": usuario_data[3],
            "email": usuario_data[4],
            "notificaciones": bool(usuario_data[5])
        }
        # Nota: app.py necesitaría manejar el almacenamiento de este diccionario en la sesión.
        # Por ahora, solo se devuelve el mensaje de éxito.
        return jsonify({"message": "Inicio de sesión exitoso", "user": usuario})
    else:
        return jsonify({"message": "Usuario o contraseña incorrectos"}), 401

def register_post():
    # Revisa si la petición es JSON; si no, toma los datos del formulario
    if request.is_json:
        datos = request.get_json()
    else:
        datos = request.form

    nombre = datos.get("nombre")
    contrasena = datos.get("contrasena")
    correo = datos.get("correo")
    tipo_usuario = datos.get("tipo_usuario")
    # Los nuevos campos tendrán valores por defecto o se pueden pasar si se requiere en el registro
    email_preferencia = datos.get("email", correo) # Por defecto, usa el correo principal
    notificaciones_preferencia = datos.get("notificaciones", True) # Por defecto, activadas

    if not nombre:
        return jsonify({"message": "El campo 'nombre' es requerido"}), 400
    if not contrasena:
        return jsonify({"message": "El campo 'contraseña' es requerido"}), 400
    if not correo:
        return jsonify({"message": "El campo 'correo' es requerido"}), 400
    if not tipo_usuario:
        return jsonify({"message": "El campo 'tipo_usuario' es requerido"}), 400

    base = sqlite3.connect("users.db")
    cursor = base.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE correo=?", (correo,))
    if cursor.fetchone():
        base.close()
        return jsonify({"message": "El correo ya está registrado"}), 400

    cursor.execute(
        "INSERT INTO usuarios (nombre, contrasena, correo, tipo_usuario, email, notificaciones) VALUES (?, ?, ?, ?, ?, ?)",
        (nombre, contrasena, correo, tipo_usuario, email_preferencia, notificaciones_preferencia)
    )
    base.commit()
    base.close()

    return jsonify({"message": "Usuario registrado exitosamente"})
