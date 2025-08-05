from litestar import Router

from .admin_controller import AdminController
from .chat_controller import ChatController
from .simulador_controller import SimuladorController



web_router = Router(
    path="",
    route_handlers=[
        AdminController,
        ChatController,
        SimuladorController
    ],
    tags=["Web"],
)

