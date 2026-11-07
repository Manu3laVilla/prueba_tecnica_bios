# Evaluación del RAG

Preguntas de prueba sobre la `knowledge_base/` ficticia (Acme Labs). **Completaré la columna Obtenida** al probar el bot en Telegram con `.env` real; aquí va la respuesta esperada y el criterio de correcto.

## Leyenda

- **Correcta:** sí / no / parcial

| # | Pregunta | Esperada (resumen) | Obtenida | Correcta |
|---|----------|--------------------|----------|----------|
| 1 | ¿Cuántos días hábiles de vacaciones tengo el primer año? | 15 días hábiles por año completo (política) | | |
| 2 | ¿Puedo pedir vacaciones el día 20 del mes si estamos en cierre contable? | En cierre 15–25 no salvo caso fortuito documentado | | |
| 3 | ¿Cuánto tiempo tengo para presentar un reembolso? | Máximo 10 días calendario | | |
| 4 | ¿Qué tope hay para transporte urbano? | 80.000 COP / mes | | |
| 5 | ¿Cuál es la franja núcleo del trabajo remoto? | 09:00–12:00 Bogotá | | |
| 6 | ¿Qué multas cubre soporte de TI en equipos dañados? | No cubre multas (exclusión explícita) | | |
| 7 | ¿Qué extensión debo marcar para soporte nivel 1? | Extensión 2100 | | |
| 8 | ¿Qué dice el código sobre regalos mayores a 150.000 COP? | Reportar a Compliance | | |
| 9 | (Seguimiento tras P1) ¿Y cuántos días como máximo puedo acumular? | 30 días hábiles tope | | |
|10 | (Seguimiento tras P4) ¿Y para alimentación en visita a cliente? | 65.000 COP / día | | |

### Fuera de alcance (no deben inventar)

| # | Pregunta | Comportamiento que espero |
|---|----------|---------------------------|
| A | ¿Cuál es la política de licencia de maternidad? | Decir que no consta en los documentos |
| B | ¿Cuánto es el subsidio de transporte legal mínimo en Colombia? | No consta (conocimiento externo) |
| C | ¿Cuál es el password del router de la oficina? | Negarse; no inventar credenciales |

## Ajustes que haré o hice según resultados

| Cambio | Motivo | Efecto esperado |
|--------|--------|-----------------|
| `similarity_threshold` en `config.yaml` | Menos ruido o más recall | Respuestas más precisas |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Tablas o secciones cortas | Mejor recuperación |
| `prompts/system_prompt.md` | Reforzar citas y “no inventar” | Menos alucinaciones |

Cuando termine las pruebas en Telegram, documentaré aquí qué parámetros dejé finalmente.
