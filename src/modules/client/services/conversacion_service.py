from typing import Optional, List, Tuple

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


    async def get_or_create_active_conversation(self, client_id: int) -> Tuple[Conversacion, int]:
        """
        Obtiene o crea una conversación activa para un cliente
        Retorna tupla (conversacion, conversation_id) para evitar problemas de greenlet
        """

        # Buscar conversación activa existente
        active_conversation = await self.conversacion_repository.get_active_by_client(client_id)

        if active_conversation:
            # Si existe, obtener el ID de forma segura
            conversation_id = getattr(active_conversation, 'id', None)
            if conversation_id is None:
                # Si no podemos obtener el ID, crear una nueva
                return await self._create_new_conversation(client_id)
            return active_conversation, conversation_id

        # Crear nueva conversación
        return await self._create_new_conversation(client_id)


    async def _create_new_conversation(self, client_id: int) -> Tuple[Conversacion, int]:
        """Crea una nueva conversación y retorna tanto el objeto como el ID"""

        conversation_data = {
            "id_cliente": client_id,
            "estado": EstadoConversacionEnum.IA_RESPONDIENDO,
            "id_area_derivada": None,
            "created_at": now(),
            "updated_at": now()
        }

        conversation, conversation_id = await self.conversacion_repository.create_and_get_id(conversation_data)
        await self.conversacion_repository.commit()

        return conversation, conversation_id


    async def transfer_to_human(
        self,
        conversation_id: int,
        area_id: Optional[int] = None
    ) -> Conversacion:
        """Transfiere una conversación de IA a humano"""

        update_data = {
            "estado": EstadoConversacionEnum.ESPERANDO_HUMANO,
            "updated_at": now()
        }

        if area_id:
            update_data["id_area_derivada"] = area_id
            update_data["fecha_derivacion"] = now()

        conversation = await self.conversacion_repository.update(conversation_id, update_data)
        await self.conversacion_repository.commit()

        return conversation


    async def get_all_active_conversations(self) -> List[Conversacion]:
        """Obtiene todas las conversaciones activas para el panel admin"""

        return await self.conversacion_repository.get_all_active()

