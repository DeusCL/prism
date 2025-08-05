from litestar import Router

from .area_controller import AreaController
from .chat_controller import ChatWebSocketController
from .configuracion_ai_controller import ConfiguracionIAController



api_router = Router(
    path="/api",
    route_handlers=[
        AreaController,
        ChatWebSocketController,
        ConfiguracionIAController
    ],
    tags=["API"],
)

