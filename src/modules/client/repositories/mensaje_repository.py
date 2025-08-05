from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.infrastructure.database.models import Mensaje



class MensajeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create(self, message_data: dict) -> Mensaje:
        """Crea un nuevo mensaje"""
        mensaje = Mensaje(**message_data)
        self.db.add(mensaje)
        await self.db.flush()
        await self.db.refresh(mensaje)
        return mensaje


    async def get_by_conversation(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Mensaje]:
        """Obtiene mensajes de una conversación ordenados por timestamp"""

        query = select(Mensaje).where(
            Mensaje.id_conversacion == conversation_id
        ).order_by(
            Mensaje.timestamp.asc()
        ).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()


    async def commit(self):
        """Confirma los cambios"""
        await self.db.commit()


    async def rollback(self):
        """Revierte los cambios"""
        await self.db.rollback()