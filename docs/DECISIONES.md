# Registro de decisiones (ADR)

Registro de decisiones técnicas del proyecto (estado en código y configuración).

## ADR-001 — Lenguaje y runtime

- **Contexto:** Necesitaba RAG + Telegram con librerías maduras.
- **Opciones:** Python vs TypeScript/Node.
- **Decisión:** **Python 3.11+**.
- **Por qué la elegí:** Ecosistema sólido (sentence-transformers, cliente OpenAI, `python-telegram-bot`).
- **Trade-off:** En Windows valido instalación local; en producción asumiría Linux o contenedor.

## ADR-002 — Cliente de Telegram

- **Contexto:** RF-06 (comandos) y RF-07 (acceso).
- **Opciones:** `python-telegram-bot`, `aiogram`, HTTP directo.
- **Decisión:** **`python-telegram-bot` 21.x**.
- **Por qué:** Documentación clara y handlers que cubren los comandos sin capa extra.

## ADR-003 — Orquestación RAG (sin LangChain ni LlamaIndex)

- **Contexto:** El enunciado exige fragmentación configurable, recuperación con umbral, citas de fuente, corte cuando no hay contexto (RF-02 a RF-04) e indexación incremental con manifiesto (RF-09). Todo eso tiene que quedar parametrizado en `config.yaml` / `.env` y auditable en este repositorio.
- **Opciones:** LangChain o LlamaIndex (cadenas de loaders, retrievers, agents) frente a **módulos Python explícitos**.
- **Decisión:** Pipeline propio: `loaders.py` → `chunking.py` → `embeddings.py` → `vector_store.py` / `manifest.py` vía `indexing.py`; consulta en `rag.py`; interfaz en `bot.py`.
- **Por qué descarté frameworks de orquestación en esta entrega:**
  - **Requisitos concretos del spec:** manifiesto por hash de archivo, reindex incremental, umbral que **evita** llamar al LLM (RF-04), pie de **Fuentes** reforzado en código (`_ensure_sources_footer()`), y `data/unanswered.log` (RF-10). Es más claro implementarlo en puntos fijos del flujo que adaptar abstracciones genéricas de un retriever.
  - **Almacén vectorial propio:** tras sustituir Chroma por NumPy + pickle (ADR-006), el índice y la búsqueda viven en `vector_store.py`; no dependo de integraciones que asumen Chroma/FAISS por defecto.
  - **Dependencias e instalación:** el proyecto ya arrastra `sentence-transformers`/torch; añadir LangChain aumenta superficie de versiones y tiempos de `pip install` sin cubrir RF obligatorios adicionales.
  - **Operación y ajuste:** `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `SIMILARITY_THRESHOLD` y rutas se leen de configuración externa; el evaluador puede cambiar comportamiento sin rastrear callbacks internos de un framework.
  - **Pruebas:** tests unitarios directos sobre chunking, vector store y pie de fuentes (`tests/`), sin mockear grafos de Runnable de terceros.
- **Trade-off aceptado:** más líneas en `src/` que un tutorial con LangChain; a cambio, un solo mapa módulo→responsabilidad (ver `docs/ARQUITECTURA.md`, sección «Pipeline RAG»).
- **Nota:** LangChain seguiría siendo opción razonable si el índice pasara a Qdrant/Chroma gestionado y el equipo estandarizara retrievers compartidos; aquí prioricé control del flujo de políticas internas y portabilidad en Windows.

## ADR-004 — Fragmentación

- **Decisión:** `CHUNK_SIZE` / `CHUNK_OVERLAP` en `config.yaml`; Markdown por encabezados; PDF con marcadores de página si el texto los trae.
- **Por qué:** Simple de ajustar y documentar en `EVALUACION.md` si hace falta afinar recall.

## ADR-005 — Embeddings

- **Decisión por defecto:** `paraphrase-multilingual-MiniLM-L12-v2` local.
- **Por qué:** El evaluador no debería necesitar segunda API key; asumo yo la primera descarga del modelo.

## ADR-006 — Almacén vectorial

- **Contexto:** Índice local; en mi PC Chroma no compiló sin MSVC.
- **Decisión:** **NumPy + pickle** en `data/vectors/`.
- **Por qué:** Portable en Windows; para el volumen de la prueba basta. Migraría a FAISS/Chroma en producción.

## ADR-007 — LLM por defecto

- **Decisión en `.env.example`:** `gpt-4o-mini` (o equivalente económico).
- **Por qué:** Balance costo/calidad para políticas en español; configurable sin código.

## ADR-008 — Prompt y alucinaciones

- **Decisión:** System prompt en archivo; si no hay retrieval útil, no llamo al LLM para “rellenar”; pie de **Fuentes** en código cuando falta.
- **Por qué:** RF-03 y RF-04; mitigo prompt injection en `system_prompt.md` (documentado en README).

## ADR-009 — Historial

- **Decisión:** En memoria por `user_id`, truncado a `HISTORY_LENGTH`.
- **Por qué:** Cumple RF-05 con mínima complejidad; documenté la limitación al reiniciar el proceso.

## ADR-010 — Configuración

- **Decisión:** `.env` (secretos) + `config.yaml` (resto).
- **Por qué:** Alineado al enunciado y a lo que espero que el evaluador toque sin editar código.
