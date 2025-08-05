from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.infrastructure.database.models import Mensaje
from src.shared.utils.timing import now



class MensajeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create(self, message_data: dict) -> Mensaje:
        """Crea un nuevo mensaje y retorna el objeto sin hacer refresh"""

        # Asegurar que tenemos timestamp
        if "timestamp" not in message_data:
            message_data["timestamp"] = now()

        mensaje = Mensaje(**message_data)
        self.db.add(mensaje)

        # Solo hacer flush, NO refresh para evitar greenlet issues
        await self.db.flush()

        # El objeto mensaje ahora tiene todos los datos necesarios
        # No accedemos a mensaje.id para evitar el refresh automático
        return mensaje


    async def create_and_get_id(self, message_data: dict) -> tuple[Mensaje, int]:
        """Crea un mensaje y retorna tanto el objeto como el ID de forma segura"""

        # Asegurar que tenemos timestamp
        if "timestamp" not in message_data:
            message_data["timestamp"] = now()

        mensaje = Mensaje(**message_data)
        self.db.add(mensaje)
        await self.db.flush()

        # Hacer una consulta separada para obtener el ID del último mensaje insertado
        # Esto evita el problema de greenlet
        result = await self.db.execute(
            text("SELECT LAST_INSERT_ID()")  # Para MySQL
            # Para PostgreSQL usarías: text("SELECT lastval()")
            # Para SQLite usarías: text("SELECT last_insert_rowid()")
        )
        message_id = result.scalar()

        return mensaje, message_id


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
        return list(result.scalars().all())


    async def get_by_id(self, message_id: int) -> Mensaje:
        """Obtiene un mensaje por ID"""
        query = select(Mensaje).where(Mensaje.id == message_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


    async def commit(self):
        """Confirma los cambios"""
        await self.db.commit()


    async def rollback(self):
        """Revierte los cambios"""
        await self.db.rollback()

