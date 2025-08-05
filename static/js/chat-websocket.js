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

            case 'active_conversations':
                this.handleActiveConversations(data);
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
    }

    handleNewMessage(data) {
        console.log('💬 Nuevo mensaje:', data);
    }

    handleAdminResponse(data) {
        console.log('👨‍💼 Respuesta admin:', data);
    }

    handleActiveConversations(data) {
        console.log('📋 Conversaciones activas:', data);
    }

    handleConversationHistory(data) {
        console.log('📜 Historial recibido:', data);
    }

    handleError(data) {
        console.error('❌ Error del servidor:', data.message);
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
    }

    handleNewMessage(data) {
        super.handleNewMessage(data);
        // Lógica adicional específica del admin se maneja en el HTML
    }

    handleAdminResponse(data) {
        super.handleAdminResponse(data);
        // Lógica adicional específica del admin se maneja en el HTML
    }

    handleActiveConversations(data) {
        super.handleActiveConversations(data);
        // Lógica adicional específica del admin se maneja en el HTML
    }

    handleConversationHistory(data) {
        super.handleConversationHistory(data);
        // Lógica adicional específica del admin se maneja en el HTML
    }
}

// Implementación específica para el Simulador Móvil
class MobileClientSimulator extends PrismChatClient {
    constructor(clientId, clientName) {
        super(`client_${clientId}`);
        this.clientId = clientId;
        this.clientName = clientName;
    }

    handleAdminResponse(data) {
        super.handleAdminResponse(data);
        // Lógica adicional específica del simulador se maneja en el HTML
    }

    sendClientMessage() {
        // Esta función se sobrescribe en el HTML para usar el input actual
        console.log('sendClientMessage debe ser implementado en el HTML');
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