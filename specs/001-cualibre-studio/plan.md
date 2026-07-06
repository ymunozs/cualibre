# Implementation Plan: CUA-LIBRE STUDIO — Estudio de Análisis Cualitativo

**Branch**: `001-cualibre-studio` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-cualibre-studio/spec.md`

## Summary

Reconstrucción estable de CUA-LIBRE STUDIO como **aplicación web local**: backend Python
(FastAPI + Uvicorn) que sirve una single-page app de HTML/CSS/JS vanilla. Se abandona
Streamlit porque su puente iframe↔session_state causó todos los fallos de v0.8.6–0.9.1
(Principio IV de la constitución). La interacción crítica —selección de texto, Nube Negra,
resaltado por posición— vive nativamente en el DOM del navegador; la comunicación con el
backend es HTTP/JSON vía `fetch`, un canal oficialmente soportado. El resaltado se ancla
por documento + offsets de caracteres (no por búsqueda de cadena) y se renderiza por
segmentación de rangos, lo que soporta citas repetidas y solapadas sin romper el HTML.

## Technical Context

**Language/Version**: Python 3.12+ gestionado por uv (el sistema solo trae 3.9; uv ya está
instalado y aprovisiona el intérprete); JavaScript ES2020 vanilla (frontend, sin framework
ni build step)

**Primary Dependencies**: FastAPI, Uvicorn, PyMuPDF (PDF), python-docx (DOCX),
python-multipart (upload), httpx (OpenAlex). Frontend: cero dependencias externas —
SVG/Canvas propio para gráficos, fuentes empaquetadas localmente.

**Storage**: JSON por proyecto en `~/Library/Application Support/cualibre/projects/`,
escritura atómica (temp + rename); `config.json` con el último proyecto activo.

**Testing**: pytest + httpx TestClient para el backend (API, extracción, NLP, CSV);
validación end-to-end del frontend según `quickstart.md` (Principio VII).

**Target Platform**: macOS (Mac del investigador), navegador moderno (Safari/Chrome),
100% offline salvo la vista Literatura (OpenAlex).

**Project Type**: Aplicación web local (backend + frontend servido estáticamente).

**Performance Goals**: corpus de 200 páginas fluido (< 1 s de respuesta perceptible al
seleccionar, SC-006); Analytics actualizadas < 2 s tras Enter (SC-005); ciclo de
codificación completo < 10 s (SC-001).

**Constraints**: offline-capable (sin CDN: fuentes y librerías locales); UTF-8 íntegro de
punta a punta; inicio con un solo comando (`./start.sh`); sin pérdida de datos ante cierre
abrupto (persistencia atómica tras cada mutación).

**Scale/Scope**: un usuario local; proyectos de decenas de documentos y cientos de códigos;
5 vistas (Pentagrama, NLP, Analytics, Exportar, Literatura) + selector de proyectos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del plan | Estado |
|-----------|----------------------|--------|
| I. Preservación total de funcionalidades | El inventario completo (importación, Canvas+resaltado, Nube Negra, Paleta, NLP triple, Analytics, exportación, OpenAlex) está en la spec (SC-008) y cada pieza tendrá tareas y verificación propias; nada se entrega sin el inventario completo. | ✅ |
| II. Canvas sagrado | El Canvas es un `<div>` de solo lectura; todos los inputs viven en la Paleta (derecha) o el importador (arriba). No existe el "bridge input" porque no hay bridge: la Nube Negra es el único elemento efímero permitido sobre el texto. | ✅ |
| III. Flujo expedito | Selección → Nube Negra con foco automático → Enter guarda / Escape cancela → resaltado y Analytics inmediatos. Todo en JS nativo + un `fetch` POST. | ✅ |
| IV. Tecnología nativamente confiable | Streamlit descartado (research.md, D1). Selección/popup/resaltado son operaciones DOM nativas; backend↔frontend por HTTP/JSON. Sin iframes, sin eventos sintéticos, sin reruns. | ✅ |
| V. Integridad de datos | Persistencia automática atómica tras cada mutación; CSV UTF-8 con BOM generado en backend con el módulo `csv` (escapado correcto); acciones destructivas con confirmación. | ✅ |
| VI. Estética brutalista | CSS propio con las tipografías empaquetadas (Space Grotesk, IBM Plex Mono, serif del sistema para corpus), paleta de 9 dominios como constantes compartidas backend/frontend. | ✅ |
| VII. Verificación antes de entrega | `quickstart.md` define el recorrido end-to-end obligatorio; pytest cubre el backend; la fase implement termina ejecutando la app real y el recorrido completo. | ✅ |

**Post-Phase 1 re-check**: sin violaciones; el diseño no introduce desviaciones. ✅

## Project Structure

### Documentation (this feature)

```text
specs/001-cualibre-studio/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones técnicas
├── data-model.md        # Fase 1: entidades y validaciones
├── quickstart.md        # Fase 1: guía de validación end-to-end
├── contracts/
│   └── api.md           # Fase 1: contrato HTTP del backend
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── __init__.py
├── app.py               # FastAPI: rutas API + estáticos + arranque
├── models.py            # Entidades (Pydantic): Project, Document, Code, dominios
├── storage.py           # Persistencia JSON atómica, multi-proyecto
├── extraction.py        # PDF (PyMuPDF), DOCX (python-docx), TXT
├── nlp.py               # Frecuencias, stopwords es/en, filtro de longitud
├── export.py            # CSV UTF-8 con BOM
├── literature.py        # Cliente OpenAlex (httpx, timeout, errores)
└── tests/
    ├── test_api.py      # Contrato HTTP completo
    ├── test_extraction.py
    ├── test_nlp.py
    ├── test_export.py
    └── test_storage.py

frontend/
├── index.html           # SPA: 5 vistas + importador + selector de proyecto
├── css/
│   └── brutal.css       # Sistema brutalista completo
├── js/
│   ├── api.js           # Capa fetch hacia el backend
│   ├── state.js         # Estado del cliente + render orquestado
│   ├── canvas.js        # Render del corpus + segmentación de resaltados + offsets
│   ├── nube.js          # Nube Negra (popup de codificación)
│   ├── paleta.js        # Paleta: códigos manuales, memos, banco de códigos
│   ├── charts.js        # Torta y barras SVG (Analytics y NLP)
│   ├── wordcloud.js     # Word cloud empaquetada (canvas, espiral)
│   └── views.js         # Navegación de pestañas, NLP, Exportar, Literatura
└── fonts/               # Space Grotesk + IBM Plex Mono (woff2, licencia OFL)

run.py                   # Lanza uvicorn y abre el navegador
start.sh                 # Comando único: uv run run.py (uv aprovisiona Python + deps)
pyproject.toml           # Dependencias y requires-python (>= 3.12)
```

**Structure Decision**: web app local con separación backend/frontend en la raíz del
repositorio. El frontend no tiene build step (archivos servidos tal cual por FastAPI
`StaticFiles`), lo que mantiene el proyecto operable por un no-programador.

## Diseño de la interacción crítica (Principios II–IV)

1. **Render del corpus**: `canvas.js` recibe los documentos y códigos del backend. Por cada
   documento genera un encabezado y su texto segmentado: se recolectan todos los offsets de
   inicio/fin de los códigos del documento, se ordenan, y el texto se parte en segmentos
   contiguos. Cada segmento se emite como nodo de texto o `<span>` plano (nunca anidado)
   con el color del código más reciente que lo cubre y `title` con los nombres de códigos.
   Resultado: HTML siempre válido, solapamientos y repeticiones seguros (FR-006, FR-007).
2. **Selección → offsets**: cada `<span>` de segmento lleva `data-doc` y `data-start`. Al
   `mouseup`, se toma `window.getSelection()`, se valida que ancla y foco estén dentro del
   mismo documento del Canvas, y se calcula `start/end` absolutos sumando el offset del
   nodo dentro de su segmento. Sin iframes: el Canvas vive en el mismo DOM que toda la app.
3. **Nube Negra**: `nube.js` posiciona el popup junto al rectángulo de la selección
   (`getBoundingClientRect`), enfoca el campo de nombre, Enter → `POST /api/codes` →
   re-render del Canvas y del contador de Analytics; Escape o clic fuera → cierra sin
   rastro. Dominio seleccionable también con teclas 1–9.
4. **Persistencia**: cada mutación (POST/PATCH/DELETE) persiste el proyecto completo de
   forma atómica antes de responder; el frontend nunca es dueño del estado durable.

## Complexity Tracking

Sin violaciones constitucionales que justificar. La única complejidad no trivial —el
algoritmo de segmentación de resaltados y el mapeo selección→offsets— es exigida
directamente por FR-006/FR-007 y queda aislada en `canvas.js` con casos de prueba propios.
