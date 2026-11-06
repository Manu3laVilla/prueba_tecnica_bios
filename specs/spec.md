# Especificación: Asistente de mesa de ayuda con RAG en Telegram

## Propósito

Entrego un asistente conversacional en Telegram que responde preguntas sobre políticas internas **solo** con documentos en `knowledge_base/`, mediante RAG.

## Actores

- **Colaborador autorizado**: usuario de Telegram en `ALLOWED_USER_IDS`.
- **Administrador**: puede usar `/reindex` (`ADMIN_USER_IDS`).
- **Sistema**: ingesta, indexación, recuperación y generación.

## Historias de usuario

| ID | Historia | Criterios de aceptación |
|----|-----------|-------------------------|
| US-01 | Como colaborador quiero hacer preguntas en lenguaje natural y recibir respuestas basadas en documentos internos. | La respuesta cita al menos una fuente (documento; sección o página cuando exista). |
| US-02 | Como colaborador quiero que el asistente admita cuando no sabe algo. | Si no hay fragmentos por encima del umbral, responde sin inventar. |
| US-03 | Como colaborador quiero preguntas de seguimiento con contexto previo. | El historial por usuario (`HISTORY_LENGTH`) se incluye en la consulta al modelo. |
| US-04 | Como administrador quiero reindexar sin reiniciar el bot. | `/reindex` solo admins; actualiza documentos nuevos o modificados. |
| US-05 | Como colaborador quiero comandos de ayuda y reinicio. | `/start`, `/help`, `/reset`, `/fuentes` según definición. |
| US-06 | Como organización quiero restringir el acceso. | Solo IDs permitidos; resto ve denegación. |

## Requisitos funcionales (trazabilidad)

| Requisito | Cómo lo implemento |
|-----------|-------------------|
| RF-01 | Cargadores `.md`, `.txt`, `.pdf`; opcional `.docx`. |
| RF-02 | Fragmentación, embeddings, persistencia en `data/vectors/`. |
| RF-03 | System prompt + pie de fuentes en `rag.py` si hace falta. |
| RF-04 | Umbral de similitud + respuesta sin inventar sin contexto. |
| RF-05 | Historial en memoria por `user_id`. |
| RF-06 | Comandos en `python-telegram-bot`. |
| RF-07 | Lista blanca de IDs. |
| RF-08 | `/reindex` solo admins. |
| RF-09 | Manifiesto + reindex incremental. |
| RF-10 | `data/unanswered.log`. |

## Requisitos no funcionales

- Parametrización en `.env` y `config.yaml`.
- README ejecutable con pocos comandos tras `.env`.
- Sin secretos en git; mitigación de prompt injection documentada.
- Errores visibles; tests en `tests/`.

## Supuestos

- El evaluador tiene API compatible con OpenAI para el LLM.
- Embeddings locales por defecto (sin segunda API key obligatoria).
- Un proceso del bot; historial y rate limit en memoria.

## Decisiones de diseño documentadas

- Orquestación RAG sin LangChain/LlamaIndex: módulos en `src/mesa_ayuda_rag/` y **ADR-003** en `docs/DECISIONES.md`.
- Almacén vectorial: `data/vectors/` (NumPy + pickle), **ADR-006**.

## Fuera de alcance

- Panel web, SSO, multi-tenant.
- LangChain / LlamaIndex como capa obligatoria (ver ADR-003 por qué no aplica en esta entrega).
