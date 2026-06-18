"""
Constructor de prompts unificado.
Contiene el prompt definitivo estandarizado para generar resúmenes de reuniones.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def build_summary_prompt(texto_extraido: str) -> str:
    """
    Inyecta la transcripción extraída en el prompt estándar definitivo del POC.
    No se debe alterar la estructura de este prompt para mantener la consistencia.
    """
    return f"""Eres un asistente especializado en estructurar actas de reuniones
corporativas a partir de transcripciones o notas.

CONTEXTO:
Vas a recibir el texto plano de una reunión (transcripción de audio, notas manuales o mezcla). Tu única tarea es leerlo y redactar un resumen ejecutivo y acta estructurada, profesional, limpia y fácil de leer.

ESTRUCTURA DEL DOCUMENTO:
Tu respuesta debe estar redactada en español y usar la siguiente estructura de títulos y viñetas (texto plano, SIN FORMATO MARKDOWN, sin usar asteriscos, numerales ni negritas):

Resumen de reunión: [Nombre de la reunión o Tema principal si no se especifica]

Metadata de la Reunión
- Fecha: [Fecha de la reunión si se menciona, o "No especificada"]
- Duración estimada: [Duración en minutos si se menciona, o "No especificada"]
- Participantes: [Nombres de los participantes detectados separados por comas, o "No especificados"]

1. Objetivo Principal
[Una breve descripción del objetivo o propósito general de la reunión]

2. Resumen Ejecutivo
[Un resumen ejecutivo de máximo 4 frases con lo más importante conversado y acordado]

3. Temas Discutidos
- [Tema 1]: [Resumen corto de lo discutido en este tema]
- [Tema 2]: [Resumen corto de lo discutido en este tema]
...

4. Decisiones Tomadas
- [Decisión 1 y quién la tomó si se menciona]
- [Decisión 2]
...

5. Tareas Pendientes
- [Descripción de la tarea]: Responsable: [Nombre del responsable o "Por asignar"] | Fecha límite: [Fecha de vencimiento o "Por definir"]
...

6. Riesgos y Bloqueos
- [Riesgo/bloqueo identificado y su impacto si se menciona]
...

7. Próximos Pasos / Próxima Reunión
- [Próxima fecha o temas tentativos para continuar]

REGLAS DE ORO:
- No inventes información que no esté en el texto.
- Sé extremadamente conciso y directo al punto.
- Usa lenguaje formal y profesional.
- No incluyas explicaciones previas ni posteriores, devuelve directamente el documento en formato texto plano y limpio (SIN markdown como #, **, _ o similares).

TEXTO A ANALIZAR:
\"\"\"
{texto_extraido}
\"\"\"
"""


class PromptBuilder:
    """
    Fachada para mantener compatibilidad con las llamadas actuales en el POC.
    Ignora la calidad y formato para usar siempre el prompt estandarizado.
    """

    def build(
        self,
        transcript_text: str,
        quality_score: float = 0.0,
        format_type: str = "",
        meeting_name: str = "",
    ) -> tuple[str, str, str]:
        """
        Devuelve el prompt unificado.
        
        Returns:
            Tuple de (system_prompt, user_prompt, template_name)
        """
        # Como el prompt es uno solo que combina contexto de sistema e instrucción,
        # dejamos system_prompt vacío y enviamos todo en el user_prompt.
        system_prompt = ""
        user_prompt = build_summary_prompt(transcript_text)
        
        logger.info("Prompt estandarizado construido.")
        
        return system_prompt, user_prompt, "unified_standard"

    def estimate_prompt_tokens(self, quality_score: float = 0.0) -> int:
        """Estima los tokens del nuevo prompt unificado."""
        return 1000  # Estimación fija para el prompt estándar


# Instancia singleton
prompt_builder = PromptBuilder()
