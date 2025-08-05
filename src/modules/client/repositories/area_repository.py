from typing import List, Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models import Area, EstadoEnum



class AreaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, include_inactive: bool = True) -> List[Area]:
        """Obtiene todas las áreas, opcionalmente filtrando por estado"""
        query = select(Area)

        if not include_inactive:
            query = query.where(Area.estado == EstadoEnum.ACTIVE)

        query = query.order_by(Area.nombre)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, area_id: int) -> Optional[Area]:
        """Obtiene un área por su ID"""
        query = select(Area).where(Area.id == area_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, nombre: str) -> Optional[Area]:
        """Obtiene un área por su nombre (para validar duplicados)"""
        query = select(Area).where(Area.nombre.ilike(nombre))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_areas(self) -> List[Area]:
        """Obtiene solo las áreas activas (para derivaciones)"""
        query = select(Area).where(Area.estado == EstadoEnum.ACTIVE).order_by(Area.nombre)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search(self, search_term: str) -> List[Area]:
        """Busca áreas por nombre, descripción o instrucciones"""
        search_pattern = f"%{search_term}%"
        query = select(Area).where(
            Area.nombre.ilike(search_pattern) |
            Area.descripcion.ilike(search_pattern) |
            Area.instrucciones.ilike(search_pattern) |
            Area.especialista_asignado.ilike(search_pattern)
        ).order_by(Area.nombre)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, area_data: dict) -> Area:
        """Crea una nueva área"""
        area = Area(**area_data)
        self.db.add(area)
        await self.db.flush()  # Para obtener el ID sin hacer commit
        await self.db.refresh(area)
        return area

    async def update(self, area_id: int, area_data: dict) -> Optional[Area]:
        """Actualiza un área existente"""
        # Primero verificamos que existe
        area = await self.get_by_id(area_id)
        if not area:
            return None

        # Actualizamos los campos
        for key, value in area_data.items():
            if hasattr(area, key):
                setattr(area, key, value)

        await self.db.flush()
        await self.db.refresh(area)
        return area

    async def delete(self, area_id: int) -> bool:
        """Elimina un área (soft delete cambiando estado o hard delete)"""
        area = await self.get_by_id(area_id)
        if not area:
            return False

        await self.db.delete(area)
        await self.db.flush()
        return True

    async def toggle_status(self, area_id: int) -> Optional[Area]:
        """Cambia el estado de un área (activa ↔ inactiva)"""
        area = await self.get_by_id(area_id)
        if not area:
            return None

        area.estado = EstadoEnum.INACTIVE if area.estado == EstadoEnum.ACTIVE else EstadoEnum.ACTIVE
        await self.db.flush()
        await self.db.refresh(area)
        return area

    async def get_stats(self) -> dict:
        """Obtiene estadísticas de las áreas para el dashboard"""
        # Contar total de áreas
        total_query = select(func.count(Area.id))
        total_result = await self.db.execute(total_query)
        total_areas = total_result.scalar()

        # Contar áreas activas
        active_query = select(func.count(Area.id)).where(Area.estado == EstadoEnum.ACTIVE)
        active_result = await self.db.execute(active_query)
        active_areas = active_result.scalar()

        # Tiempo promedio de respuesta
        avg_time_query = select(func.avg(Area.tiempo_respuesta)).where(
            Area.tiempo_respuesta.is_not(None),
            Area.estado == EstadoEnum.ACTIVE
        )
        avg_time_result = await self.db.execute(avg_time_query)
        avg_response_time = avg_time_result.scalar() or 0

        return {
            "total_areas": total_areas,
            "active_areas": active_areas,
            "inactive_areas": total_areas - active_areas,
            "avg_response_time": round(float(avg_response_time), 1)
        }

    async def get_with_relationships(self, area_id: int) -> Optional[Area]:
        """Obtiene un área con sus relaciones cargadas (conversaciones, clientes)"""
        query = select(Area).options(
            selectinload(Area.conversaciones),
            selectinload(Area.clientes)
        ).where(Area.id == area_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_name(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si existe un área con el nombre dado (para validaciones)"""
        query = select(Area.id).where(Area.nombre.ilike(nombre))

        if exclude_id:
            query = query.where(Area.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_areas_for_derivation(self) -> List[Area]:
        """Obtiene áreas disponibles para derivación (activas con especialista)"""
        query = select(Area).where(
            Area.estado == EstadoEnum.ACTIVE,
            Area.especialista_asignado.is_not(None)
        ).order_by(Area.tiempo_respuesta.asc())  # Priorizamos por tiempo de respuesta

        result = await self.db.execute(query)
        return result.scalars().all()

    async def commit(self):
        """Confirma los cambios en la base de datos"""
        await self.db.commit()

    async def rollback(self):
        """Revierte los cambios pendientes"""
        await self.db.rollback()
