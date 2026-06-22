"""
Pipeline de extracción de texto multi-formato usando MarkItDown.
Soporta múltiples formatos con evaluación de calidad y conversión nativa a Markdown.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from markitdown import MarkItDown

from app.models.schemas import ExtractionResult, FileFormat

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Error durante la extracción de texto."""
    pass


class FileExtractor:
    """
    Extrae texto de diferentes formatos de archivo convirtiéndolos a Markdown.
    Evalúa la calidad del texto extraído para adaptar el prompt del LLM.
    """

    EXTENSION_MAP = {
        ".txt": FileFormat.TXT,
        ".md": FileFormat.MD,
        ".docx": FileFormat.DOCX,
        ".pdf": FileFormat.PDF,
        ".rtf": FileFormat.RTF,
        ".xlsx": FileFormat.XLSX,
        ".pptx": FileFormat.PPTX,
        ".csv": FileFormat.CSV,
        ".html": FileFormat.HTML,
    }

    def __init__(self):
        self.md_converter = MarkItDown()

    def extract(self, file_path: Path, original_filename: str) -> ExtractionResult:
        """
        Extrae texto del archivo y evalúa su calidad.
        
        Args:
            file_path: Ruta al archivo temporal subido
            original_filename: Nombre original del archivo
            
        Returns:
            ExtractionResult con texto, metadata y score de calidad
        """
        extension = Path(original_filename).suffix.lower()
        file_format = self.EXTENSION_MAP.get(extension)

        if not file_format:
            raise ExtractionError(
                f"Formato no soportado: '{extension}'. "
                f"Formatos válidos: {', '.join(self.EXTENSION_MAP.keys())}"
            )

        warnings = []
        try:
            result = self.md_converter.convert(str(file_path))
            text = result.text_content
            method_name = "markitdown"
        except Exception as e:
            raise ExtractionError(f"Error inesperado al extraer texto con MarkItDown: {str(e)}")

        # Limpiar texto
        text = self._clean_text(text)

        if not text or len(text.strip()) < 20:
            raise ExtractionError(
                "El archivo no contiene suficiente texto útil o está corrupto. "
                "Se requieren al menos ~20 caracteres de contenido."
            )

        # Evaluar calidad
        quality_score = self._evaluate_quality(text)
        word_count = len(text.split())

        return ExtractionResult(
            text=text,
            format_detected=file_format,
            char_count=len(text),
            word_count=word_count,
            estimated_tokens=self._estimate_tokens(text),
            quality_score=round(quality_score, 2),
            extraction_warnings=warnings,
            extraction_method=method_name,
        )

    # --- Utilidades ---

    def _clean_text(self, text: str) -> str:
        """Limpia el texto extraído de artefactos comunes."""
        # Remover caracteres de control excepto saltos de línea y tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # Colapsar múltiples líneas en blanco a máximo 2
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        # Remover espacios trailing
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    def _evaluate_quality(self, text: str) -> float:
        """
        Evalúa la calidad del texto en una escala 0-1.
        Factores: ratio de palabras válidas, longitud promedio, caracteres extraños.
        """
        if not text:
            return 0.0

        words = text.split()
        if len(words) < 10:
            return 0.3

        score = 1.0

        # Factor 1: Ratio de caracteres alfanuméricos vs total
        alnum_count = sum(1 for c in text if c.isalnum() or c.isspace() or c in ['#', '*', '-', '_', '`', '|'])
        alnum_ratio = alnum_count / len(text) if text else 0
        if alnum_ratio < 0.7:
            score -= 0.3

        # Factor 2: Longitud promedio de palabras (palabras muy cortas = OCR roto)
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 2.5:
            score -= 0.2
        elif avg_word_len > 15:
            score -= 0.1  # Palabras pegadas

        # Factor 3: Ratio de palabras con al menos 3 letras
        real_words = sum(1 for w in words if len(w) >= 3)
        real_word_ratio = real_words / len(words)
        if real_word_ratio < 0.5:
            score -= 0.2

        # Factor 4: Repeticiones excesivas (headers/footers de PDF)
        lines = text.split("\n")
        if len(lines) > 10:
            unique_lines = set(line.strip() for line in lines if line.strip())
            repetition_ratio = len(unique_lines) / len([l for l in lines if l.strip()])
            if repetition_ratio < 0.5:
                score -= 0.2

        return max(0.0, min(1.0, score))

    def _estimate_tokens(self, text: str) -> int:
        """
        Estima tokens de forma aproximada.
        Regla general: ~1 token por cada 4 caracteres en español/inglés.
        """
        return max(1, len(text) // 4)


# Instancia singleton
file_extractor = FileExtractor()
