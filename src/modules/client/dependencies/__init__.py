from .area_dependency import provide_area_repository, provide_area_service
from .cliente_dependency import provide_cliente_repository, provide_cliente_service
from .conversacion_dependency import provide_conversacion_repository, provide_conversacion_service
from .mensaje_dependency import provide_mensaje_repository, provide_mensaje_service
from .ia_dependency import provide_ai_service, provide_configuracion_repository, provide_configuracion_service



__all__ = [
    "provide_area_repository", "provide_area_service",
    "provide_cliente_repository", "provide_cliente_service",
    "provide_conversacion_repository", "provide_conversacion_service",
    "provide_mensaje_repository", "provide_mensaje_service",
    "provide_ai_service", "provide_configuracion_repository", "provide_configuracion_service"
]