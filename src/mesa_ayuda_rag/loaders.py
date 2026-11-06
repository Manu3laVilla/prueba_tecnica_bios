"""Carga de texto desde documentos en `knowledge_base/`."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pypdf import PdfReader


class DocumentLoader(ABC):
    """Carga texto desde un archivo."""

    @abstractmethod
    def load(self, path: Path) -> str:
        """Devuelve texto plano o lanza ValueError si el archivo es ilegible."""


class MarkdownLoader(DocumentLoader):
    suffixes = {".md", ".markdown"}

    def load(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")


class TextLoader(DocumentLoader):
    suffixes = {".txt"}

    def load(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")


class PdfLoader(DocumentLoader):
    suffixes = {".pdf"}

    def load(self, path: Path) -> str:
        reader = PdfReader(str(path))
        parts: list[str] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                parts.append(f"--- Página {i + 1} ---\n{text.strip()}")
        return "\n\n".join(parts).strip()


class DocxLoader(DocumentLoader):
    suffixes = {".docx"}

    def load(self, path: Path) -> str:
        try:
            import docx  # type: ignore[import-untyped]
        except ImportError as e:
            raise ValueError("python-docx no está instalado") from e

        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())


LOADERS: tuple[type[DocumentLoader], ...] = (
    MarkdownLoader,
    TextLoader,
    PdfLoader,
    DocxLoader,
)


def get_loader(path: Path) -> DocumentLoader | None:
    """Selecciona el cargador adecuado por sufijo."""
    suffix = path.suffix.lower()
    for cls in LOADERS:
        if suffix in cls.suffixes:
            return cls()
    return None


def load_document_text(path: Path) -> str:
    """Carga el texto de un archivo soportado."""
    loader = get_loader(path)
    if loader is None:
        msg = f"Formato no soportado: {path.suffix}"
        raise ValueError(msg)
    return loader.load(path)
