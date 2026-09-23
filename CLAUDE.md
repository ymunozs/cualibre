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

- `backend/` — FastAPI: `app.py` (rutas + middleware de idioma y escrituras en fila),
  `models.py` (Pydantic + 9 dominios), `storage.py` (JSON atómico por proyecto, caché en
  memoria, papelera, importación), `analysis.py` (análisis spaCy por documento, una vez,
  con caché en disco y trabajo de fondo), `i18n.py`, `extraction.py` (+ `ocr.py`: Vision /
  Windows.Media.Ocr), `nlp.py`, `sentiment.py` (+ `lexicons.py`: NRC por idioma),
  `agreement.py` (kappa/alfa), `qdpx.py` (REFI-QDA), `export.py`, `literature.py`,
  `tests/` (pytest; `tests/data/` trae el XSD oficial REFI-QDA para validar).
- `frontend/` — `index.html`, `css/brutal.css`, `js/` (api, state, canvas, nube, paleta,
  charts, wordcloud, views), `fonts/` (woff2 locales, sin CDN).
- `run.py` / `start.sh` / `start.bat` — arranque con un comando: ventana propia
  (pywebview) con respaldo en el navegador (`--navegador`); puerto 8734 (o el siguiente
  libre hasta 8743). pywebview DEBE crearse con `text_select=True` (si no, no se puede
  seleccionar texto para codificar) y `webview.start(private_mode=False, storage_path=…)`
  (si no, se pierde el localStorage al cerrar).
- `specs/001-cualibre-studio/` — spec, plan, research, data-model, contracts, quickstart.

## Decisiones clave (ver specs/001-cualibre-studio/research.md)

- Resaltados anclados por `doc_id + start/end` (offsets UTF-16 calculados y consumidos
  solo en JS; el backend los trata como opacos). Render por segmentación de rangos:
  spans planos, jamás anidados — así los solapamientos no rompen el HTML.
- Persistencia: `~/Library/Application Support/cualibre/projects/<uuid>.json` (Windows:
  `%APPDATA%\cualibre\`), escritura atómica (temp + `os.replace` con reintentos para
  Windows) tras cada mutación, antes de responder. Proyectos en memoria validados por
  mtime/tamaño; ante un error a mitad de una mutación se invalida la caché.
- Rendimiento con corpus grandes: el Canvas reconstruye solo el documento que cambió
  (firma por documento) y usa `content-visibility` sobre 400k caracteres; los íconos
  usan `var(--symbols)` (sin eso, la búsqueda de fuente de respaldo costaba ~3 ms por
  botón). Medir en navegador antes de declarar mejoras (ver bench en la sesión v1.11).
- Gráficos SVG/canvas propios (sin Plotly/Chart.js); word cloud con espiral propia.
- Estética brutalista: Space Grotesk (títulos), IBM Plex Mono (UI), serif (corpus),
  fondo #FAFAFA, canvas #FDFDF7, acento #FF3300, bordes negros 3px, sombras duras.
  Paleta de dominios en `models.py` y `brutal.css` (mantener sincronizadas).

- Licencia NRC: prohíbe redistribuir el léxico («Do not redistribute the data»). Desde
  v1.12.1 NINGÚN idioma viene incluido (el castellano se incluía de v1.6 a v1.12.0; el
  investigador eligió retirarlo el 2026-09-23): una descarga única desde el sitio oficial
  instala castellano, inglés y portugués (`lexicons.py`). NUNCA volver a incluir datos del
  NRC en el repo ni en los instaladores. Los tests usan el .zip sintético de conftest.py.
- REFI-QDA: posiciones en puntos de código según el estándar, PERO NVivo para Windows usa
  UTF-16 + saltos de línea como 2 (verificado con un .qdpx real). La importación detecta
  la convención por fuente; la exportación tiene perfil `standard` y `nvivo`.

## Comandos

- Ejecutar: `./start.sh` (usa uv: aprovisiona Python 3.12+ y deps, abre navegador)
- Tests: `uv run -m pytest backend/tests/ -v`

## Idioma

Idioma fuente: **español** (código, comentarios, commits, documentación interna).
La interfaz es trilingüe desde v1.11 (es-419 · en-GB · pt-BR):

- Texto de la SPA: `frontend/js/i18n.js` (atributos `data-i18n*` en el HTML +
  `I18N.t("clave")` en JS). Toda cadena nueva de cara al usuario DEBE ir en los tres
  diccionarios. Reporte académico: `Reporte.TEXT` en `reporte.js`.
- Mensajes del backend (errores, CSV/ZIP, demo): `backend/i18n.py` (`tr("clave")`);
  el idioma llega en la cabecera `X-Cua-Lang` o el parámetro `?ui=`.
- Manual: `MANUAL.md` + `MANUAL.en.md` + `MANUAL.pt.md` (actualizar los tres; los tres
  viajan en los instaladores vía `--add-data`).
- Los DATOS no se traducen: claves de Categorías Básicas y tipos de relación siempre en
  castellano; solo cambian sus etiquetas visibles (`I18N.domain`, `I18N.relType`).
