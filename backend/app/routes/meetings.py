"""
Endpoints de la API para gestión de reuniones.
Maneja upload, análisis, procesamiento, listado y descarga.
"""
from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from app.config import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from app.models.schemas import (
    CostEstimate,
    ErrorResponse,
    ExtractionMetadata,
    MeetingListItem,
    MeetingRecord,
    ProcessingStatus,
    ProcessResponse,
    ProcessStartedResponse,
    SourceFileInfo,
    UploadResponse,
)
from app.services.cost_estimator import cost_estimator
from app.services.file_extractor import ExtractionError, file_extractor
from app.services.llm_service import LLMError, get_llm_service
from app.services.prompt_builder import prompt_builder
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

# Store temporal para datos de sesión (en producción sería Redis/DB)
_session_data: dict[str, dict] = {}


@router.post("/upload", response_model=UploadResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    meeting_name: str = Form(...),
):
    """
    Fase 1: Sube un archivo, extrae texto, y devuelve estimación de costo.
    El usuario ve el resultado antes de confirmar el procesamiento con LLM.
    """
    # --- Validación del archivo ---
    if not file.filename:
        raise HTTPException(400, detail="No se recibió un archivo.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            detail=f"Formato '{extension}' no soportado. "
            f"Formatos válidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            413,
            detail=f"Archivo demasiado grande ({len(content) / 1024 / 1024:.1f}MB). "
            f"Máximo permitido: {MAX_FILE_SIZE_MB}MB.",
        )

    if len(content) == 0:
        raise HTTPException(400, detail="El archivo está vacío.")

    # --- Guardar temporalmente ---
    meeting_id = str(uuid.uuid4())

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # --- Extraer texto ---
        extraction = file_extractor.extract(tmp_path, file.filename)

        # --- Estimar costo ---
        prompt_tokens = prompt_builder.estimate_prompt_tokens(extraction.quality_score)
        cost = cost_estimator.estimate(
            text_tokens=extraction.estimated_tokens,
            prompt_tokens=prompt_tokens,
        )

        # --- Guardar en storage ---
        storage = get_storage_service()
        storage.save_original_file(meeting_id, tmp_path, extension, meeting_name=meeting_name.strip())
        storage.save_text(meeting_id, "extracted_text.txt", extraction.text, meeting_name=meeting_name.strip())

        # Crear y guardar metadata inicial
        file_info = SourceFileInfo(
            original_name=file.filename,
            format=extraction.format_detected,
            size_bytes=len(content),
            mime_type=file.content_type or "application/octet-stream",
        )

        record = MeetingRecord(
            meeting_id=meeting_id,
            meeting_name=meeting_name.strip(),
            status=ProcessingStatus.EXTRACTED,
            source_file=file_info,
            extraction=ExtractionMetadata(
                method=extraction.extraction_method,
                quality_score=extraction.quality_score,
                char_count=extraction.char_count,
                word_count=extraction.word_count,
                warnings=extraction.extraction_warnings,
            ),
        )

        storage.save_json(meeting_id, "metadata.json", record.model_dump(), meeting_name=meeting_name.strip())

        # Guardar datos de sesión para la fase 2
        _session_data[meeting_id] = {
            "text": extraction.text,
            "quality_score": extraction.quality_score,
            "format": extraction.format_detected.value,
            "meeting_name": meeting_name.strip(),
        }

        # Preparar preview del texto
        text_preview = extraction.text[:500]
        if len(extraction.text) > 500:
            text_preview += "..."

        return UploadResponse(
            meeting_id=meeting_id,
            meeting_name=meeting_name.strip(),
            file_info=file_info,
            extraction=extraction,
            cost_estimate=cost,
            text_preview=text_preview,
        )

    except ExtractionError as e:
        raise HTTPException(422, detail=str(e))
    except Exception as e:
        logger.error(f"Error en upload: {e}", exc_info=True)
        raise HTTPException(500, detail=f"Error interno al procesar el archivo: {str(e)}")
    finally:
        # Limpiar archivo temporal
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

def _process_meeting_bg(meeting_id: str, session: dict):
    """
    Worker en segundo plano para procesar la reunión con LLM de manera asíncrona.
    """
    storage = get_storage_service()
    record = storage.get_meeting(meeting_id)
    if not record:
        logger.error(f"Error BG Task: Meeting metadata not found para {meeting_id}")
        return

    try:
        # Construir prompt adaptativo
        system_prompt, user_prompt, template_name = prompt_builder.build(
            transcript_text=session["text"],
            quality_score=session["quality_score"],
            format_type=session["format"],
            meeting_name=session["meeting_name"],
        )

        # Generar resumen con LLM
        llm = get_llm_service()
        summary, processing_meta = llm.generate_summary(
            meeting_id=meeting_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            template_name=template_name,
            meeting_name=session["meeting_name"],
        )

        # Guardar resumen
        storage.save_json(meeting_id, "summary.json", summary.model_dump(), meeting_name=session["meeting_name"])

        # Actualizar metadata final
        cost = cost_estimator.estimate(
            text_tokens=processing_meta.input_tokens,
            prompt_tokens=0,
            estimated_output_tokens=processing_meta.output_tokens,
        )

        record.status = ProcessingStatus.COMPLETED
        record.processing = processing_meta
        record.summary = summary
        storage.save_json(meeting_id, "metadata.json", record.model_dump(), meeting_name=session["meeting_name"])
        logger.info(f"BG Task Completa para meeting {meeting_id}")

    except Exception as e:
        logger.error(f"Error procesando reunión en background {meeting_id}: {e}", exc_info=True)
        record.status = ProcessingStatus.FAILED
        storage.save_json(meeting_id, "metadata.json", record.model_dump())

@router.post("/process/{meeting_id}", response_model=ProcessStartedResponse)
async def process_meeting(meeting_id: str, background_tasks: BackgroundTasks):
    """
    Fase 2: Encola el procesamiento con LLM en segundo plano y retorna inmediatamente.
    """
    # Verificar que la reunión existe y tiene datos de sesión
    session = _session_data.get(meeting_id)
    if not session:
        # Intentar cargar desde storage
        storage = get_storage_service()
        if not storage.meeting_exists(meeting_id):
            raise HTTPException(404, detail="Reunión no encontrada.")

        try:
            text = storage.load_text(meeting_id, "extracted_text.txt")
            record = storage.get_meeting(meeting_id)
            if not record:
                raise HTTPException(404, detail="Metadata de reunión no encontrada.")

            session = {
                "text": text,
                "quality_score": record.extraction.quality_score if record.extraction else 0.8,
                "format": record.source_file.format.value if record.source_file else "txt",
                "meeting_name": record.meeting_name,
            }
        except FileNotFoundError:
            raise HTTPException(404, detail="Texto extraído no encontrado. Sube el archivo de nuevo.")

    storage = get_storage_service()

    # Actualizar estado
    record = storage.get_meeting(meeting_id)
    if record:
        record.status = ProcessingStatus.PROCESSING
        storage.save_json(meeting_id, "metadata.json", record.model_dump())

    # Limpiar datos de sesión ya que pasamos el diccionario completo al hilo background
    _session_data.pop(meeting_id, None)

    # Añadir a las tareas en segundo plano
    background_tasks.add_task(_process_meeting_bg, meeting_id, session)

    return ProcessStartedResponse(
        meeting_id=meeting_id,
        message="El procesamiento ha iniciado en segundo plano.",
        status=ProcessingStatus.PROCESSING
    )


@router.get("/", response_model=list[MeetingListItem])
async def list_meetings():
    """Lista todas las reuniones procesadas."""
    storage = get_storage_service()
    return storage.list_meetings()


@router.get("/formats/supported")
async def get_supported_formats():
    """Retorna los formatos de archivo soportados y sus características."""
    return {
        "formats": [
            {"extension": ".txt", "name": "Texto plano", "complexity": "low", "cost_factor": 1.0},
            {"extension": ".md", "name": "Markdown", "complexity": "low", "cost_factor": 1.0},
            {"extension": ".docx", "name": "Microsoft Word", "complexity": "medium", "cost_factor": 1.1},
            {"extension": ".pdf", "name": "PDF", "complexity": "medium", "cost_factor": 1.2},
            {"extension": ".rtf", "name": "Rich Text Format", "complexity": "medium", "cost_factor": 1.1},
            {"extension": ".xlsx", "name": "Microsoft Excel", "complexity": "medium", "cost_factor": 1.1},
            {"extension": ".pptx", "name": "Microsoft PowerPoint", "complexity": "medium", "cost_factor": 1.1},
            {"extension": ".csv", "name": "Valores separados por comas", "complexity": "low", "cost_factor": 1.0},
            {"extension": ".html", "name": "Página Web (HTML)", "complexity": "low", "cost_factor": 1.0},
        ],
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Obtiene el detalle completo de una reunión."""
    storage = get_storage_service()
    record = storage.get_meeting(meeting_id)
    if not record:
        raise HTTPException(404, detail="Reunión no encontrada.")
    return record


@router.get("/{meeting_id}/download/{format}")
async def download_summary(meeting_id: str, format: str):
    """Descarga el resumen en el formato especificado (json o html)."""
    storage = get_storage_service()

    if format not in ("json", "html"):
        raise HTTPException(400, detail="Formato de descarga no válido. Usa 'json' o 'html'.")

    filename = f"summary.{format}"
    file_path = storage.get_file_path(meeting_id, filename)

    if not file_path:
        raise HTTPException(404, detail=f"Resumen en formato {format} no encontrado.")

    media_type = "application/json" if format == "json" else "text/html"
    record = storage.get_meeting(meeting_id)
    download_name = f"resumen_{record.meeting_name if record else meeting_id}.{format}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=download_name,
    )


def _generate_summary_html(summary) -> str:
    """Genera un HTML limpio y profesional del resumen."""
    tasks_html = ""
    for task in summary.pending_tasks:
        responsible = f" — <em>{task.responsible}</em>" if task.responsible else ""
        deadline = f" (Plazo: {task.deadline})" if task.deadline else ""
        tasks_html += f"<li>{task.task}{responsible}{deadline}</li>\n"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resumen: {summary.meeting_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #1a1a2e; max-width: 800px; margin: 0 auto; padding: 2rem; background: #f8f9fa; }}
        h1 {{ color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 0.5rem; margin-bottom: 1.5rem; font-size: 1.8rem; }}
        h2 {{ color: #0f3460; margin: 1.5rem 0 0.75rem; font-size: 1.2rem; }}
        .meta {{ background: #e8eaf6; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; }}
        .meta span {{ margin-right: 2rem; }}
        .executive {{ background: #fff3e0; padding: 1.25rem; border-radius: 8px; border-left: 4px solid #ff9800; margin: 1rem 0; }}
        ul, ol {{ padding-left: 1.5rem; }}
        li {{ margin: 0.4rem 0; }}
        .section {{ background: white; padding: 1.25rem; border-radius: 8px; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .risks {{ border-left: 4px solid #e74c3c; }}
        .decisions {{ border-left: 4px solid #27ae60; }}
        .tasks {{ border-left: 4px solid #3498db; }}
        .footer {{ text-align: center; color: #888; margin-top: 2rem; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <h1>📋 {summary.meeting_name}</h1>

    <div class="meta">
        {f'<span>📅 <strong>Fecha:</strong> {summary.date_detected}</span>' if summary.date_detected else ''}
        <span>👥 <strong>Participantes:</strong> {", ".join(summary.participants) if summary.participants else "No especificados"}</span>
    </div>

    {f'<div class="section"><h2>🎯 Objetivo</h2><p>{summary.meeting_objective}</p></div>' if summary.meeting_objective else ''}

    <div class="executive">
        <h2>📝 Resumen Ejecutivo</h2>
        <p>{summary.executive_summary}</p>
    </div>

    {'<div class="section"><h2>💬 Temas Discutidos</h2><ul>' + "".join(f"<li>{t}</li>" for t in summary.topics_discussed) + '</ul></div>' if summary.topics_discussed else ''}

    {'<div class="section decisions"><h2>✅ Decisiones Tomadas</h2><ul>' + "".join(f"<li>{d}</li>" for d in summary.decisions_made) + '</ul></div>' if summary.decisions_made else ''}

    {'<div class="section tasks"><h2>📌 Tareas Pendientes</h2><ul>' + tasks_html + '</ul></div>' if summary.pending_tasks else ''}

    {'<div class="section risks"><h2>⚠️ Riesgos y Bloqueos</h2><ul>' + "".join(f"<li>{r}</li>" for r in summary.risks_and_blockers) + '</ul></div>' if summary.risks_and_blockers else ''}

    {'<div class="section"><h2>➡️ Próximos Pasos</h2><ol>' + "".join(f"<li>{s}</li>" for s in summary.next_steps) + '</ol></div>' if summary.next_steps else ''}

    <div class="footer">
        <p>Generado automáticamente por Meeting Summary AI</p>
    </div>
</body>
</html>"""
