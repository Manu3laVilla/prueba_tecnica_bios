# Uso de inteligencia artificial

Documento del punto **6.4** del enunciado. Trabajo habitual: leo el reto, defino alcance, uso el **Agent de Cursor** para avanzar en bloques (spec, código, docs), y **cierro yo** con instalación local, pruebas y lo que no puede delegarse (token de Telegram, `.env`).

---

## 1. Herramientas, modelo y versión

| Herramienta | Versión / modelo | Uso |
|-------------|------------------|-----|
| **Cursor IDE** | Escritorio, nov. 2025 | Proyecto, terminal, revisión de diffs |
| **Cursor Agent** | **Composer** | Generación y refactors en `specs/`, `src/`, `docs/` |
| **Cursor Chat** | Mismo IDE | Depuración (`pip`, `pytest`, mensajes de error) |
| **SDD** | `specs/` (spec, plan, tasks) | Especificación antes de implementación; sin herramienta Spec Kit aparte |

El LLM del bot (`LLM_MODEL` en `.env`) es independiente: solo atiende conversaciones en Telegram.

---

## 2. Uso por etapa

| Etapa | Qué pedí / hice yo | Qué aceleró la IA |
|-------|-------------------|-------------------|
| **Especificación** | Leí el PDF, prioricé RF obligatorios y alcance de la entrega | Borrador de `specs/spec.md`, `plan.md`, `tasks.md` |
| **Diseño** | Elegí pipeline sin LangChain, embeddings locales, Telegram con lista blanca | Diagramas y texto inicial de `ARQUITECTURA.md` y ADR |
| **Código** | Revisé `bot.py` (acceso), `rag.py` (umbral, sin contexto, fuentes), corrí install en Windows | Implementación de loaders, chunking, índice, bot y comandos |
| **Pruebas** | Definí tests sin red ni API key; ejecuté `pytest -q` | Casos de chunking, config, vector store, pie de fuentes |
| **Documentación** | Ajusté coherencia con el código (p. ej. tras cambiar el índice) | README, `knowledge_base/` de ejemplo, plantillas en `docs/` |
| **Operación** | Configuración de `.env`, BotFather, prueba en Telegram | — |

---

## 3. Flujo de trabajo

1. **Contexto:** abrí el repo en Cursor y describí el objetivo (bot RAG, carpeta de conocimiento, configuración externa, documentación del enunciado).
2. **Orden de trabajo:** primero `specs/`, luego ingesta e índice, RAG, bot, tests y README, para mantener trazabilidad en commits.
3. **Contexto en el chat:** referencias a archivos (`@rag.py`, `@spec.md`) y tracebacks completos cuando falló la instalación.
4. **Revisión antes de dar por bueno:** leí los cambios en los módulos centrales, corrí `pytest -q` y `ruff check`, y actualicé spec/ADR si cambiaba una decisión (vector store, RF-02).

---

## 4. Prompts representativos

Reconstrucción de mensajes típicos; no tengo export del historial.

### 4.1 Arranque

> Asistente RAG en Telegram, solo con `knowledge_base/`. Carpeta `specs/` (SDD), Python, RF obligatorios primero, docs del enunciado, parametrización en `.env` y YAML, sin secretos en git. Propón stack y justifícalo.

**Por qué:** necesitaba entregable clonable, no un prototipo suelto.

### 4.2 Ingesta e índice incremental

> Carga md/txt/pdf/docx, chunk configurable, embeddings locales por defecto, índice en disco con manifiesto para no reindexar todo. Enlaza tareas a RF-01, RF-02 y RF-09.

**Por qué:** concentré ingesta en un mensaje para no perder trazabilidad.

### 4.3 Comportamiento del asistente (RF-03 y RF-04)

> RAG con top-k y umbral. System prompt en archivo. Sin chunks útiles: no inventar políticas. Siempre citar fuentes en la respuesta.

**Por qué:** es lo que más peso tiene en calidad del RAG.

### 4.4 Bot y controles

> python-telegram-bot: comandos del enunciado, lista blanca, rate limit, `/reindex` para admins, mensajes claros si falla LLM o índice.

**Por qué:** checklist de RF-06 a RF-08 en una iteración.

### 4.5 Instalación en Windows

> `pip install` falla con chroma-hnswlib (pide Build Tools de Visual C++). Sustituye el vector store por persistencia local sin compilar nativos; actualiza plan, ADR y README.

**Por qué:** bloqueo real en mi máquina; sin resolverlo no podía validar el README.

---

## 5. Sugerencias que rechacé o corregí

No adopté todo lo que sugiere un asistente genérico ni el primer diff que compilaba “en teoría”.

**ChromaDB en Windows.** La primera versión del proyecto traía Chroma. En mi PC la instalación exigía compilar `chroma-hnswlib` (Visual C++ Build Tools). Rechacé esa dependencia para la entrega y pedí un almacén en `vector_store.py` con **NumPy + pickle** bajo `data/vectors/`. Actualicé ADR-006, `specs/plan.md` y RF-02 en `spec.md`. Mantuve persistencia local; cambié la implementación.

**LangChain / LlamaIndex.** Lo rechacé; el **por qué técnico** (manifiesto incremental, umbral RF-04, vector store propio, pruebas, dependencias) está en **ADR-003** (`docs/DECISIONES.md`) y en la tabla de módulos de `docs/ARQUITECTURA.md`. En `USO_IA.md` solo registro que no adopté el primer stack “tipo tutorial”.

**RF-04 sin corte duro.** Corregí el flujo para que, si nada supera el umbral de similitud, no se llame al LLM para “rellenar”; respuesta al usuario y registro en `data/unanswered.log`.

**RF-03 solo con prompt.** En pruebas el modelo a veces respondía bien pero omitía el bloque **Fuentes:**. Añadí `_ensure_sources_footer()` en `rag.py` y cobertura en `test_rag_sources.py`.

**structlog.** Quité la dependencia y unifiqué logging estándar: menos peso en `pip install` y un solo estilo de log.

**Embeddings 100 % por API.** Mantuve **local por defecto** para no exigir segunda API key al quien evalúa.

**Historial en Redis/SQLite.** Rechacé ampliar alcance: memoria por usuario basta para RF-05 en esta prueba (documentado en README).

**Tests con llamadas reales al LLM.** Rechacé flakes y dependencia de claves en CI local; la calidad conversacional la registro en `EVALUACION.md` con el bot en Telegram.

**PDF con librería pesada.** Dejé un PDF de ejemplo en repo y generación opcional con script mínimo (`tools/write_minimal_pdf.py`).

**Spec y docs desfasados del código.** Tras pasar a NumPy, corregí referencias a Chroma que seguían en plan o diagramas. No entregué documentación que contradijera `vector_store.py`.

**Lo que acepté tras revisar.** `python-telegram-bot`, cliente OpenAI-compatible, `.env` + `config.yaml`, manifiesto incremental, comandos y controles de acceso, system prompt externo, Docker opcional y documentos ficticios de `knowledge_base/` — siempre validando parámetros y comportamiento en mi entorno.

---

## 6. Verificación manual

- `pip install -e ".[dev]"` en Windows (tras el cambio de vector store).
- `pytest -q` y `ruff check src tests`.
- Coherencia entre `.env.example`, `config.yaml` y `config.py`.
- Lectura del PDF de ejemplo desde el loader.
- Arranque y lista blanca (`ALLOWED_USER_IDS`).
- Prueba en Telegram con mi token y mis IDs, y relleno de **Obtenida** en `EVALUACION.md` (no delegable).

---

## 7. Proporción aproximada (honesta)

No uso un solo porcentaje para todo el repo:

| Ámbito | Con asistencia de IA | Principalmente mío |
|--------|----------------------|-------------------|
| Código de negocio (`src/`) | Borrador y refactors de módulos | Decisiones de RF, fix Windows, pie de fuentes, revisión de seguridad Telegram |
| `specs/` | Redacción inicial | Alcance, prioridad de RF, alineación tras cambios de diseño |
| Resto de `docs/` | Borradores | Contenido alineado al código que quedó en git |
| Este `USO_IA.md` | — | Redacción y criterio de qué contar |
| `.env`, git de entrega, prueba E2E | — | Configuración y validación en mi cuenta |

En conjunto: la IA me **aceleró** scaffolding, boilerplate y primera versión de docs; **yo** dirigí el alcance, rechacé stack que no instalaba en mi PC, corrí pruebas y dejé coherente spec, código y documentación técnica.

---

## 8. `knowledge_base/`

Políticas ficticias de Acme Labs con borrador asistido; revisé cifras y que las preguntas de `EVALUACION.md` se respondan desde los documentos, sin atajos en código por nombre de archivo.
