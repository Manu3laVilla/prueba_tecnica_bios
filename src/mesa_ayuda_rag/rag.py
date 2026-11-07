"""Núcleo RAG: recuperación + generación con el LLM."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from mesa_ayuda_rag.config import AppConfig
from mesa_ayuda_rag.embeddings import build_embedding_provider
from mesa_ayuda_rag.logging_setup import get_logger
from mesa_ayuda_rag.vector_store import RetrievedChunk, VectorStore

logger = get_logger(__name__)

_LOCAL_EMBEDDING = frozenset({"local", "sentence-transformers", "st"})


@dataclass(frozen=True)
class RagAnswer:
    text: str
    sources: list[dict[str, Any]]
    had_context: bool


def _read_system_prompt(path: Path) -> str:
    if not path.is_file():
        msg = f"No se encontró el prompt de sistema en {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def _distance_to_similarity(distance: float) -> float:
    """Con embeddings normalizados y espacio coseno, Chroma usa distancia ~ 1 - cos."""
    return max(0.0, min(1.0, 1.0 - float(distance)))


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    lines: list[str] = []
    for i, ch in enumerate(chunks, start=1):
        src = ch.metadata.get("source_path", "desconocido")
        sec = ch.metadata.get("section_hint")
        page = ch.metadata.get("page_hint")
        meta = []
        if sec:
            meta.append(f"sección: {sec}")
        if page:
            meta.append(f"página: {page}")
        meta_s = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"### Fragmento {i}{meta_s}\n**Archivo:** {src}\n{ch.text}")
    return "\n\n".join(lines)


class RagEngine:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._system_prompt = _read_system_prompt(config.system_prompt_path.resolve())
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
        self._client = OpenAI(
            api_key=config.settings.llm_api_key,
            base_url=config.settings.llm_base_url,
        )

    def answer(
        self,
        *,
        user_message: str,
        history: Sequence[dict[str, str]],
    ) -> RagAnswer:
        q_emb = self._embed.embed([user_message])[0]
        raw = self._store.query(query_embedding=q_emb, top_k=self._config.retrieval_top_k)
        filtered: list[RetrievedChunk] = []
        for ch in raw:
            sim = _distance_to_similarity(ch.distance)
            if sim >= self._config.similarity_threshold:
                filtered.append(ch)

        if not filtered:
            return RagAnswer(
                text=(
                    "No encontré información suficiente en los documentos internos para "
                    "responder con seguridad. Si necesitas ayuda específica, indica a qué política "
                    "te refieres o consulta con mesa de ayuda/RRHH según corresponda."
                ),
                sources=[],
                had_context=False,
            )

        context = build_context_block(filtered)

        hist_lines: list[str] = []
        for m in history:
            role = m.get("role", "user")
            content = m.get("content", "")
            hist_lines.append(f"{role.upper()}: {content}")
        history_block = "\n".join(hist_lines) if hist_lines else "(sin mensajes previos)"

        user_block = (
            f"## Historial reciente (ordenado)\n{history_block}\n\n"
            f"## Pregunta actual\n{user_message}\n\n"
            f"## Documentos recuperados\n{context}"
        )

        try:
            resp = self._client.chat.completions.create(
                model=self._config.settings.llm_model,
                temperature=self._config.settings.llm_temperature,
                max_tokens=self._config.settings.llm_max_tokens,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_block},
                ],
            )
        except Exception as exc:
            logger.error("llm_call_failed error=%s", exc)
            raise

        choice = resp.choices[0].message
        content = (choice.content or "").strip()
        if not content:
            msg = "El modelo devolvió una respuesta vacía"
            raise RuntimeError(msg)

        sources: list[dict[str, Any]] = []
        for ch in filtered:
            sources.append(
                {
                    "source_path": ch.metadata.get("source_path"),
                    "section_hint": ch.metadata.get("section_hint"),
                    "page_hint": ch.metadata.get("page_hint"),
                    "similarity": _distance_to_similarity(ch.distance),
                }
            )

        content_out = _ensure_sources_footer(content, sources)
        return RagAnswer(text=content_out, sources=sources, had_context=True)


def _ensure_sources_footer(content: str, sources: list[dict[str, Any]]) -> str:
    """Añade un bloque **Fuentes:** si el modelo no lo incluyó ya."""
    lower = content.lower()
    if "fuentes:" in lower:
        return content

    lines: list[str] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for s in sources:
        path = str(s.get("source_path") or "desconocido")
        sec = s.get("section_hint")
        page = s.get("page_hint")
        key = (path, sec, page)
        if key in seen:
            continue
        seen.add(key)
        bits = [path]
        if sec:
            bits.append(f"sección: {sec}")
        if page:
            bits.append(f"página: {page}")
        lines.append("- " + " · ".join(bits))

    if not lines:
        return content

    return content.rstrip() + "\n\nFuentes:\n" + "\n".join(lines)
