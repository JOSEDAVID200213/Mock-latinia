"""
Modelos Pydantic para validación y serialización de datos.
Define los schemas para requests, responses, y estructuras internas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class FileFormat(str, Enum):
    TXT = "txt"
    MD = "md"
    DOCX = "docx"
    PDF = "pdf"
    RTF = "rtf"


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    ESTIMATING = "estimating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Extracción de texto ---

class ExtractionResult(BaseModel):
    """Resultado del pipeline de extracción de texto."""
    text: str
    format_detected: FileFormat
    char_count: int
    word_count: int
    estimated_tokens: int
    quality_score: float = Field(ge=0.0, le=1.0, description="0=basura, 1=texto perfecto")
    extraction_warnings: list[str] = []
    extraction_method: str = ""


# --- Estimación de costos ---

class CostEstimate(BaseModel):
    """Estimación del costo de procesamiento con el LLM."""
    input_tokens: int
    prompt_tokens: int
    estimated_output_tokens: int = 1000
    total_estimated_tokens: int
    estimated_cost_usd: float
    model_used: str
    is_free_tier: bool = True


# --- Resumen de reunión ---

class TaskItem(BaseModel):
    """Una tarea pendiente identificada en la reunión."""
    task: str
    responsible: Optional[str] = None
    deadline: Optional[str] = None


class MeetingSummary(BaseModel):
    """Resumen estructurado generado por el LLM."""
    meeting_name: str
    date_detected: Optional[str] = None
    participants: list[str] = []
    meeting_objective: Optional[str] = None
    topics_discussed: list[str] = []
    decisions_made: list[str] = []
    pending_tasks: list[TaskItem] = []
    risks_and_blockers: list[str] = []
    next_steps: list[str] = []
    executive_summary: str = ""
    doc_url: Optional[str] = None


# --- Metadata de procesamiento ---

class SourceFileInfo(BaseModel):
    """Información del archivo original subido."""
    original_name: str
    format: FileFormat
    size_bytes: int
    mime_type: str


class ExtractionMetadata(BaseModel):
    """Metadata del proceso de extracción."""
    method: str
    quality_score: float
    char_count: int
    word_count: int
    warnings: list[str] = []


class ProcessingMetadata(BaseModel):
    """Metadata completa del procesamiento."""
    model: str
    prompt_template: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    processing_time_seconds: float
    is_free_tier: bool = True


class MeetingRecord(BaseModel):
    """Registro completo de una reunión procesada."""
    meeting_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    meeting_name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    source_file: Optional[SourceFileInfo] = None
    extraction: Optional[ExtractionMetadata] = None
    processing: Optional[ProcessingMetadata] = None
    summary: Optional[MeetingSummary] = None


# --- API Responses ---

class UploadResponse(BaseModel):
    """Respuesta tras subir un archivo."""
    meeting_id: str
    meeting_name: str
    file_info: SourceFileInfo
    extraction: ExtractionResult
    cost_estimate: CostEstimate
    text_preview: str = Field(description="Primeros 500 chars del texto extraído")


class ProcessResponse(BaseModel):
    """Respuesta tras procesar con el LLM."""
    meeting_id: str
    meeting_name: str
    summary: MeetingSummary
    processing: ProcessingMetadata
    cost: CostEstimate


class MeetingListItem(BaseModel):
    """Item resumido para la lista de reuniones."""
    meeting_id: str
    meeting_name: str
    created_at: str
    status: ProcessingStatus
    file_format: Optional[FileFormat] = None
    file_size_bytes: Optional[int] = None


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada."""
    error: str
    detail: Optional[str] = None
    code: str = "UNKNOWN_ERROR"
