// chat-websocket.js - JavaScript para conectar con el backend de chat

class PrismChatClient {
    constructor(connectionId, wsUrl = null) {
        this.connectionId = connectionId;
        this.wsUrl = wsUrl || `ws://localhost:8000/api/chat/ws/${connectionId}`;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;

        // Callbacks
        this.onMessage = null;
        this.onConnect = null;
        this.onDisconnect = null;
        this.onError = null;

        this.connect();
    }

    connect() {
        try {
            console.log(`🔌 Conectando a Prism Chat: ${this.wsUrl}`);

            this.socket = new WebSocket(this.wsUrl);

            this.socket.onopen = (event) => {
                console.log('✅ Conectado a Prism Chat');
                this.isConnected = true;
                this.reconnectAttempts = 0;

                if (this.onConnect) {
                    this.onConnect(event);
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📨 Mensaje recibido:', data);

                    this.handleMessage(data);

                    if (this.onMessage) {
                        this.onMessage(data);
                    }
                } catch (error) {
                    console.error('❌ Error parseando mensaje:', error);
                }
            };

            this.socket.onclose = (event) => {
                console.log('🔌 Conexión cerrada:', event.code, event.reason);
                this.isConnected = false;

                if (this.onDisconnect) {
                    this.onDisconnect(event);
                }

                // Reconectar automáticamente
                this.attemptReconnect();
            };

            this.socket.onerror = (error) => {
                console.error('❌ Error WebSocket:', error);

                if (this.onError) {
                    this.onError(error);
                }
            };

        } catch (error) {
            console.error('❌ Error creando WebSocket:', error);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;

            console.log(`🔄 Reintentando conexión (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.log('❌ Máximo número de reintentos alcanzado');
        }
    }

    send(data) {
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            const message = JSON.stringify(data);
            this.socket.send(message);
            console.log('📤 Mensaje enviado:', data);
            return true;
        } else {
            console.warn('⚠️ WebSocket no conectado, no se puede enviar mensaje');
            return false;
        }
    }

    // Métodos específicos para diferentes tipos de mensajes
    sendClientMessage(clientId, clientName, message) {
        return this.send({
            type: "new_client_message",
            client_id: clientId,
            client_name: clientName,
            message: message,
            timestamp: new Date().toISOString()
        });
    }

    sendAdminResponse(conversationId, message, adminName = "Administrador") {
        return this.send({
            type: "admin_response",
            conversation_id: conversationId,
            message: message,
            admin_name: adminName,
            timestamp: new Date().toISOString()
        });
    }

    joinConversation(conversationId) {
        return this.send({
            type: "join_conversation",
            conversation_id: conversationId
        });
    }

    sendTypingIndicator(conversationId, isTyping, senderName) {
        return this.send({
            type: "typing_indicator",
            conversation_id: conversationId,
            is_typing: isTyping,
            sender_name: senderName
        });
    }

    getConversationHistory(conversationId, limit = 50) {
        return this.send({
            type: "get_conversation_history",
            conversation_id: conversationId,
            limit: limit
        });
    }

    handleMessage(data) {
        const messageType = data.type;

        switch (messageType) {
            case 'connection_established':
                this.handleConnectionEstablished(data);
                break;

            case 'new_message':
                this.handleNewMessage(data);
                break;

            case 'admin_response':
                this.handleAdminResponse(data);
                break;

            case 'typing_indicator':
                this.handleTypingIndicator(data);
                break;

            case 'conversation_history':
                this.handleConversationHistory(data);
                break;

            case 'error':
                this.handleError(data);
                break;

            default:
                console.log('🤷 Tipo de mensaje desconocido:', messageType);
        }
    }

    handleConnectionEstablished(data) {
        console.log('🎉 Conexión establecida:', data.message);
        this.updateConnectionStatus(true);
    }

    handleNewMessage(data) {
        console.log('💬 Nuevo mensaje:', data);
        this.displayMessage(data.message, 'received');
        this.updateChatList(data.client_id, data.client_name, data.message.content);
    }

    handleAdminResponse(data) {
        console.log('👨‍💼 Respuesta admin:', data);
        this.displayMessage(data.message, 'sent');
    }

    handleTypingIndicator(data) {
        console.log('⌨️ Indicador de escritura:', data);
        this.showTypingIndicator(data.conversation_id, data.is_typing, data.sender);
    }

    handleConversationHistory(data) {
        console.log('📜 Historial recibido:', data);
        this.loadConversationHistory(data.messages);
    }

    handleError(data) {
        console.error('❌ Error del servidor:', data.message);
        this.showErrorMessage(data.message);
    }

    // Métodos para actualizar la UI (deben ser sobrescritos o conectados)
    displayMessage(message, type) {
        // Implementar en la página específica
        console.log('📝 Mostrar mensaje:', message, type);
    }

    updateChatList(clientId, clientName, lastMessage) {
        // Implementar en la página específica
        console.log('📋 Actualizar lista de chats:', clientId, clientName, lastMessage);
    }

    updateConnectionStatus(isConnected) {
        // Implementar en la página específica
        console.log('🔗 Estado de conexión:', isConnected);
    }

    showTypingIndicator(conversationId, isTyping, sender) {
        // Implementar en la página específica
        console.log('⌨️ Mostrar indicador:', conversationId, isTyping, sender);
    }

    loadConversationHistory(messages) {
        // Implementar en la página específica
        console.log('📜 Cargar historial:', messages);
    }

    showErrorMessage(errorMessage) {
        // Implementar en la página específica
        console.error('💥 Mostrar error:', errorMessage);
    }

    disconnect() {
        if (this.socket) {
            console.log('🔌 Desconectando WebSocket...');
            this.socket.close();
            this.isConnected = false;
        }
    }

    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            connectionId: this.connectionId,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// Implementación específica para el Panel de Administración
class AdminChatClient extends PrismChatClient {
    constructor() {
        super('admin');
        this.currentConversationId = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Configurar callbacks específicos del admin
        this.onConnect = () => {
            this.updateConnectionIndicator(true);
        };

        this.onDisconnect = () => {
            this.updateConnectionIndicator(false);
        };

        this.onMessage = (data) => {
            // Lógica adicional específica del admin
            if (data.type === 'new_message') {
                this.playNotificationSound();
                this.showDesktopNotification(data);
            }
        };
    }

    displayMessage(message, type) {
        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;

        const timeString = new Date(message.timestamp).toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageElement.innerHTML = `
            <div class="message-bubble">
                ${message.content}
                <div class="message-info">
                    ${message.sender} • ${timeString}
                    ${message.message_type === 'ia' ? '<span class="ai-indicator">IA</span>' : ''}
                </div>
            </div>
        `;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    updateChatList(clientId, clientName, lastMessage) {
        let chatItem = document.querySelector(`[data-client-id="${clientId}"]`);

        if (!chatItem) {
            // Crear nuevo item en la lista
            const chatList = document.querySelector('.chat-list');
            if (chatList) {
                chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                chatItem.dataset.clientId = clientId;
                chatItem.innerHTML = `
                    <h4>${clientName} <span class="chat-status status-ai">IA</span></h4>
                    <p>${lastMessage.substring(0, 50)}...</p>
                `;
                chatItem.addEventListener('click', () => this.switchToChat(clientId));
                chatList.appendChild(chatItem);
            }
        } else {
            // Actualizar mensaje existente
            const messagePreview = chatItem.querySelector('p');
            if (messagePreview) {
                messagePreview.textContent = lastMessage.substring(0, 50) + '...';
            }
        }

        // Mover al top de la lista
        if (chatItem && chatItem.parentNode) {
            chatItem.parentNode.insertBefore(chatItem, chatItem.parentNode.firstChild);
        }
    }

    updateConnectionIndicator(isConnected) {
        const indicator = document.getElementById('connectionStatus');
        if (indicator) {
            indicator.className = isConnected ? 'connection-status' : 'connection-status disconnected';
        }
    }

    switchToChat(clientId) {
        // Actualizar UI para mostrar chat específico
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });

        const selectedChat = document.querySelector(`[data-client-id="${clientId}"]`);
        if (selectedChat) {
            selectedChat.classList.add('active');
        }

        // Simular ID de conversación (en producción obtendrías esto del backend)
        this.currentConversationId = parseInt(clientId);

        // Cargar historial
        this.getConversationHistory(this.currentConversationId);

        // Unirse a la conversación
        this.joinConversation(this.currentConversationId);
    }

    sendAdminMessage() {
        const input = document.getElementById('messageInput');
        if (!input || !this.currentConversationId) return;

        const message = input.value.trim();
        if (!message) return;

        // Enviar respuesta usando el método base
        this.send({
            type: "admin_response",
            conversation_id: this.currentConversationId,
            message: message,
            admin_name: 'Administrador',
            timestamp: new Date().toISOString()
        });

        // Limpiar input
        input.value = '';
    }

    playNotificationSound() {
        // Reproducir sonido de notificación (opcional)
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAQABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+D0xW0gBjiR1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+D0xW0gBjiR1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+D0xW0gBjiR1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+D0xW0gBjiR1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+D0xW0gBjiR1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn+D0xW0gBjiR1/LNeSsFJHfH8N2QQAoUXrTp66hVFApGn==');
            audio.play().catch(() => {}); // Ignorar errores de autoplay
        } catch (e) {
            // Silencioso si no se puede reproducir
        }
    }

    showDesktopNotification(data) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`Nuevo mensaje de ${data.client_name}`, {
                body: data.message.content.substring(0, 100),
                icon: '/favicon.ico'
            });
        }
    }
}

// Implementación específica para el Simulador Móvil
class MobileClientSimulator extends PrismChatClient {
    constructor(clientId, clientName) {
        super(`client_${clientId}`);
        this.clientId = clientId;
        this.clientName = clientName;
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.onConnect = () => {
            this.updateConnectionStatus(true);
        };

        this.onDisconnect = () => {
            this.updateConnectionStatus(false);
        };
    }

    displayMessage(message, type) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const timeString = new Date(message.timestamp).toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const aiBadge = message.message_type === 'ia' ? '<span class="ai-badge">IA</span>' : '';

        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${message.content}
                <div class="message-time">${timeString}${aiBadge}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    updateConnectionStatus(isConnected) {
        const status = document.getElementById('connectionStatus');
        if (status) {
            status.className = isConnected ? 'connection-status' : 'connection-status disconnected';
        }
    }

    sendClientMessage() {
        const input = document.getElementById('messageInput');
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        // Enviar mensaje del cliente usando el método base
        this.send({
            type: "new_client_message",
            client_id: this.clientId,
            client_name: this.clientName,
            message: message,
            timestamp: new Date().toISOString()
        });

        // Mostrar mensaje localmente
        this.displayMessage({
            content: message,
            sender: this.clientName,
            timestamp: new Date().toISOString(),
            message_type: 'cliente'
        }, 'sent');

        // Limpiar input
        input.value = '';
    }
}

// Funciones de utilidad globales
window.PrismChat = {
    // Factory functions
    createAdminClient: () => new AdminChatClient(),
    createMobileClient: (clientId, clientName) => new MobileClientSimulator(clientId, clientName),

    // Solicitar permisos de notificación
    requestNotificationPermission: () => {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    },

    // Verificar soporte WebSocket
    isWebSocketSupported: () => {
        return 'WebSocket' in window;
    }
};

// Auto-inicialización para notificaciones
document.addEventListener('DOMContentLoaded', () => {
    window.PrismChat.requestNotificationPermission();
});