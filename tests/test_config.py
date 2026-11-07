from pathlib import Path

import pytest

from mesa_ayuda_rag.config import AppConfig, Settings


def test_settings_parses_user_lists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    env = {
        "TELEGRAM_BOT_TOKEN": "x:y",
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_API_KEY": "sk-test",
        "ALLOWED_USER_IDS": "1, 2",
        "ADMIN_USER_IDS": "1",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    s = Settings()
    assert s.allowed_user_ids == {1, 2}
    assert s.admin_user_ids == {1}


def test_app_config_yaml_merge(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(
        "chunk_size: 100\nsimilarity_threshold: 0.4\n", encoding="utf-8"
    )
    for k, v in {
        "TELEGRAM_BOT_TOKEN": "a:b",
        "LLM_MODEL": "m",
        "LLM_API_KEY": "k",
        "ALLOWED_USER_IDS": "9",
    }.items():
        monkeypatch.setenv(k, v)
    cfg = AppConfig()
    assert cfg.chunk_size == 100
    assert cfg.similarity_threshold == 0.4
