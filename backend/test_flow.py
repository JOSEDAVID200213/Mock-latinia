import asyncio
import os
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from app.main import app
from app.config import STORAGE_DIR

# Limpiar storage para la prueba
if STORAGE_DIR.exists():
    shutil.rmtree(STORAGE_DIR)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

client = TestClient(app)

# JSON de respuesta simulada por Gemini basado en el nuevo prompt
mock_llm_response = {
    "metadata": {
        "nombre_reunion": "Reunión de prueba Mock",
        "categoria_sugerida": "Reunión de seguimiento",
        "fecha": "2026-06-16",
        "hora_inicio": "10:00",
        "duracion_minutos": 30,
        "idioma_detectado": "es",
        "calidad_transcripcion": "alta"
    },
    "participantes": [
        {"nombre": "María", "rol": "Organizador"},
        {"nombre": "Juan", "rol": "Participante"},
        {"nombre": "Ana", "rol": "Participante"}
    ],
    "contenido": {
        "objetivo_principal": "Revisar Q3 y contrataciones",
        "resumen_ejecutivo": "Se revisaron los ingresos del Q3 que subieron un 10%. Se decidió abrir una vacante para el equipo de ventas mañana.",
        "temas_discutidos": [
            {"tema": "Ingresos Q3", "resumen": "Aumento del 10%"}
        ]
    },
    "decisiones": [
        {"descripcion": "Abrir vacante para ventas", "tomada_por": "María", "fecha_efectiva": "2026-06-17"}
    ],
    "tareas_pendientes": [
        {"descripcion": "Enviar reporte final", "responsable": "Juan", "fecha_vencimiento": "2026-06-19", "prioridad": "Alta"}
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
        self.usage_metadata = MagicMock(prompt_token_count=100, candidates_token_count=150)

def mock_generate_content(*args, **kwargs):
    return MockResponse(json.dumps(mock_llm_response))

print("Iniciando pruebas con LLM Mockeado...")

# Parcheamos genai en el servicio
with patch('app.services.llm_service.genai.GenerativeModel.generate_content', side_effect=mock_generate_content):
    
    # 1. Prueba: Conversación
    print("\n--- PRUEBA 1: Conversación ---")
    conv_text = """
    [10:00:00] María: Buenos días, vamos a revisar el Q3.
    [10:01:00] Juan: Los ingresos subieron 10%.
    [10:02:00] María: Excelente. Juan, ¿puedes enviar el reporte final el viernes?
    [10:02:30] Juan: Sí, lo tengo listo.
    [10:03:00] Ana: También necesitamos decidir si contratamos a alguien más para ventas.
    [10:04:00] María: Decidido, abriremos la vacante mañana.
    """
    with open("test_conv.txt", "w", encoding="utf-8") as f:
        f.write(conv_text)

    with open("test_conv.txt", "rb") as f:
        resp1 = client.post("/api/meetings/upload", data={"meeting_name": "Reunión Q3"}, files={"file": ("test_conv.txt", f, "text/plain")})

    assert resp1.status_code == 200, f"Upload failed: {resp1.text}"
    meeting_id_1 = resp1.json()["meeting_id"]

    resp1_process = client.post(f"/api/meetings/process/{meeting_id_1}")
    assert resp1_process.status_code == 200, f"Process failed: {resp1_process.text}"
    print("Conversación procesada OK.")
    print("Resumen aplanado generado:")
    print(json.dumps(resp1_process.json()["summary"], indent=2, ensure_ascii=False))

    # 3. Prueba: Archivo corrupto/vacío
    print("\n--- PRUEBA 3: Archivo casi vacío ---")
    empty_text = "hola mundo"
    with open("test_empty.txt", "w", encoding="utf-8") as f:
        f.write(empty_text)

    with open("test_empty.txt", "rb") as f:
        resp3 = client.post("/api/meetings/upload", data={"meeting_name": "Vacía"}, files={"file": ("test_empty.txt", f, "text/plain")})

    print(f"Status esperado 422, obtenido: {resp3.status_code}")
    print(f"Mensaje de error interceptado: {resp3.json().get('detail')}")

    # Verificar persistencia doble
    print("\n--- VERIFICACIÓN DE PERSISTENCIA ---")
    p = STORAGE_DIR / "meetings" / meeting_id_1
    files = [f.name for f in p.iterdir() if f.is_file()]
    print(f"Archivos en meeting {meeting_id_1}: {files}")
    assert any(f.startswith("original") for f in files), "Original file missing"
    assert "summary.json" in files, "Summary JSON missing"
    assert "extracted_text.txt" in files, "Extracted text missing"

print("\nTodo funcionando correctamente.")
