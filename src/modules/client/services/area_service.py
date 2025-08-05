from typing import List, Optional, Dict, Any

from src.modules.client.repositories import AreaRepository
from src.infrastructure.database.models import Area, EstadoEnum



class AreaService:
    def __init__(self, area_repository: AreaRepository):
        self.area_repository = area_repository


    async def get_all_areas(self, include_inactive: bool = True) -> List[Area]:
        """Obtiene todas las áreas con validaciones de negocio"""
        return await self.area_repository.get_all(include_inactive=include_inactive)


    async def get_area_by_id(self, area_id: int) -> Optional[Area]:
        """Obtiene un área específica por ID"""
        if area_id <= 0:
            raise ValueError("El ID del área debe ser mayor a 0")

        return await self.area_repository.get_by_id(area_id)


    async def search_areas(self, search_term: str) -> List[Area]:
        """Busca áreas con validación del término de búsqueda"""
        if not search_term or len(search_term.strip()) < 2:
            return await self.get_all_areas()

        return await self.area_repository.search(search_term.strip())


    async def create_area(self, area_data: Dict[str, Any]) -> Area:
        """Crea una nueva área con validaciones de negocio"""
        # Validaciones básicas
        await self._validate_area_data(area_data)

        # Verificar que no existe un área con el mismo nombre
        if await self.area_repository.exists_by_name(area_data["nombre"]):
            raise ValueError(f"Ya existe un área con el nombre '{area_data['nombre']}'")

        # Limpiar y procesar datos
        processed_data = await self._process_area_data(area_data)

        # Crear área
        area = await self.area_repository.create(processed_data)
        await self.area_repository.commit()
        await self.area_repository.db.refresh(area)

        return area


    async def update_area(self, area_id: int, area_data: Dict[str, Any]) -> Area:
        """Actualiza un área existente con validaciones"""
        if area_id <= 0:
            raise ValueError("El ID del área debe ser mayor a 0")

        # Verificar que el área existe
        existing_area = await self.area_repository.get_by_id(area_id)
        if not existing_area:
            raise ValueError(f"No se encontró el área con ID {area_id}")

        # Validaciones de datos
        await self._validate_area_data(area_data, is_update=True)

        # Verificar nombre duplicado (excluyendo el área actual)
        if "nombre" in area_data:
            if await self.area_repository.exists_by_name(area_data["nombre"], exclude_id=area_id):
                raise ValueError(f"Ya existe otra área con el nombre '{area_data['nombre']}'")

        # Procesar datos
        processed_data = await self._process_area_data(area_data)

        # Actualizar
        updated_area = await self.area_repository.update(area_id, processed_data)
        await self.area_repository.commit()
        await self.area_repository.db.refresh(updated_area)

        return updated_area


    async def delete_area(self, area_id: int) -> bool:
        """Elimina un área con validaciones de negocio"""
        if area_id <= 0:
            raise ValueError("El ID del área debe ser mayor a 0")

        # Verificar que existe
        area = await self.area_repository.get_by_id(area_id)
        if not area:
            raise ValueError(f"No se encontró el área con ID {area_id}")

        # Verificar si tiene conversaciones o clientes activos
        area_with_relations = await self.area_repository.get_with_relationships(area_id)
        if area_with_relations and (area_with_relations.conversaciones or area_with_relations.clientes):
            raise ValueError("No se puede eliminar un área que tiene conversaciones o clientes asignados. Desactívala en su lugar.")

        # Eliminar
        success = await self.area_repository.delete(area_id)
        if success:
            await self.area_repository.commit()

        return success


    async def toggle_area_status(self, area_id: int) -> Area:
        """Cambia el estado de un área (activa ↔ inactiva)"""
        if area_id <= 0:
            raise ValueError("El ID del área debe ser mayor a 0")

        area = await self.area_repository.get_by_id(area_id)
        if not area:
            raise ValueError(f"No se encontró el área con ID {area_id}")

        updated_area = await self.area_repository.toggle_status(area_id)
        await self.area_repository.commit()

        return updated_area


    async def get_areas_for_derivation(self) -> List[Area]:
        """Obtiene áreas disponibles para derivación automática"""
        areas = await self.area_repository.get_areas_for_derivation()

        # Filtrar áreas que tengan instrucciones válidas
        valid_areas = []
        for area in areas:
            if self._is_area_ready_for_derivation(area):
                valid_areas.append(area)

        return valid_areas


    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas para el dashboard"""
        stats = await self.area_repository.get_stats()

        # Agregar análisis adicional
        areas = await self.area_repository.get_all()

        # Estadísticas adicionales
        areas_with_specialist = sum(1 for area in areas if area.especialista_asignado)
        areas_without_specialist = len(areas) - areas_with_specialist

        fastest_response = min((area.tiempo_respuesta for area in areas if area.tiempo_respuesta), default=0)
        slowest_response = max((area.tiempo_respuesta for area in areas if area.tiempo_respuesta), default=0)

        return {
            **stats,
            "areas_with_specialist": areas_with_specialist,
            "areas_without_specialist": areas_without_specialist,
            "fastest_response_time": fastest_response,
            "slowest_response_time": slowest_response,
            "total_specialists": len(set(area.especialista_asignado for area in areas if area.especialista_asignado))
        }


    async def find_best_area_for_query(self, query: str) -> Optional[Area]:
        """
        Encuentra la mejor área para una consulta específica
        (Lógica básica - en producción usarías IA más sofisticada)
        """
        active_areas = await self.area_repository.get_active_areas()

        query_lower = query.lower()
        best_match = None
        best_score = 0

        for area in active_areas:
            score = self._calculate_match_score(query_lower, area)
            if score > best_score:
                best_score = score
                best_match = area

        # Solo devolver si hay un match razonable
        return best_match if best_score > 0.3 else None


    def _calculate_match_score(self, query: str, area: Area) -> float:
        """Calcula un score de coincidencia entre query y área"""
        score = 0.0

        # Palabras clave por área (esto sería más sofisticado en producción)
        keywords_map = {
            "contable": ["renta", "declaracion", "contabilidad", "estados", "financieros", "libros"],
            "legal": ["empresa", "constitucion", "contrato", "legal", "juridico", "derecho"],
            "financiera": ["inversion", "financiero", "flujo", "caja", "credito", "prestamo"],
            "tributaria": ["impuesto", "fiscal", "tributario", "iva", "retencion", "planeacion"]
        }

        area_name_lower = area.nombre.lower()
        instructions_lower = area.instrucciones.lower()

        # Buscar coincidencias en instrucciones
        for word in query.split():
            if word in instructions_lower:
                score += 0.2

        # Buscar palabras clave específicas
        for area_type, keywords in keywords_map.items():
            if area_type in area_name_lower:
                for keyword in keywords:
                    if keyword in query:
                        score += 0.3

        return min(score, 1.0)  # Normalizar a máximo 1.0


    async def _validate_area_data(self, area_data: Dict[str, Any], is_update: bool = False) -> None:
        """Valida los datos de entrada para crear/actualizar área"""
        required_fields = ["nombre", "instrucciones"] if not is_update else []

        # Validar campos requeridos
        for field in required_fields:
            if field not in area_data or not area_data[field]:
                raise ValueError(f"El campo '{field}' es obligatorio")

        # Validar nombre
        if "nombre" in area_data:
            nombre = area_data["nombre"].strip()
            if len(nombre) < 3:
                raise ValueError("El nombre del área debe tener al menos 3 caracteres")
            if len(nombre) > 255:
                raise ValueError("El nombre del área no puede exceder 255 caracteres")

        # Validar instrucciones
        if "instrucciones" in area_data:
            instrucciones = area_data["instrucciones"].strip()
            if len(instrucciones) < 10:
                raise ValueError("Las instrucciones deben tener al menos 10 caracteres")

        # Validar tiempo de respuesta
        if "tiempo_respuesta" in area_data and area_data["tiempo_respuesta"] is not None:
            tiempo = area_data["tiempo_respuesta"]
            if not isinstance(tiempo, int) or tiempo < 1 or tiempo > 120:
                raise ValueError("El tiempo de respuesta debe ser entre 1 y 120 minutos")

        # Validar estado
        if "estado" in area_data:
            if area_data["estado"] not in [EstadoEnum.ACTIVE.value, EstadoEnum.INACTIVE.value]:
                raise ValueError("El estado debe ser 'active' o 'inactive'")


    async def _process_area_data(self, area_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa y limpia los datos antes de guardar"""
        processed = area_data.copy()

        # Limpiar strings
        string_fields = ["nombre", "descripcion", "instrucciones", "especialista_asignado"]
        for field in string_fields:
            if field in processed and isinstance(processed[field], str):
                processed[field] = processed[field].strip()
                # Convertir strings vacíos a None
                if not processed[field]:
                    processed[field] = None

        # Convertir estado a enum si es string
        if "estado" in processed and isinstance(processed["estado"], str):
            processed["estado"] = EstadoEnum.ACTIVE if processed["estado"] == "active" else EstadoEnum.INACTIVE

        return processed


    def _is_area_ready_for_derivation(self, area: Area) -> bool:
        """Verifica si un área está lista para recibir derivaciones"""
        return (
            area.estado == EstadoEnum.ACTIVE and
            area.instrucciones and
            len(area.instrucciones.strip()) >= 10 and
            area.especialista_asignado is not None
        )
