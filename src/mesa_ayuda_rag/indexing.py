"""Ingesta e indexación de documentos en el almacén vectorial."""

from __future__ import annotations

import uuid
from pathlib import Path

from mesa_ayuda_rag.chunking import TextChunk, iter_chunks_for_file
from mesa_ayuda_rag.config import AppConfig
from mesa_ayuda_rag.embeddings import build_embedding_provider
from mesa_ayuda_rag.loaders import get_loader
from mesa_ayuda_rag.logging_setup import get_logger
from mesa_ayuda_rag.manifest import Manifest, fingerprint
from mesa_ayuda_rag.vector_store import VectorStore

logger = get_logger(__name__)

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".pdf", ".docx"}
_LOCAL_EMBEDDING = frozenset({"local", "sentence-transformers", "st"})


def _chunk_id(chunk: TextChunk) -> str:
    raw = f"{chunk.source_path}#{chunk.chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def iter_kb_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.is_dir():
        return files
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path)
    return files


def _metadata_for_chunk(chunk: TextChunk) -> dict[str, str | int | float | bool]:
    meta: dict[str, str | int | float | bool] = {
        "source_path": chunk.source_path,
        "chunk_index": chunk.chunk_index,
    }
    if chunk.section_hint:
        meta["section_hint"] = chunk.section_hint
    if chunk.page_hint:
        meta["page_hint"] = chunk.page_hint
    return meta


class IndexingService:
    """Indexación incremental y reconstrucción completa."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        ep = config.settings.embedding_provider.lower()
        api_key = config.settings.embedding_key() if ep not in _LOCAL_EMBEDDING else None
        self._embed = build_embedding_provider(
            provider=config.settings.embedding_provider,
            model=config.embedding_model,
            api_key=api_key,
            base_url=config.settings.embedding_base_url,
        )
        self._store = VectorStore(
            persist_dir=config.data_dir / "vectors",
            collection_name=config.vector_index_name,
        )
        self._manifest = Manifest(config.manifest_path)

    def reindex(self, *, full: bool = False) -> dict[str, int]:
        """Procesa documentos nuevos o modificados; con `full` reindexa todos los archivos."""
        kb = self._config.knowledge_base_path.resolve()
        files = iter_kb_files(kb)
        current_rel = {str(p.relative_to(kb)).replace("\\", "/") for p in files}

        # Archivos eliminados del disco: borrar del índice y del manifiesto
        for rel in self._manifest.removed_paths(current_rel):
            self._store.delete_by_source(rel)
            self._manifest.entries.pop(rel, None)

        to_process: list[Path] = []
        if full:
            to_process = list(files)
        else:
            for path in files:
                fp = fingerprint(path, root=kb)
                if not self._manifest.is_unchanged(fp):
                    to_process.append(path)

        chunks_total = 0
        for path in to_process:
            rel = str(path.relative_to(kb)).replace("\\", "/")
            loader = get_loader(path)
            if loader is None:
                continue
            try:
                text = loader.load(path)
            except Exception as exc:
                logger.warning("document_load_failed path=%s error=%s", path, exc)
                continue
            if not text.strip():
                logger.warning("document_empty path=%s", path)
                continue

            self._store.delete_by_source(rel)

            chunks = iter_chunks_for_file(
                path,
                root=kb,
                text=text,
                chunk_size=self._config.chunk_size,
                chunk_overlap=self._config.chunk_overlap,
            )
            if not chunks:
                continue

            embeddings = self._embed.embed([c.text for c in chunks])
            ids = [_chunk_id(c) for c in chunks]
            docs = [c.text for c in chunks]
            metas = [_metadata_for_chunk(c) for c in chunks]

            self._store.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=docs,
                metadatas=metas,
            )
            chunks_total += len(chunks)
            self._manifest.upsert(fingerprint(path, root=kb))

        self._manifest.save()
        logger.info(
            "reindex_done scanned=%s processed=%s chunks=%s full=%s",
            len(files),
            len(to_process),
            chunks_total,
            full,
        )
        return {
            "files_scanned": len(files),
            "files_processed": len(to_process),
            "chunks_upserted": chunks_total,
        }
