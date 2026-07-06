# CUA-LIBRE STUDIO

Aplicación web local de análisis cualitativo (QDA/CAQDAS) para un investigador en ciencias
sociales. Backend FastAPI (Python 3.11+) + SPA vanilla HTML/CSS/JS sin build step.

## Regla suprema

`.specify/memory/constitution.md` gobierna todo. En particular:
- **Nunca eliminar funcionalidades al iterar** (Principio I). Inventario protegido:
  importación PDF/DOCX/TXT, Canvas con resaltado por dominio y pestañas de documentos,
  Nube Negra, Paleta con códigos manuales/memos/edición/eliminación, arrastre de
  selección a códigos existentes, NLP triple (word cloud + barras + tabla), Analytics,
  relaciones entre códigos (jerarquía/asociación/causalidad/contradicción con
  organizador SVG y árbol), exportación CSV UTF-8 BOM, búsqueda OpenAlex,
  multi-proyecto con botón de guardado explícito.
- **Ningún control de entrada sobre el Canvas** (Principio II). Solo la Nube Negra
  (popup efímero) puede aparecer sobre el texto.
- **Prohibido el patrón iframe-bridge de Streamlit** (Principio IV). La interacción
  selección→popup→resaltado es DOM nativo; backend↔frontend solo HTTP/JSON.
- **Verificar ejecutando la app real antes de declarar algo funcional** (Principio VII):
  seguir `specs/001-cualibre-studio/quickstart.md`.

## Estructura

- `backend/` — FastAPI: `app.py` (rutas), `models.py` (Pydantic + 9 dominios), `storage.py`
  (JSON atómico por proyecto), `extraction.py`, `nlp.py`, `export.py`, `literature.py`,
  `tests/` (pytest).
- `frontend/` — `index.html`, `css/brutal.css`, `js/` (api, state, canvas, nube, paleta,
  charts, wordcloud, views), `fonts/` (woff2 locales, sin CDN).
- `run.py` / `start.sh` — arranque con un comando; puerto 8734.
- `specs/001-cualibre-studio/` — spec, plan, research, data-model, contracts, quickstart.

## Decisiones clave (ver specs/001-cualibre-studio/research.md)

- Resaltados anclados por `doc_id + start/end` (offsets UTF-16 calculados y consumidos
  solo en JS; el backend los trata como opacos). Render por segmentación de rangos:
  spans planos, jamás anidados — así los solapamientos no rompen el HTML.
- Persistencia: `~/Library/Application Support/cualibre/projects/<uuid>.json`, escritura
  atómica (temp + `os.replace`) tras cada mutación, antes de responder.
- Gráficos SVG/canvas propios (sin Plotly/Chart.js); word cloud con espiral propia.
- Estética brutalista: Space Grotesk (títulos), IBM Plex Mono (UI), serif (corpus),
  fondo #FAFAFA, canvas #FDFDF7, acento #FF3300, bordes negros 3px, sombras duras.
  Paleta de dominios en `models.py` y `brutal.css` (mantener sincronizadas).

## Comandos

- Ejecutar: `./start.sh` (usa uv: aprovisiona Python 3.12+ y deps, abre navegador)
- Tests: `uv run -m pytest backend/tests/ -v`

## Idioma

Interfaz, mensajes de error y documentación de cara al usuario: **español**.
