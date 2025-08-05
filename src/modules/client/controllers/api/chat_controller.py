from datetime import datetime
from typing import Dict, List, Any, Optional

from litestar import Controller, WebSocket, websocket
from litestar.exceptions import WebSocketException
from litestar.di import Provide

from src.modules.client.dependencies import (
    provide_mensaje_repository, provide_mensaje_service,
    provide_conversacion_repository, provide_conversacion_service,
    provide_cliente_repository, provide_cliente_service
)

from src.modules.client.services import MensajeService, ConversacionService, ClienteService



class ChatWebSocketController(Controller):
    path = "/chat"

    # Diccionario para mantener conexiones activas
    connections: Dict[str, WebSocket] = {}

    # Conexiones por conversación (para broadcast)
    conversation_connections: Dict[int, List[str]] = {}

    dependencies = {
        "mensaje_repository": Provide(provide_mensaje_repository),
        "mensaje_service": Provide(provide_mensaje_service),
        "conversacion_repository": Provide(provide_conversacion_repository),
        "conversacion_service": Provide(provide_conversacion_service),
        "cliente_repository": Provide(provide_cliente_repository),
        "cliente_service": Provide(provide_cliente_service)
    }


    @websocket("/ws/{connection_id:str}")
    async def chat_websocket(
        self,
        socket: WebSocket,
        connection_id: str,
        mensaje_service: MensajeService,
        conversacion_service: ConversacionService,
        cliente_service: ClienteService
    ) -> None:
        """
        WebSocket endpoint para chat en tiempo real

        connection_id puede ser:
        - "admin" para el panel administrativo
        - "client_{client_id}" para simuladores de cliente
        """
        await socket.accept()

        # Registrar conexión
        self.connections[connection_id] = socket


        # Enviar mensaje de bienvenida
        await self._send_message(socket, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Conectado a Prism Chat"
        })

        # Loop principal para recibir mensajes
        async for message in socket.iter_json():
            await self._handle_message(
                connection_id,
                message,
                socket,
                mensaje_service,
                conversacion_service,
                cliente_service
            )




    async def _handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
        socket: WebSocket,
        mensaje_service: MensajeService,
        conversacion_service: ConversacionService,
        cliente_service: ClienteService
    ) -> None:
        """Maneja diferentes tipos de mensajes"""

        message_type = message.get("type")

        try:
            if message_type == "new_client_message":
                await self._handle_new_client_message(
                    message, mensaje_service, conversacion_service, cliente_service
                )

            elif message_type == "admin_response":
                await self._handle_admin_response(
                    message, mensaje_service
                )

            elif message_type == "join_conversation":
                await self._handle_join_conversation(
                    connection_id, message["conversation_id"]
                )

            elif message_type == "typing_indicator":
                await self._handle_typing_indicator(
                    message
                )

            elif message_type == "get_conversation_history":
                await self._handle_get_history(
                    socket, message, mensaje_service
                )

            else:
                await self._send_error(socket, f"Tipo de mensaje desconocido: {message_type}")

        except Exception as e:
            await self._send_error(socket, f"Error procesando mensaje: {str(e)}")


    async def _handle_new_client_message(
        self,
        message: Dict[str, Any],
        mensaje_service: MensajeService,
        conversacion_service: ConversacionService,
        cliente_service: ClienteService
    ) -> None:
        """Maneja mensajes nuevos de clientes"""

        client_id = message.get("client_id")
        client_name = message.get("client_name", f"Cliente {client_id}")
        message_text = message.get("message")

        if not all([client_id, message_text]):
            return

        # Crear o obtener cliente
        cliente = await cliente_service.get_or_create_client(client_id, client_name)

        # Crear o obtener conversación activa
        conversacion = await conversacion_service.get_or_create_active_conversation(client_id)

        # Crear mensaje
        mensaje = await mensaje_service.create_message({
            "id_conversacion": conversacion.id,
            "contenido": message_text,
            "tipo": "cliente",
            "remitente": client_name,
            "es_derivacion": False
        })

        # Broadcast a todas las conexiones (panel admin y cliente)
        await self._broadcast_message({
            "type": "new_message",
            "conversation_id": conversacion.id,
            "client_id": client_id,
            "client_name": client_name,
            "message": {
                "id": mensaje.id,
                "content": message_text,
                "sender": client_name,
                "timestamp": mensaje.timestamp.isoformat(),
                "message_type": "cliente"
            }
        })


    async def _handle_admin_response(
        self,
        message: Dict[str, Any],
        mensaje_service: MensajeService
    ) -> None:
        """Maneja respuestas del administrador"""

        conversation_id = message.get("conversation_id")
        response_text = message.get("message")
        admin_name = message.get("admin_name", "Administrador")

        if not all([conversation_id, response_text]):
            return

        # Crear mensaje de respuesta
        mensaje = await mensaje_service.create_message({
            "id_conversacion": conversation_id,
            "contenido": response_text,
            "tipo": "humano",
            "remitente": admin_name,
            "es_derivacion": False
        })

        # Broadcast la respuesta
        await self._broadcast_message({
            "type": "admin_response",
            "conversation_id": conversation_id,
            "message": {
                "id": mensaje.id,
                "content": response_text,
                "sender": admin_name,
                "timestamp": mensaje.timestamp.isoformat(),
                "message_type": "humano"
            }
        })


    async def _handle_join_conversation(
        self,
        connection_id: str,
        conversation_id: int
    ) -> None:
        """Registra una conexión a una conversación específica"""

        if conversation_id not in self.conversation_connections:
            self.conversation_connections[conversation_id] = []

        if connection_id not in self.conversation_connections[conversation_id]:
            self.conversation_connections[conversation_id].append(connection_id)


    async def _handle_typing_indicator(
        self,
        message: Dict[str, Any]
    ) -> None:
        """Maneja indicadores de escritura"""

        conversation_id = message.get("conversation_id")
        is_typing = message.get("is_typing", False)
        sender_name = message.get("sender_name", "Usuario")

        if conversation_id:
            await self._broadcast_to_conversation(conversation_id, {
                "type": "typing_indicator",
                "conversation_id": conversation_id,
                "is_typing": is_typing,
                "sender": sender_name
            })


    async def _handle_get_history(
        self,
        socket: WebSocket,
        message: Dict[str, Any],
        mensaje_service: MensajeService
    ) -> None:
        """Envía el historial de una conversación"""

        conversation_id = message.get("conversation_id")
        limit = message.get("limit", 50)

        if not conversation_id:
            return

        # Obtener mensajes
        mensajes = await mensaje_service.get_conversation_messages(
            conversation_id, limit=limit
        )

        # Formatear mensajes
        formatted_messages = []
        for msg in mensajes:
            formatted_messages.append({
                "id": msg.id,
                "content": msg.contenido,
                "sender": msg.remitente,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.tipo.value,
                "is_derivation": msg.es_derivacion
            })

        await self._send_message(socket, {
            "type": "conversation_history",
            "conversation_id": conversation_id,
            "messages": formatted_messages
        })


    async def _broadcast_message(self, message: Dict[str, Any]) -> None:
        """Envía un mensaje a todas las conexiones activas"""

        disconnected = []

        for connection_id, socket in self.connections.items():
            try:
                await self._send_message(socket, message)
            except:
                disconnected.append(connection_id)

        # Limpiar conexiones muertas
        for conn_id in disconnected:
            await self._cleanup_connection(conn_id)


    async def _broadcast_to_conversation(
        self,
        conversation_id: int,
        message: Dict[str, Any]
    ) -> None:
        """Envía un mensaje solo a las conexiones de una conversación específica"""

        if conversation_id not in self.conversation_connections:
            return

        disconnected = []

        for connection_id in self.conversation_connections[conversation_id]:
            if connection_id in self.connections:
                try:
                    await self._send_message(
                        self.connections[connection_id],
                        message
                    )
                except:
                    disconnected.append(connection_id)

        # Limpiar conexiones muertas
        for conn_id in disconnected:
            await self._cleanup_connection(conn_id)


    async def _send_message(self, socket: WebSocket, message: Dict[str, Any]) -> None:
        """Envía un mensaje a una conexión específica"""
        await socket.send_json(message)


    async def _send_error(self, socket: WebSocket, error_message: str) -> None:
        """Envía un mensaje de error"""
        await self._send_message(socket, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })


    async def _cleanup_connection(self, connection_id: str) -> None:
        """Limpia una conexión cerrada"""

        # Remover de conexiones principales
        self.connections.pop(connection_id, None)

        # Remover de conversaciones
        for conv_id, connections in self.conversation_connections.items():
            if connection_id in connections:
                connections.remove(connection_id)

        # Limpiar conversaciones vacías
        empty_conversations = [
            conv_id for conv_id, connections in self.conversation_connections.items()
            if not connections
        ]

        for conv_id in empty_conversations:
            del self.conversation_connections[conv_id]


    # Métodos de utilidad para debugging/monitoreo
    async def get_active_connections(self) -> Dict[str, Any]:
        """Obtiene información de conexiones activas"""
        return {
            "total_connections": len(self.connections),
            "connections": list(self.connections.keys()),
            "conversations": {
                conv_id: len(connections)
                for conv_id, connections in self.conversation_connections.items()
            }
        }
