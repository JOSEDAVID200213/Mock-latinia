import os
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.config import STORAGE_DIR
from app.services.file_extractor import FileExtractor

# Directorio de datos de prueba
TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

client = TestClient(app)

# JSON de respuesta simulada por Gemini basado en el nuevo prompt
mock_llm_response = {
    "metadata": {
        "nombre_reunion": "Reunión de concejo de Long Beach (Prueba)",
        "categoria_sugerida": "Concejo Municipal",
        "fecha": "2026-06-17",
        "hora_inicio": "17:00",
        "duracion_minutos": 90,
        "idioma_detectado": "en",
        "calidad_transcripcion": "alta"
    },
    "participantes": [
        {"nombre": "Mayor", "rol": "Alcalde"},
        {"nombre": "Councilmember", "rol": "Miembro del Concejo"}
    ],
    "contenido": {
        "objetivo_principal": "Discutir resoluciones de la ciudad",
        "resumen_ejecutivo": "Se discutieron varios puntos del concejo incluyendo presupuestos y permisos de zonificación.",
        "temas_discutidos": [
            {"tema": "Presupuesto", "resumen": "Aprobación de enmiendas presupuestarias"}
        ]
    },
    "decisiones": [
        {"descripcion": "Aprobación de la resolución 22-0511", "tomada_por": "Mayor", "fecha_efectiva": "2026-06-17"}
    ],
    "tareas_pendientes": [
        {"descripcion": "Publicar enmiendas en el sitio web de la ciudad", "responsable": "City Clerk", "fecha_vencimiento": "2026-06-20", "prioridad": "Alta"}
    ],
    "riesgos_bloqueos": [],
    "proxima_reunion": {
        "fecha_tentativa": None,
        "tema_tentativo": None
    },
    "notas_adicionales": None
}

class MockResponse:
    def __init__(self, text):
        self.text = text
        self.usage_metadata = MagicMock(prompt_token_count=1000, candidates_token_count=1500)

def mock_generate_content(*args, **kwargs):
    return MockResponse(json.dumps(mock_llm_response))

def setup_module(module):
    """Limpia y crea directorios de prueba si es necesario."""
    if STORAGE_DIR.exists():
        shutil.rmtree(STORAGE_DIR)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def test_file_extractor_on_meetingbank():
    """Verifica que el FileExtractor puede procesar las transcripciones de MeetingBank."""
    # Buscar archivos de transcripción disponibles
    transcript_files = list(TEST_DATA_DIR.glob("*_transcript.txt"))
    assert len(transcript_files) > 0, "No se encontraron archivos de transcripción para probar."
    
    extractor = FileExtractor()
    
    # Probar con los primeros 3 archivos para no tardar demasiado
    for file_path in transcript_files[:3]:
        result = extractor.extract(file_path, file_path.name)
        
        assert result.text is not None
        assert len(result.text) > 20
        assert result.char_count > 0
        assert result.word_count > 0
        assert result.quality_score >= 0.0
        assert result.quality_score <= 1.0
        print(f"\nArchivo: {file_path.name}")
        print(f"  Caracteres: {result.char_count}, Calidad: {result.quality_score}")

def test_upload_and_process_meetingbank_pipeline():
    """Prueba el pipeline completo (subida y procesamiento) con una transcripción real mockeada."""
    transcript_files = list(TEST_DATA_DIR.glob("*_transcript.txt"))
    assert len(transcript_files) > 0, "No se encontraron archivos de transcripción para probar."
    
    test_file = transcript_files[0]
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/meetings/upload", 
            data={"meeting_name": "Test MeetingBank"}, 
            files={"file": (test_file.name, f, "text/plain")}
        )
        
    assert response.status_code == 200, f"Upload fallido: {response.text}"
    meeting_id = response.json()["meeting_id"]
    
    # Parchear el servicio de LLM para evitar llamadas reales a la API de Gemini
    with patch('app.services.llm_service.genai.GenerativeModel.generate_content', side_effect=mock_generate_content):
        process_response = client.post(f"/api/meetings/process/{meeting_id}")
        assert process_response.status_code == 200, f"Procesamiento fallido: {process_response.text}"
        
        data = process_response.json()
        assert "summary" in data
        assert data["summary"]["meeting_name"] == "Reunión de concejo de Long Beach (Prueba)"
        
        # Verificar persistencia en el almacenamiento local
        meeting_storage_path = STORAGE_DIR / "meetings" / meeting_id
        assert meeting_storage_path.exists()
        assert (meeting_storage_path / "metadata.json").exists()
        assert (meeting_storage_path / "summary.json").exists()
        assert (meeting_storage_path / "extracted_text.txt").exists()
        
        # El archivo original guardado debe ser de tipo .txt
        original_files = list(meeting_storage_path.glob("original.txt"))
        assert len(original_files) == 1

if __name__ == "__main__":
    setup_module(None)
    print("Ejecutando test_file_extractor_on_meetingbank...")
    test_file_extractor_on_meetingbank()
    print("Ejecutando test_upload_and_process_meetingbank_pipeline...")
    test_upload_and_process_meetingbank_pipeline()
    print("¡Todas las pruebas locales de MeetingBank pasaron con éxito!")
