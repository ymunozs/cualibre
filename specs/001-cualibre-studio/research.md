# Research — CUA-LIBRE STUDIO (Fase 0)

**Date**: 2026-07-06 | **Plan**: [plan.md](./plan.md)

## D1. Framework de la aplicación: FastAPI + SPA vanilla (Streamlit descartado)

- **Decision**: Backend FastAPI + Uvicorn sirviendo una SPA de HTML/CSS/JS vanilla.
- **Rationale**: La interacción central del producto (seleccionar texto → popup → commit →
  resaltado inmediato) es una operación de DOM. En Streamlit el texto vive dentro de un
  iframe (`components.html`) aislado del árbol de widgets; todas las versiones 0.8.6–0.9.1
  fracasaron intentando puentear ese aislamiento (inyectar valores en inputs ocultos y
  disparar eventos sintéticos esperando un rerun). El Principio IV de la constitución
  prohíbe ese patrón. Con una SPA propia, la selección, el popup y el resaltado son código
  nativo del navegador y el backend solo persiste/procesa vía HTTP/JSON.
- **Alternatives considered**:
  - *Streamlit + custom bidirectional component*: técnicamente posible
    (`streamlit-component-lib`), pero exige build tooling de Node, sigue atado al modelo
    rerun (latencia y pérdida de foco) y mantiene la fragilidad estructural que la
    constitución veta.
  - *Electron/Tauri*: empaquetado de escritorio real, pero añade toolchain pesada (Node/
    Rust) injustificada para un solo usuario que acepta "comando único + navegador".
  - *Flask*: viable; FastAPI se prefiere por validación Pydantic integrada (modelos de
    datos tipados = menos corrupción de estado) y `TestClient` asíncrono maduro.

## D2. Anclaje del resaltado: documento + offsets de caracteres

- **Decision**: Cada código con cita guarda `doc_id`, `start`, `end` (offsets UTF-16 del
  texto del documento) además de la cadena de la cita. El render usa segmentación de
  rangos: se parten los textos en los límites de todos los códigos y cada segmento se emite
  como un único `<span>` plano.
- **Rationale**: El `str.replace` de las versiones anteriores rompía el HTML (etiquetas
  dentro de etiquetas, "espagueti") y pintaba todas las ocurrencias de una cadena repetida.
  Los offsets anclan a la posición exacta seleccionada (FR-007) y la segmentación plana
  garantiza HTML válido con cualquier combinación de solapamientos (FR-006).
- **Nota Unicode**: los offsets se calculan y se consumen exclusivamente en JavaScript
  (UTF-16 code units). El backend los trata como enteros opacos y nunca rebana el texto
  con ellos (la cita textual viaja redundante en el payload), así que la discrepancia
  UTF-16 vs code points de Python no puede corromper nada.
- **Alternatives considered**: anclaje por búsqueda de cadena (roto, pinta repeticiones);
  anclaje por XPath/DOM-range serializado (frágil ante re-render); CRDT/annotation layers
  (sobredimensionado).

## D3. Gráficos: SVG/Canvas propio, sin librerías

- **Decision**: Torta y barras en SVG generado por `charts.js`; word cloud en `<canvas>`
  con layout de espiral de Arquímedes + detección de colisiones por `measureText`.
- **Rationale**: Requisito offline (sin CDN) + estética brutalista total (Plotly no se deja
  estilizar a bordes duros y tipografía propia sin pelear). Una torta y unas barras son
  ~150 líneas de SVG; la word cloud empaquetada (FR-034) requiere layout propio de todos
  modos porque la de v0.9.1 (scatter de Plotly) fue explícitamente rechazada en clarify.
- **Alternatives considered**: vendorizar Chart.js (~200 KB, estilo ajeno al sistema);
  vendorizar wordcloud2.js (posible, pero el layout espiral propio es ~100 líneas y
  mantiene cero dependencias); volver a Plotly (estética y peso injustificados).

## D4. Persistencia: JSON por proyecto con escritura atómica

- **Decision**: `~/Library/Application Support/cualibre/projects/<uuid>.json` (un archivo
  por proyecto, UTF-8, `ensure_ascii=False`) + `config.json` con `active_project_id`.
  Escritura: volcar a archivo temporal en el mismo directorio + `os.replace` (atómico en
  APFS). Persistir tras cada mutación, antes de responder al frontend.
- **Rationale**: Un investigador, un archivo legible y respaldable por proyecto; `os.replace`
  garantiza que un cierre abrupto deja o la versión anterior o la nueva, nunca un archivo
  a medias (edge case "apagón" de la spec). JSON permite inspección manual y migración
  futura.
- **Alternatives considered**: SQLite (más robusto para concurrencia que aquí no existe;
  menos transparente para respaldo manual); pickle (opaco, inseguro, fue el enfoque
  original); localStorage del navegador (se pierde al limpiar el navegador, viola FR-025).

## D5. Extracción de texto

- **Decision**: PyMuPDF (`fitz`) para PDF, python-docx para DOCX, decodificación UTF-8 con
  fallback `latin-1` para TXT. Si un PDF no tiene capa de texto (extracción vacía), se
  rechaza con mensaje claro (FR-004, edge case de PDF escaneado).
- **Rationale**: Son las bibliotecas ya validadas por el proyecto (constitución,
  Restricciones Técnicas) y las más maduras del ecosistema.
- **Alternatives considered**: pdfplumber (más lento); textract (dependencias del sistema).

## D6. NLP: Python puro con stopwords embebidas

- **Decision**: Tokenización `\w+` sobre el corpus en minúsculas, stopwords completas
  embebidas para español (~300 palabras) e inglés (~180), filtro de longitud mínima,
  `collections.Counter`. Endpoint `GET /api/nlp?lang=es&min_len=4`.
- **Rationale**: Las listas de 7 stopwords de las versiones anteriores eran decorativas;
  listas completas embebidas dan resultados útiles sin arrastrar NLTK/spaCy (decenas de MB
  y descargas en runtime que violarían el modo offline).
- **Alternatives considered**: NLTK/spaCy (peso y descargas injustificadas para conteo de
  frecuencias); stop-words de PyPI (lista razonable, pero embeber elimina una dependencia).

## D7. OpenAlex

- **Decision**: `httpx` con timeout de 10 s, parámetro `mailto` (cortesía de la API),
  máximo 10 resultados con título, año, citas y DOI. Errores de red → HTTP 502 con mensaje
  amigable; el resto de la app no se ve afectada (FR-024).
- **Rationale**: API pública sin key; `httpx` ya está en el stack (tests). Funcionalidad
  protegida por el Principio I tras haber sido borrada por el agente anterior.
- **Alternatives considered**: `requests` (una dependencia más sin ventaja); Crossref
  (OpenAlex fue el pedido explícito del investigador).

## D8. Tipografías offline

- **Decision**: Empaquetar Space Grotesk e IBM Plex Mono como woff2 locales (licencia OFL)
  en `frontend/fonts/` con `@font-face`; el corpus usa la pila serif del sistema
  (Georgia/Charter). Si los archivos no pudieran obtenerse durante la implementación, la
  pila de respaldo del sistema mantiene la jerarquía visual y se deja tarea pendiente.
- **Rationale**: El `@import` de Google Fonts de las versiones anteriores viola el
  requisito offline. OFL permite redistribución local.
- **Alternatives considered**: Google Fonts CDN (online-only, descartado); solo fuentes de
  sistema (pierde identidad del Principio VI).

## D9. Arranque con comando único

- **Decision**: `start.sh` (ejecutable) basado en **uv** (ya instalado en la máquina del
  investigador; el sistema solo trae Python 3.9 de Xcode y no hay Homebrew): `uv run run.py`
  con `pyproject.toml` (requires-python >=3.12) hace que uv aprovisione el intérprete y las
  dependencias automáticamente. `run.py` lanza Uvicorn en `127.0.0.1:8734` y abre el
  navegador con `webbrowser.open` cuando el servidor responde. uv ya tiene CPython 3.14
  instalado localmente.
- **Rationale**: SC-007 exige que un no-programador inicie la app con un comando; uv
  resuelve intérprete + dependencias sin pasos manuales; el puerto fijo poco común evita
  colisiones y hace la URL predecible.
- **Alternatives considered**: venv + pip con el Python del sistema (3.9 es demasiado
  viejo para FastAPI/Pydantic modernos); empaquetar con PyInstaller (frágil con PyMuPDF,
  lento de iterar); pedir instalación manual de Python (fricción para el usuario objetivo).
