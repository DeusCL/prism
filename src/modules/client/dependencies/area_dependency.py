from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.repositories import AreaRepository
from src.modules.client.services import AreaService



async def provide_area_repository(db: AsyncSession) -> AreaRepository:
    return AreaRepository(db)


async def provide_area_service(area_repository: AreaRepository) -> AreaService:
    return AreaService(area_repository)
