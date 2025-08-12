// Espera a que el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar componentes de Materialize
    const sidenavElems = document.querySelectorAll('.sidenav');
    M.Sidenav.init(sidenavElems);

    const textareaElems = document.querySelectorAll('.materialize-textarea');
    textareaElems.forEach(el => M.textareaAutoResize(el));

    // Cargar plantillas y luego el historial del usuario
    loadSampleQuestions();
    initializeFullHistory();
});

// VARIABLES GLOBALES
const sendButton = document.getElementById('sendButton');
const userInput = document.getElementById('userInput');
const chatHistory = document.getElementById('chatHistory');
const conversationsContainer = document.getElementById('conversations');
const newConversationBtn = document.getElementById('newConversationBtn');
const sampleQuestionsContainer = document.getElementById('sampleQuestions');
const deleteCurrentChatBtn = document.getElementById('deleteCurrentChatBtn'); // Nuevo: Obtener el botón de eliminar chat

let conversations = {};
let currentConversationId = null;
let userTipo = null;

// Obtener tipo de usuario
async function fetchUserTipo() {
    try {
        const response = await fetch('/api/usuario_tipo');
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        const data = await response.json();
        return data.tipo_usuario ? data.tipo_usuario.toLowerCase() : null;
    } catch (error) {
        console.error('Error al obtener tipo de usuario:', error);
        return null;
    }
}

// Plantillas por tipo de usuario
const plantillasPorTipo = {
    agricultor: [
        "¿Cuál es la mejor época para sembrar [nombre del cultivo] en [ubicación]?",
        "¿Qué tipo de suelo es ideal para [nombre del cultivo]?",
        "¿Cada cuánto debería regar mis plantas?",
        "Dime la humedad de mi cultivo AGRO-XXX-Y",
        "¿Qué pH tiene el suelo de mi cultivo AGRO-XXX-Y?",
        "Dame la temperatura de mi cultivo AGRO-XXX-Y",
        "¿Cuáles son los niveles de nutrientes de mi cultivo AGRO-XXX-Y?",
        "¿Qué datos de ubicación tiene mi cultivo AGRO-XXX-Y?"
    ],
    agronomo: [
        "¿Cuáles son los principales problemas de un cultivo de [nombre]?",
        "¿Cómo afecta la temperatura o humedad al crecimiento?",
        "Dame los datos de mi cultivo AGRO-XXX-Y",
        "Necesito la información de sensores del cultivo AGRO-XXX-Y",
        "¿Cuál es la latitud y longitud del cultivo AGRO-XXX-Y?"
    ],
    admin: [
        "¿Qué datos tengo sobre los cultivos?",
        "¿Cuáles son los sensores disponibles?"
    ]
};

// Muestra preguntas de ejemplo
async function loadSampleQuestions() {
    userTipo = await fetchUserTipo() || 'agricultor';
    sampleQuestionsContainer.innerHTML = '';

    const preguntas = plantillasPorTipo[userTipo] || [];
    if (!preguntas.length) {
        sampleQuestionsContainer.innerHTML = '<p>No hay plantillas disponibles para tu tipo de usuario.</p>';
        return;
    }

    preguntas.forEach(pregunta => {
        const p = document.createElement('p');
        p.className = 'sample-question-item';
        p.textContent = pregunta;
        p.title = "Haz clic para usar esta plantilla";
        p.addEventListener('click', () => {
            userInput.value = pregunta;
            userInput.focus();
            M.textareaAutoResize(userInput);
        });
        sampleQuestionsContainer.appendChild(p);
    });
}

// Inicializa historial
async function initializeFullHistory() {
    try {
        const response = await fetch('/chat/historial/todo');
        const data = await response.json();

        if (data.error || !data.conversations || Object.keys(data.conversations).length === 0) {
            await startNewConversation();
        } else {
            conversations = data.conversations;
            const convIds = Object.keys(conversations).sort((a, b) => {
                const fechaA = new Date(getLastMessageFecha(conversations[a]));
                const fechaB = new Date(getLastMessageFecha(conversations[b]));
                return fechaB - fechaA;
            });
            currentConversationId = convIds[0];
            renderConversations();
            renderChat();
        }
    } catch (error) {
        console.error("Error al cargar historial:", error);
        await startNewConversation();
    }
}

// Nueva conversación
async function startNewConversation() {
    try {
        const response = await fetch('/chat/nueva_conversacion', { method: 'POST' });
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        currentConversationId = data.conversacion_id;
        conversations[currentConversationId] = [];
        renderConversations();
        renderChat();
        userInput?.focus();
    } catch (error) {
        console.error("Error al iniciar nueva conversación:", error);
    }
}

// Renderiza lista de conversaciones
function renderConversations() {
    conversationsContainer.innerHTML = '';
    const convIds = Object.keys(conversations).sort((a, b) => {
        const fechaA = new Date(getLastMessageFecha(conversations[a]));
        const fechaB = new Date(getLastMessageFecha(conversations[b]));
        return fechaB - fechaA;
    });

    convIds.forEach(id => {
        const convItem = document.createElement('li');
        convItem.className = 'collection-item conversation-item' + (id === currentConversationId ? ' active' : '');
        const firstMsg = conversations[id][0];
        const displayText = firstMsg?.pregunta?.substring(0, 25) || `Conversación ${id.slice(-4)}`;
        convItem.textContent = displayText + (displayText.length >= 25 ? '...' : '');
        convItem.dataset.id = id;
        convItem.addEventListener('click', () => {
            if (currentConversationId !== id) {
                currentConversationId = id;
                renderConversations();
                renderChat();
                userInput?.focus();
            }
        });
        conversationsContainer.appendChild(convItem);
    });
}

// Renderiza el chat
function renderChat() {
    chatHistory.innerHTML = '';
    const mensajes = conversations[currentConversationId] || [];
    if (!mensajes.length) {
        const welcome = document.createElement('div');
        welcome.className = 'chat-entry chat-bot';
        welcome.textContent = '¡Hola! Soy EcoSmart, tu asistente experto en agricultura. ¿En qué puedo ayudarte hoy?';
        chatHistory.appendChild(welcome);
        scrollToBottom();
        return;
    }

    mensajes.forEach(msg => {
        if (msg.pregunta) appendMessageToDOM('Usuario', msg.pregunta, 'chat-user', msg.fecha);
        if (msg.respuesta) appendMessageToDOM('EcoSmart', msg.respuesta, 'chat-bot', msg.fecha);
    });

    scrollToBottom();
}

function getLastMessageFecha(conversation) {
    if (!conversation || !conversation.length) return '1970-01-01T00:00:00.000Z';
    return conversation[conversation.length - 1].fecha;
}

// Agrega mensaje al DOM
function appendMessageToDOM(sender, text, className, timestamp = new Date().toISOString()) {
    const entry = document.createElement('div');
    entry.className = `chat-entry ${className}`;
    const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    entry.innerHTML = `<strong>${sender} [${time}]:</strong> ${text}`;
    chatHistory.appendChild(entry);
}

// Agrega mensaje y lo almacena
function appendMessage(sender, text, className) {
    const fecha = new Date().toISOString();
    appendMessageToDOM(sender, text, className, fecha);

    if (currentConversationId && conversations[currentConversationId]) {
        if (className === 'chat-user') {
            conversations[currentConversationId].push({ pregunta: text, respuesta: null, fecha });
        } else {
            const last = conversations[currentConversationId].findLast(entry => entry.pregunta && entry.respuesta === null);
            if (last) last.respuesta = text;
            else conversations[currentConversationId].push({ pregunta: null, respuesta: text, fecha });
        }
    }

    renderConversations();
    scrollToBottom();
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Envía mensaje al servidor
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage('Usuario', message, 'chat-user');
    userInput.value = '';

    const typingMsg = document.createElement('div');
    typingMsg.className = 'chat-entry chat-bot typing';
    typingMsg.textContent = 'EcoSmart está pensando...';
    chatHistory.appendChild(typingMsg);
    scrollToBottom();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: message, conversacion_id: currentConversationId }),
        });

        const data = await response.json();
        typingMsg.remove();
        const botResponse = data.respuesta || data.error || 'Ocurrió un error inesperado.';
        appendMessage('EcoSmart', botResponse, 'chat-bot');
    } catch (error) {
        typingMsg.remove();
        console.error('Error al enviar mensaje:', error);
        appendMessage('EcoSmart', 'Error al enviar mensaje. Intenta de nuevo.', 'chat-bot');
    }
}

// Función para eliminar la conversación actual
async function deleteCurrentChatVisually() {
    if (currentConversationId && conversations[currentConversationId]) {
        // Llamar a la API para cambiar el estado de la conversación a 0
        await fetch(`/chat/eliminar/${currentConversationId}`, { method: 'POST' });

        // Eliminar la conversación del objeto 'conversations'
        delete conversations[currentConversationId];

        // Remover visualmente la conversación del historial de la izquierda
        const conversationItem = conversationsContainer.querySelector(`[data-id="${currentConversationId}"]`);
        if (conversationItem) {
            conversationItem.remove();
        }

        // Iniciar una nueva conversación para reemplazar la eliminada
        startNewConversation();
        M.toast({html: 'Chat actual eliminado. Los datos se mantienen en la base de datos.', classes: 'green darken-1'});
    } else {
        M.toast({html: 'No hay chat actual para eliminar.', classes: 'red darken-1'});
    }
}

// Eventos
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
newConversationBtn.addEventListener('click', async () => {
    await startNewConversation();
    userInput?.focus();
});
// Nuevo: Event listener para el botón de eliminar chat
deleteCurrentChatBtn.addEventListener('click', deleteCurrentChatVisually);
