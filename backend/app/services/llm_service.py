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
                temperature=0.1,  # Fijado a 0.1 según requerimiento
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
            )

            max_retries = 1
            response = None
            summary_data = None
            for attempt in range(max_retries + 1):
                try:
                    # Generar respuesta
                    content_parts = [system_prompt, user_prompt] if system_prompt else [user_prompt]
                    response = self.model.generate_content(
                        content_parts,
                        generation_config=generation_config,
                    )

                    # Parsear JSON de la respuesta
                    raw_text = response.text
                    summary_data = self._parse_json_response(raw_text)
                    
                    # Manejar error explícito del modelo desde el JSON
                    if "error" in summary_data and len(summary_data) == 1:
                        raise LLMError(summary_data["error"])
                        
                    break
                except LLMError:
                    raise  # No reintentar si es un error explícito
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Fallo en intento {attempt + 1}: {str(e)}. Reintentando en 2s...")
                        time.sleep(2)
                    else:
                        raise

            processing_time = time.time() - start_time

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
        """Construye un MeetingSummary aplanando el nuevo formato JSON para compatibilidad."""
        # Si el JSON viene en el formato antiguo, mantener soporte básico
        if "metadata" not in data and "contenido" not in data:
            tasks = []
            for task in data.get("pending_tasks", []):
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

        # Mapeo del nuevo formato (PROMPT INTERNO definitivo)
        metadata = data.get("metadata", {})
        contenido = data.get("contenido", {})
        
        # Participantes
        participants = [p.get("nombre", "") for p in data.get("participantes", []) if isinstance(p, dict)]
        
        # Temas discutidos
        topics = [f"{t.get('tema', '')}: {t.get('resumen', '')}".strip(": ") for t in contenido.get("temas_discutidos", [])]
        
        # Decisiones
        decisions = [d.get("descripcion", "") for d in data.get("decisiones", [])]
        
        # Tareas
        tasks = []
        for t in data.get("tareas_pendientes", []):
            if isinstance(t, dict):
                tasks.append(TaskItem(
                    task=t.get("descripcion", ""),
                    responsible=t.get("responsable", "Por asignar"),
                    deadline=t.get("fecha_vencimiento")
                ))
        
        # Riesgos
        risks = [r.get("descripcion", "") for r in data.get("riesgos_bloqueos", [])]
        
        # Próximos pasos
        next_steps = []
        proxima = data.get("proxima_reunion")
        if proxima and isinstance(proxima, dict) and any(proxima.values()):
            fecha = proxima.get("fecha_tentativa") or "TBD"
            tema = proxima.get("tema_tentativo") or "TBD"
            next_steps.append(f"Próxima reunión: {fecha} - {tema}")

        return MeetingSummary(
            meeting_name=metadata.get("nombre_reunion") or "",
            date_detected=metadata.get("fecha"),
            participants=participants,
            meeting_objective=contenido.get("objetivo_principal"),
            topics_discussed=topics,
            decisions_made=decisions,
            pending_tasks=tasks,
            risks_and_blockers=risks,
            next_steps=next_steps,
            executive_summary=contenido.get("resumen_ejecutivo", ""),
        )


# Instancia singleton (lazy init)
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Obtiene la instancia del servicio LLM (lazy initialization)."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
