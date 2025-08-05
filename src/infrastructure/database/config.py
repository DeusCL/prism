from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig

from .models import Base
from src.shared.settings import settings



def get_database_config() -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        connection_string=settings.url_db,
        create_all=False,
        metadata=Base.metadata,
        session_dependency_key="db",
        engine_dependency_key="db_engine",
        before_send_handler="autocommit"
    )
