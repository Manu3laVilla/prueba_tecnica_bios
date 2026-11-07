FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md config.yaml ./
COPY src ./src
COPY prompts ./prompts
COPY knowledge_base ./knowledge_base

RUN pip install --upgrade pip \
    && pip install .

# Sentence-transformers cache (evita re-descargas si se monta volumen)
ENV HF_HOME=/app/data/huggingface

CMD ["python", "-m", "mesa_ayuda_rag"]
