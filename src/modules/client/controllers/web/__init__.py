from litestar import Router

from .admin_controller import AdminController



web_router = Router(
    path="",
    route_handlers=[
        AdminController,
    ],
    tags=["Web"],
)

