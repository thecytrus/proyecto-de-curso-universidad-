// static/js/cultivos.js

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar selects de Materialize
    const selectElems = document.querySelectorAll('select');
    M.FormSelect.init(selectElems);

    // Variables para los marcadores temporales de añadir y editar en los mapas de los formularios
    let addFormMapMarker = null; // Changed from addModalMapMarker
    let editFormMapMarker = null; // Changed from editModalMapMarker

    // Elementos del DOM
    const mainMap = L.map('map').setView([-34.9825, -71.2317], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(mainMap);

    // Nuevas instancias de mapa para los formularios (no más modales)
    let addFormMap = null; // Changed from addModalMap
    let editFormMap = null; // Changed from editModalMap

    const cropsTableBody = document.getElementById('crops-table-body');
    const addCropSection = document.getElementById('add-crop-section'); // New element
    const editCropSection = document.getElementById('edit-crop-section'); // New element
    const addCropBtn = document.getElementById('add-crop-btn');
    const addCropForm = document.getElementById('add-crop-form');
    const editCropForm = document.getElementById('edit-crop-form');
    const cancelAddBtn = document.getElementById('cancel-add-btn'); // New
    const cancelEditBtn = document.getElementById('cancel-edit-btn'); // New

    let currentEditCropId = null; // Variable para almacenar el ID del cultivo que se está editando

    let cropsData = []; // Esta variable ahora solo se usa para los marcadores del mapa principal

    function showNotification(message, isError = false) {
        M.toast({
            html: message,
            classes: isError ? 'red darken-1' : 'green darken-1',
            displayLength: 3000
        });
    }

    // Poblar dinámicamente los selects con usuarios (solo agricultores)
    async function loadAgricultoresToSelects() {
        try {
            const response = await fetch('/api/usuarios');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            const addSelect = document.getElementById('usuario_id');
            const editSelect = document.getElementById('edit-usuario_id');
            let optionsHTML = '<option value="" disabled selected>Selecciona un agricultor</option>';
            data.forEach(usuario => {
                optionsHTML += `<option value="${usuario.id}">${usuario.nombre}</option>`;
            });
            if (addSelect) {
                addSelect.innerHTML = optionsHTML;
                M.FormSelect.init(addSelect);
            }
            if (editSelect) {
                editSelect.innerHTML = optionsHTML;
                M.FormSelect.init(editSelect);
            }
        } catch (error) {
            console.error('Error al cargar usuarios:', error);
            showNotification('Error al cargar la lista de agricultores.', true);
        }
    }

    loadAgricultoresToSelects(); // Cargar agricultores al cargar la página

    // Esta función solo se encarga de los marcadores del mapa principal
    function renderMainMapMarkers() {
        mainMap.eachLayer(layer => {
            if (layer instanceof L.Marker && layer.options && layer.options.cropId) {
                mainMap.removeLayer(layer);
            }
        });

        cropsData.forEach(crop => {
            const lat = parseFloat(crop.latitud);
            const lng = parseFloat(crop.longitud);
            if (!isNaN(lat) && !isNaN(lng)) {
                L.marker([lat, lng], { cropId: crop.numero })
                    .bindPopup(`<b>${crop.tipo}</b><br>Agricultor: ${crop.agricultor}<br>Ciudad: ${crop.ciudad}`)
                    .addTo(mainMap);
            }
        });

        attachTableActionListeners();
    }

    function attachTableActionListeners() {
        document.querySelectorAll('.edit-button').forEach(button => {
            button.onclick = async function() {
                const cropNumero = this.dataset.id;
                try {
                    const response = await fetch('/api/cultivos');
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
                    }
                    const allCrops = await response.json();
                    // Cambio aquí: usar == en vez de === para comparar crop.numero con cropNumero
                    const cropToEdit = allCrops.find(crop => crop.numero == cropNumero);

                    if (cropToEdit) {
                        currentEditCropId = cropNumero;
                        document.getElementById('edit-numero').value = cropToEdit.numero;
                        document.getElementById('edit-ciudad').value = cropToEdit.ciudad;
                        document.getElementById('edit-tipo').value = cropToEdit.tipo;
                        document.getElementById('edit-latitud').value = cropToEdit.latitud;
                        document.getElementById('edit-longitud').value = cropToEdit.longitud;

                        const editSelect = document.getElementById('edit-usuario_id');
                        if (editSelect) {
                            await loadAgricultoresToSelects();
                            editSelect.value = cropToEdit.usuario_id;
                            M.FormSelect.init(editSelect);
                        }

                        M.updateTextFields();

                        // Show the edit form section
                        editCropSection.classList.remove('hide');
                        // Hide the add form section if it's open
                        addCropSection.classList.add('hide');

                        // Initialize/Update edit map
                        if (!editFormMap) {
                            editFormMap = L.map('edit-form-map').setView([-34.9825, -71.2317], 12); // Changed ID
                            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                                attribution: '&copy; OpenStreetMap contributors',
                                maxZoom: 18
                            }).addTo(editFormMap);
                            editFormMap.on('click', onEditFormMapClick); // Changed handler
                        }

                        // Invalidate size and set marker/view
                        editFormMap.invalidateSize(true);
                        const lat = parseFloat(cropToEdit.latitud);
                        const lon = parseFloat(cropToEdit.longitud);
                        if (!isNaN(lat) && !isNaN(lon)) {
                            if (editFormMapMarker) {
                                editFormMap.removeLayer(editFormMapMarker);
                            }
                            editFormMapMarker = L.marker([lat, lon]).addTo(editFormMap);
                            editFormMap.setView([lat, lon], 14);
                        } else {
                            editFormMap.setView([-34.9825, -71.2317], 12);
                        }

                        // Scroll to the edit form
                        editCropSection.scrollIntoView({ behavior: 'smooth' });

                    } else {
                        showNotification('No se encontró el cultivo para editar o no tiene permiso.', true);
                    }
                } catch (error) {
                    console.error('Error al obtener cultivo para editar:', error);
                    showNotification(`Error al cargar datos del cultivo para edición: ${error.message}`, true);
                }
            };
        });

        document.querySelectorAll('.delete-button').forEach(button => {
            button.onclick = function() {
                const cropNumero = this.dataset.id;
                if (confirm(`¿Estás seguro de que quieres eliminar el cultivo con número ${cropNumero}?`)) {
                    fetch(`/api/cultivos/${cropNumero}`, { method: 'DELETE' })
                        .then(async response => {  // Cambio aquí para usar async y response correctamente
                            const data = await response.json();
                            if (response.ok) {
                                showNotification(data.message);
                                window.location.reload();
                            } else {
                                showNotification(data.message, true);
                            }
                        })
                        .catch(error => {
                            console.error('Error al eliminar el cultivo:', error);
                            showNotification('Error al eliminar el cultivo.', true);
                        });
                }
            };
        });
    }

    function fetchCrops() {
        fetch('/api/cultivos')
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.message || response.statusText); });
                }
                return response.json();
            })
            .then(data => {
                cropsData = data;
                renderMainMapMarkers();
            })
            .catch(error => {
                console.error('Error al cargar los cultivos:', error);
                showNotification(`Error al cargar los cultivos: ${error.message}. Inténtalo de nuevo más tarde.`, true);
            });
    }

    fetchCrops(); // Llamada inicial para cargar cultivos

    if (addCropBtn) {
        addCropBtn.addEventListener('click', () => {
            // Hide edit section if it's open
            editCropSection.classList.add('hide');

            // Show add section
            addCropSection.classList.remove('hide');

            // Initialize add map if not already
            if (!addFormMap) {
                addFormMap = L.map('add-form-map').setView([-34.9825, -71.2317], 12); // Changed ID
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors',
                    maxZoom: 18
                }).addTo(addFormMap);
                addFormMap.on('click', onAddFormMapClick); // Changed handler
            }

            // Invalidate size for the add map and reset view/marker
            addFormMap.invalidateSize(true);
            addFormMap.setView([-34.9825, -71.2317], 12);
            if (addFormMapMarker) {
                addFormMap.removeLayer(addFormMapMarker);
                addFormMapMarker = null;
            }
            document.getElementById('latitud').value = '';
            document.getElementById('longitud').value = '';
            M.updateTextFields(); // Update Materialize text fields for empty values

            addCropForm.reset(); // Clear form fields for new entry
            M.FormSelect.init(document.getElementById('usuario_id')); // Re-init select

            // Scroll to the add form
            addCropSection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Cancel button for Add form
    if (cancelAddBtn) {
        cancelAddBtn.addEventListener('click', () => {
            addCropSection.classList.add('hide');
            addCropForm.reset();
            // Clear map marker if exists
            if (addFormMapMarker) {
                addFormMap.removeLayer(addFormMapMarker);
                addFormMapMarker = null;
            }
        });
    }

    // Cancel button for Edit form
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', () => {
            editCropSection.classList.add('hide');
            editCropForm.reset();
            currentEditCropId = null;
            // Clear map marker if exists
            if (editFormMapMarker) {
                editFormMap.removeLayer(editFormMapMarker);
                editFormMapMarker = null;
            }
        });
    }


    // Envío del formulario de agregado
    if (addCropForm) {
        addCropForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(addCropForm);
            const addSelect = document.getElementById('usuario_id');
            const selectedOption = addSelect.options[addSelect.selectedIndex];

            const newCrop = {
                numero: formData.get('numero'),
                ciudad: formData.get('ciudad'),
                tipo: formData.get('tipo'),
                latitud: formData.get('latitud'),
                longitud: formData.get('longitud'),
                usuario_id: formData.get('usuario_id'),
            };

            fetch('/api/cultivos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newCrop),
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.message || response.statusText); });
                }
                return response.json();
            })
            .then(data => {
                showNotification(data.message);
                addCropForm.reset();
                addCropSection.classList.add('hide');
                window.location.reload();
            })
            .catch(error => {
                console.error('Error al agregar el cultivo:', error);
                showNotification(`Error al agregar el cultivo: ${error.message}`, true);
            });
        });
    }

    // Envío del formulario de edición
    if (editCropForm) {
        editCropForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            if (!currentEditCropId) {
                showNotification('No hay cultivo seleccionado para editar.', true);
                return;
            }

            const formData = new FormData(editCropForm);
            const editedCrop = {
                ciudad: formData.get('ciudad'),
                tipo: formData.get('tipo'),
                usuario_id: formData.get('usuario_id'),
                latitud: document.getElementById('edit-latitud').value || undefined,
                longitud: document.getElementById('edit-longitud').value || undefined
            };

            try {
                const response = await fetch(`/api/cultivos/${currentEditCropId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(editedCrop),
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || 'Error al editar cultivo');
                }

                showNotification(data.message);
                editCropForm.reset();
                editCropSection.classList.add('hide');
                currentEditCropId = null;
                fetchCrops(); // Actualiza la lista de cultivos
            } catch (error) {
                console.error('Error al editar el cultivo:', error);
                showNotification(`Error al editar el cultivo: ${error.message}`, true);
            }
        });
    }

    // Click en el mapa de agregar cultivo
    function onAddFormMapClick(e) {
        if (addFormMapMarker) {
            addFormMap.removeLayer(addFormMapMarker);
        }
        addFormMapMarker = L.marker(e.latlng).addTo(addFormMap);
        document.getElementById('latitud').value = e.latlng.lat.toFixed(6);
        document.getElementById('longitud').value = e.latlng.lng.toFixed(6);
        M.updateTextFields();
    }

    // Click en el mapa de editar cultivo
    function onEditFormMapClick(e) {
        if (editFormMapMarker) {
            editFormMap.removeLayer(editFormMapMarker);
        }
        editFormMapMarker = L.marker(e.latlng).addTo(editFormMap);
        document.getElementById('edit-latitud').value = e.latlng.lat.toFixed(6);
        document.getElementById('edit-longitud').value = e.latlng.lng.toFixed(6);
        M.updateTextFields();
    }

});
