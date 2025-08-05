from typing import Optional, Dict, Any
from datetime import datetime

from src.modules.client.repositories import ConfiguracionIARepository
from src.infrastructure.database.models import ConfiguracionIA



class ConfiguracionIAService:
    def __init__(self, configuracion_repository: ConfiguracionIARepository):
        self.configuracion_repository = configuracion_repository


    async def get_current_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual de la IA como diccionario"""

        config = await self.configuracion_repository.get_active_config()

        if not config:
            # Crear configuración por defecto si no existe
            default_config_data = {
                "system_prompt": """Eres Prism, el asistente de IA de Biplan, una empresa de consultoría contable, legal, financiera y tributaria.

Debes ser profesional, amigable y eficiente. Responde preguntas generales sobre los servicios y deriva consultas específicas o técnicas al área correspondiente.

Si necesitas derivar una consulta, incluye en tu respuesta: "🔄 DERIVAR: [nombre_del_área]"
""",
                "temperatura": 0.7,
                "min_tokens": 50,
                "max_tokens": 300,
                "model": "gemini-pro",
                "auto_derivacion_activa": True
            }

            await self.configuracion_repository.create_or_update_config(default_config_data)
            await self.configuracion_repository.commit()

            # Retornar los datos por defecto directamente
            return {
                "id": 1,
                "system_prompt": default_config_data["system_prompt"],
                "temperatura": default_config_data["temperatura"],
                "min_tokens": default_config_data["min_tokens"],
                "max_tokens": default_config_data["max_tokens"],
                "model": default_config_data["model"],
                "auto_derivacion_activa": default_config_data["auto_derivacion_activa"],
                "updated_at": datetime.utcnow().isoformat()
            }

        # Convertir objeto existente a diccionario de forma segura
        try:
            return {
                "id": getattr(config, 'id', 1),
                "system_prompt": getattr(config, 'system_prompt', ''),
                "temperatura": getattr(config, 'temperatura', 0.7),
                "min_tokens": getattr(config, 'min_tokens', 50),
                "max_tokens": getattr(config, 'max_tokens', 300),
                "model": getattr(config, 'model', 'gemini-pro'),
                "auto_derivacion_activa": getattr(config, 'auto_derivacion_activa', True),
                "updated_at": getattr(config, 'updated_at', datetime.utcnow()).isoformat()
            }
        except Exception as e:
            print(f"❌ Error accediendo a propiedades del config: {str(e)}")
            # Fallback: retornar configuración por defecto
            return {
                "id": 1,
                "system_prompt": """Eres Prism, el asistente de IA de Biplan, una empresa de consultoría contable, legal, financiera y tributaria.

Debes ser profesional, amigable y eficiente. Responde preguntas generales sobre los servicios y deriva consultas específicas o técnicas al área correspondiente.

Si necesitas derivar una consulta, incluye en tu respuesta: "🔄 DERIVAR: [nombre_del_área]"
""",
                "temperatura": 0.7,
                "min_tokens": 50,
                "max_tokens": 300,
                "model": "gemini-pro",
                "auto_derivacion_activa": True,
                "updated_at": datetime.utcnow().isoformat()
            }


    async def update_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza la configuración de la IA y retorna un diccionario
        construido directamente de los datos enviados
        """

        # Validar datos
        self._validate_config_data(config_data)

        # Agregar timestamp de actualización
        update_timestamp = datetime.utcnow()
        config_data_with_timestamp = config_data.copy()
        config_data_with_timestamp['updated_at'] = update_timestamp

        # Actualizar configuración en la base de datos
        await self.configuracion_repository.create_or_update_config(config_data_with_timestamp)
        await self.configuracion_repository.commit()

        # NO acceder al objeto retornado, construir respuesta directamente de los datos
        return {
            "id": 1,  # Siempre será 1 para singleton
            "system_prompt": config_data.get("system_prompt", ""),
            "temperatura": config_data.get("temperatura", 0.7),
            "min_tokens": config_data.get("min_tokens", 50),
            "max_tokens": config_data.get("max_tokens", 300),
            "model": config_data.get("model", "gemini-pro"),
            "auto_derivacion_activa": config_data.get("auto_derivacion_activa", True),
            "updated_at": update_timestamp.isoformat()
        }


    def _validate_config_data(self, config_data: Dict[str, Any]) -> None:
        """Valida los datos de configuración"""

        if "temperatura" in config_data:
            temp = config_data["temperatura"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                raise ValueError("La temperatura debe estar entre 0 y 2")

        if "min_tokens" in config_data:
            min_tokens = config_data["min_tokens"]
            if not isinstance(min_tokens, int) or min_tokens < 1:
                raise ValueError("min_tokens debe ser un entero positivo")

        if "max_tokens" in config_data:
            max_tokens = config_data["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 50 or max_tokens > 2000:
                raise ValueError("max_tokens debe estar entre 50 y 2000")

        if "system_prompt" in config_data:
            prompt = config_data["system_prompt"]
            if not isinstance(prompt, str) or len(prompt.strip()) < 10:
                raise ValueError("system_prompt debe ser un texto de al menos 10 caracteres")


    async def reset_to_default(self) -> Dict[str, Any]:
        """Resetea la configuración a los valores por defecto"""

        default_config = {
            "system_prompt": """Eres Prism, el asistente de IA de Biplan, una empresa de consultoría contable, legal, financiera y tributaria.

Debes ser profesional, amigable y eficiente. Responde preguntas generales sobre los servicios y deriva consultas específicas o técnicas al área correspondiente.

Si necesitas derivar una consulta, incluye en tu respuesta: "🔄 DERIVAR: [nombre_del_área]"
""",
            "temperatura": 0.7,
            "min_tokens": 50,
            "max_tokens": 300,
            "model": "gemini-pro",
            "auto_derivacion_activa": True
        }

        return await self.update_config(default_config)


    async def get_config_for_ai(self) -> ConfiguracionIA:
        """
        Método especial para obtener configuración para uso de la IA
        Retorna un objeto ConfiguracionIA construido manualmente
        """
        config_dict = await self.get_current_config()

        # Crear objeto ConfiguracionIA manualmente para evitar problemas de sesión
        config_obj = ConfiguracionIA(
            id=config_dict["id"],
            system_prompt=config_dict["system_prompt"],
            temperatura=config_dict["temperatura"],
            min_tokens=config_dict["min_tokens"],
            max_tokens=config_dict["max_tokens"],
            model=config_dict["model"],
            auto_derivacion_activa=config_dict["auto_derivacion_activa"],
            updated_at=datetime.fromisoformat(config_dict["updated_at"].replace('Z', '+00:00'))
        )

        return config_obj

