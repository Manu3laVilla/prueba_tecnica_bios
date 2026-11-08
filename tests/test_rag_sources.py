from mesa_ayuda_rag.rag import _ensure_sources_footer


def test_ensure_sources_footer_adds_when_missing() -> None:
    body = "La política indica 15 días hábiles."
    sources = [
        {"source_path": "vacaciones.md", "section_hint": "# Vacaciones", "page_hint": None},
    ]
    out = _ensure_sources_footer(body, sources)
    assert "Fuentes:" in out
    assert "vacaciones.md" in out


def test_ensure_sources_footer_skips_if_present() -> None:
    body = "OK\n\nFuentes:\n- x.md"
    out = _ensure_sources_footer(body, [])
    assert out == body
