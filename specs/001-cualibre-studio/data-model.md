# Data Model — CUA-LIBRE STUDIO (Fase 1)

**Date**: 2026-07-06 | **Plan**: [plan.md](./plan.md)

Todas las entidades se serializan como JSON UTF-8 (`ensure_ascii=False`). Los modelos
Pydantic en `backend/models.py` son la fuente de verdad de validación.

## Domain (dominio de código) — constante

9 dominios fijos (FR-016), compartidos entre backend (validación) y frontend (colores).

| clave | color |
|-------|-------|
| Emocional | #FF3300 |
| Descriptivo | #0066FF |
| In Vivo | #FFCC00 |
| Tensión/CHAT | #FF0066 |
| Proceso | #6600CC |
| Teórico | #00CC66 |
| Relacional | #0099CC |
| Crítico | #CC0000 |
| Método | #333333 |

Validación: todo `Code.domain` debe pertenecer a este conjunto (422 si no).

## Project

| campo | tipo | reglas |
|-------|------|--------|
| id | str (uuid4) | inmutable |
| name | str | 1–120 chars, requerido; renombrable (FR-032) |
| created_at | str ISO-8601 | asignado al crear |
| updated_at | str ISO-8601 | actualizado en cada mutación |
| documents | list[Document] | orden = orden de importación |
| codes | list[Code] | |
| next_code_id | int | contador monotónico, nunca se reutiliza un id |

Archivo: `~/Library/Application Support/cualibre/projects/<id>.json`.
`config.json`: `{ "active_project_id": "<id>" }` (FR-026).

## Document

| campo | tipo | reglas |
|-------|------|--------|
| id | str (uuid4) | inmutable |
| filename | str | nombre original del archivo |
| text | str | texto extraído, UTF-8 íntegro (FR-003); no vacío (FR-004) |
| imported_at | str ISO-8601 | |

Eliminación: `DELETE /api/documents/{id}` elimina el documento **y** sus códigos anclados;
el frontend advierte antes cuántos códigos se perderán (FR-033). Los códigos manuales no
se ven afectados.

## Code (registro de codificación)

| campo | tipo | reglas |
|-------|------|--------|
| id | int | secuencial por proyecto (`next_code_id`) |
| created_at | str ISO-8601 | fecha y hora (FR-015) |
| doc_id | str \| null | null ⇔ código manual (origen "Manual") |
| domain | str | uno de los 9 dominios (FR-016) |
| name | str | 1–200 chars, no vacío (FR-012) |
| quote | str | cita textual; `""` para manuales |
| start | int \| null | offset UTF-16 inicial en `document.text`; null para manuales |
| end | int \| null | offset final (exclusivo); `end > start`; null para manuales |
| memo | str | puede ser vacío |

Invariantes:
- `doc_id != null` ⇒ `start`, `end` válidos dentro de `len(document.text)` y
  `quote == document.text[start:end]` según el cliente (el backend valida rango, no
  contenido — ver research D2 sobre UTF-16).
- `doc_id == null` ⇒ `start == end == null`, `quote == ""`.
- Edición (FR-030): mutables `name`, `domain`, `memo`. `doc_id/start/end/quote` inmutables.
- Eliminación (FR-031): quita el registro; el re-render del Canvas elimina su resaltado.

## Transiciones de estado

```
Proyecto:   crear → activo → (renombrar)* → (reiniciar: documents=[], codes=[],
            next_code_id=1, con confirmación FR-014)
Documento:  importar → en corpus → eliminar (con advertencia si tiene códigos)
Código:     crear (Nube Negra | Paleta manual) → editar (name/domain/memo) → eliminar
```

Toda transición persiste el proyecto completo de forma atómica antes de responder (FR-025).

## Derivados (no persistidos)

- **NLP result**: `[{word, count}]` calculado bajo demanda desde la concatenación de
  `documents[].text` con `lang` y `min_len` (FR-017).
- **Analytics**: agregaciones de `codes` por `domain` (torta) y por `name` (barras),
  calculadas por el frontend desde el estado ya cargado (FR-019, FR-020).
- **CSV export**: filas `id, fecha, documento, dominio, codigo, cita, memo`; documento =
  `filename` o `"Manual"`; UTF-8 con BOM, escapado RFC 4180 (FR-021, FR-022).
- **Literature result**: `[{title, year, cited_by_count, doi}]` desde OpenAlex (FR-023).
