# module/cultivos.py
import sqlite3
from flask import jsonify, request, session

DATABASE = "users.db"

def crear_tabla_cultivos():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cultivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            ciudad TEXT NOT NULL,
            agricultor TEXT NOT NULL,
            tipo TEXT NOT NULL,
            latitud REAL NOT NULL,
            longitud REAL NOT NULL,
            usuario_id INTEGER NOT NULL,
            agronomist_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (agronomist_id) REFERENCES usuarios(id)
        )
    """)
    conn.commit()
    conn.close()

def obtener_cultivos():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cultivos")
    cultivos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(cultivos)

def obtener_cultivos_por_usuario(usuario_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cultivos WHERE usuario_id=?", (usuario_id,))
    cultivos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(cultivos)

def obtener_cultivos_por_agronomo(agronomist_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cultivos WHERE agronomist_id=?", (agronomist_id,))
    cultivos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(cultivos)

def obtener_datos_cultivo(numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cultivos WHERE numero=?", (numero_cultivo,))
    cultivo = cursor.fetchone()
    conn.close()
    return dict(cultivo) if cultivo else None

def agregar_cultivo():
    datos = request.get_json()
    try:
        ciudad = datos['ciudad']
        tipo = datos['tipo']
        latitud = float(datos['latitud'])
        longitud = float(datos['longitud'])
        usuario_id = int(datos['usuario_id'])

        agronomist_id = session['usuario']['id'] if session.get('usuario') and session['usuario']['tipo_usuario'] == 'agronomo' else None
        if not agronomist_id:
            return jsonify({"message": "Usuario no autorizado o no es agrónomo"}), 403

    except (KeyError, ValueError) as e:
        return jsonify({"message": f"Datos inválidos o incompletos: {e}"}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM usuarios WHERE id=?", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"message": "Agricultor no encontrado con ese usuario_id"}), 400
    agricultor_nombre = row[0]

    cursor.execute("SELECT COUNT(*) FROM cultivos WHERE agronomist_id=?", (agronomist_id,))
    cantidad = cursor.fetchone()[0]

    numero = f"AGRO-{agronomist_id}-{cantidad + 1}"

    try:
        cursor.execute("""
            INSERT INTO cultivos (numero, ciudad, agricultor, tipo, latitud, longitud, usuario_id, agronomist_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (numero, ciudad, agricultor_nombre, tipo, latitud, longitud, usuario_id, agronomist_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "Error al insertar cultivo. Verifica que no esté duplicado."}), 400

    conn.close()
    return jsonify({"message": "Cultivo agregado exitosamente", "numero": numero})

def editar_cultivo(numero_cultivo):
    datos = request.get_json()
    if not datos:
        return jsonify({"message": "No se proporcionaron datos para actualizar"}), 400

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cultivos WHERE numero=?", (numero_cultivo,))
    cultivo = cursor.fetchone()
    if cultivo is None:
        conn.close()
        return jsonify({"message": f"Cultivo con número {numero_cultivo} no encontrado"}), 404

    # Validar y preparar datos
    campos_actualizados = {}
    for campo in ['ciudad', 'agricultor', 'tipo', 'latitud', 'longitud', 'usuario_id']:
        if campo in datos and datos[campo] is not None:
            if campo in ['latitud', 'longitud']:
                try:
                    campos_actualizados[campo] = float(datos[campo])
                except ValueError:
                    conn.close()
                    return jsonify({"message": f"El campo {campo} debe ser un número válido"}), 400
            elif campo == 'usuario_id':
                try:
                    campos_actualizados[campo] = int(datos[campo])
                except ValueError:
                    conn.close()
                    return jsonify({"message": "ID de usuario debe ser un número entero"}), 400
            else:
                campos_actualizados[campo] = datos[campo]

    # Verificar que al menos un campo fue proporcionado
    if not campos_actualizados:
        conn.close()
        return jsonify({"message": "No se proporcionaron datos válidos para actualizar"}), 400

    # Construir consulta dinámica
    set_clause = ", ".join([f"{campo}=?" for campo in campos_actualizados.keys()])
    valores = list(campos_actualizados.values())
    valores.append(numero_cultivo)

    cursor.execute(f"""
        UPDATE cultivos SET {set_clause}
        WHERE numero=?
    """, valores)

    conn.commit()
    conn.close()
    return jsonify({"message": f"Cultivo {numero_cultivo} actualizado exitosamente"})

def eliminar_cultivo(numero_cultivo):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cultivos WHERE numero=?", (numero_cultivo,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"message": f"Cultivo con número {numero_cultivo} no encontrado"}), 404
    conn.close()
    return jsonify({"message": f"Cultivo {numero_cultivo} eliminado exitosamente"})