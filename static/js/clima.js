document.addEventListener("DOMContentLoaded", function () {
  const weatherForm = document.getElementById("weatherForm");
  weatherForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const city = document.getElementById("cityInput").value;
    if (city) {
      fetchWeather(city);
    }
  });

  // Automatically fetch weather for Curicó, Maule, Chile on page load
  fetchWeather("Curicó"); // Initial city

  activateDarkModeAtNight();
});

function fetchWeather(city) {
  fetch("/api/weather", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city: city }),
  })
    .then((response) => response.json())
    .then((data) => {
      // Check if data, forecast, and current exist and forecast is an array
      if (data && data.forecast && Array.isArray(data.forecast) && data.current) {
        updateDOMWithWeather(data);
        updateBackground(data.current.description);
        if (
          data.current.description.toLowerCase().includes("rain") ||
          data.current.description.toLowerCase().includes("lluvia") ||
          data.current.description.toLowerCase().includes("drizzle") ||
          data.current.description.toLowerCase().includes("tormenta") ||
          data.current.description.toLowerCase().includes("thunderstorm")
        ) {
          createRain();
        } else {
          clearRain();
        }
      } else {
        // Reemplazar alert() con un mensaje en la UI o un toast
        M.toast({html: "No se encontró pronóstico para la ciudad especificada o los datos no son válidos.", classes: 'red darken-1'});
      }
    })
    .catch((error) => {
      console.error("Error al obtener el clima:", error);
      // Reemplazar alert() con un mensaje en la UI o un toast
      M.toast({html: "Ocurrió un error al cargar el clima. Por favor, intenta de nuevo.", classes: 'red darken-1'});
    });
}

function getWeatherIcon(description) {
  description = description.toLowerCase();
  if (description.includes("lluvia") || description.includes("rain")) return "umbrella";
  if (description.includes("nublado") || description.includes("cloud")) return "cloud";
  if (description.includes("soleado") || description.includes("sunny") || description.includes("despejado") || description.includes("cielo claro")) return "wb_sunny";
  if (description.includes("tormenta") || description.includes("storm") || description.includes("thunderstorm")) return "flash_on";
  if (description.includes("nieve") || description.includes("snow")) return "ac_unit";
  return "wb_cloudy";
}

function updateDOMWithWeather(data) {
  const locationDiv = document.getElementById("location");
  locationDiv.innerHTML = `<h2>${data.city} - Actualizado: ${data.current.time}</h2>`;

  const forecastDiv = document.getElementById("forecast");
  forecastDiv.innerHTML = "";

  function getDayName(dateString) {
    // Convertir ambas fechas a la zona horaria de Chile
    const chileTime = new Date().toLocaleString("en-US", { timeZone: "America/Santiago" });
    const todayChile = new Date(chileTime);
    todayChile.setHours(0, 0, 0, 0);

    const forecastDate = new Date(dateString + "T00:00:00-04:00"); // asume horario Chile
    forecastDate.setHours(0, 0, 0, 0);

    const diffTime = forecastDate.getTime() - todayChile.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Hoy";
    if (diffDays === 1) return "Mañana";
    if (diffDays === 2) return "Pasado Mañana";

    const options = { weekday: 'long' };
    return forecastDate.toLocaleDateString('es-ES', options);
  }

  data.forecast.forEach((dayData, index) => {
    const prediction = dayData.prediction;
    const displayDay = getDayName(dayData.date);
    const cardColorClass = (index === 0) ? "green lighten-4" : "white";

    const dayDiv = document.createElement("div");
    dayDiv.className = "col s12 m4";
    dayDiv.innerHTML = `
      <div class="card hoverable waves-effect ${cardColorClass}">
        <div class="card-content">
          <span class="card-title">
            <i class="material-icons left">${getWeatherIcon(prediction.description)}</i>
            ${displayDay} ${prediction.hour !== "N/A" ? ` ${prediction.hour}` : ''}
          </span>
          <p><strong>Temp:</strong> ${prediction.temp !== "N/A" ? prediction.temp + '°C' : 'N/A'}</p>
          <p><strong>Humedad:</strong> ${prediction.humidity !== "N/A" ? prediction.humidity + '%' : 'N/A'}</p>
          <p><strong>Lluvia:</strong> ${prediction.rain_prob !== "N/A" ? prediction.rain_prob + '%' : 'N/A'}</p>
          <p><strong>Viento:</strong> ${prediction.wind !== "N/A" ? prediction.wind + ' m/s' : 'N/A'}</p>
          <p>${prediction.description}</p>
        </div>
      </div>
    `;
    forecastDiv.appendChild(dayDiv);
  });
}

function updateBackground(description) {
  if (!description) return;
  const body = document.body;
  description = description.toLowerCase();
  if (description.includes("clear") || description.includes("despejado") || description.includes("cielo claro")) {
    body.className = "sunny";
  } else if (description.includes("cloud") || description.includes("nube") || description.includes("nublado")) {
    body.className = "cloudy";
  } else if (description.includes("rain") || description.includes("lluvia") || description.includes("drizzle") || description.includes("tormenta") || description.includes("thunderstorm")) {
    body.className = "rainy";
  } else {
    body.className = "";
  }
}

function createRain() {
  const rainContainer = document.getElementById("rain-container");
  if (!rainContainer) {
    console.error("Rain container not found.");
    return;
  }
  rainContainer.innerHTML = "";
  for (let i = 0; i < 30; i++) {
    const drop = document.createElement("div");
    drop.className = "raindrop";
    drop.style.left = `${Math.random() * window.innerWidth}px`;
    drop.style.animationDuration = `${Math.random() * 1.5 + 0.5}s`;
    rainContainer.appendChild(drop);
  }
}

function clearRain() {
  const rainContainer = document.getElementById("rain-container");
  if (rainContainer) {
    rainContainer.innerHTML = "";
  }
}

function activateDarkModeAtNight() {
  const hour = new Date().getHours();
  if (hour >= 19 || hour <= 6) {
    document.body.classList.add("dark-theme");
  } else {
    document.body.classList.remove("dark-theme"); // Ensure it's removed if not night
  }
}

function login() {
  window.location.href = "{{ url_for('login_route') }}";
}

// para bloquear el acceso de agricultor a cultivos
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
                M.toast({html: 'Error al verificar acceso a cultivos.', classes: 'red darken-1'});
            });
    });
});
