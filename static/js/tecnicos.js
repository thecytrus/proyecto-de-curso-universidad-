function eliminarUsuario(id) {
  if (confirm("¿Estás seguro de que deseas eliminar este usuario?")) {
      fetch(`/eliminar_usuario/${id}`, {
          method: 'GET'
      })
      .then(response => {
          if (response.ok) {
              const row = document.getElementById(`row-${id}`);
              if (row) {
                  row.remove();
              }
              alert("Usuario eliminado exitosamente.");
          } else {
              alert("No se pudo eliminar el usuario.");
          }
      })
      .catch(error => {
          console.error('Error:', error);
          alert("Ocurrió un error al intentar eliminar el usuario.");
      });
  }
}
 document.addEventListener('DOMContentLoaded', function () {
  const elems = document.querySelectorAll('.tooltipped');
  M.Tooltip.init(elems);
});
