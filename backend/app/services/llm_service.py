"""
Servicio de integración con Gemini LLM.
Envía el prompt, recibe la respuesta en Markdown y la guarda como Google Doc.
"""
from __future__ import annotations

import logging
import time

import google.generativeai as genai

from app.config import GEMINI_API_KEY, GEMINI_MAX_OUTPUT_TOKENS, GEMINI_MODEL, GEMINI_TEMPERATURE
from app.models.schemas import MeetingSummary, ProcessingMetadata
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Error durante la interacción con el LLM."""
    pass


class LLMService:
    """Servicio para interactuar con Gemini y generar resúmenes en Markdown."""

    def __init__(self):
        if not GEMINI_API_KEY:
            raise LLMError(
                "GEMINI_API_KEY no configurada. "
                "Agrega tu API key al archivo .env"
            )
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def generate_summary(
        self,
        meeting_id: str,
        system_prompt: str,
        user_prompt: str,
        template_name: str,
        meeting_name: str,
    ) -> tuple[MeetingSummary, ProcessingMetadata]:
        """
        Genera un resumen estructurado usando Gemini.

        El prompt instruye a Gemini a responder en Markdown.
        La respuesta se guarda directamente en Google Docs (via Apps Script)
        y también se persiste localmente como extracted_text.

        Args:
            meeting_id: ID único de la reunión
            system_prompt: Instrucciones del sistema (base_system.txt)
            user_prompt: Template con la transcripción inyectada
            template_name: Nombre del template usado (para metadata)
            meeting_name: Nombre de la reunión

        Returns:
            Tuple de (MeetingSummary, ProcessingMetadata)
        """
        start_time = time.time()

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
                response_mime_type="text/plain",
            )

            max_retries = 3
            for attempt in range(max_retries + 1):
                try:
                    # Enviar system_prompt + user_prompt a Gemini
                    content_parts = [system_prompt, user_prompt] if system_prompt else [user_prompt]
                    response = self.model.generate_content(
                        content_parts,
                        generation_config=generation_config,
                    )

                    # La respuesta ya viene en Markdown — no modificar el formato
                    markdown_text = response.text

                    # Convertir a texto limpio para Google Docs (sin markdown raw)
                    from app.utils.markdown_cleaner import markdown_to_docs_text
                    docs_text = markdown_to_docs_text(markdown_text)

                    # Guardar en Google Docs (via Apps Script) o localmente
                    storage = get_storage_service()
                    doc_url = storage.save_google_doc(
                        meeting_id,
                        f"{meeting_name}_resumen",
                        docs_text,
                        meeting_name=meeting_name,
                    )
                    logger.info(f"Resumen guardado como Google Doc: {doc_url}")

                    # Construir el objeto de resumen con el texto Markdown completo
                    summary = MeetingSummary(
                        meeting_name=meeting_name,
                        executive_summary=markdown_text,
                        doc_url=doc_url,
                    )

                    # Calcular tokens y costo real
                    processing_time = time.time() - start_time
                    usage = response.usage_metadata if hasattr(response, "usage_metadata") else None
                    input_tokens = getattr(usage, "prompt_token_count", 0)
                    output_tokens = getattr(usage, "candidates_token_count", 0)

                    from app.config import COST_PER_1M_INPUT_TOKENS, COST_PER_1M_OUTPUT_TOKENS
                    actual_cost = (
                        (input_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
                        + (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
                    )

                    metadata = ProcessingMetadata(
                        model=GEMINI_MODEL,
                        prompt_template=template_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=input_tokens + output_tokens,
                        estimated_cost_usd=round(actual_cost, 6),
                        processing_time_seconds=round(processing_time, 2),
                        is_free_tier=True,
                    )

                    return summary, metadata

                except LLMError:
                    raise
                except Exception as e:
                    error_msg = str(e)
                    if attempt < max_retries:
                        if "429" in error_msg or "Quota exceeded" in error_msg:
                            logger.warning(f"Límite de API (429). Esperando 12s para reintento {attempt + 1} de {max_retries}...")
                            time.sleep(12)
                        else:
                            logger.warning(f"Fallo en intento {attempt + 1}: {error_msg}. Reintentando en 3s...")
                            time.sleep(3)
                    else:
                        raise

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error en LLM tras {processing_time:.1f}s: {str(e)}")
            raise LLMError(f"Error al generar resumen: {str(e)}")


# Instancia singleton (lazy init)
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Obtiene la instancia del servicio LLM (lazy initialization)."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
