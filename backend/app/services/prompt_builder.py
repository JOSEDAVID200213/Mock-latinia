"""
Constructor de prompts adaptativo.
Selecciona y construye el prompt apropiado según la calidad del texto.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.config import PROMPTS_DIR

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Construye prompts adaptativos basados en la calidad del texto extraído.
    Calidad alta (>= 0.7) → prompt limpio (menos tokens)
    Calidad baja (< 0.7) → prompt con instrucciones de limpieza (más tokens)
    """

    QUALITY_THRESHOLD = 0.7

    def __init__(self):
        self._cache: dict[str, str] = {}

    def _load_template(self, filename: str) -> str:
        """Carga un template de prompt desde disco con caché."""
        if filename not in self._cache:
            path = PROMPTS_DIR / filename
            if not path.exists():
                raise FileNotFoundError(f"Template de prompt no encontrado: {path}")
            self._cache[filename] = path.read_text(encoding="utf-8")
        return self._cache[filename]

    def build(
        self,
        transcript_text: str,
        quality_score: float,
        format_type: str = "desconocido",
        meeting_name: str = "",
    ) -> tuple[str, str, str]:
        """
        Construye el prompt completo adaptado a la calidad del texto.

        Args:
            transcript_text: Texto extraído de la transcripción
            quality_score: Score de calidad (0-1)
            format_type: Formato del archivo original
            meeting_name: Nombre de la reunión

        Returns:
            Tuple de (system_prompt, user_prompt, template_name)
        """
        # Cargar prompt base del sistema
        system_prompt = self._load_template("base_system.txt")

        # Seleccionar template según calidad
        if quality_score >= self.QUALITY_THRESHOLD:
            template_name = "extraction_clean"
            user_template = self._load_template("extraction_clean.txt")
            user_prompt = user_template + transcript_text
        else:
            template_name = "extraction_noisy"
            user_template = self._load_template("extraction_noisy.txt")
            # Inyectar tipo de formato en las instrucciones
            user_template = user_template.replace("{format_type}", format_type)
            user_prompt = user_template + transcript_text

        logger.info(
            f"Prompt construido: template={template_name}, "
            f"quality={quality_score:.2f}, format={format_type}"
        )

        return system_prompt, user_prompt, template_name

    def estimate_prompt_tokens(self, quality_score: float) -> int:
        """
        Estima los tokens del prompt (sin contar la transcripción).
        Útil para el pre-cálculo de costos.
        """
        if quality_score >= self.QUALITY_THRESHOLD:
            # Prompt limpio: ~800 tokens
            return 800
        else:
            # Prompt con instrucciones extra: ~1200 tokens
            return 1200


# Instancia singleton
prompt_builder = PromptBuilder()
