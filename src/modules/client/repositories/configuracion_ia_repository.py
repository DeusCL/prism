from typing import Optional
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import ConfiguracionIA



class ConfiguracionIARepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_active_config(self) -> Optional[ConfiguracionIA]:
        """Obtiene la configuración activa de la IA (singleton)"""
        query = select(ConfiguracionIA).order_by(ConfiguracionIA.updated_at.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


    async def create_or_update_config(self, config_data: dict) -> ConfiguracionIA:
        """Crea o actualiza la configuración de la IA de forma segura"""

        # Buscar configuración existente
        existing_config = await self.get_active_config()

        if existing_config:
            # Actualizar configuración existente sin acceder a propiedades que causen refresh
            # Usar getattr para acceso seguro al ID
            config_id = getattr(existing_config, 'id', None)

            if config_id:
                # Actualizar por ID directamente
                for key, value in config_data.items():
                    if hasattr(existing_config, key):
                        setattr(existing_config, key, value)

                existing_config.updated_at = datetime.utcnow()
                await self.db.flush()
                return existing_config
            else:
                # Si no podemos obtener el ID, crear nueva configuración
                return await self._create_new_config(config_data)
        else:
            # Crear nueva configuración
            return await self._create_new_config(config_data)


    async def _create_new_config(self, config_data: dict) -> ConfiguracionIA:
        """Crea una nueva configuración"""
        config_data['updated_at'] = datetime.utcnow()
        config = ConfiguracionIA(**config_data)
        self.db.add(config)
        await self.db.flush()
        return config


    async def commit(self):
        await self.db.commit()


    async def rollback(self):
        await self.db.rollback()
