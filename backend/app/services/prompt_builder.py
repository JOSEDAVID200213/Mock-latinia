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
Vas a recibir el texto plano de una reunión: puede ser una
transcripción de audio, notas manuales escritas durante la reunión,
o una mezcla de ambas. Tu única tarea es leerlo y devolver un objeto
JSON con la información estructurada, siguiendo exactamente el
esquema indicado más abajo.

REGLAS DE EXTRACCIÓN (existen para eliminar la ambigüedad — síguelas
de forma estricta):

1. No inventes información que no esté en el texto. Si un dato no
   aparece, usa null.
2. Si una fecha no es exacta (ej. "el próximo lunes", "en dos
   semanas"), déjala en null. No calcules ni asumas fechas absolutas.
3. Toda tarea en "tareas_pendientes" debe tener un valor en
   "responsable": si no hay un nombre claro en el texto, escribe
   "Por asignar" (nunca lo dejes vacío o null).
4. Si encuentras información contradictoria, prioriza la mención
   más reciente dentro del texto.
5. Ignora muletillas y ruido típico de transcripción (ehh, este, o
   sea, risas, silencios marcados, repeticiones por corte de audio).
6. Detecta el idioma predominante del texto y repórtalo en
   "idioma_detectado" (ej. "es", "en", "pt").
7. Evalúa la calidad de la transcripción como "alta", "media" o
   "baja" según qué tan legible y coherente sea el texto recibido.
8. Si el texto tiene patrones de transcripción de audio (un nombre
   seguido de dos puntos, marcas de tiempo tipo [00:15:30]), apóyate
   en esos patrones para identificar participantes y estimar
   duración.
9. Si el texto tiene patrones de notas sueltas (viñetas, encabezados
   con #, palabras como "TODO:", "Acción:", "Decisión:"), tómalas
   como pista directa para llenar "tareas_pendientes" y "decisiones".
10. Para "categoria_sugerida", elige la opción que mejor describa el
    propósito general de la reunión según el contenido: "Reunión de
    seguimiento", "Actualización de proyecto", "Decisión estratégica",
    "Reunión general", u "Otro" si ninguna aplica bien.

ESQUEMA DE SALIDA (JSON estricto, sin texto adicional):

{{
  "metadata": {{
    "nombre_reunion": string | null,
    "categoria_sugerida": string | null,
    "fecha": "YYYY-MM-DD" | null,
    "hora_inicio": "HH:MM" | null,
    "duracion_minutos": integer | null,
    "idioma_detectado": string,
    "calidad_transcripcion": "alta" | "media" | "baja"
  }},
  "participantes": [
    {{ "nombre": string, "rol": "Organizador" | "Participante" | "Observador" | null }}
  ],
  "contenido": {{
    "objetivo_principal": string | null,
    "resumen_ejecutivo": string,
    "temas_discutidos": [
      {{ "tema": string, "resumen": string }}
    ]
  }},
  "decisiones": [
    {{ "descripcion": string, "tomada_por": string | null, "fecha_efectiva": "YYYY-MM-DD" | null }}
  ],
  "tareas_pendientes": [
    {{ "descripcion": string, "responsable": string, "fecha_vencimiento": "YYYY-MM-DD" | null, "prioridad": "Alta" | "Media" | "Baja" | null }}
  ],
  "riesgos_bloqueos": [
    {{ "descripcion": string, "impacto": "Alto" | "Medio" | "Bajo" | null }}
  ],
  "proxima_reunion": {{
    "fecha_tentativa": "YYYY-MM-DD" | null,
    "tema_tentativo": string | null
  }},
  "notas_adicionales": string | null
}}

NOTA SOBRE "resumen_ejecutivo": máximo 400 caracteres, 2 a 4 frases
con lo más importante de la reunión. Es un POC, no hace falta más.

FORMATO DE RESPUESTA:
Devuelve ÚNICAMENTE el objeto JSON. Sin explicaciones, sin texto
antes o después, sin envolverlo entre comillas de bloque de código.
Si el texto recibido está vacío, es ilegible, o claramente no
corresponde a una reunión, devuelve exactamente:
{{"error": "breve descripción del problema"}}

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
