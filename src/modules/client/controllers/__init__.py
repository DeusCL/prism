from litestar import Router
from .api import api_router
from .web import web_router



# Router principal que combina todo
main_router = Router(
    path="",
    route_handlers=[
        api_router,  # Tendrá prefijo /api
        web_router,  # Sin prefijo
    ]
)

