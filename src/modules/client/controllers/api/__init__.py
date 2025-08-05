from litestar import Router

from .area_controller import AreaController
from .chat_controller import ChatWebSocketController



api_router = Router(
    path="/api",
    route_handlers=[
        AreaController,
        ChatWebSocketController
    ],
    tags=["API"],
)

