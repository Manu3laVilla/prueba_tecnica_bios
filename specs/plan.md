# Plan de construcción

Plan personal para implementar la prueba según `spec.md`.

## Arquitectura (resumen)

1. **Telegram:** bot async con `python-telegram-bot`, comandos y control de acceso.
2. **Ingesta:** lectura recursiva de `knowledge_base/`.
3. **Fragmentación:** ventanas con solapamiento configurable.
4. **Embeddings:** local por defecto (`sentence-transformers`); opción API.
5. **Índice:** NumPy + pickle en `./data/vectors` (portable en Windows).
6. **RAG:** top-k, umbral, prompt externo, LLM OpenAI-compatible.
7. **Indexación incremental:** manifiesto con hash de contenido.

## Tecnologías que elegí

| Área | Elección | Requisitos |
|------|----------|------------|
| Orquestación RAG | Módulos propios (`loaders` → `chunking` → `indexing` → `rag`); sin LangChain/LlamaIndex | RF-02–RF-04, RF-09; ver ADR-003 |
| Lenguaje | Python 3.11+ | NFR |
| Telegram | python-telegram-bot 21.x | RF-06, RF-07 |
| Config | Pydantic + YAML | NFR 4.1 |
| Vector | NumPy + pickle | RF-02, local |
| Embeddings | sentence-transformers | Sin 2.ª API key |
| LLM | Cliente OpenAI-compatible | RF-03, RF-04 |
| PDF / DOCX | pypdf, python-docx | RF-01 |
| Tests | pytest | NFR 4.4 |

## Modelo de datos

- **Chunk:** texto + metadatos (`source_path`, `chunk_index`, sección/página).
- **Manifiesto:** `data/manifest.json`.
- **Historial:** pares role/content por `telegram_user_id` en memoria.

## Flujos

### Ingesta → índice

`knowledge_base/` → loaders → chunk → embeddings → upsert en el índice (solo cambios si incremental).

### Pregunta → respuesta

Telegram → acceso → rate limit → embedding → búsqueda → (sin contexto: respuesta fija) o prompt + LLM → respuesta con fuentes.

Este plan cubre US-01–US-06 y RF-01–RF-10 según `spec.md`.
