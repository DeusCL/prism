from litestar import Router

from .admin_controller import AdminController
from .chat_controller import ChatController
from .simulador_controller import SimuladorController
from .home_controller import HomeController



web_router = Router(
    path="",
    route_handlers=[
        HomeController,
        AdminController,
        ChatController,
        SimuladorController
    ],
    tags=["Web"],
)

