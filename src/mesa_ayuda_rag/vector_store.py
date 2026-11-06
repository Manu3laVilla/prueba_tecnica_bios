"""Almacén vectorial persistente en disco (sin dependencias nativas extra).

Se usa una lista de vectores en memoria + archivo pickle en ``persist_dir``.
Similitud: producto punto sobre embeddings **normalizados** (equivale a coseno).

Para miles de documentos convendría FAISS/Chroma/Qdrant; para la prueba y portabilidad en
Windows (sin compiladores C++) este enfoque es suficiente.
"""

from __future__ import annotations

import pickle
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    metadata: dict[str, Any]
    distance: float


def _normalize(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return vec
    return vec / norm


class VectorStore:
    """Índice liviano: similitud coseno vía embeddings L2-normalizados."""

    def __init__(self, persist_dir: Path, collection_name: str) -> None:
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._persist_dir / f"{collection_name}.pkl"
        self._records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            return
        with self._path.open("rb") as f:
            payload = pickle.load(f)
        if isinstance(payload, list):
            self._records = payload

    def _save(self) -> None:
        tmp = self._path.with_suffix(".pkl.tmp")
        with tmp.open("wb") as f:
            pickle.dump(self._records, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(self._path)

    def delete_by_source(self, source_rel: str) -> None:
        self._records = [
            r for r in self._records if r.get("meta", {}).get("source_path") != source_rel
        ]
        self._save()

    def upsert(
        self,
        *,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> None:
        id_set = set(ids)
        self._records = [r for r in self._records if r["id"] not in id_set]
        for rid, emb, doc, meta in zip(ids, embeddings, documents, metadatas, strict=True):
            v = np.asarray(list(emb), dtype=np.float32)
            self._records.append(
                {
                    "id": rid,
                    "embedding": _normalize(v),
                    "text": doc,
                    "meta": dict(meta),
                }
            )
        self._save()

    def query(
        self,
        *,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not self._records:
            return []
        q = _normalize(np.asarray(list(query_embedding), dtype=np.float32))
        matrix = np.stack([r["embedding"] for r in self._records], axis=0)
        sims = matrix @ q
        k = min(top_k, sims.shape[0])
        idx = np.argpartition(-sims, kth=k - 1)[:k]
        idx = idx[np.argsort(-sims[idx])]
        out: list[RetrievedChunk] = []
        for i in idx:
            sim = float(sims[int(i)])
            rec = self._records[int(i)]
            out.append(
                RetrievedChunk(
                    text=rec["text"],
                    metadata=rec["meta"],
                    distance=float(1.0 - sim),
                )
            )
        return out
