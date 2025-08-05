from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.infrastructure.database.models import Conversacion, EstadoConversacionEnum



class ConversacionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create(self, conversation_data: dict) -> Conversacion:
        """Crea una nueva conversación"""
        conversacion = Conversacion(**conversation_data)
        self.db.add(conversacion)
        await self.db.flush()
        await self.db.refresh(conversacion)
        return conversacion


    async def get_active_by_client(self, client_id: int) -> Optional[Conversacion]:
        """Obtiene conversación activa de un cliente"""

        query = select(Conversacion).where(
            Conversacion.id_cliente == client_id,
            Conversacion.estado.in_([
                EstadoConversacionEnum.IA_RESPONDIENDO,
                EstadoConversacionEnum.ESPERANDO_HUMANO
            ])
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()


    async def get_all_active(self) -> List[Conversacion]:
        """Obtiene todas las conversaciones activas"""

        query = select(Conversacion).where(
            Conversacion.estado.in_([
                EstadoConversacionEnum.IA_RESPONDIENDO,
                EstadoConversacionEnum.ESPERANDO_HUMANO
            ])
        ).order_by(Conversacion.updated_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()


    async def update(self, conversation_id: int, update_data: dict) -> Optional[Conversacion]:
        """Actualiza una conversación"""

        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return None

        for key, value in update_data.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)

        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation


    async def get_by_id(self, conversation_id: int) -> Optional[Conversacion]:
        """Obtiene conversación por ID"""

        query = select(Conversacion).where(Conversacion.id == conversation_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


    async def commit(self):
        await self.db.commit()


    async def rollback(self):
        await self.db.rollback()
