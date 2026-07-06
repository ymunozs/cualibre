# API Contract — CUA-LIBRE STUDIO (Fase 1)

**Base URL**: `http://127.0.0.1:8734` | Todas las respuestas JSON en UTF-8.
Errores: `{ "detail": "<mensaje claro en español>" }` con el status indicado.

## Estáticos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | `frontend/index.html` (SPA) |
| GET | `/static/*` | css, js, fonts |

## Proyectos

| Método | Ruta | Body | Respuesta | Notas |
|--------|------|------|-----------|-------|
| GET | `/api/projects` | — | `[{id, name, created_at, updated_at, doc_count, code_count}]` | listado para el selector |
| POST | `/api/projects` | `{name}` | `201` proyecto completo | crea y activa |
| PATCH | `/api/projects/{id}` | `{name}` | proyecto resumido | renombrar (FR-032) |
| POST | `/api/projects/{id}/activate` | — | proyecto completo | cambia el proyecto activo |
| GET | `/api/project` | — | proyecto activo completo (`documents` + `codes`) | estado inicial de la SPA; si no hay ninguno, crea "Mi proyecto" |
| POST | `/api/project/reset` | `{confirm: true}` | proyecto vacío | `400` si `confirm != true` (FR-014) |

## Documentos

| Método | Ruta | Body | Respuesta | Notas |
|--------|------|------|-----------|-------|
| POST | `/api/documents` | multipart `file` | `201 {document}` | PDF/DOCX/TXT; `415` tipo no soportado; `422` sin texto extraíble ("PDF escaneado…") — corpus intacto (FR-004) |
| DELETE | `/api/documents/{id}` | `{confirm: true}` requerido si tiene códigos | `{deleted_codes: n}` | FR-033; `409` con `{code_count}` si tiene códigos y no vino `confirm` |

## Códigos

| Método | Ruta | Body | Respuesta | Notas |
|--------|------|------|-----------|-------|
| POST | `/api/codes` | `{doc_id?, domain, name, quote?, start?, end?, memo?}` | `201 {code}` | `422`: dominio inválido, nombre vacío (FR-012), offsets fuera de rango o incoherentes con doc_id |
| PATCH | `/api/codes/{id}` | `{name?, domain?, memo?}` | `{code}` | FR-030; anclaje inmutable |
| DELETE | `/api/codes/{id}` | — | `204` | FR-031 |

## Análisis

| Método | Ruta | Query | Respuesta |
|--------|------|-------|-----------|
| GET | `/api/nlp` | `lang=es\|en`, `min_len=2..10`, `top=50` | `{words: [{word, count}]}` (FR-017) |
| GET | `/api/export.csv` | — | `text/csv; charset=utf-8` con BOM, `Content-Disposition: attachment; filename="cualibre_<proyecto>.csv"` (FR-021/022) |
| GET | `/api/literature` | `q=<términos>` | `{results: [{title, year, cited_by_count, doi}]}`; `502` con mensaje amigable si falla la red (FR-024) |

## Relaciones y guardado (cierre v1)

| Método | Ruta | Body | Respuesta | Notas |
|--------|------|------|-----------|-------|
| POST | `/api/project/save` | — | `{updated_at}` | persistencia forzada con confirmación (FR-036) |
| POST | `/api/relations` | `{source, target, type}` | `201 {relation}` | `422`: tipo inválido, source==target, código inexistente; `409` si la relación idéntica ya existe (FR-038) |
| DELETE | `/api/relations/{id}` | — | `204` | |

Tipos de relación: `jerarquía`, `asociación`, `causalidad`, `contradicción`. Las
relaciones referencian códigos por **nombre**; toda mutación de códigos poda las
relaciones cuyos extremos ya no existen.

## Reglas transversales

- Toda mutación persiste el proyecto de forma atómica **antes** de responder (FR-025).
- El backend nunca rebana texto por offsets (los trata como enteros opacos; research D2).
- CORS innecesario: mismo origen. El servidor escucha solo en 127.0.0.1.
