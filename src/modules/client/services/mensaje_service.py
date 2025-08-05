from typing import List, Dict, Any

from src.modules.client.repositories import MensajeRepository
from src.infrastructure.database.models import Mensaje, TipoMensajeEnum
from src.shared.utils.timing import now



class MensajeService:
    def __init__(self, mensaje_repository: MensajeRepository):
        self.mensaje_repository = mensaje_repository


    async def create_message(self, message_data: Dict[str, Any]) -> Mensaje:
        """Crea un nuevo mensaje de forma segura"""

        # Validaciones básicas
        if not message_data.get("contenido", "").strip():
            raise ValueError("El contenido del mensaje no puede estar vacío")

        if not message_data.get("id_conversacion"):
            raise ValueError("ID de conversación es requerido")

        # Procesar datos con timestamp explícito
        processed_data = {
            "id_conversacion": message_data["id_conversacion"],
            "contenido": message_data["contenido"].strip(),
            "tipo": TipoMensajeEnum(message_data.get("tipo", "cliente")),
            "remitente": message_data.get("remitente", "Usuario"),
            "es_derivacion": message_data.get("es_derivacion", False),
            "timestamp": now()  # Siempre establecer explícitamente
        }

        # Crear mensaje sin acceder a propiedades que causen refresh
        mensaje = await self.mensaje_repository.create(processed_data)
        await self.mensaje_repository.commit()

        return mensaje


    async def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Mensaje]:
        """Obtiene mensajes de una conversación"""
        return await self.mensaje_repository.get_by_conversation(
            conversation_id, limit=limit, offset=offset
        )


    async def create_derivation_message(
        self,
        conversation_id: int,
        area_name: str,
        specialist_name: str
    ) -> Mensaje:
        """Crea un mensaje de derivación automático"""

        content = f"🤖➡️👨‍💼 La conversación ha sido transferida al área de {area_name}"
        if specialist_name:
            content += f"\nEspecialista: {specialist_name}"

        message_data = {
            "id_conversacion": conversation_id,
            "contenido": content,
            "tipo": "sistema",
            "remitente": "Sistema Prism",
            "es_derivacion": True
        }

        return await self.create_message(message_data)

