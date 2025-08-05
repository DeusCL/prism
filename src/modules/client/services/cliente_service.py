from typing import Optional

from src.modules.client.repositories import ClienteRepository
from src.infrastructure.database.models import Cliente
from src.shared.utils.timing import now



class ClienteService:
    def __init__(self, cliente_repository: ClienteRepository):
        self.cliente_repository = cliente_repository


    async def get_or_create_client(self, client_id: int, name: str) -> Cliente:
        """Obtiene o crea un cliente"""

        # Buscar cliente existente
        existing_client = await self.cliente_repository.get_by_id(client_id)

        if existing_client:
            # Si el nombre es diferente, actualizarlo
            if existing_client.nombre != name:
                await self.cliente_repository.update(client_id, {"nombre": name})
                await self.cliente_repository.commit()
                # Actualizar el objeto local
                existing_client.nombre = name
            return existing_client

        # Crear nuevo cliente
        client_data = {
            "id": client_id,
            "nombre": name,
            "estado": "nuevo",
            "created_at": now()
        }

        client = await self.cliente_repository.create(client_data)
        await self.cliente_repository.commit()

        return client


    async def get_client_by_id(self, client_id: int) -> Optional[Cliente]:
        """Obtiene un cliente por ID"""
        return await self.cliente_repository.get_by_id(client_id)


    async def update_client_status(self, client_id: int, status: str) -> Optional[Cliente]:
        """Actualiza el estado de un cliente"""
        client = await self.cliente_repository.update(client_id, {"estado": status})
        if client:
            await self.cliente_repository.commit()
        return client

