from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.repositories import MensajeRepository
from src.modules.client.services import MensajeService



async def provide_mensaje_repository(db: AsyncSession) -> MensajeRepository:
    return MensajeRepository(db)


async def provide_mensaje_service(mensaje_repository: MensajeRepository) -> MensajeService:
    return MensajeService(mensaje_repository)
