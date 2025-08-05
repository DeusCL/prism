from typing import Optional, List

from src.modules.client.repositories import ConversacionRepository, ClienteRepository
from src.infrastructure.database.models import Conversacion, EstadoConversacionEnum
from src.shared.utils.timing import now



class ConversacionService:
    def __init__(
        self,
        conversacion_repository: ConversacionRepository,
        cliente_repository: ClienteRepository
    ):
        self.conversacion_repository = conversacion_repository
        self.cliente_repository = cliente_repository


    async def get_or_create_active_conversation(self, client_id: int) -> Conversacion:
        """Obtiene o crea una conversación activa para un cliente"""

        # Buscar conversación activa existente
        active_conversation = await self.conversacion_repository.get_active_by_client(client_id)

        if active_conversation:
            return active_conversation

        # Crear nueva conversación
        conversation_data = {
            "id_cliente": client_id,
            "estado": EstadoConversacionEnum.IA_RESPONDIENDO,
            "id_area_derivada": None
        }

        conversation = await self.conversacion_repository.create(conversation_data)
        await self.conversacion_repository.commit()

        return conversation


    async def transfer_to_human(
        self,
        conversation_id: int,
        area_id: Optional[int] = None
    ) -> Conversacion:
        """Transfiere una conversación de IA a humano"""

        update_data = {
            "estado": EstadoConversacionEnum.ESPERANDO_HUMANO
        }

        if area_id:
            update_data["id_area_derivada"] = area_id
            update_data["fecha_derivacion"] = now

        conversation = await self.conversacion_repository.update(conversation_id, update_data)
        await self.conversacion_repository.commit()

        return conversation


    async def get_all_active_conversations(self) -> List[Conversacion]:
        """Obtiene todas las conversaciones activas para el panel admin"""

        return await self.conversacion_repository.get_all_active()

