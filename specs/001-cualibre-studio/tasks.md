# Tasks: CUA-LIBRE STUDIO — Estudio de Análisis Cualitativo

**Input**: Design documents from `/specs/001-cualibre-studio/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Incluidos — el Principio VII (verificación) y el plan exigen pytest para el
backend; el frontend se verifica end-to-end con quickstart.md.

**Organization**: Tareas agrupadas por historia de usuario. Nota de secuencia: US2
(importación) se implementa antes que US1 (codificación) porque el Canvas necesita corpus
que codificar; ambas son P1.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: Inicialización del proyecto

- [X] T001 Crear `pyproject.toml` con requires-python >=3.12 y dependencias (fastapi, uvicorn, pymupdf, python-docx, python-multipart, httpx; grupo dev: pytest) y verificar `uv sync`
- [X] T002 Crear estructura de directorios (`backend/`, `backend/tests/`, `frontend/css`, `frontend/js`, `frontend/fonts`) con `__init__.py`, más `.gitignore` (venv, __pycache__, .DS_Store)
- [X] T003 [P] Descargar y empaquetar fuentes woff2 (Space Grotesk 500/700, IBM Plex Mono 400/700, licencias OFL) en `frontend/fonts/`; si no hay red, dejar pila de respaldo del sistema documentada en `frontend/css/brutal.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modelos, persistencia, esqueleto del servidor y de la SPA — bloquea todas las historias

- [X] T004 Implementar `backend/models.py`: constante `DOMAINS` (9 dominios+colores, data-model.md), modelos Pydantic `Document`, `Code`, `Project` y payloads de request con validaciones (dominio válido, nombre 1–200, invariantes de anclaje doc_id/start/end/quote)
- [X] T005 Implementar `backend/storage.py`: directorio `~/Library/Application Support/cualibre/projects/`, carga/guardado JSON UTF-8 (`ensure_ascii=False`), escritura atómica (temp + `os.replace`), `config.json` con `active_project_id`, operaciones crear/listar/renombrar/activar proyecto y auto-creación de "Mi proyecto" si no existe ninguno
- [X] T006 Implementar en `backend/app.py` el esqueleto FastAPI: montaje de estáticos (`/` → `frontend/index.html`, `/static/*`), endpoints de proyectos (`GET /api/projects`, `POST /api/projects`, `PATCH /api/projects/{id}`, `POST /api/projects/{id}/activate`, `GET /api/project`, `POST /api/project/reset` con `confirm:true`) según contracts/api.md; toda mutación persiste antes de responder
- [X] T007 [P] Escribir `backend/tests/test_storage.py`: escritura atómica, roundtrip UTF-8 (tildes/ñ), recuperación tras recarga, aislamiento entre proyectos
- [X] T008 [P] Escribir `backend/tests/test_api.py` (base): ciclo de vida de proyectos (crear/renombrar/activar/reset con y sin confirm) con TestClient
- [X] T009 [P] Crear `frontend/index.html`: shell de la SPA — cabecera con título y selector de proyecto, zona de importación superior, pestañas (◰ PENTAGRAMA, ⚡ NLP, ◫ ANALYTICS, ⇄ EXPORTAR, 📚 LITERATURA), layout Pentagrama con Canvas (izquierda, solo lectura) y Paleta (derecha); ningún input sobre el Canvas (Principio II)
- [X] T010 [P] Crear `frontend/css/brutal.css`: sistema brutalista completo — @font-face locales, variables CSS con la paleta de 9 dominios, fondo #FAFAFA, canvas #FDFDF7 con borde negro 3px, acento #FF3300, sombras duras, estilos de pestañas/botones/inputs/tablas y de la Nube Negra
- [X] T011 [P] Crear `frontend/js/api.js` (capa fetch de todos los endpoints del contrato, con manejo de errores que muestra `detail` al usuario) y `frontend/js/state.js` (estado del cliente: proyecto activo, documents, codes; carga inicial `GET /api/project`; funciones de re-render orquestado)
- [X] T012 Crear `frontend/js/views.js` (navegación de pestañas mostrando/ocultando vistas) e integrar todos los scripts en index.html
- [X] T013 Crear `run.py` (lanza Uvicorn en 127.0.0.1:8734 y abre el navegador al estar listo) y `start.sh` ejecutable (`uv run run.py`); verificar arranque real con `./start.sh`

**Checkpoint**: servidor arranca con un comando, SPA carga con proyecto vacío, tests de fundación en verde

---

## Phase 3: User Story 2 — Importación y gestión del corpus (Priority: P1)

**Goal**: Cargar PDF/DOCX/TXT, acumularlos en el corpus con identificación de origen, verlos en el Canvas, eliminar documentos con advertencia

**Independent Test**: Importar un PDF y un DOCX; ambos textos aparecen en el Canvas con separador por documento, tildes/ñ intactas; archivo corrupto → error claro sin tocar el corpus

- [X] T014 [P] [US2] Implementar `backend/extraction.py`: PDF (PyMuPDF), DOCX (python-docx), TXT (UTF-8 con fallback latin-1); error claro si el tipo no es soportado (415) o no hay texto extraíble, p. ej. PDF escaneado (422)
- [X] T015 [P] [US2] Escribir `backend/tests/test_extraction.py` con fixtures generadas (PDF vía PyMuPDF, DOCX vía python-docx, TXT con tildes/ñ) y casos de error (archivo corrupto, PDF sin capa de texto)
- [X] T016 [US2] Añadir a `backend/app.py`: `POST /api/documents` (multipart) y `DELETE /api/documents/{id}` con flujo 409+confirm cuando hay códigos asociados (borra documento y sus códigos); persistencia atómica
- [X] T017 [US2] Añadir a `backend/tests/test_api.py`: subida de documentos (los 3 formatos), rechazo de tipo no soportado, acumulación sin pérdida, DELETE con y sin códigos asociados (409 → confirm)
- [X] T018 [US2] Implementar `frontend/js/canvas.js` (render base): corpus por documento con encabezado del nombre de archivo y texto serif, saltos de línea preservados; el Canvas no contiene ningún control (Principio II) — la gestión de documentos vive en la Paleta
- [X] T019 [US2] Implementar la zona de importación en `frontend/js/views.js` + `index.html`: input de archivo (pdf/docx/txt), subida vía api.js, feedback de éxito/error visible, re-render del Canvas; sección "Documentos del corpus" en la Paleta con lista de documentos y acción de eliminar, con diálogo de advertencia que muestra cuántos códigos se perderán

**Checkpoint**: corpus importable y visible; US2 verificable por sí sola (quickstart paso 1)

---

## Phase 4: User Story 1 — Codificación expedita con Nube Negra (Priority: P1) 🎯 MVP

**Goal**: Seleccionar → dominio → nombre → Enter → código guardado + resaltado permanente con color del dominio, sin controles sobre el Canvas

**Independent Test**: Con un TXT cargado: codificar una frase con Enter; el popup desaparece, la frase queda pintada, el registro existe con cita/dominio/nombre/fecha/documento; Escape cancela; citas repetidas y solapadas no rompen la legibilidad

- [X] T020 [P] [US1] Añadir a `backend/app.py`: `POST /api/codes` con validaciones del contrato (dominio inválido, nombre vacío, offsets fuera de rango o incoherentes → 422); persistencia atómica antes de responder
- [X] T021 [P] [US1] Añadir a `backend/tests/test_api.py`: creación de códigos anclados y todos los casos 422; verificación de que el proyecto persiste el código creado
- [X] T022 [US1] Implementar en `frontend/js/canvas.js` la segmentación de rangos: recolectar límites start/end de los códigos por documento, partir el texto en segmentos contiguos, emitir cada segmento como nodo de texto o `<span>` plano (nunca anidado) con color del código más reciente que lo cubre, `title` con nombres de códigos y `data-doc`/`data-start` para el mapeo de offsets; solapamientos y repeticiones seguros (FR-006/007)
- [X] T023 [US1] Implementar en `frontend/js/canvas.js` el mapeo selección→offsets: en `mouseup`, validar que la selección (≥3 caracteres) vive dentro de un solo documento del Canvas y calcular start/end absolutos desde `data-start` + offset dentro del nodo; exponer `{docId, start, end, quote, rect}`
- [X] T024 [US1] Implementar `frontend/js/nube.js`: popup Nube Negra posicionado junto al rect de la selección, selector de dominio (con teclas 1–9), campo de nombre con foco automático, Enter → POST /api/codes → cierre + re-render Canvas/Paleta/Analytics; Escape o clic fuera → cierre sin rastro; nombre vacío → aviso sin guardar (FR-009–012)
- [ ] T025 [US1] Verificación manual del flujo crítico con la app corriendo (quickstart pasos 2–3, incluyendo citas repetidas, solapadas, Escape y nombre vacío)

**Checkpoint**: MVP — el corazón del producto funciona de punta a punta. Nota: la
verificación de "Analytics reflejan el código de inmediato" se completa en la Fase 8,
cuando exista la vista; T024 deja listo el hook de re-render.

---

## Phase 5: User Story 3 — Persistencia y multi-proyecto (Priority: P1)

**Goal**: Todo sobrevive al cierre; múltiples proyectos aislados con selector

**Independent Test**: Codificar 3 fragmentos, matar el servidor, relanzar: todo restaurado; crear segundo proyecto vacío y volver al primero intacto

- [X] T026 [US3] Implementar el selector de proyectos en `frontend/js/views.js` + `index.html`: listar, crear, renombrar y abrir proyectos vía api.js; al cambiar, recarga completa del estado (FR-032)
- [X] T027 [US3] Implementar el botón "Reiniciar proyecto" en la Paleta con diálogo de confirmación explícita que llama a `POST /api/project/reset` (FR-014); verificar que cancelar no borra nada
- [X] T028 [US3] Añadir a `backend/tests/test_api.py`: restauración del proyecto activo tras recrear la app (simula reinicio), aislamiento de corpus/códigos entre proyectos, reset rechazado sin `confirm:true`
- [X] T029 [US3] Verificación manual: quickstart pasos 9–10 (cierre y reapertura real con `./start.sh`, cambio de proyectos)

**Checkpoint**: las tres historias P1 completas — producto usable para trabajo real

---

## Phase 6: User Story 4 — Paleta: códigos manuales, memos y banco de códigos (Priority: P2)

**Goal**: Crear códigos manuales con memo; ver, editar y eliminar códigos existentes desde la Paleta

**Independent Test**: Crear código manual con memo → aparece con origen "Manual"; editar nombre/dominio de un código → el resaltado cambia de color; eliminar → resaltado desaparece

- [X] T030 [P] [US4] Añadir a `backend/app.py`: `PATCH /api/codes/{id}` (name/domain/memo mutables, anclaje inmutable) y `DELETE /api/codes/{id}` (FR-030/031)
- [X] T031 [P] [US4] Añadir a `backend/tests/test_api.py`: edición válida, intento de mutar anclaje ignorado/rechazado, eliminación, códigos manuales (doc_id null ⇒ start/end null, quote vacía)
- [X] T032 [US4] Implementar `frontend/js/paleta.js`: formulario manual (dominio, etiqueta, memo) con guardado vía POST /api/codes; banco de códigos listado en la Paleta (color de dominio, nombre, cita truncada, memo) con acciones editar (inline: nombre/dominio/memo) y eliminar con confirmación; re-render de Canvas y Analytics tras cada acción
- [ ] T033 [US4] Verificación manual: quickstart pasos 4–5

**Checkpoint**: gestión completa del banco de códigos

---

## Phase 7: User Story 5 — NLP triple (Priority: P2)

**Goal**: Frecuencias con stopwords es/en y longitud mínima; word cloud empaquetada + barras + tabla simultáneas

**Independent Test**: Con corpus cargado: cambiar idioma y longitud mínima altera resultados; las tres visualizaciones son coherentes entre sí

- [X] T034 [P] [US5] Implementar `backend/nlp.py`: tokenización `\w+` en minúsculas, stopwords embebidas completas (~300 es, ~180 en), filtro de longitud mínima, `Counter.most_common(top)`; añadir `GET /api/nlp?lang&min_len&top` a `backend/app.py`
- [X] T035 [P] [US5] Escribir `backend/tests/test_nlp.py`: exclusión de stopwords por idioma, filtro de longitud, conteos exactos, corpus vacío
- [X] T036 [US5] Implementar `frontend/js/wordcloud.js`: layout de word cloud empaquetada en `<canvas>` (espiral de Arquímedes + colisiones vía `measureText`), tamaño ∝ frecuencia, colores de la paleta (FR-034)
- [X] T037 [US5] Implementar la vista NLP en `frontend/js/views.js` + `charts.js`: controles de idioma y longitud mínima, word cloud + barras top 15 + tabla de conteo completa, renderizadas a la vez (FR-018)

**Checkpoint**: central de inteligencia léxica operativa

---

## Phase 8: User Story 6 — Analytics (Priority: P2)

**Goal**: Torta por dominios y barras por código con colores oficiales, actualizadas en cada codificación

**Independent Test**: Codificar en 2+ dominios → torta y barras con proporciones y colores correctos; nuevo código aparece sin refresco manual; sin códigos → mensaje orientador

- [X] T038 [P] [US6] Implementar en `frontend/js/charts.js` los generadores SVG brutalistas: torta (agregación por dominio) y barras (densidad por nombre de código, coloreadas por dominio), con etiquetas legibles y estado vacío con mensaje orientador
- [X] T039 [US6] Conectar la vista Analytics en `frontend/js/views.js`: cálculo de agregaciones desde `state.codes`, re-render automático tras cada mutación de códigos (crear/editar/eliminar, Nube o Paleta) — FR-019/020, SC-005

**Checkpoint**: retroalimentación analítica en tiempo real

---

## Phase 9: User Story 7 — Exportación (Priority: P2)

**Goal**: Tabla completa del banco + CSV UTF-8 con BOM que abre perfecto en Excel

**Independent Test**: Exportar códigos con tildes/ñ/comas/comillas en citas → CSV con columnas y caracteres íntegros

- [X] T040 [P] [US7] Implementar `backend/export.py` (módulo `csv`, BOM utf-8-sig, columnas id/fecha/documento/dominio/codigo/cita/memo, documento = filename o "Manual") y `GET /api/export.csv` con Content-Disposition en `backend/app.py`
- [X] T041 [P] [US7] Escribir `backend/tests/test_export.py`: BOM presente, escapado RFC 4180 (comas, comillas, saltos de línea en citas), tildes/ñ intactas, roundtrip con `csv.reader`
- [X] T042 [US7] Implementar la vista Exportar en `frontend/js/views.js`: tabla completa del banco de códigos y botón de descarga apuntando a `/api/export.csv`

**Checkpoint**: vía de salida hacia Excel garantizada

---

## Phase 10: User Story 8 — Literatura OpenAlex (Priority: P3)

**Goal**: Búsqueda por conceptos con título, año, citas y DOI; fallo de red no afecta lo local

**Independent Test**: Buscar "Vygotsky emotions education" → resultados con DOI clicable; sin red → mensaje amigable, el resto de la app sigue operativa

- [X] T043 [P] [US8] Implementar `backend/literature.py`: cliente httpx a `api.openalex.org/works?search=` con timeout 10 s y `mailto`, mapeo a `{title, year, cited_by_count, doi}`, máx. 10; `GET /api/literature?q=` en `backend/app.py` con 502 amigable ante fallo de red (FR-023/024)
- [X] T044 [P] [US8] Escribir test en `backend/tests/test_api.py` con transporte httpx mockeado: resultados bien mapeados y fallo de red → 502 con mensaje claro
- [X] T045 [US8] Implementar la vista Literatura en `frontend/js/views.js`: campo de búsqueda, tarjetas de resultado (título, año, citas, enlace DOI), estado de error visible

**Checkpoint**: inventario constitucional completo (8/8 funcionalidades)

---

## Phase 11: Polish & Cross-Cutting

- [X] T046 [P] Escribir `README.md` en español para el investigador: qué es, cómo iniciar (`./start.sh`), dónde viven los datos, cómo respaldar proyectos
- [X] T047 Prueba de rendimiento: generar un TXT sintético de ~200 páginas, importarlo y verificar fluidez de lectura/selección/codificación (SC-006); optimizar render si hace falta
- [ ] T048 Ejecutar la validación end-to-end completa de `specs/001-cualibre-studio/quickstart.md` (13 pasos) con la app real y marcar el inventario constitucional (SC-008); corregir todo lo que falle antes de declarar la versión lista

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)** → **Foundational (P2)** → historias
- **US2 (importación)** primero entre las historias: produce el corpus que US1 necesita
- **US1 (codificación)** después de US2 — es el MVP
- **US3 (persistencia/proyectos)** después de US1 (la persistencia base ya existe desde T005; aquí se completa selector + reset + verificación)
- **US4–US7** dependen solo de Foundational + US1 (usan códigos); pueden ir en cualquier orden tras la Fase 5
- **US8 (Literatura)** independiente: solo necesita Foundational
- **Polish** al final

### Parallel Opportunities

- T003 ∥ T001–T002; T007/T008/T009/T010/T011 entre sí; T014∥T015; T020∥T021; T030∥T031; T034∥T035; T038 ∥ backend de otras historias; T040∥T041; T043∥T044; T046 ∥ T047
- US5, US6, US7 y US8 son paralelizables entre sí una vez completada la Fase 6

## Implementation Strategy

**MVP** = Fases 1–4 (Setup + Foundational + US2 + US1): importar y codificar con la Nube
Negra, con resaltado estable. **Stop & validate** en cada checkpoint con la app corriendo
(Principio VII). Luego incremental: US3 → US4 → US5/US6/US7 → US8 → Polish. Cada historia
se entrega sin romper las anteriores (Principio I: nunca eliminar funcionalidades).
