# Criterio técnico (reflexión)

Respuestas en primera persona, según el enunciado de la prueba.

## ¿Qué fue lo más difícil?

Para mí fue equilibrar **recuperación útil** (tamaño de chunk, umbral de similitud) con **respuestas seguras** cuando casi no hay contexto. Lo resolví con un pipeline explícito (mapa en `docs/ARQUITECTURA.md`, ADR-003): corte antes del LLM si no hay chunks útiles, y pie de fuentes cuando el modelo omite citas.

## ¿Qué haría distinto si empezara de nuevo?

Reservaría tiempo temprano para una **tabla de evaluación** (como `EVALUACION.md`) y ajustaría umbral y chunk con datos reales antes de pulir docs. Si supiera que el evaluador trae muchos documentos, valoraría **FAISS** desde el diseño en lugar del scan lineal en NumPy.

## Producción (miles de documentos, muchos usuarios)

- **Índice:** migraría a FAISS, Qdrant o Chroma en Linux, con búsqueda aproximada.
- **Estado:** Redis o base de datos para historial y rate limits.
- **Escalado:** workers de ingesta; bot sin estado detrás de un balanceador.
- **Observabilidad:** trazas por conversación y un golden set para retrieval.

## Riesgos que identifico y cómo los mitigo hoy

| Riesgo | Qué hago en esta entrega |
|--------|--------------------------|
| Prompt injection | Reglas en `system_prompt.md` + no obedecer fuera del rol |
| Privacidad | No loguear secretos; mensajes sensibles solo en Telegram |
| Calidad del RAG | Umbral, prompt, `EVALUACION.md`, `unanswered.log` |
| Coste LLM | Modelo económico por defecto; no llamo al LLM sin contexto |

## Costo aproximado por consulta (mi configuración por defecto)

Supuestos orientativos (revisar precios vigentes):

- **gpt-4o-mini:** ~USD 0,15 / 1M tokens entrada, ~USD 0,60 / 1M salida (ejemplo).
- Consulta típica: ~1,2k tokens entrada, ~250 salida.

Cálculo:

- Entrada: 1200 / 1e6 × 0,15 ≈ **USD 0,00018**
- Salida: 250 / 1e6 × 0,60 ≈ **USD 0,00015**
- **Total ~USD 0,0003** por consulta.

Los embeddings locales no consumen API en mi configuración por defecto.

## Qué dejé fuera a propósito

Panel web, SSO, multi-tenant, BM25 híbrido y evaluación automática del LLM en CI — preferí cerrar bien los RF obligatorios y la documentación.

## Cómo mediría valor en la organización

Seguiría tasa de resolución sin escalamiento, tiempo de respuesta vs. mesa humana, feedback explícito y el volumen/temas de `data/unanswered.log` para priorizar nuevos documentos en `knowledge_base/`.
