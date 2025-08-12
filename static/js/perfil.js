function toggleEdit() {
    const form = document.getElementById('editarPerfilForm');
    const info = document.getElementById('infoUsuario');
    const button = document.getElementById('editButton');
    
    if (form.style.display === 'none') {
        form.style.display = 'block';
        info.style.display = 'none';
        button.innerText = 'Cancelar';
    } else {
        form.style.display = 'none';
        info.style.display = 'block';
        button.innerText = 'Editar Perfil';
    }
}

document.getElementById('editarPerfilForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const data = {
        nombre: document.getElementById('nombre').value,
        correo: document.getElementById('correo').value,
        password_actual: document.getElementById('password_actual').value
    };
    
    fetch('/editar_perfil', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }).then(response => response.json()).then(data => {
        if (data.message === "Perfil actualizado correctamente") {
            M.toast({html: 'Perfil actualizado con éxito!', classes: 'green'});
            toggleEdit();
            document.getElementById('nombreMostrar').textContent = data.usuario.nombre;
            document.getElementById('correoMostrar').textContent = data.usuario.correo;
        } else {
            M.toast({html: 'Error al actualizar perfil: ' + data.message, classes: 'red'});
        }
    }).catch(() => {
        M.toast({html: 'Error al conectar con el servidor', classes: 'red'});
    });
});

document.getElementById('cambiarPasswordForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const data = {
        password_actual: document.getElementById('password_actual_cambio').value,
        password_nueva: document.getElementById('password_nueva').value,
        password_nueva_confirm: document.getElementById('password_nueva_confirm').value
    };

    fetch('/cambiar_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }).then(response => response.json()).then(data => {
        if (data.message === "Contraseña actualizada correctamente") {
            M.toast({html: 'Contraseña actualizada correctamente!', classes: 'green'});
            document.getElementById('cambiarPasswordForm').reset();
        } else {
            M.toast({html: 'Error al cambiar contraseña: ' + data.message, classes: 'red'});
        }
    }).catch(() => {
        M.toast({html: 'Error al conectar con el servidor', classes: 'red'});
    });
});
