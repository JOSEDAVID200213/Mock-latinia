"""
Estimador de costos de procesamiento.
Calcula tokens y costo estimado antes de llamar al LLM.
"""
from __future__ import annotations

from app.config import (
    COST_PER_1M_INPUT_TOKENS,
    COST_PER_1M_OUTPUT_TOKENS,
    FREE_TIER_DAILY_LIMIT,
    GEMINI_MODEL,
)
from app.models.schemas import CostEstimate


class CostEstimator:
    """Estima el costo de procesar una transcripción con Gemini."""

    def estimate(
        self,
        text_tokens: int,
        prompt_tokens: int,
        estimated_output_tokens: int = 1000,
    ) -> CostEstimate:
        """
        Calcula la estimación de costo.

        Args:
            text_tokens: Tokens del texto de la transcripción
            prompt_tokens: Tokens del prompt del sistema
            estimated_output_tokens: Tokens estimados de salida (~1000 para un resumen)

        Returns:
            CostEstimate con desglose completo
        """
        total_input = text_tokens + prompt_tokens
        total = total_input + estimated_output_tokens

        # Calcular costo
        input_cost = (total_input / 1_000_000) * COST_PER_1M_INPUT_TOKENS
        output_cost = (estimated_output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        return CostEstimate(
            input_tokens=text_tokens,
            prompt_tokens=prompt_tokens,
            estimated_output_tokens=estimated_output_tokens,
            total_estimated_tokens=total,
            estimated_cost_usd=round(total_cost, 6),
            model_used=GEMINI_MODEL,
            is_free_tier=True,  # Free tier con Gemini Flash
        )


# Instancia singleton
cost_estimator = CostEstimator()
