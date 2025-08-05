from typing import Optional

from src.modules.client.repositories import ClienteRepository
from src.infrastructure.database.models import Cliente



class ClienteService:
    def __init__(self, cliente_repository: ClienteRepository):
        self.cliente_repository = cliente_repository


    async def get_or_create_client(self, client_id: int, name: str) -> Cliente:
        """Obtiene o crea un cliente"""

        # Buscar cliente existente
        existing_client = await self.cliente_repository.get_by_id(client_id)

        if existing_client:
            return existing_client

        # Crear nuevo cliente
        client_data = {
            "id": client_id,
            "nombre": name,
            "estado": "nuevo"
        }

        client = await self.cliente_repository.create(client_data)
        await self.cliente_repository.commit()

        return client


    async def update_client_status(self, client_id: int, status: str) -> Optional[Cliente]:
        """Actualiza el estado de un cliente"""

        return await self.cliente_repository.update(client_id, {"estado": status})

