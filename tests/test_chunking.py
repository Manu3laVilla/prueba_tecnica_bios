from pathlib import Path

from mesa_ayuda_rag.chunking import iter_chunks_for_file


def test_iter_chunks_for_file_respects_size(tmp_path: Path) -> None:
    root = tmp_path
    path = root / "doc.md"
    text = "# T\n" + ("x" * 2000)
    chunks = iter_chunks_for_file(path, root=root, text=text, chunk_size=500, chunk_overlap=50)
    assert chunks
    assert all(len(c.text) <= 500 for c in chunks)


def test_pdf_style_page_markers(tmp_path: Path) -> None:
    root = tmp_path
    path = root / "p.pdf"
    text = "--- Página 1 ---\nHola.\n\n--- Página 2 ---\nAdiós."
    chunks = iter_chunks_for_file(path, root=root, text=text, chunk_size=200, chunk_overlap=20)
    pages = {c.page_hint for c in chunks if c.page_hint}
    assert "1" in pages and "2" in pages
