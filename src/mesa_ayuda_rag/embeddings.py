"""Proveedores de embeddings (local con sentence-transformers u OpenAI-compatible API)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from openai import OpenAI


class EmbeddingProvider(ABC):
    """Interfaz para generar vectores de texto."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Devuelve un vector por cada texto (mismo orden)."""


class LocalSentenceTransformerProvider(EmbeddingProvider):
    """Modelo local multilingüe (sin costo por token de embedding)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """Embeddings vía API compatible con OpenAI (`/v1/embeddings`)."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None,
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        # La API acepta lotes; para simplicidad pedimos en un solo request si no es demasiado grande
        resp = self._client.embeddings.create(model=self._model, input=list(texts))
        # Ordenar por index por seguridad
        data = sorted(resp.data, key=lambda d: d.index)
        return [d.embedding for d in data]


def build_embedding_provider(
    *,
    provider: str,
    model: str,
    api_key: str | None,
    base_url: str | None,
) -> EmbeddingProvider:
    p = provider.lower().strip()
    if p in {"local", "sentence-transformers", "st"}:
        return LocalSentenceTransformerProvider(model)
    if p in {"openai", "groq", "api"}:
        if not api_key:
            msg = "Se requiere API key para embeddings remotos"
            raise ValueError(msg)
        return OpenAICompatibleEmbeddingProvider(api_key=api_key, model=model, base_url=base_url)
    msg = f"Proveedor de embeddings no soportado: {provider}"
    raise ValueError(msg)
