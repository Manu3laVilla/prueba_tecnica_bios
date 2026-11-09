"""Fragmentación de documentos largos en chunks con solapamiento."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextChunk:
    """Fragmento indexable con metadatos mínimos para citar fuentes."""

    text: str
    source_path: str
    chunk_index: int
    section_hint: str | None = None
    page_hint: str | None = None


HEADING_RE = re.compile(r"^(#{1,6}\s+.+)$", re.MULTILINE)


def split_markdown_sections(text: str) -> list[tuple[str | None, str]]:
    """Divide Markdown por encabezados; devuelve lista de (título o None, cuerpo)."""
    parts = HEADING_RE.split(text)
    if len(parts) == 1:
        return [(None, text.strip())]

    sections: list[tuple[str | None, str]] = []
    if parts[0].strip():
        sections.append((None, parts[0].strip()))
        i = 1
    else:
        # Con split() el primer trozo suele ser vacío; el encabezado empieza en índice 1.
        i = 1
    while i < len(parts) - 1:
        title = parts[i].strip()
        body = parts[i + 1].strip()
        sections.append((title, body))
        i += 2
    return sections or [(None, text.strip())]


def chunk_text(
    text: str,
    *,
    source_rel: str,
    chunk_size: int,
    chunk_overlap: int,
    is_markdown: bool,
) -> list[TextChunk]:
    """Divide texto en ventanas con solapamiento; intenta respetar secciones en Markdown."""
    chunks: list[TextChunk] = []
    idx = 0

    def add_piece(piece: str, section: str | None, page_hint: str | None) -> None:
        nonlocal idx
        piece = piece.strip()
        if not piece:
            return
        start = 0
        n = len(piece)
        while start < n:
            end = min(n, start + chunk_size)
            window = piece[start:end].strip()
            if window:
                chunks.append(
                    TextChunk(
                        text=window,
                        source_path=source_rel,
                        chunk_index=idx,
                        section_hint=section,
                        page_hint=page_hint,
                    )
                )
                idx += 1
            if end >= n:
                break
            start = max(0, end - chunk_overlap)

    if is_markdown:
        for title, body in split_markdown_sections(text):
            section = title
            add_piece(body, section, None)
    else:
        # PDF: el cargador puede anteponer marcadores "--- Página N ---"
        if "--- Página" in text:
            segments = re.split(r"(?=--- Página \d+ ---)", text)
            for seg in segments:
                seg_stripped = seg.strip()
                if not seg_stripped:
                    continue
                m_page = re.match(r"--- Página (\d+) ---\s*", seg_stripped, re.IGNORECASE)
                page_num = m_page.group(1) if m_page else None
                body = seg_stripped[m_page.end() :].strip() if m_page else seg_stripped
                add_piece(body, None, page_num)
        else:
            add_piece(text, None, None)

    if not chunks:
        add_piece(text, None, None)

    return chunks


def iter_chunks_for_file(
    path: Path,
    *,
    root: Path,
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Construye chunks para un archivo ya leído."""
    rel = str(path.relative_to(root)).replace("\\", "/")
    is_md = path.suffix.lower() in {".md", ".markdown"}
    return chunk_text(
        text,
        source_rel=rel,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        is_markdown=is_md,
    )
