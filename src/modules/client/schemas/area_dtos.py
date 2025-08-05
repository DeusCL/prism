from datetime import datetime

from typing import Optional
from pydantic import BaseModel, Field



# DTOs (Data Transfer Objects)
class AreaCreateDTO(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del área")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del área")
    instrucciones: str = Field(..., min_length=10, description="Instrucciones para derivación")
    estado: str = Field("active", pattern="^(active|inactive)$", description="Estado del área")
    tiempo_respuesta: Optional[int] = Field(None, ge=1, le=120, description="Tiempo estimado en minutos")
    especialista_asignado: Optional[str] = Field(None, max_length=255, description="Especialista asignado")


class AreaUpdateDTO(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    descripcion: Optional[str] = None
    instrucciones: Optional[str] = Field(None, min_length=10)
    estado: Optional[str] = Field(None, pattern="^(active|inactive)$")
    tiempo_respuesta: Optional[int] = Field(None, ge=1, le=120)
    especialista_asignado: Optional[str] = Field(None, max_length=255)


class AreaResponseDTO(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    instrucciones: str
    estado: str
    tiempo_respuesta: Optional[int]
    especialista_asignado: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AreaStatsDTO(BaseModel):
    total_areas: int
    active_areas: int
    inactive_areas: int
    avg_response_time: float
    areas_with_specialist: int
    areas_without_specialist: int
    fastest_response_time: int
    slowest_response_time: int
    total_specialists: int
