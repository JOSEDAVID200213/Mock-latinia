"""
Servicio de almacenamiento con abstracción para múltiples backends.
Implementación actual: LocalStorage (desarrollo).
Fase 2: GoogleDriveStorage (producción/oficina).
"""
from __future__ import annotations

import json
import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
from io import BytesIO

from app.config import (
    STORAGE_BACKEND,
    STORAGE_DIR,
    GDRIVE_CREDENTIALS_PATH,
    GDRIVE_FOLDER_ID,
)
from app.models.schemas import MeetingListItem, MeetingRecord, ProcessingStatus

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Interfaz abstracta para backends de almacenamiento."""

    @abstractmethod
    def save_original_file(self, meeting_id: str, file_path: Path, extension: str, meeting_name: str | None = None) -> str:
        """Guarda el archivo original. Retorna la ruta/URL del archivo guardado."""
        ...

    @abstractmethod
    def save_text(self, meeting_id: str, filename: str, content: str, meeting_name: str | None = None) -> str:
        """Guarda un archivo de texto."""
        ...

    @abstractmethod
    def save_json(self, meeting_id: str, filename: str, data: dict, meeting_name: str | None = None) -> str:
        """Guarda un archivo JSON."""
        ...

    @abstractmethod
    def save_google_doc(self, meeting_id: str, title: str, content: str, meeting_name: str | None = None) -> str:
        """Crea un Google Docs con el contenido de texto y devuelve la URL del documento."""
        ...

    @abstractmethod
    def load_json(self, meeting_id: str, filename: str) -> dict:
        """Carga un archivo JSON."""
        ...

    @abstractmethod
    def load_text(self, meeting_id: str, filename: str) -> str:
        """Carga un archivo de texto."""
        ...

    @abstractmethod
    def list_meetings(self) -> list[MeetingListItem]:
        """Lista todas las reuniones almacenadas."""
        ...

    @abstractmethod
    def get_meeting(self, meeting_id: str) -> MeetingRecord | None:
        """Obtiene el registro completo de una reunión."""
        ...

    @abstractmethod
    def meeting_exists(self, meeting_id: str) -> bool:
        """Verifica si existe una reunión."""
        ...

    @abstractmethod
    def get_file_path(self, meeting_id: str, filename: str) -> Path | None:
        ...

    @abstractmethod
    def save_binary(self, meeting_id: str, filename: str, content: bytes, meeting_name: str | None = None) -> str:
        """Guarda un archivo binario."""
        ...


class LocalStorage(StorageBackend):
    """
    Almacenamiento local en sistema de archivos.
    Estructura: storage/meetings/{meeting_id}/
    """

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or STORAGE_DIR / "meetings"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage inicializado en: {self.base_dir}")

    def _meeting_dir(self, meeting_id: str) -> Path:
        """Obtiene/crea el directorio de una reunión."""
        meeting_dir = self.base_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)
        return meeting_dir

    def save_original_file(self, meeting_id: str, file_path: Path, extension: str, meeting_name: str | None = None) -> str:
        dest = self._meeting_dir(meeting_id) / f"original{extension}"
        shutil.copy2(str(file_path), str(dest))
        logger.info(f"Archivo original guardado: {dest}")
        return str(dest)

    def save_text(self, meeting_id: str, filename: str, content: str, meeting_name: str | None = None) -> str:
        dest = self._meeting_dir(meeting_id) / filename
        dest.write_text(content, encoding="utf-8")
        return str(dest)

    def save_json(self, meeting_id: str, filename: str, data: dict, meeting_name: str | None = None) -> str:
        dest = self._meeting_dir(meeting_id) / filename
        dest.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(dest)

    def save_binary(self, meeting_id: str, filename: str, content: bytes, meeting_name: str | None = None) -> str:
        """Guarda contenido binario (p.ej., .docx) en el directorio de la reunión.
        Retorna la ruta del archivo guardado."""
        dest = self._meeting_dir(meeting_id) / filename
        with open(dest, "wb") as f:
            f.write(content)
        return str(dest)

    def save_google_doc(self, meeting_id: str, title: str, content: str, meeting_name: str | None = None) -> str:
        """Guarda un documento usando Google Apps Script si está configurado, o localmente."""
        # Guardar copia local de respaldo
        dest = self._meeting_dir(meeting_id) / f"{title}.gdoc.txt"
        dest.write_text(content, encoding="utf-8")
        
        from app.config import APPS_SCRIPT_URL
        if APPS_SCRIPT_URL:
            import requests
            try:
                response = requests.post(
                    APPS_SCRIPT_URL,
                    json={"title": title, "content": content},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                if "url" in data:
                    logger.info("Google Doc creado via Apps Script: %s", data["url"])
                    return data["url"]
            except Exception as e:
                logger.error("Error llamando a Apps Script: %s", e)
                
        return str(dest)

    def load_json(self, meeting_id: str, filename: str) -> dict:
        path = self._meeting_dir(meeting_id) / filename
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def load_text(self, meeting_id: str, filename: str) -> str:
        path = self._meeting_dir(meeting_id) / filename
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        return path.read_text(encoding="utf-8")

    def list_meetings(self) -> list[MeetingListItem]:
        meetings = []
        if not self.base_dir.exists():
            return meetings

        for meeting_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not meeting_dir.is_dir():
                continue

            metadata_path = meeting_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                record = MeetingRecord(**data)
                meetings.append(MeetingListItem(
                    meeting_id=record.meeting_id,
                    meeting_name=record.meeting_name,
                    created_at=record.created_at,
                    status=record.status,
                    file_format=record.source_file.format if record.source_file else None,
                    file_size_bytes=record.source_file.size_bytes if record.source_file else None,
                ))
            except Exception as e:
                logger.warning(f"Error leyendo metadata de {meeting_dir.name}: {e}")
                continue

        return meetings

    def get_meeting(self, meeting_id: str) -> MeetingRecord | None:
        metadata_path = self._meeting_dir(meeting_id) / "metadata.json"
        if not metadata_path.exists():
            return None
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            return MeetingRecord(**data)
        except Exception as e:
            logger.error(f"Error cargando meeting {meeting_id}: {e}")
            return None

    def meeting_exists(self, meeting_id: str) -> bool:
        return (self.base_dir / meeting_id / "metadata.json").exists()

    def get_file_path(self, meeting_id: str, filename: str) -> Path | None:
        path = self._meeting_dir(meeting_id) / filename
        return path if path.exists() else None

# Google Drive storage implementation
class GoogleDriveStorage(StorageBackend):
    """Backend that stores files in a shared Google Drive folder."""
    def __init__(self):
        creds_path = Path(GDRIVE_CREDENTIALS_PATH)
        if not creds_path.exists():
            raise FileNotFoundError(f"Google Drive credentials not found: {creds_path}")
        credentials = service_account.Credentials.from_service_account_file(str(creds_path))
        self.service = build('drive', 'v3', credentials=credentials)
        self.root_folder_id = GDRIVE_FOLDER_ID
        logger.info("GoogleDriveStorage initialized with root folder %s", self.root_folder_id)

    def _ensure_meeting_folder(self, meeting_id: str, meeting_name: str | None = None) -> str:
        """Return folder ID for meeting, create if needed."""
        query = f"mimeType='application/vnd.google-apps.folder' and name contains '{meeting_id}' and '{self.root_folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields='files(id, name)', pageSize=1).execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
        folder_name = f"{meeting_name} - {meeting_id}" if meeting_name else meeting_id
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.root_folder_id]
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        logger.info("Meeting folder '%s' created in Drive with id %s", folder_name, folder.get('id'))
        return folder.get('id')

    def _upload_file(self, meeting_id: str, filename: str, data: bytes, mime_type: str, meeting_name: str | None = None) -> dict:
        """Sube un archivo a Drive y devuelve el diccionario con id y webViewLink."""
        folder_id = self._ensure_meeting_folder(meeting_id, meeting_name)
        media = MediaIoBaseUpload(BytesIO(data), mimetype=mime_type, resumable=True)
        file_metadata = {'name': filename, 'parents': [folder_id]}
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        logger.info("Uploaded %s to Drive (id=%s)", filename, file.get('id'))
        return {'id': file.get('id'), 'webViewLink': file.get('webViewLink')}

    def save_original_file(self, meeting_id: str, file_path: Path, extension: str, meeting_name: str | None = None) -> str:
        content = file_path.read_bytes()
        result = self._upload_file(meeting_id, f"original{extension}", content, 'application/octet-stream', meeting_name)
        return result['webViewLink']

    def save_text(self, meeting_id: str, filename: str, content: str, meeting_name: str | None = None) -> str:
        result = self._upload_file(meeting_id, filename, content.encode('utf-8'), 'text/plain', meeting_name)
        return result['webViewLink']

    def save_json(self, meeting_id: str, filename: str, data: dict, meeting_name: str | None = None) -> str:
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        result = self._upload_file(meeting_id, filename, json_bytes, 'application/json', meeting_name)
        return result['webViewLink']

    def save_binary(self, meeting_id: str, filename: str, content: bytes, meeting_name: str | None = None) -> str:
        result = self._upload_file(meeting_id, filename, content, 'application/octet-stream', meeting_name)
        return result['webViewLink']

    def save_google_doc(self, meeting_id: str, title: str, content: str, meeting_name: str | None = None) -> str:
        """Crea un Google Doc a partir de contenido en texto plano y devuelve su webViewLink."""
        folder_id = self._ensure_meeting_folder(meeting_id, meeting_name)
        media = MediaIoBaseUpload(
            BytesIO(content.encode('utf-8')),
            mimetype='text/plain',
            resumable=True
        )
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        return file.get('webViewLink')

    def load_json(self, meeting_id: str, filename: str) -> dict:
        file_id = self._find_file_id(meeting_id, filename)
        if not file_id:
            raise FileNotFoundError(f"JSON file {filename} not found in Drive")
        request = self.service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return json.loads(fh.read().decode('utf-8'))

    def load_text(self, meeting_id: str, filename: str) -> str:
        file_id = self._find_file_id(meeting_id, filename)
        if not file_id:
            raise FileNotFoundError(f"Text file {filename} not found in Drive")
        request = self.service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read().decode('utf-8')

    def _find_file_id(self, meeting_id: str, filename: str) -> str | None:
        folder_id = self._ensure_meeting_folder(meeting_id)
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields='files(id)', pageSize=1).execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def list_meetings(self) -> list[MeetingListItem]:
        query = f"mimeType='application/vnd.google-apps.folder' and '{self.root_folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields='files(id, name)', pageSize=1000).execute()
        meetings = []
        for folder in results.get('files', []):
            meeting_id = folder['name']
            try:
                metadata = self.load_json(meeting_id, 'metadata.json')
                record = MeetingRecord(**metadata)
                meetings.append(MeetingListItem(
                    meeting_id=record.meeting_id,
                    meeting_name=record.meeting_name,
                    created_at=record.created_at,
                    status=record.status,
                    file_format=record.source_file.format if record.source_file else None,
                    file_size_bytes=record.source_file.size_bytes if record.source_file else None,
                ))
            except Exception as e:
                logger.warning(f"Error reading metadata for meeting {meeting_id} in Drive: {e}")
        return meetings

    def get_meeting(self, meeting_id: str) -> MeetingRecord | None:
        try:
            data = self.load_json(meeting_id, 'metadata.json')
            return MeetingRecord(**data)
        except Exception as e:
            logger.error(f"Error fetching meeting {meeting_id} from Drive: {e}")
            return None

    def meeting_exists(self, meeting_id: str) -> bool:
        return self._find_file_id(meeting_id, 'metadata.json') is not None

    def get_file_path(self, meeting_id: str, filename: str) -> Path | None:
        file_id = self._find_file_id(meeting_id, filename)
        if not file_id:
            return None
        request = self.service.files().get_media(fileId=file_id)
        tmp_dir = Path(os.getenv('TMP', '/tmp')) / 'gdrive_downloads'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{meeting_id}_{filename}"
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        tmp_path.write_bytes(fh.getvalue())
        return tmp_path


def get_storage() -> StorageBackend:
    """Factory para obtener el backend de almacenamiento configurado."""
    if STORAGE_BACKEND == "gdrive":
        return GoogleDriveStorage()
    return LocalStorage()


# Instancia singleton
_storage: StorageBackend | None = None


def get_storage_service() -> StorageBackend:
    """Obtiene la instancia singleton del storage."""
    global _storage
    if _storage is None:
        _storage = get_storage()
    return _storage
