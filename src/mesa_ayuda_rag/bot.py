"""Bot de Telegram: comandos, control de acceso, rate limiting e invocación RAG."""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict, deque
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from mesa_ayuda_rag.config import AppConfig
from mesa_ayuda_rag.indexing import IndexingService, iter_kb_files
from mesa_ayuda_rag.logging_setup import get_logger
from mesa_ayuda_rag.manifest import Manifest
from mesa_ayuda_rag.rag import RagEngine

logger = get_logger(__name__)


def _split_telegram(text: str, limit: int = 4000) -> list[str]:
    """Divide mensajes largos respetando el límite aproximado de Telegram."""
    if len(text) <= limit:
        return [text]
    return [text[i : i + limit] for i in range(0, len(text), limit)]


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self._per = max(1, per_minute)
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, user_id: int) -> bool:
        now = time.monotonic()
        dq = self._hits[user_id]
        while dq and now - dq[0] > 60.0:
            dq.popleft()
        if len(dq) >= self._per:
            return False
        dq.append(now)
        return True


class ConversationMemory:
    """Historial por usuario (en RAM): lista de dicts {role, content}."""

    def __init__(self, history_length: int) -> None:
        # history_length = número de *mensajes* conservados (user+assistant)
        self._max = max(2, history_length)
        self._store: dict[int, list[dict[str, str]]] = {}

    def get(self, user_id: int) -> list[dict[str, str]]:
        return list(self._store.get(user_id, []))

    def append(self, user_id: int, role: str, content: str) -> None:
        hist = self._store.setdefault(user_id, [])
        hist.append({"role": role, "content": content})
        if len(hist) > self._max:
            self._store[user_id] = hist[-self._max :]

    def reset(self, user_id: int) -> None:
        self._store.pop(user_id, None)


class HelpDeskBot:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._rag = RagEngine(config)
        self._indexer = IndexingService(config)
        self._limiter = RateLimiter(config.rate_limit_per_minute)
        self._memory = ConversationMemory(config.history_length)
        self._manifest = Manifest(config.manifest_path)

    def _access_allowed(self, user_id: int | None) -> bool:
        if user_id is None:
            return False
        allowed = self._config.settings.allowed_user_ids
        return bool(allowed) and user_id in allowed

    def _is_admin(self, user_id: int | None) -> bool:
        if user_id is None:
            return False
        return user_id in self._config.settings.admin_user_ids

    async def _deny(self, update: Update) -> None:
        chat = update.effective_chat
        if chat:
            await chat.send_message(
                "Acceso denegado: tu usuario de Telegram no está autorizado para usar este bot."
            )

    async def cmd_start(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._access_allowed(update.effective_user.id if update.effective_user else None):
            await self._deny(update)
            return
        chat = update.effective_chat
        if chat:
            await chat.send_message(
                "Hola, soy el asistente de mesa de ayuda. Hazme preguntas sobre políticas internas "
                "según la base de conocimiento. Usa /help para ver comandos."
            )

    async def cmd_help(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._access_allowed(update.effective_user.id if update.effective_user else None):
            await self._deny(update)
            return
        chat = update.effective_chat
        if not chat:
            return
        text = (
            "Comandos:\n"
            "/start — mensaje de bienvenida\n"
            "/help — esta ayuda\n"
            "/reset — borra tu historial de conversación en este bot\n"
            "/fuentes — lista los documentos indexados en la base de conocimiento\n"
            "/reindex — (solo admins) actualiza el índice con archivos nuevos o modificados\n\n"
            "Escribe tu pregunta en texto. El asistente responderá usando solo los documentos "
            "cargados en `knowledge_base/`."
        )
        await chat.send_message(text)

    async def cmd_reset(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        uid = update.effective_user.id if update.effective_user else None
        if not self._access_allowed(uid):
            await self._deny(update)
            return
        if uid is not None:
            self._memory.reset(uid)
        chat = update.effective_chat
        if chat:
            await chat.send_message("Listo: tu historial fue borrado.")

    async def cmd_fuentes(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._access_allowed(update.effective_user.id if update.effective_user else None):
            await self._deny(update)
            return
        chat = update.effective_chat
        if not chat:
            return
        self._manifest.load()
        kb = self._config.knowledge_base_path.resolve()
        indexed = sorted(self._manifest.entries.keys())
        on_disk = {str(p.relative_to(kb)).replace("\\", "/") for p in iter_kb_files(kb)}
        lines = ["Documentos indexados (manifiesto):"]
        for rel in indexed:
            status = "✓" if rel in on_disk else "(ausente en disco)"
            lines.append(f"- {rel} {status}")
        if len(lines) == 1:
            lines.append("(vacío: un administrador puede ejecutar /reindex)")
        await chat.send_message("\n".join(lines))

    async def cmd_reindex(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        uid = update.effective_user.id if update.effective_user else None
        if not self._access_allowed(uid):
            await self._deny(update)
            return
        chat = update.effective_chat
        if not chat:
            return
        if not self._is_admin(uid):
            await chat.send_message("No tienes permisos para /reindex.")
            return
        await chat.send_message("Reindexando…")
        stats = await asyncio.to_thread(self._indexer.reindex)
        self._manifest.load()
        await chat.send_message(
            "Reindexación terminada.\n"
            f"- Archivos escaneados: {stats['files_scanned']}\n"
            f"- Archivos procesados: {stats['files_processed']}\n"
            f"- Fragmentos generados/actualizados: {stats['chunks_upserted']}"
        )

    async def on_text(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        uid = update.effective_user.id if update.effective_user else None
        if not self._access_allowed(uid):
            await self._deny(update)
            return
        if uid is None:
            return
        chat = update.effective_chat
        if not chat or not update.message:
            return
        if not self._limiter.allow(uid):
            await chat.send_message(
                "Has superado el límite de mensajes por minuto. Espera un momento."
            )
            return
        text = (update.message.text or "").strip()
        if not text:
            await chat.send_message("No recibí texto. Envía una pregunta escrita.")
            return

        history = self._memory.get(uid)
        try:
            answer = await asyncio.to_thread(
                self._rag.answer,
                user_message=text,
                history=history,
            )
        except Exception as exc:
            logger.error("rag_failed user_id=%s error=%s", uid, exc)
            await chat.send_message(
                "No pude generar una respuesta en este momento "
                "(error al llamar al modelo o al índice). "
                "Intenta de nuevo más tarde."
            )
            return

        self._memory.append(uid, "user", text)
        if not answer.had_context:
            self._log_unanswered(uid, text)
        self._memory.append(uid, "assistant", answer.text)

        for part in _split_telegram(answer.text):
            await chat.send_message(part)

    async def on_non_text(self, update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._access_allowed(update.effective_user.id if update.effective_user else None):
            await self._deny(update)
            return
        chat = update.effective_chat
        if chat:
            await chat.send_message("Solo puedo leer mensajes de texto.")

    def _log_unanswered(self, user_id: int, question: str) -> None:
        path = Path(self._config.unanswered_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": time.time(), "user_id": user_id, "question": question}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def build_application(self) -> Application:
        async def post_init(application: Application) -> None:
            _ = application
            logger.info("startup_reindex_begin")
            await asyncio.to_thread(self._indexer.reindex)
            self._manifest.load()
            logger.info("startup_reindex_done")

        app = (
            Application.builder()
            .token(self._config.settings.telegram_bot_token)
            .post_init(post_init)
            .concurrent_updates(True)
            .build()
        )
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("reset", self.cmd_reset))
        app.add_handler(CommandHandler("fuentes", self.cmd_fuentes))
        app.add_handler(CommandHandler("reindex", self.cmd_reindex))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text))
        app.add_handler(MessageHandler(~filters.TEXT, self.on_non_text))
        return app


def run_bot(config: AppConfig) -> None:
    desk = HelpDeskBot(config)
    application = desk.build_application()
    application.run_polling(close_loop=False)
