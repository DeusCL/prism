from litestar import Litestar
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin

from src.shared.settings import template_config, static_files, logging_config
from src.modules.client.controllers import main_router
from src.infrastructure.database.config import get_database_config



app = Litestar(
    route_handlers=[main_router, static_files],
    template_config=template_config,
    plugins=[
        SQLAlchemyPlugin(config=get_database_config())
    ],
    logging_config=logging_config
)
