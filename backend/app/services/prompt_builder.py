"""
Constructor de prompts.
Lee los templates desde los archivos .txt en app/prompts/.
Elige entre extraction_clean y extraction_noisy según la calidad del documento.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Directorio donde viven los archivos de prompts
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Umbrales de calidad para seleccionar el template
CLEAN_QUALITY_THRESHOLD = 0.8
NOISY_QUALITY_THRESHOLD = 0.45


def _load_prompt(filename: str) -> str:
    """Lee un archivo de prompt del disco."""
    path = PROMPTS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"Archivo de prompt no encontrado: {path}")
        raise


class PromptBuilder:
    """
    Construye el prompt final combinando:
    - base_system.txt  → system prompt (rol e instrucciones globales)
    - extraction_clean.txt   → template para documentos limpios (quality >= 0.8)
    - extraction_intermediate.txt → template para calidad media (0.45 <= quality < 0.8)
    - extraction_noisy.txt   → template para documentos con ruido (quality < 0.45)

    El template elegido ya incluye la instrucción al final 'TRANSCRIPCIÓN:'
    a la que se le concatena el texto extraído.
    """

    def build(
        self,
        transcript_text: str,
        quality_score: float = 0.0,
        format_type: str = "",
        meeting_name: str = "",
    ) -> tuple[str, str, str]:
        """
        Construye el par (system_prompt, user_prompt) y el nombre del template usado.

        Returns:
            Tuple de (system_prompt, user_prompt, template_name)
        """
        # Seleccionar template según calidad del documento
        if quality_score < NOISY_QUALITY_THRESHOLD:
            template_file = "extraction_noisy.txt"
        elif quality_score < CLEAN_QUALITY_THRESHOLD:
            template_file = "extraction_intermediate.txt"
        else:
            template_file = "extraction_clean.txt"

        system_prompt = _load_prompt("base_system.txt")
        user_template = _load_prompt(template_file)

        # Reemplazar placeholder {format_type} si existe en el template
        user_template = user_template.replace("{format_type}", format_type or "desconocido")

        # Lógica dinámica: Si detectamos que es una presentación (pptx) agregamos instrucciones extra
        if format_type == "pptx":
            presentation_instructions = (
                "\n\n### INSTRUCCIONES ESPECIALES PARA PRESENTACIONES (PPTX) ###\n"
                "El texto a continuación proviene de las diapositivas de una presentación. "
                "Por favor, enfócate también en extraer:\n"
                "- El título principal de la presentación y la temática central.\n"
                "- Los puntos clave de cada diapositiva importante.\n"
                "- Conclusiones clave que el presentador intentó transmitir.\n"
                "Asegúrate de estructurar el resumen de forma que tenga sentido como una 'exposición' "
                "además de los acuerdos y próximos pasos."
            )
            user_template += presentation_instructions

        # Concatenar la transcripción al final del template
        user_prompt = user_template + "\n\nTRANSCRIPCIÓN:\n" + transcript_text

        # Log claro y visible del path de procesamiento elegido
        if quality_score < NOISY_QUALITY_THRESHOLD:
            logger.warning(
                f"🔴 PROMPT RUIDOSO seleccionado | quality={quality_score:.2f} "
                f"(umbral={NOISY_QUALITY_THRESHOLD}) | format={format_type} | template={template_file}"
            )
        elif quality_score < CLEAN_QUALITY_THRESHOLD:
            logger.info(
                f"🟡 PROMPT INTERMEDIO seleccionado | quality={quality_score:.2f} "
                f"(umbrales={NOISY_QUALITY_THRESHOLD}-{CLEAN_QUALITY_THRESHOLD}) | format={format_type} | template={template_file}"
            )
        else:
            logger.info(
                f"🟢 PROMPT LIMPIO seleccionado  | quality={quality_score:.2f} "
                f"(umbral={CLEAN_QUALITY_THRESHOLD}) | format={format_type} | template={template_file}"
            )

        return system_prompt, user_prompt, template_file

    def estimate_prompt_tokens(self, quality_score: float = 0.0) -> int:
        """
        Estima los tokens del prompt para el cálculo de costo previo.
        Se basa en el tamaño aproximado de los archivos de template.
        """
        try:
            system_size = len(_load_prompt("base_system.txt"))
            if quality_score < NOISY_QUALITY_THRESHOLD:
                template_file = "extraction_noisy.txt"
            elif quality_score < CLEAN_QUALITY_THRESHOLD:
                template_file = "extraction_intermediate.txt"
            else:
                template_file = "extraction_clean.txt"
            template_size = len(_load_prompt(template_file))
            # Aproximación: 1 token ≈ 4 caracteres
            return (system_size + template_size) // 4
        except Exception:
            return 1200  # Fallback conservador


# Instancia singleton
prompt_builder = PromptBuilder()
