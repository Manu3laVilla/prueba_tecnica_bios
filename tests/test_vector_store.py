import numpy as np

from mesa_ayuda_rag.vector_store import VectorStore


def test_vector_store_upsert_and_query(tmp_path) -> None:
    store = VectorStore(tmp_path, "test_coll")
    emb = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    store.upsert(
        ids=["a"],
        embeddings=[emb.tolist()],
        documents=["uno"],
        metadatas=[{"source_path": "x.txt"}],
    )
    res = store.query(query_embedding=emb.tolist(), top_k=1)
    assert len(res) == 1
    assert res[0].text == "uno"


def test_delete_by_source(tmp_path) -> None:
    store = VectorStore(tmp_path, "c2")
    store.upsert(
        ids=["1"],
        embeddings=[[1.0, 0.0]],
        documents=["a"],
        metadatas=[{"source_path": "a.md"}],
    )
    store.delete_by_source("a.md")
    assert store.query(query_embedding=[1.0, 0.0], top_k=3) == []
