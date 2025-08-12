// static/js/alertas.js

// Función para agregar una nueva alerta
async function agregarAlerta(event) {
    event.preventDefault(); // Evita el envío del formulario por defecto

    const tipoAlerta = document.querySelector('select[name="tipo_alerta"]').value;
    const umbral = document.querySelector('input[name="umbral"]').value;
    const condicion = document.querySelector('select[name="condicion"]').value;

    // Validación básica en el cliente
    if (!tipoAlerta || !umbral || !condicion) {
        alert('Por favor, complete todos los campos de la alerta.');
        return;
    }
    if (isNaN(umbral)) {
        alert('El umbral debe ser un número válido.');
        return;
    }

    try {
        const response = await fetch('/alertas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tipo_alerta: tipoAlerta,
                umbral: parseFloat(umbral),
                condicion: condicion
            })
        });

        const responseData = await response.json();

        if (response.ok) {
            alert(responseData.message);
            location.reload(); // Recarga la página para ver la nueva alerta
        } else {
            console.error('Error al agregar alerta:', responseData);
            alert(`Error: ${responseData.message || 'No se pudo agregar la alerta.'}`);
        }
    } catch (error) {
        console.error('Error de red o inesperado al agregar alerta:', error);
        alert('Ocurrió un error inesperado. Por favor, inténtelo de nuevo.');
    }
}

// Función para eliminar una alerta
async function eliminarAlerta(alertaId) {
    if (!confirm("¿Estás seguro de que deseas eliminar esta alerta?")) {
        return;
    }
    try {
        const response = await fetch(`/alertas/eliminar/${alertaId}`, {
            method: 'POST',  // Se utiliza POST para eliminar la alerta
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const responseData = await response.json();
        if (response.ok) {
            alert(responseData.message);
            // Remueve la fila correspondiente sin recargar la página
            const row = document.getElementById(`alerta-${alertaId}`);
            if (row) {
                row.remove();
            }
        } else {
            console.error('Error al eliminar alerta:', responseData);
            alert(`Error: ${responseData.message}`);
        }
    } catch (error) {
        console.error('Error de red o inesperado al eliminar alerta:', error);
        alert('Ocurrió un error inesperado. Por favor, inténtalo de nuevo.');
    }
}

// Función para cargar el historial de alertas
async function cargarHistorial() {
    const tableBody = document.querySelector('#historial-body');
    if (!tableBody) return; // Si el contenedor no existe, salir

    try {
        const response = await fetch('/api/historial_alertas');
        if (response.ok) {
            const historial = await response.json();
            console.log("Historial recibido:", historial);
            tableBody.innerHTML = ''; // Limpiar el contenido anterior

            if (historial.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6">No hay historial de alertas.</td></tr>';
                return;
            }

            historial.forEach(alerta => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${alerta.fecha}</td>
                    <td>${alerta.tipo_alerta.replace('_', ' ').charAt(0).toUpperCase() + alerta.tipo_alerta.replace('_', ' ').slice(1)}</td>
                    <td>${(alerta.valor_sensor !== null && alerta.valor_sensor !== undefined) ? alerta.valor_sensor : 'N/A'}</td>
                    <td>${alerta.condicion ? alerta.condicion : 'N/A'}</td>
                    <td>${alerta.umbral}</td>
                    <td>${(alerta.numero_cultivo !== null && alerta.numero_cultivo !== undefined) ? alerta.numero_cultivo : 'N/A'}</td>
                `;
                tableBody.appendChild(row);
            });
        } else {
            const errorData = await response.json();
            console.error('Error al cargar el historial de alertas:', errorData);
            alert(`Error al cargar el historial de alertas: ${errorData.message || ''}`);
        }
    } catch (error) {
        console.error('Error de red o inesperado al cargar historial:', error);
        alert('Ocurrió un error inesperado al cargar el historial.');
    }
}

// Función para gestionar preferencias de notificación
async function gestionarPreferencias(event) {
    event.preventDefault();

    const emailInput = document.querySelector('input[name="email_preferencia"]');
    const notificacionesCheckbox = document.querySelector('input[name="notificaciones"]');

    const email = emailInput ? emailInput.value : '';
    const notificaciones = notificacionesCheckbox ? notificacionesCheckbox.checked : false;

    try {
        const response = await fetch('/api/preferencias_notificacion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                notificaciones: notificaciones
            })
        });

        const responseData = await response.json();
        if (response.ok) {
            alert(responseData.message);
        } else {
            console.error('Error al actualizar preferencias:', responseData);
            alert(`Error: ${responseData.message || 'No se pudieron actualizar las preferencias.'}`);
        }
    } catch (error) {
        console.error('Error de red o inesperado al gestionar preferencias:', error);
        alert('Ocurrió un error inesperado al gestionar las preferencias.');
    }
}

// Función para cargar notificaciones (centro de notificaciones in-app)
async function cargarNotificaciones() {
    const notificacionesContainer = document.querySelector('#notificaciones-container');
    if (!notificacionesContainer) return;

    try {
        const response = await fetch('/api/notificaciones');
        if (response.ok) {
            const notificaciones = await response.json();
            notificacionesContainer.innerHTML = '';

            if (notificaciones.length === 0) {
                notificacionesContainer.innerHTML = '<p>No hay notificaciones recientes.</p>';
                return;
            }

            notificaciones.forEach(notificacion => {
                const notificacionElement = document.createElement('div');
                notificacionElement.classList.add('notification-item');
                notificacionElement.innerHTML = `
                    <strong>Alerta de ${notificacion.tipo_alerta.replace('_', ' ').charAt(0).toUpperCase() + notificacion.tipo_alerta.replace('_', ' ').slice(1)}</strong>
                    <br>Umbral: ${notificacion.umbral} - Fecha: ${new Date(notificacion.fecha).toLocaleString()}
                `;
                notificacionesContainer.appendChild(notificacionElement);
            });
        } else {
            const errorData = await response.json();
            console.error('Error al cargar las notificaciones:', errorData);
            notificacionesContainer.innerHTML = `<p>Error al cargar notificaciones: ${errorData.message || ''}</p>`;
        }
    } catch (error) {
        console.error('Error de red o inesperado al cargar notificaciones:', error);
        notificacionesContainer.innerHTML = '<p>Ocurrió un error inesperado al cargar las notificaciones.</p>';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    const alertasForm = document.querySelector('#alertas-form');
    if (alertasForm) {
        alertasForm.addEventListener('submit', agregarAlerta);
    }

    const preferenciasForm = document.querySelector('#preferencias-form');
    if (preferenciasForm) {
        preferenciasForm.addEventListener('submit', gestionarPreferencias);
    }
    
    if (document.querySelector('#historial-body')) {
        cargarHistorial();
    }
    
    // Cargar el centro de notificaciones
    cargarNotificaciones();
});
