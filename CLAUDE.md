# CUA-LIBRE STUDIO

Aplicación web local de análisis cualitativo (QDA/CAQDAS) para un investigador en ciencias
sociales. Backend FastAPI (Python 3.11+) + SPA vanilla HTML/CSS/JS sin build step.

## Regla suprema

`.specify/memory/constitution.md` gobierna todo. En particular:
- **Nunca eliminar funcionalidades al iterar** (Principio I). Inventario protegido:
  importación PDF/DOCX/DOC/TXT, Canvas con resaltado por dominio y pestañas de documentos,
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
  con caché en disco y trabajo de fondo), `i18n.py`, `extraction.py` (+ `legacy_doc.py`: Word 97-2003 y RTF en Python puro; `ocr.py`: Vision /
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

- Word antiguo (.doc, v1.13): `legacy_doc.py` lee el binario de Word 97-2003 siguiendo la
  tabla de piezas de [MS-DOC] y también RTF; decide por el contenido, no por la extensión.
  En Windows no hay conversor del sistema (como textutil en Mac), por eso es Python puro
  (única dependencia: `olefile`). Validado contra textutil con documentos reales; las
  diferencias aceptadas son encabezados/pies (no se importan) e instrucciones de campo
  (se muestra solo el resultado visible, como Word).
- Instaladores (v1.13): nombres SIN versión (`CUA-LIBRE-Studio-windows-setup.exe`,
  `…-mac-applesilicon.dmg`, `…-mac-intel.dmg`) porque el README enlaza a
  `releases/latest/download/<nombre>`; cambiar un nombre rompe esos enlaces. La versión
  sale de `pyproject.toml` (más `APP_VERSION` en `app.py` y el `<small id="version">` de
  `index.html`; un test exige que coincidan). El instalador de Windows no muestra página
  de carpeta ni pide administrador. `packaging/windows/smoke_test.ps1` (CI) lo instala,
  abre la app, importa un .doc, actualiza y desinstala, también en rutas con tildes;
  `packaging/smoke_test.sh` hace lo equivalente con la .app de Mac. `cualibre.iss` y
  `smoke_test.ps1` llevan BOM UTF-8: no quitarlo.
- v2.0 (FR-084..086): `Project.codebook`/`category_notes` (libro de códigos; nunca se
  borran solos, migran al fusionar), `Relation.source_kind/target_kind` ("code" |
  "category"; `_prune_relations` y `_remap_relations` respetan el tipo), `general_board`
  (id 0, muestra todas las relaciones; sus nodos solo guardan posición/color) + `boards`
  propios, y `sentiment_overrides[lang]` aplicados al puntuar (`sentiment.apply_overrides`)
  sobre la caché v4, que guarda las posiciones negadas (`neg`): ajustar el léxico NO
  vuelve a pasar el corpus por spaCy. Libro: `frontend/js/libro.js`.
- **Simbología nativa de Cua-libre (regla de diseño, decisión del investigador
  2026-10-15):** círculo = código, cuadrado = categoría (borde grueso, nombre en
  mayúsculas). Es SIEMPRE la forma por defecto; el investigador puede elegir otra por
  nodo (`BoardNode.shape`: circle, square, diamond, hexagon, box) y «Nativa» la restaura.
  Las categorías conservan su borde grueso con cualquier forma. Trazos por tipo
  (`Relations.STROKES`): jerarquía gruesa con rombo en el origen, asociación de guiones,
  causalidad seguida con flecha, contradicción de puntos con marca de choque; el color
  de una relación es solo un añadido. Los cuadros se guardan enteros (PUT): todo nodo
  que se envíe pasa por `Relations._nodeOut` para no perder forma ni candado. En el
  organizador ⌘Z NO deshace codificaciones (tiene «↶ DESHACER MOVIMIENTO»).
- Windows sin WebView2: pywebview NO lanza error, recurre al motor de Internet Explorer
  y deja la ventana en blanco. `run.py` lo detecta (`window_engine_ok`) y usa el navegador.

## Licencia (decisión del investigador, 2026-10-15)

Cua-libre es **AGPL-3.0-or-later** (`LICENSE`, `pyproject.toml`, README, «Acerca de»),
sin mención institucional. Toda dependencia nueva DEBE ser compatible con la AGPL-3.0 y
quedar registrada en `AVISOS-DE-TERCEROS.md` (con su texto en `licencias/` si la licencia
lo exige, como las OFL de las fuentes o la Apache-2.0 de PDF.js). Comprobar la licencia
real con `importlib.metadata`, no de memoria (p. ej., `es_core_news_sm` es GPL-3.0 y
`pt_core_news_sm`, CC BY-SA 4.0). `LICENSE`, `AVISOS-DE-TERCEROS.md` y `licencias/`
viajan en los instaladores (los 4 lugares de empaquetado).

## Comandos

- Ejecutar: `./start.sh` (usa uv: aprovisiona Python 3.12+ y deps, abre la ventana)
- Solo servidor, sin ventana ni navegador: `CUALIBRE_PORT=8760 uv run run.py --servidor`
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
