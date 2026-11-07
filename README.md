# Asistente de mesa de ayuda con RAG en Telegram

Entrega de la **prueba técnica – Transformación Digital (Grupo Bios)**. Bot de Telegram que responde **únicamente** con documentos en `knowledge_base/`, usando RAG: fragmentación → embeddings → búsqueda por similitud → respuesta del LLM con citas de fuente.

## Requisitos previos

- **Python 3.11+**
- Cuenta con API compatible con **OpenAI** (OpenAI, Groq, OpenRouter, etc.) para el **LLM**
- Con **embeddings locales** (configuración por defecto en `.env.example`): espacio y red para la primera descarga de `sentence-transformers`

## Crear el bot y obtener tu ID de Telegram

1. Habla con [@BotFather](https://t.me/BotFather), crea el bot con `/newbot` y copia el **token**.
2. Obtén tu **user id** con [@userinfobot](https://t.me/userinfobot) o desde logs en desarrollo.

## Instalación (desarrollo local)

```bash
cd prueba_técnica_bios
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # Linux/macOS
pip install -e ".[dev]"
copy .env.example .env          # Windows; en Unix: cp .env.example .env
```

## Configuración

1. Edita **`.env`** (token, claves, IDs; ver comentarios en `.env.example`).
2. Opcional: ajusta **`config.yaml`** (chunks, umbral, rutas).
3. Coloca documentos en **`knowledge_base/`**; al iniciar o con `/reindex` (admins) se indexan.

## Ejecución

```bash
python -m mesa_ayuda_rag
```

También: `mesa-ayuda` si instalaste el paquete en editable.

## Docker (opcional)

```bash
docker compose up --build
```

Requiere `.env` en la raíz (no va dentro de la imagen).

## Comandos del bot

| Comando    | Descripción |
|-----------|-------------|
| `/start`  | Bienvenida |
| `/help`   | Ayuda |
| `/reset`  | Borra historial del usuario |
| `/fuentes` | Lista documentos indexados |
| `/reindex` | Reindexa (solo `ADMIN_USER_IDS`) |

## Proveedores soportados

- **LLM:** API OpenAI-compatible (`LLM_API_KEY`, opcional `LLM_BASE_URL`).
- **Embeddings:** `EMBEDDING_PROVIDER=local` (por defecto) u OpenAI-compatible vía config.

## Pruebas

```bash
pytest -q
ruff check src tests
```

## Mapa de documentación

| Documento | Contenido |
|-----------|-----------|
| `specs/spec.md` | Alcance y requisitos |
| `specs/plan.md` | Plan y stack |
| `specs/tasks.md` | Tareas y trazabilidad |
| `docs/ARQUITECTURA.md` | Diagramas y flujos |
| `docs/DECISIONES.md` | ADR |
| `docs/EVALUACION.md` | Pruebas del RAG |
| `docs/CRITERIO_TECNICO.md` | Reflexión técnica |
| `docs/USO_IA.md` | Uso de IA (punto 6.4) |

## Limitaciones que dejé documentadas

- Historial y rate limit **en memoria** (se pierden al reiniciar).
- Índice **lineal** en NumPy; adecuado para la prueba, no para millones de vectores sin migrar a FAISS/Chroma/Qdrant.
- Primera ejecución con embeddings locales **descarga** el modelo.
