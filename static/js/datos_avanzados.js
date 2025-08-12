document.addEventListener('DOMContentLoaded', function () {
    M.AutoInit();

    const cultivoSelector = document.getElementById('cultivo_selector');
    const timeRangeButtons = document.querySelectorAll('.time-range-btn');
    const sensorSummaryList = document.getElementById('sensor-summary-list');
    const iaRecommendationsDiv = document.getElementById('ia-recommendations');
    const weatherForecastDiv = document.getElementById('weather-forecast');
    const enviarEmailBtn = document.getElementById('enviar-email-btn');
    const emailStatusDiv = document.getElementById('email-status');

    let currentCultivo = cultivoSelector.value;
    let currentTimeRange = 7;
    let comparativoChartInstance = null;
    let tendenciasChartInstance = null;

    // Event listeners
    cultivoSelector.addEventListener('change', (event) => {
        currentCultivo = event.target.value;
        fetchAndRenderData();
    });

    timeRangeButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            currentTimeRange = parseInt(event.target.dataset.days);
            timeRangeButtons.forEach(btn => btn.classList.remove('blue', 'darken-2'));
            event.target.classList.add('blue', 'darken-2');
            fetchAndRenderData();
        });
    });

    enviarEmailBtn.addEventListener('click', function() {
        if (!currentCultivo) {
            emailStatusDiv.innerHTML = '<span style="color: red;">Selecciona un cultivo primero</span>';
            return;
        }
        
        enviarEmailBtn.disabled = true;
        enviarEmailBtn.innerHTML = '<i class="material-icons left">hourglass_empty</i> Enviando...';
        emailStatusDiv.innerHTML = '';
        
        fetch(`/enviar_resumen_email/${currentCultivo}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                emailStatusDiv.innerHTML = `<span style="color: red;">Error: ${data.error}</span>`;
            } else {
                emailStatusDiv.innerHTML = `<span style="color: green;">${data.mensaje || 'Resumen enviado con éxito'}</span>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            emailStatusDiv.innerHTML = `<span style="color: red;">${error.error || 'Error al enviar el email'}</span>`;
        })
        .finally(() => {
            enviarEmailBtn.disabled = false;
            enviarEmailBtn.innerHTML = '<i class="material-icons left">email</i> Enviar Resumen';
        });
    });

    // En la función fetchAndRenderData, antes de obtener los datos avanzados, llama a generar_datos_avanzados
    function fetchAndRenderData() {
        if (!currentCultivo) {
            sensorSummaryList.innerHTML = '<li class="collection-item">No hay cultivo seleccionado.</li>';
            iaRecommendationsDiv.innerHTML = '<p>Por favor, selecciona un cultivo para ver los datos.</p>';
            weatherForecastDiv.innerHTML = '';
            destroyCharts();
            return;
        }

        // Mostrar cargando
        sensorSummaryList.innerHTML = `
            <li class="collection-header"><h5>Estadísticas de Sensores</h5></li>
            <li class="collection-item">
                <div class="progress">
                    <div class="indeterminate"></div>
                </div>
                <span style="margin-left: 10px;">Cargando datos para Cultivo ${currentCultivo}...</span>
            </li>
        `;
        
        iaRecommendationsDiv.innerHTML = `
            <div class="progress">
                <div class="indeterminate"></div>
            </div>
            <p>Cargando recomendaciones para Cultivo ${currentCultivo}...</p>
        `;
        
        weatherForecastDiv.innerHTML = `
            <div class="progress">
                <div class="indeterminate"></div>
            </div>
            <p>Cargando pronóstico para Cultivo ${currentCultivo}...</p>
        `;

        // Primero generamos los datos avanzados para el cultivo seleccionado
        fetch(`/api/datos_avanzados/generar/${currentCultivo}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al generar datos avanzados');
            }
            return response.json();
        })
        .then(() => {
            // Después de generar los datos, obtenemos los datos avanzados, recomendaciones y pronóstico
            return Promise.all([
                fetch(`/api/datos_avanzados/${currentCultivo}`).then(res => res.json()),
                fetch(`/api/ia_recommendations/${currentCultivo}`).then(res => res.json()),
                fetch(`/api/pronostico/${currentCultivo}`).then(res => res.json())
            ]);
        })
        .then(([datos, recomendaciones, pronostico]) => {
            if (datos.error) throw new Error(datos.error);
            if (recomendaciones.error) throw new Error(recomendaciones.error);
            if (pronostico.error) throw new Error(pronostico.error);
            
            renderSensorSummary(datos);
            renderComparativoChart(datos);
            renderTendenciasChart(datos);
            renderIARecommendations(recomendaciones);
            renderWeatherForecast(pronostico);
        })
        .catch(error => {
            console.error('Error:', error);
            M.toast({html: `Error: ${error.message}`, classes: 'red'});
            sensorSummaryList.innerHTML = '<li class="collection-item">Error al cargar datos.</li>';
            iaRecommendationsDiv.innerHTML = '<p>Error al cargar recomendaciones.</p>';
            weatherForecastDiv.innerHTML = '<p>Error al cargar pronóstico.</p>';
        });
    }

    function renderSensorSummary(data) {
        sensorSummaryList.innerHTML = '<li class="collection-header"><h5>Estadísticas de Sensores</h5></li>';
        
        const params = [
            {key: 'humedad', name: 'Humedad Suelo', icon: 'opacity', unit: '%'},
            {key: 'ph', name: 'pH Suelo', icon: 'science', unit: ''},
            {key: 'temp', name: 'Temperatura', icon: 'thermostat', unit: '°C'},
            {key: 'nitrogeno', name: 'Nitrógeno', icon: 'grass', unit: 'ppm'},
            {key: 'fosforo', name: 'Fósforo', icon: 'eco', unit: 'ppm'},
            {key: 'potasio', name: 'Potasio', icon: 'grain', unit: 'ppm'}
        ];

        params.forEach(param => {
            const itemData = data[param.key];
            if (!itemData || itemData.ultimo === null) return;

            const listItem = document.createElement('li');
            listItem.className = 'collection-item';
            
            let content = `<i class="material-icons left">${param.icon}</i><strong>${param.name}</strong>: `;
            content += `Último: ${itemData.ultimo.toFixed(2)}${param.unit} | `;
            content += `Prom: ${itemData.promedio.toFixed(2)}${param.unit} | `;
            content += `Rango: ${itemData.minimo.toFixed(2)}-${itemData.maximo.toFixed(2)}${param.unit}`;
            
            if (itemData.anomalia === 1) {
                content += ` <span class="new badge red" data-badge-caption="ANOMALÍA"></span>`;
            }

            listItem.innerHTML = content;
            sensorSummaryList.appendChild(listItem);
        });

        if (data.probabilidad_lluvia !== null) {
            const rainItem = document.createElement('li');
            rainItem.className = 'collection-item';
            rainItem.innerHTML = `
                <i class="material-icons left">cloud</i>
                <strong>Probabilidad Lluvia</strong>: ${data.probabilidad_lluvia.toFixed(0)}%
            `;
            sensorSummaryList.appendChild(rainItem);
        }
    }

    function renderComparativoChart(data) {
        destroyChart(comparativoChartInstance);
        
        const ctx = document.getElementById('comparativoChart').getContext('2d');
        const labels = [];
        const valores = [];
        const colores = [];
        const bordes = [];
        const tooltipInfo = [];

        const parametros = [
            {key: 'humedad', name: 'Humedad', color: 'rgba(75, 192, 192, 0.6)', unit: '%'},
            {key: 'ph', name: 'pH', color: 'rgba(153, 102, 255, 0.6)', unit: ''},
            {key: 'temp', name: 'Temp.', color: 'rgba(255, 159, 64, 0.6)', unit: '°C'},
            {key: 'nitrogeno', name: 'Nitrógeno', color: 'rgba(54, 162, 235, 0.6)', unit: 'ppm'},
            {key: 'fosforo', name: 'Fósforo', color: 'rgba(255, 99, 132, 0.6)', unit: 'ppm'},
            {key: 'potasio', name: 'Potasio', color: 'rgba(201, 203, 207, 0.6)', unit: 'ppm'}
        ];

        parametros.forEach(param => {
            if (data[param.key] && data[param.key].ultimo !== null) {
                labels.push(param.name);
                valores.push(data[param.key].ultimo);
                colores.push(param.color);
                
                // Resaltar anomalías con borde rojo
                if (data[param.key].anomalia === 1) {
                    bordes.push('rgba(255, 0, 0, 1)');
                } else {
                    bordes.push('rgba(0, 0, 0, 0.1)');
                }

                // Preparar información para tooltip
                tooltipInfo.push({
                    ultimo: data[param.key].ultimo,
                    promedio: data[param.key].promedio,
                    minimo: data[param.key].minimo,
                    maximo: data[param.key].maximo,
                    desviacion: data[param.key].desviacion,
                    anomalia: data[param.key].anomalia,
                    unit: param.unit
                });
            }
        });

        comparativoChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Últimos Valores',
                    data: valores,
                    backgroundColor: colores,
                    borderColor: bordes,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Comparativo de Valores Actuales',
                        font: { size: 16 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const info = tooltipInfo[context.dataIndex];
                                let label = `${context.dataset.label}: ${info.ultimo.toFixed(2)}${info.unit}`;
                                if (info.anomalia === 1) {
                                    label += ' (Anomalía detectada!)';
                                }
                                return label;
                            },
                            afterLabel: function(context) {
                                const info = tooltipInfo[context.dataIndex];
                                return [
                                    `Promedio: ${info.promedio.toFixed(2)}${info.unit}`,
                                    `Rango: ${info.minimo.toFixed(2)}-${info.maximo.toFixed(2)}${info.unit}`,
                                    `Desviación: ${info.desviacion.toFixed(2)}${info.unit}`
                                ];
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Valores'
                        },
                        ticks: {
                            callback: function(value) {
                                // Mostrar unidades solo si son consistentes (no es el caso aquí)
                                return value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
    }

    async function renderTendenciasChart(data) {
        destroyChart(tendenciasChartInstance);
        
        if (!data.humedad || data.humedad.ultimo === null) {
            renderEmptyTendenciaChart();
            return;
        }

        try {
            // Obtener datos históricos de humedad
            const response = await fetch(`/api/datos_avanzados/historial_humedad/${currentCultivo}`);
            const historial = await response.json();
            
            if (!historial || historial.length < 3) {
                renderEmptyTendenciaChart("Se necesitan al menos 3 datos históricos para calcular tendencia");
                return;
            }

            // Procesar datos históricos
            const historialValues = historial.map(item => item.valor).reverse();
            const fechas = historial.map(item => new Date(item.fecha).toLocaleDateString()).reverse();
            
            // Calcular regresión lineal para la tendencia
            const regression = linearRegression(historialValues);
            
            // Proyectar 6 días en el futuro
            const diasProyeccion = 6;
            const proyeccion = [];
            for (let i = 0; i <= diasProyeccion; i++) {
                proyeccion.push(regression.predict(historialValues.length + i));
            }

            // Ajustar según probabilidad de lluvia (si existe)
            const ajusteLluvia = data.probabilidad_lluvia ? data.probabilidad_lluvia / 100 * 5 : 0;
            const proyeccionAjustada = proyeccion.map(val => {
                // Aumentar humedad si hay probabilidad de lluvia
                let ajustado = val + ajusteLluvia;
                // Mantener entre 0-100%
                return Math.max(0, Math.min(100, ajustado));
            });

            // Crear etiquetas para el gráfico
            const labels = [...fechas];
            for (let i = 1; i <= diasProyeccion; i++) {
                labels.push(`Día +${i}`);
            }

            const ctx = document.getElementById('tendenciasChart').getContext('2d');
            tendenciasChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Histórico Humedad (%)',
                            data: [...historialValues, ...Array(diasProyeccion).fill(null)],
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1,
                            pointRadius: 3
                        },
                        {
                            label: 'Tendencia Proyectada (%)',
                            data: [...Array(historialValues.length).fill(null), ...proyeccionAjustada],
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            borderDash: [5, 5],
                            tension: 0.4,
                            pointRadius: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Tendencia de Humedad y Proyección',
                            font: { size: 16 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += context.parsed.y.toFixed(2) + '%';
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Humedad (%)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Fecha'
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Error al generar gráfico de tendencia:', error);
            renderEmptyTendenciaChart("Error al calcular tendencia");
        }
    }

    // Función auxiliar para regresión lineal
    function linearRegression(data) {
        const n = data.length;
        let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
        
        data.forEach((y, x) => {
            sumX += x;
            sumY += y;
            sumXY += x * y;
            sumXX += x * x;
        });
        
        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;
        
        return {
            predict: (x) => slope * x + intercept
        };
    }

    // Función para mostrar gráfico vacío
    function renderEmptyTendenciaChart(message = "No hay datos suficientes") {
        const ctx = document.getElementById('tendenciasChart').getContext('2d');
        tendenciasChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Día 1', 'Día 2', 'Día 3', 'Día 4', 'Día 5', 'Día 6', 'Día 7'],
                datasets: [{
                    label: message,
                    data: [],
                    borderColor: 'rgba(200, 200, 200, 1)',
                    backgroundColor: 'rgba(200, 200, 200, 0.2)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tendencia de Humedad'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function renderWeatherForecast(pronostico) {
        if (!pronostico || pronostico.length === 0) {
            weatherForecastDiv.innerHTML = '<p>No hay datos meteorológicos disponibles.</p>';
            return;
        }

        let html = '<h5>Pronóstico Meteorológico</h5><div class="row">';
        
        pronostico.forEach(dia => {
            html += `
                <div class="col s12 m4">
                    <div class="card-panel blue-grey lighten-5">
                        <h6>${dia.fecha}</h6>
                        <p><i class="material-icons left">thermostat</i> Temp: ${dia.temp}°C</p>
                        <p><i class="material-icons left">opacity</i> Lluvia: ${dia.probabilidad_lluvia}%</p>
                        <p>${dia.description}</p>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        weatherForecastDiv.innerHTML = html;
    }

    function renderIARecommendations(data) {
        if (data.recommendation) {
            iaRecommendationsDiv.innerHTML = `
                <div class="card-panel teal lighten-5">
                    <h5>Recomendaciones Inteligentes</h5>
                    <p>${data.recommendation.replace(/\n/g, '<br>')}</p>
                </div>
            `;
        } else {
            iaRecommendationsDiv.innerHTML = '<p>No hay recomendaciones disponibles.</p>';
        }
    }

    function destroyChart(chartInstance) {
        if (chartInstance) {
            chartInstance.destroy();
        }
    }

    function destroyCharts() {
        destroyChart(comparativoChartInstance);
        destroyChart(tendenciasChartInstance);
    }

    // Inicialización
    if (currentCultivo) {
        fetchAndRenderData();
        document.querySelector(`.time-range-btn[data-days="${currentTimeRange}"]`).classList.add('blue', 'darken-2');
    }
});