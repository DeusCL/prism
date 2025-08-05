from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.repositories import ConversacionRepository, ClienteRepository
from src.modules.client.services import ConversacionService



async def provide_conversacion_repository(db: AsyncSession) -> ConversacionRepository:
    return ConversacionRepository(db)


async def provide_conversacion_service(
    conversacion_repository: ConversacionRepository,
    cliente_repository: ClienteRepository
) -> ConversacionService:
    return ConversacionService(conversacion_repository, cliente_repository)
