import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from src.modules.client.repositories import AreaRepository
from src.infrastructure.database.models import ConfiguracionIA, Area
from src.shared.settings.base import settings


class AIService:
    def __init__(self, area_repository: AreaRepository):
        self.area_repository = area_repository
        self.client = None
        self._initialize_client()


    def _initialize_client(self):
        """Inicializa el cliente de Gemini"""
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno")

        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-pro')
        print("✅ Cliente Gemini inicializado")


    async def process_client_message(
        self,
        message: str,
        client_name: str,
        conversation_history: List[Dict[str, str]] = None,
        config: Optional[ConfiguracionIA] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje de cliente y determina si responder o derivar

        Returns:
        {
            "should_respond": bool,
            "response": str,
            "should_transfer": bool,
            "transfer_area": Optional[Area],
            "confidence": float
        }
        """

        if not self.client:
            raise ValueError("Cliente de IA no inicializado")

        try:
            # Obtener configuración por defecto si no se proporciona
            if not config:
                config = await self._get_default_config()

            # Obtener áreas activas para derivación
            areas = await self.area_repository.get_areas_for_derivation()

            # Construir el prompt del sistema
            system_prompt = await self._build_system_prompt(config, areas)

            # Construir el contexto de la conversación
            conversation_context = self._build_conversation_context(
                message, client_name, conversation_history or []
            )

            # Generar respuesta de la IA
            full_prompt = f"{system_prompt}\n\n{conversation_context}"

            # Usar getattr para acceso seguro a las propiedades de configuración
            temperatura = getattr(config, 'temperatura', 0.7)
            max_tokens = getattr(config, 'max_tokens', 300)

            generation_config = GenerationConfig(
                temperature=temperatura,
                max_output_tokens=max_tokens,
                top_p=0.8,
                top_k=40
            )

            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            if not response.text:
                raise ValueError("Respuesta vacía de la IA")

            # Analizar la respuesta para determinar derivación
            analysis = await self._analyze_response_for_transfer(response.text, areas)

            return {
                "should_respond": True,
                "response": response.text.strip(),
                "should_transfer": analysis["should_transfer"],
                "transfer_area": analysis["area"],
                "confidence": analysis["confidence"],
                "reasoning": analysis.get("reasoning", "")
            }

        except Exception as e:
            print(f"❌ Error procesando mensaje con IA: {str(e)}")

            # Respuesta de fallback
            return {
                "should_respond": True,
                "response": "Disculpa, estoy experimentando dificultades técnicas. Un especialista te atenderá pronto.",
                "should_transfer": True,
                "transfer_area": None,
                "confidence": 0.5,
                "reasoning": f"Error técnico: {str(e)}"
            }


    async def _build_system_prompt(self, config: ConfiguracionIA, areas: List[Area]) -> str:
        """Construye el prompt del sistema con instrucciones de áreas"""

        # Acceso seguro al system_prompt
        base_prompt = getattr(config, 'system_prompt', None) or """
Eres Prism, el asistente de IA de Biplan, una empresa de consultoría contable, legal, financiera y tributaria.

Tu objetivo es:
1. Responder preguntas generales sobre los servicios de Biplan
2. Derivar consultas específicas o técnicas al área correspondiente
3. Ser profesional, amigable y eficiente

Información de la empresa:
- Biplan ofrece consultoría contable, legal, financiera y tributaria
- Atendemos tanto personas naturales como empresas
- Nos especializamos en soluciones integrales de negocio
"""

        # Agregar instrucciones de derivación por áreas
        areas_instructions = "\n\nÁREAS DE DERIVACIÓN:\n"
        for area in areas:
            area_name = getattr(area, 'nombre', 'Área desconocida')
            area_instructions = getattr(area, 'instrucciones', 'Sin instrucciones')
            area_specialist = getattr(area, 'especialista_asignado', None)
            area_time = getattr(area, 'tiempo_respuesta', None)

            areas_instructions += f"\n🔹 {area_name}:\n"
            areas_instructions += f"   Instrucciones: {area_instructions}\n"
            if area_specialist:
                areas_instructions += f"   Especialista: {area_specialist}\n"
            if area_time:
                areas_instructions += f"   Tiempo estimado: {area_time} minutos\n"

        # Instrucciones finales
        final_instructions = """

INSTRUCCIONES IMPORTANTES:
1. Si la consulta es general sobre servicios, responde directamente
2. Si la consulta es específica o técnica, indica que derivarás al especialista
3. Si derivás, menciona el área específica y el tiempo estimado de respuesta
4. Sé conciso pero completo en tus respuestas
5. Siempre mantén un tono profesional y cordial

FORMATO DE DERIVACIÓN:
Si decides derivar, incluye en tu respuesta: "🔄 DERIVAR: [nombre_del_área]"
"""

        return base_prompt + areas_instructions + final_instructions


    def _build_conversation_context(
        self,
        current_message: str,
        client_name: str,
        history: List[Dict[str, str]]
    ) -> str:
        """Construye el contexto de la conversación"""

        context = f"CONVERSACIÓN CON {client_name}:\n\n"

        # Agregar historial si existe
        if history:
            context += "Historial previo:\n"
            for msg in history[-5:]:  # Solo últimos 5 mensajes
                sender = "Cliente" if msg.get("message_type") == "cliente" else "Asistente"
                context += f"{sender}: {msg.get('content', '')}\n"
            context += "\n"

        # Agregar mensaje actual
        context += f"Cliente: {current_message}\n\n"
        context += "Respuesta del Asistente:"

        return context


    async def _analyze_response_for_transfer(
        self,
        response: str,
        areas: List[Area]
    ) -> Dict[str, Any]:
        """Analiza la respuesta para determinar si se debe derivar"""

        response_lower = response.lower()

        # Buscar indicador explícito de derivación
        if "🔄 derivar:" in response_lower:
            # Extraer el área mencionada
            for area in areas:
                area_name = getattr(area, 'nombre', '').lower()
                if area_name and area_name in response_lower:
                    return {
                        "should_transfer": True,
                        "area": area,
                        "confidence": 0.9,
                        "reasoning": "Derivación explícita solicitada por la IA"
                    }

        # Análisis por palabras clave de áreas
        for area in areas:
            area_instructions = getattr(area, 'instrucciones', '')
            area_keywords = self._extract_keywords_from_instructions(area_instructions)
            keyword_matches = sum(1 for keyword in area_keywords if keyword in response_lower)

            if keyword_matches >= 2:  # Al menos 2 palabras clave coinciden
                return {
                    "should_transfer": True,
                    "area": area,
                    "confidence": min(0.8, keyword_matches * 0.2),
                    "reasoning": f"Múltiples palabras clave detectadas: {keyword_matches}"
                }

        return {
            "should_transfer": False,
            "area": None,
            "confidence": 0.1,
            "reasoning": "No se detectaron criterios de derivación"
        }


    def _extract_keywords_from_instructions(self, instructions: str) -> List[str]:
        """Extrae palabras clave de las instrucciones de un área"""

        # Palabras clave comunes por área (esto se podría mejorar con NLP)
        common_keywords = [
            "declaracion", "renta", "impuesto", "contabilidad", "estados", "financieros",
            "legal", "juridico", "contrato", "empresa", "constitucion", "sociedad",
            "inversion", "financiero", "credito", "prestamo", "flujo", "caja",
            "tributario", "fiscal", "iva", "retencion", "planeacion"
        ]

        instructions_lower = instructions.lower()
        found_keywords = []

        for keyword in common_keywords:
            if keyword in instructions_lower:
                found_keywords.append(keyword)

        return found_keywords


    async def _get_default_config(self) -> ConfiguracionIA:
        """Obtiene la configuración por defecto de la IA"""

        # Esta configuración vendría normalmente de la base de datos
        # Por ahora retornamos valores por defecto
        return ConfiguracionIA(
            id=1,
            system_prompt="",  # Se construirá dinámicamente
            temperatura=0.7,
            min_tokens=50,
            max_tokens=300,
            model="gemini-pro",
            auto_derivacion_activa=True,
            updated_at=datetime.utcnow()
        )


    async def should_ai_respond(self, message: str, conversation_history: List = None) -> bool:
        """Determina si la IA debe responder basado en el contexto"""

        # Por ahora, la IA siempre responde a menos que sea una derivación manual
        return True


    def format_transfer_message(self, area: Area, response: str) -> str:
        """Formatea el mensaje de derivación"""

        area_name = getattr(area, 'nombre', 'Área desconocida')
        area_specialist = getattr(area, 'especialista_asignado', None)
        area_time = getattr(area, 'tiempo_respuesta', None)

        transfer_msg = f"📋 Te he derivado al área de **{area_name}**"

        if area_specialist:
            transfer_msg += f"\n👨‍💼 Especialista: {area_specialist}"

        if area_time:
            transfer_msg += f"\n⏱️ Tiempo estimado: {area_time} minutos"

        transfer_msg += "\n\nUn especialista humano se pondrá en contacto contigo pronto."

        return transfer_msg

