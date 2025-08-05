import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from litestar.static_files import create_static_files_router

from litestar.template.config import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.static_files import create_static_files_router

from .constants import ROOT_PATH



def register_template_callables(engine: JinjaTemplateEngine, callables: Dict[str, Callable[[Dict[str, Any]], Any]],) -> None:
    for key, template_callable in callables.items():
        engine.register_template_callable(
            key=key,
            template_callable=template_callable,
        )


def configure_template_engine(engine: JinjaTemplateEngine) -> None:
    # Definir las funciones que se registrarán en las plantillas
    template_callables = {
        "static_version": static_version,
    }
    register_template_callables(engine, template_callables)


def static_version(ctx, file_path) -> str:
    # Implementación para obtener la versión estática del archivo (Ej. fecha de modificación)

    full_path = ROOT_PATH / "static" / file_path.lstrip("/")

    if full_path.exists():
        modified_time = os.path.getmtime(full_path)
        version = datetime.fromtimestamp(modified_time, tz=timezone.utc).strftime('%Y%m%d%H%M%S')
        return f"static/{file_path}?v={version}"
    return f"static/{file_path}"


# Configuración de templates
template_config = TemplateConfig(
    directory = ROOT_PATH / "templates",
    engine = JinjaTemplateEngine,
    engine_callback=configure_template_engine,
)


# Configuración de static files
static_files = create_static_files_router(
    path = "/static",
    directories = [ROOT_PATH / "static"]
)
