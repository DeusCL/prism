from litestar.logging import LoggingConfig
from litestar.exceptions import HTTPException, ValidationException, NotFoundException



logging_config = LoggingConfig(
    root={"level": "WARNING", "handlers": []},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    },
    log_exceptions="always",
    disable_stack_trace={HTTPException, ValidationException, NotFoundException}
)

logger = logging_config.configure()()