from litestar import Router

from .area_controller import AreaController



api_router = Router(
    path="/api",
    route_handlers=[
        AreaController
    ],
    tags=["API"],
)

