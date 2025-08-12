from flask import Blueprint, render_template, redirect, url_for, request, session, flash
import sqlite3

tecnicos_bp = Blueprint('tecnicos_bp', __name__)

def obtener_conexion():
    """Retorna una conexión a la base de datos users.db."""
    conexion = sqlite3.connect("users.db")
    conexion.row_factory = sqlite3.Row  # Permite acceder a los datos con nombres de columna en lugar de índices
    return conexion

@tecnicos_bp.route('/tecnicos')
def tecnicos_route():
    """
    Recupera los registros de la tabla 'usuarios' filtrando aquellos cuyo
    tipo_usuario es 'agricultor' o 'agronomo' y los muestra en la plantilla.
    Solo permite el acceso a usuarios ADMIN.
    """
    if 'usuario' not in session or session['usuario']['tipo_usuario'].upper() != 'ADMIN':
        flash("Acceso restringido: Solo administradores pueden ver esta página.", "error")
        return redirect(url_for('login_admin'))  # Redirige al login si no es ADMIN

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, nombre, correo, tipo_usuario 
            FROM usuarios 
            WHERE tipo_usuario IN ('agricultor', 'agronomo')
        """)
        usuarios = cursor.fetchall()

    return render_template('tecnicos.html', usuarios=usuarios)

@tecnicos_bp.route('/eliminar_usuario/<int:id>', methods=['GET'])
def eliminar_usuario(id):
    """
    Elimina el usuario cuyo id coincide y redirige a la vista.
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        if cursor.rowcount == 0:
            flash("El usuario no existe o ya fue eliminado.", "error")
        else:
            conexion.commit()
            flash("Usuario eliminado correctamente.", "success")

    return redirect(url_for('tecnicos_bp.tecnicos_route'))

@tecnicos_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if request.method == 'POST':
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()

            nombre = request.form.get('nombre')
            correo = request.form.get('correo')
            contrasena_nueva = request.form.get('contrasena')
            tipo_usuario = request.form.get('tipo_usuario')

            # Obtener la contraseña actual para comparar
            cursor.execute("SELECT contrasena FROM usuarios WHERE id = ?", (id,))
            fila = cursor.fetchone()
            if fila is None:
                flash("El usuario no existe.", "error")
                return redirect(url_for('tecnicos_bp.tecnicos_route'))

            contrasena_actual = fila['contrasena']

            # Validar que la nueva contraseña sea diferente a la actual
            if contrasena_nueva == contrasena_actual:
                flash("La nueva contraseña no puede ser igual a la actual.", "error")
                return redirect(url_for('tecnicos_bp.editar_usuario', id=id))

            cursor.execute(
                "UPDATE usuarios SET nombre = ?, correo = ?, contrasena = ?, tipo_usuario = ? WHERE id = ?",
                (nombre, correo, contrasena_nueva, tipo_usuario, id)
            )

            if cursor.rowcount == 0:
                flash("No se pudo actualizar el usuario.", "error")
            else:
                conexion.commit()
                flash("Usuario actualizado correctamente.", "success")

        return redirect(url_for('tecnicos_bp.tecnicos_route'))

    # GET request
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id, nombre, correo, contrasena, tipo_usuario FROM usuarios WHERE id = ?", (id,)
        )
        usuario = cursor.fetchone()

    if usuario is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for('tecnicos_bp.tecnicos_route'))

    return render_template("editar_usuario.html", usuario=usuario)
