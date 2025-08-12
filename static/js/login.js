document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const nombre = document.getElementById("nombre").value.trim();
      const contrasena = document.getElementById("contrasena").value.trim();
      const mensajeElem = document.getElementById("mensaje");

      mensajeElem.textContent = ""; // limpia mensajes previos

      if (!nombre || !contrasena) {
        mensajeElem.textContent = "Por favor, completa todos los campos.";
        return;
      }

      try {
        const response = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombre, contrasena }),
        });

        const data = await response.json();

        if (response.ok && data.message === "Inicio de sesión exitoso") {
          // Redirigir a la página principal o dashboard
          window.location.href = "/";
        } else {
          mensajeElem.textContent = data.message || "Usuario o contraseña incorrectos.";
        }
      } catch (error) {
        console.error("Error en el login:", error);
        mensajeElem.textContent = "Error de conexión al servidor.";
      }
    });
  }
});
