from pydantic import Field
from pydantic_settings import BaseSettings



class DatabaseSettings(BaseSettings):
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=3306, description="Database port")
    db_user: str = Field(description="Database username")
    db_password: str = Field(description="Database password")
    db_name: str = Field(description="Database name")

    @property
    def url_db(self) -> str:
        """Construye la URL de conexión MySQL."""
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def url_db_sync(self) -> str:
        """URL síncrona para migraciones."""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_prefix = "DB_"
        case_sensitive = False
