// Define el componente Alpine para manejar el estado de autenticación y la interacción del header
function authComponent() {
    return {
        logoClicked: false,
        isLoggedIn: false,
        // Realiza una petición a la API para verificar si la sesión está activa
        checkSession() {
            fetch('/api/verificar_sesion')
                .then(response => response.json())
                .then(data => {
                    this.isLoggedIn = data.sesion_activa;
                })
                .catch(() => {
                    this.isLoggedIn = false;
                });
        },
        // Al hacer clic en el botón, se verifica la sesión y se redirige a perfil o login según corresponda
        handleLogin() {
            fetch('/api/verificar_sesion')
                .then(response => response.json())
                .then(data => {
                    if (data.sesion_activa) {
                        window.location.href = "/perfil";
                    } else {
                        window.location.href = "/login";
                    }
                })
                .catch(() => {
                    window.location.href = '/login';
                });
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const link = document.getElementById('cultivos-link');

    link.addEventListener('click', function(event) {
        event.preventDefault();  // Evita que el enlace redirija inmediatamente

        fetch("/cultivos")
            .then(response => {
                if (response.status === 403) {
                    response.json().then(data => {
                        M.toast({html: data.message, classes: 'red darken-1'});
                    });
                } else if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    window.location.href = "/cultivos";
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });
});
