from typing import Dict, Any

from litestar import Controller, get, post, put
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST

from src.modules.client.dependencies.ia_dependency import (
    provide_configuracion_repository, provide_configuracion_service
)
from src.modules.client.services import ConfiguracionIAService
from pydantic import BaseModel, Field

from src.shared.settings.base import settings


class ConfiguracionIAUpdateDTO(BaseModel):
    system_prompt: str = Field(..., min_length=10, description="Prompt del sistema para la IA")
    temperatura: float = Field(..., ge=0.0, le=2.0, description="Temperatura de la IA (0.0 - 2.0)")
    min_tokens: int = Field(..., ge=1, le=500, description="Tokens mínimos")
    max_tokens: int = Field(..., ge=50, le=2000, description="Tokens máximos")
    model: str = Field(..., description="Modelo de IA a usar")
    auto_derivacion_activa: bool = Field(..., description="Si la auto-derivación está activa")



class ConfiguracionIAController(Controller):
    path = "/configuracion-ia"
    dependencies = {
        "configuracion_repository": Provide(provide_configuracion_repository),
        "configuracion_service": Provide(provide_configuracion_service)
    }
    tags = ["Configuración IA"]


    @get("/")
    async def get_current_config(
        self,
        configuracion_service: ConfiguracionIAService
    ) -> Dict[str, Any]:
        """Obtiene la configuración actual de la IA"""
        try:
            # El servicio ya retorna un diccionario, no necesitamos conversión
            config_dict = await configuracion_service.get_current_config()
            return config_dict

        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al obtener configuración: {str(e)}"
            )


    @put("/")
    async def update_config(
        self,
        configuracion_service: ConfiguracionIAService,
        data: ConfiguracionIAUpdateDTO
    ) -> Dict[str, Any]:
        """Actualiza la configuración de la IA"""
        try:
            config_data = data.model_dump()
            # El servicio ya retorna un diccionario construido de los datos enviados
            updated_config = await configuracion_service.update_config(config_data)
            return updated_config

        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al actualizar configuración: {str(e)}"
            )


    @post("/reset")
    async def reset_to_default(
        self,
        configuracion_service: ConfiguracionIAService
    ) -> Dict[str, Any]:
        """Resetea la configuración a los valores por defecto"""
        try:
            default_config = await configuracion_service.reset_to_default()
            return default_config

        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Error al resetear configuración: {str(e)}"
            )


    @get("/test")
    async def test_ai_connection(self) -> Dict[str, Any]:
        """Prueba la conexión con la IA"""
        try:
            api_key = settings.gemini_api_key

            if not api_key:
                return {
                    "status": "error",
                    "message": "GEMINI_API_KEY no encontrada en variables de entorno"
                }

            # Verificar que la clave no esté vacía y tenga formato válido
            if len(api_key) < 10:
                return {
                    "status": "error",
                    "message": "GEMINI_API_KEY parece inválida (muy corta)"
                }

            # Intentar inicializar el cliente
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # Hacer una prueba simple
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Di 'Hola' en español")

            if response.text:
                return {
                    "status": "success",
                    "message": "Conexión con Gemini exitosa",
                    "test_response": response.text.strip()
                }
            else:
                return {
                    "status": "error",
                    "message": "Respuesta vacía de Gemini"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error conectando con Gemini: {str(e)}"
            }