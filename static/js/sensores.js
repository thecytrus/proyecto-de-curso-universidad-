document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el menú lateral de Materialize
    M.Sidenav.init(document.querySelectorAll('.sidenav'));

    // Objetos globales para intervalos de actualización y para los gráficos Chart.js
    window.sensorRefreshIntervals = {};
    window.cropCharts = {};

    // Función para crear o actualizar un gráfico de líneas (Temperatura, pH)
    function createOrUpdateLineChart(ctx, chartId, label, unit, data, timestamps, color) {
        if (window.cropCharts[chartId]) {
            window.cropCharts[chartId].data.labels = timestamps;
            window.cropCharts[chartId].data.datasets[0].data = data;
            window.cropCharts[chartId].update();
        } else {
            window.cropCharts[chartId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: [{
                        label: label,
                        data: data,
                        borderColor: color,
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'category',
                            labels: timestamps,
                            title: { display: true, text: 'Tiempo' }
                        },
                        y: {
                            beginAtZero: false,
                            title: { display: true, text: unit }
                        }
                    },
                    plugins: {
                        tooltip: { mode: 'index', intersect: false }
                    }
                }
            });
        }
    }

    // Función para crear o actualizar un gráfico de barras (Humedad)
    function createOrUpdateBarChart(ctx, chartId, label, unit, data, timestamps) {
        if (window.cropCharts[chartId]) {
            window.cropCharts[chartId].data.labels = timestamps;
            window.cropCharts[chartId].data.datasets[0].data = data;
            window.cropCharts[chartId].update();
        } else {
            window.cropCharts[chartId] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: timestamps,
                    datasets: [{
                        label: label,
                        data: data,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: 'Tiempo' } },
                        y: { beginAtZero: true, title: { display: true, text: unit } }
                    }
                }
            });
        }
    }

    // Función para crear o actualizar un gráfico de líneas para Nutrientes (N, P, K)
    function createOrUpdateMultiLineNutrientChart(ctx, chartId, timestamps, nitrogenoData, fosforoData, potasioData) {
        if (window.cropCharts[chartId]) {
            window.cropCharts[chartId].data.labels = timestamps;
            window.cropCharts[chartId].data.datasets[0].data = nitrogenoData;
            window.cropCharts[chartId].data.datasets[1].data = fosforoData;
            window.cropCharts[chartId].data.datasets[2].data = potasioData;
            window.cropCharts[chartId].update();
        } else {
            window.cropCharts[chartId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: [
                        {
                            label: 'Nitrógeno (N)',
                            data: nitrogenoData,
                            borderColor: 'rgba(153, 102, 255, 1)',
                            backgroundColor: 'rgba(153, 102, 255, 0.2)',
                            fill: false,
                            tension: 0.1
                        },
                        {
                            label: 'Fósforo (P)',
                            data: fosforoData,
                            borderColor: 'rgba(255, 159, 64, 1)',
                            backgroundColor: 'rgba(255, 159, 64, 0.2)',
                            fill: false,
                            tension: 0.1
                        },
                        {
                            label: 'Potasio (K)',
                            data: potasioData,
                            borderColor: 'rgba(199, 199, 199, 1)',
                            backgroundColor: 'rgba(199, 199, 199, 0.2)',
                            fill: false,
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'category',
                            labels: timestamps,
                            title: { display: true, text: 'Tiempo' }
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'ppm' }
                        }
                    },
                    plugins: {
                        tooltip: { mode: 'index', intersect: false }
                    }
                }
            });
        }
    }

    // Función showPopup: genera un popup nuevo para cada notificación
    function showPopup(type, message) {
        console.log("showPopup llamado:", type, message);  // Para depuración
        const container = document.querySelector('.popup-container');
        let popupHTML = "";
        if (type === 'success') {
            popupHTML = `
                <div class="popup success-popup">
                  <div class="popup-icon success-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="success-svg">
                      <path fill-rule="evenodd"
                        d="M12 1C5.925 1 1 5.925 1 12s4.925 11 11 11 11-4.925 11-11S18.075 1 12 1zm4.768 9.14c.0878-.1004.1546-.21726.1966-.34383.0419-.12657.0581-.26026.0477-.39319-.0105-.13293-.0475-.26242-.1087-.38085-.0613-.11844-.1456-.22342-.2481-.30879-.1024-.08536-.2209-.14938-.3484-.18828s-.2616-.0519-.3942-.03823c-.1327.01366-.2612.05372-.3782.1178-.1169.06409-.2198.15091-.3027.25537l-4.3 5.159-2.225-2.226c-.1886-.1822-.4412-.283-.7034-.2807s-.51301.1075-.69842.2929-.29058.4362-.29285.6984c-.00228.2622.09851.5148.28067.7034l3 3c.0983.0982.2159.1748.3454.2251.1295.0502.2681.0729.4069.0665.1387-.0063.2747-.0414.3991-.1032.1244-.0617.2347-.1487.3236-.2554z"
                        clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <div class="success-message">${message}</div>
                  <div class="popup-icon close-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" aria-hidden="true" class="close-svg">
                      <path d="M15.8333 5.34166l-1.175-1.175-4.6583 4.65834-4.65833-4.65834-1.175 1.175 4.65833 4.65834-4.65833 4.6583 1.175 1.175 4.65833-4.6583 4.6583 4.6583 1.175-1.175-4.6583-4.6583z" class="close-path"></path>
                    </svg>
                  </div>
                </div>`;
        } else if (type === 'alert') {
            popupHTML = `
                <div class="popup alert-popup">
                  <div class="popup-icon alert-icon">
                    <svg class="alert-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" aria-hidden="true">
                      <path fill-rule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <div class="alert-message">${message}</div>
                  <div class="popup-icon close-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" class="close-svg">
                      <path d="M15.8333 5.34166l-1.175-1.175-4.6583 4.65834-4.65833-4.65834-1.175 1.175 4.65833 4.65834-4.65833 4.6583 1.175 1.175 4.65833-4.6583 4.6583 4.6583 1.175-1.175-4.6583-4.6583z" class="close-path"></path>
                    </svg>
                  </div>
                </div>`;
        } else if (type === 'error') {
            popupHTML = `
                <div class="popup error-popup">
                  <div class="popup-icon error-icon">
                    <svg class="error-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" aria-hidden="true">
                      <path fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  <div class="error-message">${message}</div>
                  <div class="popup-icon close-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" class="close-svg">
                      <path d="M15.8333 5.34166l-1.175-1.175-4.6583 4.65834-4.65833-4.65834-1.175 1.175 4.65833 4.65834-4.65833 4.6583 1.175 1.175 4.65833-4.6583 4.6583 4.6583 1.175-1.175-4.6583-4.6583z" class="close-path"></path>
                    </svg>
                  </div>
                </div>`;
        } else if (type === 'info') {
            popupHTML = `
                <div class="popup info-popup">
                  <div class="popup-icon info-icon">
                    <svg aria-hidden="true" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" class="info-svg">
                      <path clip-rule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                        fill-rule="evenodd"></path>
                    </svg>
                  </div>
                  <div class="info-message">${message}</div>
                  <div class="popup-icon close-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" class="close-svg">
                      <path d="M15.8333 5.34166l-1.175-1.175-4.6583 4.65834-4.65833-4.65834-1.175 1.175 4.65833 4.65834-4.65833 4.6583 1.175 1.175 4.65833-4.6583 4.6583 4.6583 1.175-1.175-4.6583-4.6583z" class="close-path"></path>
                    </svg>
                  </div>
                </div>`;
        }

        // Crear un nuevo elemento con el contenido HTML generado
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = popupHTML;
        const newPopup = tempDiv.firstElementChild;

        // Agregar el nuevo popup al contenedor
        container.appendChild(newPopup);

        // Configurar el cierre al hacer clic en su ícono y eliminación automática después de 7 segundos
        newPopup.querySelector('.close-icon').addEventListener('click', function() {
            container.removeChild(newPopup);
        });
        setTimeout(() => {
            if (container.contains(newPopup)) {
                container.removeChild(newPopup);
            }
        }, 7000);
    }

    // Función para obtener y graficar los datos históricos de un cultivo
    async function fetchHistoricalData(numero_cultivo) {
        try {
            const response = await fetch(`/api/sensores/${numero_cultivo}/historial`);
            if (!response.ok) {
                if (response.status === 403) {
                    console.warn(`Autorización perdida para el cultivo ${numero_cultivo}. No se pudieron cargar los datos históricos.`);
                    return;
                }
                throw new Error('Respuesta incorrecta al obtener datos históricos.');
            }
            const historicalData = await response.json();
            if (historicalData.length === 0) {
                console.log(`No hay datos históricos para el cultivo ${numero_cultivo}.`);
                // Destruir gráficos existentes si no hay datos
                ['temperatura', 'humedad', 'ph', 'nutrientes'].forEach(type => {
                    const chartId = `${type}-${numero_cultivo}`;
                    if (window.cropCharts[chartId]) {
                        window.cropCharts[chartId].destroy();
                        delete window.cropCharts[chartId];
                    }
                });
                return;
            }
            const timestamps = historicalData.map(d => new Date(d.timestamp).toLocaleTimeString());
            const temperaturaData = historicalData.map(d => d.temperatura_ambiente);
            const humedadData = historicalData.map(d => d.humedad_suelo);
            const phData = historicalData.map(d => d.ph_suelo);
            const nitrogenoData = historicalData.map(d => d.nitrogeno);
            const fosforoData = historicalData.map(d => d.fosforo);
            const potasioData = historicalData.map(d => d.potasio);

            // Obtener los contextos de los canvas
            const ctxTemp = document.getElementById(`chart-temperatura-${numero_cultivo}`).getContext('2d');
            const ctxHum = document.getElementById(`chart-humedad-${numero_cultivo}`).getContext('2d');
            const ctxPh = document.getElementById(`chart-ph-${numero_cultivo}`).getContext('2d');
            const ctxNutrientes = document.getElementById(`chart-nutrientes-${numero_cultivo}`).getContext('2d');

            // Crear o actualizar los gráficos
            createOrUpdateLineChart(ctxTemp, `temperatura-${numero_cultivo}`, 'Temperatura Ambiente', '°C', temperaturaData, timestamps, 'rgba(255, 99, 132, 1)');
            createOrUpdateBarChart(ctxHum, `humedad-${numero_cultivo}`, 'Humedad del Suelo', '%', humedadData, timestamps);
            createOrUpdateLineChart(ctxPh, `ph-${numero_cultivo}`, 'pH del Suelo', 'pH', phData, timestamps, 'rgba(75, 192, 192, 1)');
            createOrUpdateMultiLineNutrientChart(ctxNutrientes, `nutrientes-${numero_cultivo}`, timestamps, nitrogenoData, fosforoData, potasioData);
        } catch (error) {
            console.error('Error al obtener datos históricos:', error);
        }
    }

    // Función para obtener y actualizar los datos del sensor para un cultivo específico
    function fetchSensorData(numero_cultivo) {
        fetch(`/api/sensores/${numero_cultivo}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 403) {
                        console.warn(`Autorización perdida para el cultivo ${numero_cultivo}. Actualizaciones detenidas.`);
                        const button = document.querySelector(`.generar-datos[data-cultivo-numero="${numero_cultivo}"]`);
                        if (button) {
                            button.textContent = 'Iniciar Generación';
                            button.dataset.status = 'stopped';
                        }
                        clearInterval(window.sensorRefreshIntervals[numero_cultivo]);
                        delete window.sensorRefreshIntervals[numero_cultivo];
                        return Promise.reject('Problema de autorización');
                    }
                    throw new Error('Respuesta incorrecta del servidor.');
                }
                return response.json();
            })
            .then(data => {
                console.log("Datos del sensor (cultivo " + numero_cultivo + "):", data);
                const sensorDataDiv = document.getElementById(`data-${numero_cultivo}`);
                if (sensorDataDiv) {
                    if (Object.keys(data).length > 0) {
                        sensorDataDiv.querySelector('.humedad-suelo').textContent = data.humedad_suelo !== null ? data.humedad_suelo : 'N/A';
                        sensorDataDiv.querySelector('.ph-suelo').textContent = data.ph_suelo !== null ? data.ph_suelo : 'N/A';
                        sensorDataDiv.querySelector('.temperatura-ambiente').textContent = data.temperatura_ambiente !== null ? data.temperatura_ambiente : 'N/A';
                        sensorDataDiv.querySelector('.nitrogeno').textContent = data.nitrogeno !== null ? data.nitrogeno : 'N/A';
                        sensorDataDiv.querySelector('.fosforo').textContent = data.fosforo !== null ? data.fosforo : 'N/A';
                        sensorDataDiv.querySelector('.potasio').textContent = data.potasio !== null ? data.potasio : 'N/A';
                        sensorDataDiv.querySelector('.timestamp').textContent = data.timestamp || 'N/A';

                        // Actualizar gráficos con los datos nuevos
                        fetchHistoricalData(numero_cultivo);
                    } else {
                        sensorDataDiv.querySelector('.humedad-suelo').textContent = 'N/A';
                        sensorDataDiv.querySelector('.ph-suelo').textContent = 'N/A';
                        sensorDataDiv.querySelector('.temperatura-ambiente').textContent = 'N/A';
                        sensorDataDiv.querySelector('.nitrogeno').textContent = 'N/A';
                        sensorDataDiv.querySelector('.fosforo').textContent = 'N/A';
                        sensorDataDiv.querySelector('.potasio').textContent = 'N/A';
                        sensorDataDiv.querySelector('.timestamp').textContent = 'N/A';
                    }
                }

                // Mostrar alerta si alertTriggered es true
                if (data.alertTriggered) {
                    console.log("Alert triggered detected for cultivo " + numero_cultivo + ". Invocando showPopup().");
                    showPopup('alert', "¡Alerta activada! Revisar sensor.");
                }
            })
            .catch(error => {
                console.error('Error al obtener datos del sensor:', error);
            });
    }

    // Función para configurar el intervalo de actualización para un cultivo
    function setupRefreshInterval(numeroCultivo) {
        if (window.sensorRefreshIntervals[numeroCultivo]) {
            clearInterval(window.sensorRefreshIntervals[numeroCultivo]);
        }
        fetchSensorData(numeroCultivo);
        window.sensorRefreshIntervals[numeroCultivo] = setInterval(() => fetchSensorData(numeroCultivo), 5000);
    }

    // Manejo del botón "Generar Datos" para administradores y agrónomos
    const generarDatosButtons = document.querySelectorAll('.generar-datos');
    if (generarDatosButtons.length > 0) {
        generarDatosButtons.forEach(button => {
            const numeroCultivo = button.dataset.cultivoNumero;
            let currentStatus = button.dataset.status;
            fetchHistoricalData(numeroCultivo);
            if (currentStatus === 'running') {
                setupRefreshInterval(numeroCultivo);
            } else {
                fetchSensorData(numeroCultivo);
            }
            button.addEventListener('click', function() {
                const action = this.dataset.status === 'running' ? 'stop' : 'start';
                const buttonElement = this;
                fetch('/control_generacion_datos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ numero_cultivo: numeroCultivo, action: action })
                })
                .then(response => response.json())
                .then(data => {
                    showPopup('success', data.message);
                    if (action === 'start' && data.message.includes('iniciada')) {
                        buttonElement.textContent = 'Detener Generación';
                        buttonElement.dataset.status = 'running';
                        setupRefreshInterval(numeroCultivo);
                    } else if (action === 'stop' && data.message.includes('detenida')) {
                        buttonElement.textContent = 'Iniciar Generación';
                        buttonElement.dataset.status = 'stopped';
                        clearInterval(window.sensorRefreshIntervals[numeroCultivo]);
                        delete window.sensorRefreshIntervals[numeroCultivo];
                        // Optionally, fetch data one last time to show the final values before stopping
                        fetchSensorData(numeroCultivo);
                    }
                })
                .catch(error => {
                    console.error('Error al controlar la generación de datos:', error);
                    showPopup('error', 'Error al controlar la generación de datos.');
                });
            });
        });
    }

    // Para cada cultivo (aunque no tenga botón), configurar actualización periódica
    const sensorDataDivs = document.querySelectorAll('[id^="data-"]');
    sensorDataDivs.forEach(div => {
        const numeroCultivo = div.id.replace("data-", "");
        fetchHistoricalData(numeroCultivo);
        fetchSensorData(numeroCultivo);
        if (!window.sensorRefreshIntervals[numeroCultivo]) {
            window.sensorRefreshIntervals[numeroCultivo] = setInterval(() => fetchSensorData(numeroCultivo), 5000);
        }
    });
});