from typing import List, Optional, Dict, Any

from litestar import Controller, get, post, put, patch, delete
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src.modules.client.dependencies import (
    provide_area_repository,
    provide_area_service
)

from src.modules.client.schemas import (
    AreaUpdateDTO,
    AreaCreateDTO,
    AreaResponseDTO,
    AreaStatsDTO
)

from src.modules.client.services import AreaService



class AreaController(Controller):
    path = "/areas"
    dependencies = {
        "area_repository": Provide(provide_area_repository),
        "area_service": Provide(provide_area_service)
    }
    tags = ["Áreas"]


    @get("/")
    async def get_all_areas(
        self,
        area_service: AreaService,
        include_inactive: bool = True
    ) -> List[AreaResponseDTO]:
        """
        Obtiene todas las áreas

        Parameters:
        - include_inactive: Si incluir áreas inactivas (default: True)
        """
        try:
            areas = await area_service.get_all_areas(include_inactive=include_inactive)
            return [AreaResponseDTO.model_validate(area) for area in areas]
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al obtener áreas: {str(e)}"
            )


    @get("/active")
    async def get_active_areas(self, area_service: AreaService) -> List[AreaResponseDTO]:
        """Obtiene solo las áreas activas (útil para derivaciones)"""
        try:
            areas = await area_service.get_areas_for_derivation()
            return [AreaResponseDTO.model_validate(area) for area in areas]
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al obtener áreas activas: {str(e)}"
            )


    @get("/stats")
    async def get_area_stats(self, area_service: AreaService) -> AreaStatsDTO:
        """Obtiene estadísticas de las áreas para el dashboard"""
        try:
            stats = await area_service.get_dashboard_stats()
            return AreaStatsDTO(**stats)
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al obtener estadísticas: {str(e)}"
            )


    @get("/search")
    async def search_areas(
        self,
        area_service: AreaService,
        q: str
    ) -> List[AreaResponseDTO]:
        """
        Busca áreas por nombre, descripción, instrucciones o especialista

        Parameters:
        - q: Término de búsqueda (mínimo 2 caracteres)
        """
        try:
            if len(q.strip()) < 2:
                raise ValueError("El término de búsqueda debe tener al menos 2 caracteres")
            areas = await area_service.search_areas(q)
            return [AreaResponseDTO.model_validate(area) for area in areas]
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error en búsqueda: {str(e)}"
            )


    @get("/match-query")
    async def find_area_for_query(
        self,
        area_service: AreaService,
        query: str
    ) -> Optional[AreaResponseDTO]:
        """
        Encuentra la mejor área para una consulta específica (para IA)

        Parameters:
        - query: Consulta del cliente (mínimo 5 caracteres)
        """
        try:
            if len(query.strip()) < 5:
                raise ValueError("La consulta debe tener al menos 5 caracteres")
            area = await area_service.find_best_area_for_query(query)
            return AreaResponseDTO.model_validate(area) if area else None
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al encontrar área: {str(e)}"
            )


    @get("/{area_id:int}")
    async def get_area_by_id(
        self,
        area_service: AreaService,
        area_id: int
    ) -> AreaResponseDTO:
        """Obtiene un área específica por ID"""
        try:
            area = await area_service.get_area_by_id(area_id)
            if not area:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Área con ID {area_id} no encontrada"
                )
            return AreaResponseDTO.model_validate(area)
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al obtener área: {str(e)}"
            )


    @post("/", status_code=HTTP_201_CREATED)
    async def create_area(
        self,
        area_service: AreaService,
        data: AreaCreateDTO
    ) -> AreaResponseDTO:
        """Crea una nueva área"""

        area_data = data.model_dump(exclude_unset=True)
        print(area_data)
        area = await area_service.create_area(area_data)
        return AreaResponseDTO.model_validate(area)



    @put("/{area_id:int}")
    async def update_area(
        self,
        area_service: AreaService,
        area_id: int,
        data: AreaUpdateDTO
    ) -> AreaResponseDTO:
        """Actualiza un área existente"""
        area_data = data.model_dump(exclude_unset=True)
        if not area_data:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron datos para actualizar"
            )

        area = await area_service.update_area(area_id, area_data)
        return AreaResponseDTO.model_validate(area)



    @patch("/{area_id:int}/toggle-status")
    async def toggle_area_status(
        self,
        area_service: AreaService,
        area_id: int
    ) -> AreaResponseDTO:
        """Cambia el estado de un área (activa ↔ inactiva)"""
        try:
            area = await area_service.toggle_area_status(area_id)
            return AreaResponseDTO.model_validate(area)
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al cambiar estado: {str(e)}"
            )


    @delete("/{area_id:int}", status_code=HTTP_204_NO_CONTENT)
    async def delete_area(
        self,
        area_service: AreaService,
        area_id: int
    ) -> None:
        """Elimina un área"""
        try:
            success = await area_service.delete_area(area_id)
            if not success:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Área con ID {area_id} no encontrada"
                )
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al eliminar área: {str(e)}"
            )


    # Endpoints adicionales para la demo
    @post("/demo/reset")
    async def reset_demo_data(self, area_service: AreaService) -> Dict[str, str]:
        """Resetea los datos de demostración (útil para presentaciones)"""
        try:
            # Aquí podrías implementar lógica para resetear a datos por defecto
            # Por ahora solo retornamos confirmación
            return {"message": "Datos de demostración reseteados exitosamente"}
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al resetear datos: {str(e)}"
            )


    @get("/export/json")
    async def export_areas_json(self, area_service: AreaService) -> List[Dict[str, Any]]:
        """Exporta todas las áreas en formato JSON (útil para backup/migración)"""
        try:
            areas = await area_service.get_all_areas()
            return [
                {
                    "id": area.id,
                    "nombre": area.nombre,
                    "descripcion": area.descripcion,
                    "instrucciones": area.instrucciones,
                    "estado": area.estado.value,
                    "tiempo_respuesta": area.tiempo_respuesta,
                    "especialista_asignado": area.especialista_asignado
                }
                for area in areas
            ]
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al exportar áreas: {str(e)}"
            )

