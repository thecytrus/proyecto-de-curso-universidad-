## 🌱Integrantes de EcoSmart 
```
thecytrus: Dylan Moreno
fabiandres13: Fabian Paredes
Fel2003: Felipe Reyes
EGuzman723: Esteban Guzmán 

```
---

## 🌾EcoSmart 


EcoSmart es una plataforma inteligente para la gestión agrícola basada en tecnologías IoT, inteligencia artificial y análisis de datos. Permite monitorear cultivos en tiempo real, generar alertas, visualizar información meteorológica y optimizar decisiones agrícolas para agricultores, agrónomos y técnicos.


---
## 📁 Estructura lógica del proyecto 

```
EcoSmart/
├── app.py              # Inicio de la app Flask
├── module/             # Lógica del sistema (sensores, clima, cultivos, etc.)
├── templates/          # Vistas HTML del sistema
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── *.txt               # Archivos de persistencia (usuarios, clima, cultivos...)


```
---


## 📁 Estructura del Proyecto

```


EcoSmart
│
├── app.py                  #Archivo principal que inicia la aplicación Flask
├── README.md               #Documentación del proyecto
├── requirements.txt        #Dependencias del entorno
├── .gitignore              #Archivos ignorados por Git
├── chat_log.txt            #Registro del chatbot
├── clima.txt               #Registro del clima
├── datos_sensores.txt      #Datos simulados de sensores
├── cultivos.txt            #Encargada de guardar los cultivos
│
│
├── module/                 #Módulos lógicos del backend
│ ├── pycache/              #Archivos compilados por Python
│ │ ├── chatbot.cpython-313.pyc
│ │ ├── clima.cpython-313.pyc
│ │ ├── cultivos.cpython-313.pyc
│ │ ├── sensores.cpython-313.pyc
│ │ ├── tecnicos.cpython-313.pyc
│ │ └── usuarios.cpython-313.pyc
│ │
│ ├── chatbot.py            #Módulo del asistente conversacional
│ ├── clima.py              #Gestión de datos climáticos
│ ├── cultivos.py           #Lógica de cultivos agrícolas
│ ├── sensores.py           #Lectura y simulación de sensores
│ ├── tecnicos.py           #Gestión de técnicos
│ └── usuarios.py           #Gestión de usuarios y autenticación
│
│
├── static/                 #Archivos estáticos (CSS, JS, imágenes)
│ │
│ ├── css/                 #Hojas de estilo personalizadas
│ │ ├── chatbot.css
│ │ ├── clima.css
│ │ ├── cultivos.css
│ │ ├── index.css
│ │ ├── login.css
│ │ ├── sensores.css
│ │ └── tecnicos.css
│ │
│ ├── images/             #Recursos gráficos del sitio
│ │ ├── clima.jpg
│ │ ├── cultivos.jpg
│ │ ├── foto1carrusel.jpg
│ │ ├── foto2carrusel.jpg
│ │ ├── foto3carrusel.jpg
│ │ ├── ia.pg
│ │ ├── imagen-principal.jpg
│ │ ├── logo.png
│ │ ├── monitoreo.jpg
│ │ └── user-profile.png
│ │
│ └── js/                 #Scripts para interacción en el frontend
│ ├── chatbot.js
│ ├── clima.js
│ ├── cultivos.js
│ ├── index.js
│ ├── login.js
│ ├── login_admin.js
│ ├── perfil.js
│ ├── sensores.js
│ └── tecnicos.js
│
└── templates/            #Vistas HTML renderizadas por Flask
  ├── chatbot.html
  ├── clima.html
  ├── cultivos.html
  ├── editar_usuario.html
  ├── index.html
  ├── login.html
  ├── login_admin.html
  ├── perfil.html
  ├── register.html
  ├── register_admin.html
  ├── sensores.html
  └── tecnicos.html



```
---

## 🚀 Funcionalidades Principales


📊 Monitoreo de Sensores

Simula sensores de temperatura, humedad del suelo y otros parámetros clave. 


☁️ Clima en Tiempo Real

Consulta y registra las condiciones climáticas actuales.


🌾 Gestión de Cultivos

Permite registrar, visualizar y actualizar los cultivos.


🧠 Asistente Virtual (Chatbot)

Integra un chatbot capaz de responder preguntas frecuentes.


👩‍🔧 Gestión de Técnicos

Los técnicos acceden como administradores del sistema y se encargan del
mantenimiento del sistema.


👤 Gestión de Usuarios

Incluye login y registro tanto para usuarios generales como para administradores, cada uno con diferentes permisos y vistas personalizadas.



---


## 🧪 Herramientas de Desarrollo Usadas

- Python `3.13.3`
- [Flask](https://flask.palletsprojects.com/) para el backend
- HTML (plantillas en `/templates`)
- CSS y JavaScript
- Jinja2 para plantillas

- Git + GitHub para control de versiones
- Recomendado: Visual Studio Code como entorno de desarrollo

---


## 🚀 Instalación y Configuración

1. **Clona el repositorio**:

```
git clone https://github.com/fabiandres13/EcoSmart-Shishi-Gang.git
cd EcoSmart-Shishi-Gang
```

2. **Crea un entorno virtual (opcional pero recomendado)**:

```
python -m venv venv
source venv/bin/activate  # En Linux/Mac
venv\Scripts\activate     # En Windows
```

3. **Instala las dependencias**:

```
pip install -r requirements.txt
```

4. **Ejecuta la aplicación**:

```
python run.py
```

---


## 👤 Tipos de Usuario y Funcionalidades

| Tipo de Usuario | Funcionalidades |
|-----------------|-----------------|
| **Agricultores** | Monitoreo de cultivos, alertas, visualización simplificada |
| **Agrónomos** | Análisis detallado, consultas IA, evaluación de estrategias |
| **Técnicos (ADMIN)** | Configuración del sistema, simulación, mantenimiento |

---


## 🧑‍💻 Contribuciones

¿Tienes ideas o sugerencias? ¡Estás invitado a contribuir! Haz un fork del repositorio, trabaja en tu rama y haz un pull request.

---

## 📝 Licencia
Proyecto académico desarrollado por estudiantes de Ingeniería Civil en Computación - Universidad de Talca

