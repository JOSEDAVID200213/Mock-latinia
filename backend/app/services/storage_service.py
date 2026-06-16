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

from app.config import STORAGE_BACKEND, STORAGE_DIR
from app.models.schemas import MeetingListItem, MeetingRecord, ProcessingStatus

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Interfaz abstracta para backends de almacenamiento."""

    @abstractmethod
    def save_original_file(self, meeting_id: str, file_path: Path, extension: str) -> str:
        """Guarda el archivo original. Retorna la ruta/URL del archivo guardado."""
        ...

    @abstractmethod
    def save_text(self, meeting_id: str, filename: str, content: str) -> str:
        """Guarda un archivo de texto."""
        ...

    @abstractmethod
    def save_json(self, meeting_id: str, filename: str, data: dict) -> str:
        """Guarda un archivo JSON."""
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
        """Obtiene la ruta local de un archivo (para descarga)."""
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

    def save_original_file(self, meeting_id: str, file_path: Path, extension: str) -> str:
        dest = self._meeting_dir(meeting_id) / f"original{extension}"
        shutil.copy2(str(file_path), str(dest))
        logger.info(f"Archivo original guardado: {dest}")
        return str(dest)

    def save_text(self, meeting_id: str, filename: str, content: str) -> str:
        dest = self._meeting_dir(meeting_id) / filename
        dest.write_text(content, encoding="utf-8")
        return str(dest)

    def save_json(self, meeting_id: str, filename: str, data: dict) -> str:
        dest = self._meeting_dir(meeting_id) / filename
        dest.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
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


def get_storage() -> StorageBackend:
    """Factory para obtener el backend de almacenamiento configurado."""
    if STORAGE_BACKEND == "gdrive":
        # TODO: Implementar GoogleDriveStorage en fase 2
        raise NotImplementedError(
            "Google Drive storage no implementado aún. "
            "Usa STORAGE_BACKEND=local por ahora."
        )
    return LocalStorage()


# Instancia singleton
_storage: StorageBackend | None = None


def get_storage_service() -> StorageBackend:
    """Obtiene la instancia singleton del storage."""
    global _storage
    if _storage is None:
        _storage = get_storage()
    return _storage
