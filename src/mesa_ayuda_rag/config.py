"""Carga de configuración desde `config.yaml` y variables de entorno."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        msg = f"El archivo de configuración debe ser un mapping YAML: {path}"
        raise ValueError(msg)
    return data


def _parse_id_list(raw: str | None) -> list[int]:
    if not raw or not raw.strip():
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


class Settings(BaseSettings):
    """Parámetros cargados de `.env` (secretos y overrides)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    llm_provider: str = Field("openai", alias="LLM_PROVIDER")
    llm_model: str = Field(..., alias="LLM_MODEL")
    llm_api_key: str = Field(..., alias="LLM_API_KEY")
    llm_base_url: str | None = Field(None, alias="LLM_BASE_URL")
    llm_temperature: float = Field(0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(900, alias="LLM_MAX_TOKENS")

    embedding_provider: str = Field("local", alias="EMBEDDING_PROVIDER")
    embedding_model: str | None = Field(None, alias="EMBEDDING_MODEL")
    embedding_api_key: str | None = Field(None, alias="EMBEDDING_API_KEY")
    embedding_base_url: str | None = Field(None, alias="EMBEDDING_BASE_URL")

    knowledge_base_path: Path | None = Field(None, alias="KNOWLEDGE_BASE_PATH")
    system_prompt_path: Path | None = Field(None, alias="SYSTEM_PROMPT_PATH")

    allowed_user_ids_raw: str = Field(..., alias="ALLOWED_USER_IDS")
    admin_user_ids_raw: str = Field("", alias="ADMIN_USER_IDS")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Overrides opcionales (nombres exigidos por la prueba técnica)
    chunk_size: int | None = Field(None, alias="CHUNK_SIZE")
    chunk_overlap: int | None = Field(None, alias="CHUNK_OVERLAP")
    retrieval_top_k: int | None = Field(None, alias="RETRIEVAL_TOP_K")
    similarity_threshold: float | None = Field(None, alias="SIMILARITY_THRESHOLD")
    history_length: int | None = Field(None, alias="HISTORY_LENGTH")
    rate_limit_per_minute: int | None = Field(None, alias="RATE_LIMIT_PER_MINUTE")

    @property
    def allowed_user_ids(self) -> set[int]:
        return set(_parse_id_list(self.allowed_user_ids_raw))

    @property
    def admin_user_ids(self) -> set[int]:
        return set(_parse_id_list(self.admin_user_ids_raw))

    def embedding_key(self) -> str:
        return self.embedding_api_key or self.llm_api_key


class AppConfig:
    """Parámetros efectivos: YAML + env."""

    def __init__(self, yaml_path: Path | None = None) -> None:
        root = Path.cwd()
        path = yaml_path or (root / "config.yaml")
        yml = _load_yaml_config(path)
        self.settings = Settings()

        self.chunk_size: int = int(self.settings.chunk_size or yml.get("chunk_size", 900))
        self.chunk_overlap: int = int(self.settings.chunk_overlap or yml.get("chunk_overlap", 150))
        self.retrieval_top_k: int = int(
            self.settings.retrieval_top_k or yml.get("retrieval_top_k", 5)
        )
        self.similarity_threshold: float = float(
            self.settings.similarity_threshold if self.settings.similarity_threshold is not None
            else yml.get("similarity_threshold", 0.32)
        )
        self.history_length: int = int(
            self.settings.history_length or yml.get("history_length", 12)
        )
        self.rate_limit_per_minute: int = int(
            self.settings.rate_limit_per_minute or yml.get("rate_limit_per_minute", 20)
        )

        kb = self.settings.knowledge_base_path or Path(
            yml.get("knowledge_base_path", "./knowledge_base")
        )
        self.knowledge_base_path: Path = Path(kb)

        sp = self.settings.system_prompt_path or Path(
            yml.get("system_prompt_path", "./prompts/system_prompt.md")
        )
        self.system_prompt_path: Path = Path(sp)

        self.data_dir: Path = Path(yml.get("data_dir", "./data"))
        self.vector_index_name: str = str(
            yml.get("vector_index_name", yml.get("chroma_collection_name", "mesa_ayuda_kb"))
        )
        self.embedding_model: str = str(
            yml.get(
                "embedding_model",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
        )
        self.manifest_path: Path = Path(yml.get("manifest_path", "./data/manifest.json"))
        self.unanswered_log_path: Path = Path(
            yml.get("unanswered_log_path", "./data/unanswered.log")
        )

        if self.settings.embedding_model:
            self.embedding_model = self.settings.embedding_model

        self.data_dir.mkdir(parents=True, exist_ok=True)


def load_config(yaml_path: Path | None = None) -> AppConfig:
    return AppConfig(yaml_path=yaml_path)
