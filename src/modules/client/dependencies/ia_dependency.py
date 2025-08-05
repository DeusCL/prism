from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.repositories import ConfiguracionIARepository
from src.modules.client.services import ConfiguracionIAService, AIService
from src.modules.client.repositories import AreaRepository



async def provide_configuracion_repository(db: AsyncSession) -> ConfiguracionIARepository:
    return ConfiguracionIARepository(db)


async def provide_configuracion_service(
    configuracion_repository: ConfiguracionIARepository
) -> ConfiguracionIAService:
    return ConfiguracionIAService(configuracion_repository)


async def provide_ai_service(area_repository: AreaRepository) -> AIService:
    return AIService(area_repository)
