"""Punto de entrada: `python -m mesa_ayuda_rag` o `mesa-ayuda`."""

from __future__ import annotations

import sys

from mesa_ayuda_rag.bot import run_bot
from mesa_ayuda_rag.config import load_config
from mesa_ayuda_rag.logging_setup import configure_logging


def main() -> None:
    try:
        config = load_config()
    except Exception as exc:
        print(f"Error al cargar configuración: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    configure_logging(config.settings.log_level)

    if not config.settings.allowed_user_ids:
        print(
            "Debes definir ALLOWED_USER_IDS en `.env` con al menos un ID de Telegram.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not config.knowledge_base_path.is_dir():
        print(
            f"No existe la carpeta de conocimiento: {config.knowledge_base_path}. "
            "Créala o ajusta KNOWLEDGE_BASE_PATH.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    run_bot(config)


if __name__ == "__main__":
    main()
