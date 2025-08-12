document.addEventListener("DOMContentLoaded", () => {
    // Manejo del formulario de Login para Admin
    const loginFormAdmin = document.getElementById("loginFormAdmin");
    if (loginFormAdmin) {
        loginFormAdmin.addEventListener("submit", async (event) => {
            event.preventDefault();
            const nombre = document.getElementById("nombreAdmin").value;
            const contrasena = document.getElementById("contrasenaAdmin").value;

            try {
                const response = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ nombre, contrasena })
                });
                const data = await response.json();
                const mensajeElem = document.getElementById("mensajeAdmin");
                if (mensajeElem) mensajeElem.textContent = data.message;

                if (response.ok) {
                    window.location.href = "/tecnicos";  // Redirige si el login fue exitoso
                }
            } catch (error) {
                console.error("Error en el login admin:", error);
            }
        });
    }

    // Manejo del formulario de Registro para Admin
    const registerFormAdmin = document.getElementById("registerFormAdmin");
    if (registerFormAdmin) {
        registerFormAdmin.addEventListener("submit", async (event) => {
            event.preventDefault();
            const nombre = document.getElementById("nombreRegistroAdmin").value;
            const contrasena = document.getElementById("contrasenaRegistroAdmin").value;
            const correo = document.getElementById("correoRegistroAdmin").value;

            try {
                const response = await fetch("/api/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ nombre, contrasena, correo })
                });
                const data = await response.json();
                const mensajeRegistroElem = document.getElementById("mensajeRegistroAdmin");
                if (mensajeRegistroElem) mensajeRegistroElem.textContent = data.message;

                if (response.ok) {
                    window.location.href = "/login_admin";  // Redirige al login después del registro
                }
            } catch (error) {
                console.error("Error en el registro admin:", error);
            }
        });
    }
});
