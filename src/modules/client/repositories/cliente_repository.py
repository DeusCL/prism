from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.infrastructure.database.models import Cliente



class ClienteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_by_id(self, client_id: int) -> Optional[Cliente]:
        result = await self.db.execute(
            select(Cliente).where(Cliente.id == client_id)
        )
        return result.scalar_one_or_none()


    async def create(self, data: dict) -> Cliente:
        client = Cliente(**data)
        self.db.add(client)
        return client


    async def update(self, client_id: int, data: dict) -> Optional[Cliente]:
        client = await self.get_by_id(client_id)
        if not client:
            return None

        for key, value in data.items():
            setattr(client, key, value)

        self.db.add(client)
        return client


    async def commit(self):
        await self.db.commit()
