"""
Configuración centralizada del sistema.
Carga variables de entorno y define constantes del proyecto.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- Rutas del proyecto ---
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = Path(os.getenv("LOCAL_STORAGE_PATH", str(BASE_DIR / "storage")))
PROMPTS_DIR = BASE_DIR / "app" / "prompts"

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096"))

# --- Storage ---
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # "local" | "gdrive"

# Google Drive (fase 2)
GDRIVE_CREDENTIALS_PATH = os.getenv("GDRIVE_CREDENTIALS_PATH", "")
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")

# Google Drive / Apps Script
APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "")

# --- Archivos ---
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf", ".rtf"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/pdf",
    "application/rtf",
    "text/rtf",
    # Algunos sistemas reportan estos MIME types alternativos
    "application/x-rtf",
    "application/msword",
}

# --- CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# --- Costos estimados (por 1M tokens, Gemini 2.0 Flash) ---
COST_PER_1M_INPUT_TOKENS = 0.10   # USD
COST_PER_1M_OUTPUT_TOKENS = 0.40  # USD
FREE_TIER_DAILY_LIMIT = 1500      # requests/día
FREE_TIER_TOKEN_LIMIT = 1_000_000  # tokens/minuto
