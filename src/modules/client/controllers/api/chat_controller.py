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
        print(f"✅ Conexión establecida: {connection_id}")

        # Enviar mensaje de bienvenida
        await self._send_message(socket, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Conectado a Prism Chat"
        })

        try:
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
        except WebSocketException:
            print(f"🔌 Conexión WebSocket cerrada: {connection_id}")
        except Exception as e:
            print(f"❌ Error en WebSocket {connection_id}: {str(e)}")
        finally:
            # Limpiar conexión
            await self._cleanup_connection(connection_id)


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
        print(f"📨 Mensaje recibido de {connection_id}: {message_type}")

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

            elif message_type == "get_conversation_history":
                await self._handle_get_history(
                    socket, message, mensaje_service
                )

            elif message_type == "get_active_conversations":
                await self._handle_get_active_conversations(
                    socket, conversacion_service, cliente_service
                )

            else:
                await self._send_error(socket, f"Tipo de mensaje desconocido: {message_type}")

        except Exception as e:
            print(f"❌ Error procesando mensaje: {str(e)}")
            await self._send_error(socket, f"Error procesando mensaje: {str(e)}")


    async def _handle_new_client_message(
        self,
        message: Dict[str, Any],
        mensaje_service: MensajeService,
        conversacion_service: ConversacionService,
        cliente_service: ClienteService
    ) -> None:
        """Maneja mensajes nuevos de clientes"""

        client_id = int(message.get("client_id"))
        client_name = message.get("client_name", f"Cliente {client_id}")
        message_text = message.get("message")
        timestamp = datetime.utcnow()

        if not all([client_id, message_text]):
            print("❌ Datos incompletos en mensaje de cliente")
            return

        print(f"💬 Nuevo mensaje de {client_name} (ID: {client_id}): {message_text}")

        try:
            # Crear o obtener cliente
            cliente = await cliente_service.get_or_create_client(client_id, client_name)

            # Crear o obtener conversación activa - ahora retorna tupla (conversacion, conversation_id)
            conversacion, conversation_id = await conversacion_service.get_or_create_active_conversation(client_id)

            # Crear mensaje usando el conversation_id seguro
            mensaje = await mensaje_service.create_message({
                "id_conversacion": conversation_id,
                "contenido": message_text,
                "tipo": "cliente",
                "remitente": client_name,
                "es_derivacion": False
            })

            print(f"💾 Mensaje guardado exitosamente")

            # Broadcast a todas las conexiones usando el conversation_id seguro
            await self._broadcast_message({
                "type": "new_message",
                "conversation_id": conversation_id,
                "client_id": client_id,
                "client_name": client_name,
                "message": {
                    "id": f"temp_{timestamp.timestamp()}",  # ID temporal
                    "content": message_text,
                    "sender": client_name,
                    "timestamp": timestamp.isoformat(),
                    "message_type": "cliente"
                }
            })

        except Exception as e:
            print(f"❌ Error manejando mensaje de cliente: {str(e)}")
            raise


    async def _handle_admin_response(
        self,
        message: Dict[str, Any],
        mensaje_service: MensajeService
    ) -> None:
        """Maneja respuestas del administrador"""

        conversation_id = int(message.get("conversation_id"))
        response_text = message.get("message")
        admin_name = message.get("admin_name", "Administrador")
        timestamp = datetime.utcnow()

        if not all([conversation_id, response_text]):
            print("❌ Datos incompletos en respuesta de admin")
            return

        print(f"👨‍💼 Respuesta de admin para conversación {conversation_id}: {response_text}")

        try:
            # Crear mensaje de respuesta usando directamente el conversation_id
            mensaje = await mensaje_service.create_message({
                "id_conversacion": conversation_id,
                "contenido": response_text,
                "tipo": "humano",
                "remitente": admin_name,
                "es_derivacion": False
            })

            print(f"💾 Respuesta guardada exitosamente")

            # Broadcast la respuesta
            await self._broadcast_message({
                "type": "admin_response",
                "conversation_id": conversation_id,
                "message": {
                    "id": f"temp_{timestamp.timestamp()}",  # ID temporal
                    "content": response_text,
                    "sender": admin_name,
                    "timestamp": timestamp.isoformat(),
                    "message_type": "humano"
                }
            })

        except Exception as e:
            print(f"❌ Error manejando respuesta de admin: {str(e)}")
            raise


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
            print(f"🔗 {connection_id} se unió a conversación {conversation_id}")


    async def _handle_get_history(
        self,
        socket: WebSocket,
        message: Dict[str, Any],
        mensaje_service: MensajeService
    ) -> None:
        """Envía el historial de una conversación"""

        conversation_id = int(message.get("conversation_id"))
        limit = message.get("limit", 50)

        if not conversation_id:
            return

        print(f"📜 Solicitando historial de conversación {conversation_id}")

        try:
            # Obtener mensajes
            mensajes = await mensaje_service.get_conversation_messages(
                conversation_id, limit=limit
            )

            # Formatear mensajes
            formatted_messages = []
            for msg in mensajes:
                formatted_messages.append({
                    "id": getattr(msg, 'id', f"msg_{msg.timestamp.timestamp()}" if msg.timestamp else "msg_unknown"),
                    "content": msg.contenido,
                    "sender": msg.remitente,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else datetime.utcnow().isoformat(),
                    "message_type": msg.tipo.value,
                    "is_derivation": msg.es_derivacion
                })

            await self._send_message(socket, {
                "type": "conversation_history",
                "conversation_id": conversation_id,
                "messages": formatted_messages
            })

        except Exception as e:
            print(f"❌ Error obteniendo historial: {str(e)}")
            raise


    async def _handle_get_active_conversations(
        self,
        socket: WebSocket,
        conversacion_service: ConversacionService,
        cliente_service: ClienteService
    ) -> None:
        """Envía la lista de conversaciones activas al panel admin"""

        print("📋 Solicitando conversaciones activas")

        try:
            conversaciones = await conversacion_service.get_all_active_conversations()

            formatted_conversations = []
            for conv in conversaciones:
                # Obtener información del cliente de forma segura
                client_id = getattr(conv, 'id_cliente', None)
                if client_id is None:
                    continue

                cliente = await cliente_service.get_client_by_id(client_id)
                client_name = cliente.nombre if cliente else f"Cliente {client_id}"

                # Obtener ID de conversación de forma segura
                conversation_id = getattr(conv, 'id', None)
                if conversation_id is None:
                    continue

                formatted_conversations.append({
                    "conversation_id": conversation_id,
                    "client_id": client_id,
                    "client_name": client_name,
                    "status": conv.estado.value if hasattr(conv, 'estado') else 'ia_respondiendo',
                    "created_at": conv.created_at.isoformat() if hasattr(conv, 'created_at') and conv.created_at else datetime.utcnow().isoformat(),
                    "updated_at": conv.updated_at.isoformat() if hasattr(conv, 'updated_at') and conv.updated_at else datetime.utcnow().isoformat()
                })

            await self._send_message(socket, {
                "type": "active_conversations",
                "conversations": formatted_conversations
            })

        except Exception as e:
            print(f"❌ Error obteniendo conversaciones activas: {str(e)}")
            await self._send_error(socket, f"Error obteniendo conversaciones: {str(e)}")


    async def _broadcast_message(self, message: Dict[str, Any]) -> None:
        """Envía un mensaje a todas las conexiones activas"""

        disconnected = []
        sent_count = 0

        for connection_id, socket in self.connections.items():
            try:
                await self._send_message(socket, message)
                sent_count += 1
            except:
                disconnected.append(connection_id)

        print(f"📡 Mensaje enviado a {sent_count} conexiones")

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
            "timestamp": datetime.utcnow().isoformat()
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

        print(f"🧹 Conexión limpiada: {connection_id}")


    # Método de utilidad para debugging/monitoreo
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
