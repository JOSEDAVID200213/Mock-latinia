"""
Servicio de integración con Gemini LLM.
Maneja la generación de resúmenes y el parsing de respuestas.
"""
from __future__ import annotations

import json
import logging
import re
import time

import google.generativeai as genai

from app.config import GEMINI_API_KEY, GEMINI_MAX_OUTPUT_TOKENS, GEMINI_MODEL, GEMINI_TEMPERATURE
from app.models.schemas import MeetingSummary, ProcessingMetadata, TaskItem

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Error durante la interacción con el LLM."""
    pass


class LLMService:
    """Servicio para interactuar con Gemini y generar resúmenes."""

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
        system_prompt: str,
        user_prompt: str,
        template_name: str,
        meeting_name: str,
    ) -> tuple[MeetingSummary, ProcessingMetadata]:
        """
        Genera un resumen estructurado usando Gemini.

        Args:
            system_prompt: Instrucciones del sistema
            user_prompt: Prompt con la transcripción
            template_name: Nombre del template usado
            meeting_name: Nombre de la reunión

        Returns:
            Tuple de (MeetingSummary, ProcessingMetadata)
        """
        start_time = time.time()

        try:
            # Configurar generación
            generation_config = genai.types.GenerationConfig(
                temperature=GEMINI_TEMPERATURE,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
            )

            # Generar respuesta
            response = self.model.generate_content(
                [system_prompt, user_prompt],
                generation_config=generation_config,
            )

            processing_time = time.time() - start_time

            # Extraer tokens usados
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count if usage else 0
            output_tokens = usage.candidates_token_count if usage else 0

            # Parsear JSON de la respuesta
            raw_text = response.text
            summary_data = self._parse_json_response(raw_text)

            # Asegurar que meeting_name esté seteado
            if not summary_data.get("meeting_name"):
                summary_data["meeting_name"] = meeting_name

            # Construir MeetingSummary
            summary = self._build_summary(summary_data)

            # Construir metadata
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

            logger.info(
                f"Resumen generado: {input_tokens} input + {output_tokens} output tokens, "
                f"{processing_time:.1f}s, ${actual_cost:.6f}"
            )

            return summary, metadata

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error en LLM tras {processing_time:.1f}s: {str(e)}")
            raise LLMError(f"Error al generar resumen: {str(e)}")

    def _parse_json_response(self, raw_text: str) -> dict:
        """
        Parsea la respuesta JSON del LLM.
        Maneja casos donde el LLM envuelve el JSON en markdown.
        """
        text = raw_text.strip()

        # Intentar parsear directamente
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Intentar extraer JSON de bloques de código markdown
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Intentar encontrar el primer { ... } válido
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise LLMError(
            f"No se pudo parsear la respuesta del LLM como JSON. "
            f"Respuesta recibida: {text[:500]}..."
        )

    def _build_summary(self, data: dict) -> MeetingSummary:
        """Construye un MeetingSummary desde el dict parseado, manejando variaciones."""
        # Normalizar pending_tasks
        tasks = []
        raw_tasks = data.get("pending_tasks", [])
        for task in raw_tasks:
            if isinstance(task, str):
                tasks.append(TaskItem(task=task))
            elif isinstance(task, dict):
                tasks.append(TaskItem(
                    task=task.get("task", task.get("description", "")),
                    responsible=task.get("responsible", task.get("assignee")),
                    deadline=task.get("deadline", task.get("due_date")),
                ))

        return MeetingSummary(
            meeting_name=data.get("meeting_name", ""),
            date_detected=data.get("date_detected"),
            participants=data.get("participants", []),
            meeting_objective=data.get("meeting_objective"),
            topics_discussed=data.get("topics_discussed", []),
            decisions_made=data.get("decisions_made", []),
            pending_tasks=tasks,
            risks_and_blockers=data.get("risks_and_blockers", []),
            next_steps=data.get("next_steps", []),
            executive_summary=data.get("executive_summary", ""),
        )


# Instancia singleton (lazy init)
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Obtiene la instancia del servicio LLM (lazy initialization)."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
