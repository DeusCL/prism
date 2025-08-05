from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.repositories import ClienteRepository
from src.modules.client.services import ClienteService



async def provide_cliente_repository(db: AsyncSession) -> ClienteRepository:
    return ClienteRepository(db)


async def provide_cliente_service(cliente_repository: ClienteRepository) -> ClienteService:
    return ClienteService(cliente_repository)
