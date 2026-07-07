# Feature Specification: CUA-LIBRE STUDIO — Estudio de Análisis Cualitativo

**Feature Branch**: `001-cualibre-studio`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "Aplicación local de análisis cualitativo de datos (QDA/CAQDAS) para investigadores en ciencias sociales, que reconstruye y estabiliza lo intentado en las versiones 0.8.6–0.9.1: importación de corpus (PDF/DOCX/TXT), Canvas de lectura con resaltado por dominio, Nube Negra de codificación expedita, Paleta de control con códigos manuales y memos, NLP triple, Analytics sincronizadas, exportación CSV UTF-8 y búsqueda de literatura OpenAlex, con persistencia local automática y estética brutalista."

## Clarifications

### Session 2026-07-06

- Q: ¿Debe esta versión permitir corregir códigos ya creados? → A: Sí, edición (nombre,
  dominio, memo) y eliminación individual, con retiro del resaltado al eliminar.
- Q: ¿Un solo proyecto o múltiples proyectos separados? → A: Múltiples proyectos con
  selector (crear/abrir/renombrar); cada proyecto aísla su corpus, códigos y memos; al
  abrir la app se restaura el último proyecto activo.
- Q: ¿Se puede eliminar un documento individual del corpus? → A: Sí, con advertencia: si
  tiene códigos asociados se informa cuántos se perderán y se pide confirmación explícita.
- Q: ¿Cómo debe verse la nube de palabras del NLP? → A: Nube real empaquetada (layout
  clásico de word cloud: palabras llenando el espacio, tamaño proporcional a frecuencia,
  colores de la paleta), no el texto disperso de v0.9.1.

### Session 2026-07-06 (cierre v1, tras validación del investigador)

- Pestañas de documentos en el Pentagrama para cambiar entre documentos del corpus
  (más una vista "Todos").
- Botón visible de guardar proyecto con confirmación horaria (el autoguardado se mantiene).
- Arrastrar una selección textual sobre un código existente del banco re-aplica ese
  código (nueva cita con el mismo nombre y dominio).
- Relaciones entre códigos con tipos jerarquía/asociación/causalidad/contradicción,
  con organizador visual (grafo) y árbol de jerarquía.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Codificación expedita desde el Canvas (Priority: P1)

El investigador carga un documento de su corpus (una entrevista en PDF, DOCX o TXT), lo lee
en el Canvas y, cuando encuentra una unidad de sentido, la selecciona con el cursor. Junto a
la selección aparece un popup efímero (la "Nube Negra") donde elige el dominio del código
(de 9 categorías fijas), escribe el nombre del código y presiona Enter. El popup desaparece,
el fragmento queda resaltado permanentemente en el Canvas con el color de su dominio, y el
código con su cita textual queda registrado en el banco de códigos.

**Why this priority**: Es el corazón de la herramienta y la interacción que falló en todas
las versiones anteriores (0.8.6–0.9.1). Sin este flujo confiable, no existe el producto.

**Independent Test**: Cargar un TXT de prueba, seleccionar una frase, codificarla con Enter,
y verificar que (a) el popup desaparece, (b) la frase queda pintada con el color del dominio
elegido, (c) el registro aparece en el banco de códigos con cita, dominio, nombre, fecha y
documento de origen.

**Acceptance Scenarios**:

1. **Given** un documento cargado en el Canvas, **When** el investigador selecciona un
   fragmento de más de 2 caracteres, **Then** la Nube Negra aparece adyacente a la selección
   con el selector de dominio y el campo de nombre enfocado, lista para escribir.
2. **Given** la Nube Negra abierta con dominio elegido y nombre escrito, **When** presiona
   Enter, **Then** el código se guarda, el popup desaparece, el fragmento queda resaltado con
   el color del dominio y las Analytics reflejan el nuevo código de inmediato.
3. **Given** la Nube Negra abierta, **When** presiona Escape o hace clic fuera, **Then** el
   popup desaparece sin guardar nada y sin dejar residuos visuales.
4. **Given** un fragmento ya codificado (resaltado), **When** el investigador codifica otro
   fragmento que se solapa o repite texto del primero, **Then** ambos resaltados se muestran
   sin corromper la legibilidad del corpus (nunca texto con etiquetas rotas visibles).
5. **Given** cualquier estado de la aplicación, **When** el investigador mira el Canvas,
   **Then** no hay ningún control de entrada de datos (campos de texto, botones permanentes)
   visible sobre o dentro del área de lectura.

---

### User Story 2 - Importación y gestión del corpus (Priority: P1)

El investigador importa uno o varios documentos (PDF, DOCX, TXT) desde la zona de
importación ubicada en la parte superior de la página. Cada documento se acumula en el
corpus y el Canvas muestra el texto identificando de qué documento proviene cada sección.

**Why this priority**: Sin corpus no hay nada que codificar; es prerrequisito del flujo P1
y funcionalidad de primera necesidad en cada sesión.

**Independent Test**: Importar un PDF y un DOCX; verificar que ambos textos aparecen en el
Canvas con un separador que indica el nombre de archivo de origen, con tildes y ñ intactas.

**Acceptance Scenarios**:

1. **Given** la aplicación abierta, **When** el investigador carga un PDF, **Then** el texto
   extraído aparece en el Canvas encabezado por el nombre del documento.
2. **Given** un corpus con un documento, **When** carga un segundo documento, **Then** el
   nuevo texto se acumula a continuación sin borrar el anterior ni sus codificaciones.
3. **Given** un documento con caracteres del español (á, é, ñ, ü), **When** se importa,
   **Then** todos los caracteres se muestran correctamente.
4. **Given** un archivo corrupto o ilegible, **When** se intenta importar, **Then** la
   aplicación muestra un error claro y el corpus existente queda intacto.

---

### User Story 3 - Persistencia automática del proyecto (Priority: P1)

El investigador trabaja durante una sesión (importa documentos, codifica, escribe memos),
cierra la aplicación o su computadora, y al reabrir la aplicación encuentra todo su trabajo
exactamente como lo dejó: corpus, códigos, resaltados y memos.

**Why this priority**: Los datos codificados representan horas de juicio experto
irreproducible; perderlos rompe la confianza en la herramienta de forma terminal.

**Independent Test**: Codificar 3 fragmentos, cerrar completamente la aplicación, reabrirla
y verificar que corpus, resaltados y banco de códigos están íntegros.

**Acceptance Scenarios**:

1. **Given** una sesión con corpus y códigos, **When** el investigador cierra y reabre la
   aplicación, **Then** todo el estado (corpus, códigos, memos, resaltados) se restaura.
2. **Given** cualquier acción de codificación o memo, **When** se completa, **Then** se
   persiste automáticamente sin requerir un botón "guardar proyecto".
3. **Given** el botón de reiniciar proyecto, **When** se presiona, **Then** se solicita
   confirmación explícita antes de borrar cualquier dato.

---

### User Story 4 - Codificación manual y memos desde la Paleta (Priority: P2)

El investigador usa la Paleta de control (columna derecha) para registrar códigos que no
provienen de una selección (códigos teóricos, categorías emergentes) eligiendo dominio,
escribiendo la etiqueta y opcionalmente un memo de investigación.

**Why this priority**: Complementa el flujo expedito; el análisis cualitativo requiere
también códigos conceptuales sin cita textual.

**Independent Test**: Crear un código manual con memo desde la Paleta y verificar que
aparece en el banco de códigos marcado como de origen manual.

**Acceptance Scenarios**:

1. **Given** la Paleta visible, **When** el investigador elige dominio, escribe etiqueta y
   guarda, **Then** el código queda registrado con origen "Manual" y aparece en Analytics.
2. **Given** un memo escrito junto al código manual, **When** se guarda, **Then** el memo
   queda asociado al registro y es visible en el banco de códigos y la exportación.

---

### User Story 5 - Análisis NLP del corpus (Priority: P2)

El investigador abre la vista NLP para explorar las frecuencias léxicas de su corpus:
elige el idioma (español o inglés) para aplicar las stopwords correctas, ajusta la longitud
mínima de palabra, y obtiene tres visualizaciones simultáneas: una nube de palabras, un
gráfico de barras con los términos top y una tabla con el listado y conteo exacto.

**Why this priority**: Herramienta exploratoria valiosa que orienta la codificación, pero
el análisis puede avanzar sin ella.

**Independent Test**: Con un corpus cargado, abrir NLP, cambiar idioma y longitud mínima, y
verificar que las tres visualizaciones se generan y responden a los filtros.

**Acceptance Scenarios**:

1. **Given** un corpus en español, **When** se procesa con idioma "Español", **Then** las
   palabras funcionales del español (para, este, con, del…) quedan excluidas del conteo.
2. **Given** el filtro de longitud mínima en N caracteres, **When** se procesa, **Then**
   ninguna palabra de menos de N caracteres aparece en los resultados.
3. **Given** resultados generados, **When** el investigador mira la vista, **Then** ve
   nube de palabras, barras de frecuencia y tabla de conteo a la vez, coherentes entre sí.

---

### User Story 6 - Analytics de codificación (Priority: P2)

El investigador consulta la vista Analytics para ver la distribución de su codificación:
un gráfico de torta con la proporción por dominios y un gráfico de barras con la densidad
de códigos, ambos usando los colores oficiales de la paleta de dominios.

**Why this priority**: Retroalimenta el proceso analítico; depende de que exista
codificación previa (P1).

**Independent Test**: Codificar fragmentos de al menos dos dominios distintos y verificar
que la torta y las barras muestran los colores y proporciones correctos.

**Acceptance Scenarios**:

1. **Given** códigos registrados, **When** se abre Analytics, **Then** la torta muestra la
   distribución por dominios con los colores oficiales de cada dominio.
2. **Given** un nuevo código creado (por Nube Negra o Paleta), **When** se vuelve a la
   vista Analytics, **Then** los gráficos incluyen el nuevo código sin acción adicional.
3. **Given** ningún código registrado, **When** se abre Analytics, **Then** se muestra un
   mensaje orientador en lugar de gráficos vacíos.

---

### User Story 7 - Exportación del banco de códigos (Priority: P2)

El investigador revisa la tabla completa de su banco de códigos y la descarga como archivo
CSV en UTF-8 (con BOM) que abre correctamente en Excel, con tildes y ñ intactas.

**Why this priority**: Es la vía de salida del trabajo hacia informes y otros análisis;
esencial pero de uso menos frecuente que la codificación.

**Independent Test**: Codificar fragmentos con tildes/ñ en los nombres, exportar el CSV y
abrirlo en Excel verificando la integridad de los caracteres y de todas las columnas.

**Acceptance Scenarios**:

1. **Given** un banco de códigos con registros, **When** se abre la vista Exportar,
   **Then** se muestra la tabla completa (id, fecha, documento, dominio, código, cita, memo).
2. **Given** la tabla visible, **When** se descarga el CSV y se abre en Excel, **Then**
   todos los caracteres del español se muestran correctamente y no se pierde ninguna columna.

---

### User Story 8 - Búsqueda de literatura en OpenAlex (Priority: P3)

El investigador busca literatura científica por conceptos desde la vista Literatura; la
aplicación consulta OpenAlex y muestra los resultados con título, año de publicación,
número de citas y enlace DOI.

**Why this priority**: Funcionalidad satélite valiosa (y protegida por la constitución tras
haber sido borrada por el agente anterior), pero no bloquea el análisis cualitativo.

**Independent Test**: Buscar un concepto (p. ej. "Vygotsky emotions education") y verificar
que se listan resultados con título, año, citas y DOI clicable.

**Acceptance Scenarios**:

1. **Given** la vista Literatura, **When** se busca un término, **Then** se muestran hasta
   los primeros resultados relevantes con título, año, conteo de citas y enlace DOI.
2. **Given** una búsqueda sin conexión a internet, **When** se ejecuta, **Then** la
   aplicación informa el problema sin afectar el resto del trabajo local.

---

### Edge Cases

- Selección que cruza el separador entre dos documentos del corpus: no es codificable (un
  código pertenece a un único documento); la Nube Negra no se abre y la selección se ignora
  sin afectar los encabezados.
- Citas idénticas o repetidas en el corpus (frases que aparecen varias veces): el resaltado
  debe anclarse a la posición seleccionada, no a todas las ocurrencias del texto.
- Citas solapadas (una selección dentro de otra ya codificada): ambas deben persistir y
  mostrarse sin HTML roto; la más reciente debe ser visualmente distinguible.
- Selección de menos de 3 caracteres: no debe abrir la Nube Negra.
- Confirmar la Nube Negra con el nombre de código vacío: no debe guardar; debe indicar que
  falta el nombre.
- PDF escaneado sin capa de texto: informar que no hay texto extraíble en lugar de importar
  contenido vacío en silencio.
- Corpus muy grande (cientos de páginas): la lectura y el resaltado deben seguir siendo
  fluidos.
- Reapertura tras un cierre abrupto (fuerza de cierre, apagón): el estado persistido más
  reciente debe recuperarse sin corrupción.
- Exportación con comillas, saltos de línea o comas dentro de las citas: el CSV debe
  mantener la estructura de columnas.

## Requirements *(mandatory)*

### Functional Requirements

**Importación de corpus**

- **FR-001**: El sistema MUST permitir importar documentos PDF, DOCX y TXT desde una zona
  de carga ubicada en la jerarquía superior de la página (nunca en la Paleta ni sobre el
  Canvas).
- **FR-002**: El sistema MUST acumular los documentos importados en un corpus único,
  identificando visualmente el documento de origen de cada sección.
- **FR-003**: El sistema MUST preservar íntegramente los caracteres UTF-8 (tildes, ñ, ü)
  desde la importación hasta la exportación.
- **FR-004**: El sistema MUST rechazar con mensaje claro los archivos ilegibles o sin texto
  extraíble, sin alterar el corpus existente.
- **FR-033**: El sistema MUST permitir eliminar un documento individual del corpus; si el
  documento tiene códigos asociados, MUST advertir cuántos se perderán y pedir confirmación
  explícita antes de eliminar documento y códigos.

**Canvas de lectura**

- **FR-005**: El Canvas MUST mostrar el corpus en tipografía serif legible y ser exclusivo
  para lectura, selección y resaltado: ningún control de entrada de datos puede quedar
  visible sobre, dentro o inmediatamente encima del Canvas.
- **FR-006**: El Canvas MUST mostrar los fragmentos codificados resaltados permanentemente
  con el color del dominio de su código, sin corromper jamás la legibilidad del texto,
  incluso con citas repetidas o solapadas.
- **FR-007**: El resaltado MUST anclarse a la posición del texto seleccionado (no a todas
  las ocurrencias de la misma cadena).
- **FR-008**: Al pasar el cursor sobre un fragmento resaltado, el sistema MUST mostrar el
  nombre del código asociado.

**Nube Negra (codificación expedita)**

- **FR-009**: Al seleccionar 3 o más caracteres en el Canvas, el sistema MUST mostrar un
  popup efímero adyacente a la selección con: selector de dominio (9 categorías), campo de
  nombre de código (con foco automático) e indicación de confirmar con Enter.
- **FR-010**: Enter MUST guardar el código (dominio + nombre + cita + documento + fecha),
  cerrar el popup, aplicar el resaltado y actualizar Analytics, todo de inmediato.
- **FR-011**: Escape o clic fuera del popup MUST cancelar sin guardar ni dejar residuos.
- **FR-012**: El sistema MUST impedir guardar desde la Nube Negra si el nombre del código
  está vacío, indicándolo al investigador.

**Paleta de control**

- **FR-013**: La Paleta (columna derecha) MUST permitir crear códigos manuales con dominio,
  etiqueta y memo opcional, registrados con origen "Manual".
- **FR-014**: La Paleta MUST ofrecer la acción de reiniciar el proyecto solo con
  confirmación explícita previa.

**Banco de códigos**

- **FR-015**: Cada registro del banco de códigos MUST contener: identificador, fecha y hora,
  documento de origen, dominio, nombre del código, cita textual (o marca de manual) y memo.
- **FR-016**: Los 9 dominios y sus colores son fijos: Emocional #FF3300, Descriptivo
  #0066FF, In Vivo #FFCC00, Tensión/CHAT #FF0066, Proceso #6600CC, Teórico #00CC66,
  Relacional #0099CC, Crítico #CC0000, Método #333333.
- **FR-030**: El sistema MUST permitir editar un código existente (nombre, dominio y memo);
  al cambiar el dominio, el color del resaltado asociado se actualiza en el Canvas.
- **FR-031**: El sistema MUST permitir eliminar un código individual con confirmación; al
  eliminarlo, su resaltado desaparece del Canvas y las Analytics se actualizan.

**NLP**

- **FR-017**: La vista NLP MUST procesar el corpus con selector de idioma (español/inglés)
  aplicando stopwords apropiadas al idioma elegido, y filtro configurable de longitud
  mínima de palabra.
- **FR-018**: La vista NLP MUST presentar simultáneamente tres visualizaciones coherentes:
  nube de palabras, gráfico de barras de términos top y tabla de listado con conteo exacto.
- **FR-034**: La nube de palabras MUST usar un layout de word cloud real (palabras
  empaquetadas llenando el espacio, tamaño proporcional a la frecuencia, colores de la
  paleta del proyecto), no una disposición lineal de texto.

**Analytics**

- **FR-019**: La vista Analytics MUST mostrar la distribución de códigos por dominio
  (torta) y la densidad de códigos (barras), usando los colores oficiales de los dominios.
- **FR-020**: Las Analytics MUST reflejar cada nueva codificación de inmediato, sin acción
  manual de refresco.

**Exportación**

- **FR-021**: La vista Exportar MUST mostrar la tabla completa del banco de códigos y
  permitir descargar un CSV en UTF-8 con BOM que abra correctamente en Excel.
- **FR-022**: El CSV MUST escapar correctamente comillas, comas y saltos de línea dentro de
  las citas y memos.

**Literatura**

- **FR-023**: La vista Literatura MUST permitir buscar obras por conceptos en OpenAlex y
  mostrar título, año, número de citas y enlace DOI de cada resultado.
- **FR-024**: Un fallo de red en Literatura MUST informarse sin afectar el trabajo local.

**Navegación de documentos y guardado (cierre v1)**

- **FR-035**: Cuando el corpus tenga más de un documento, el Pentagrama MUST ofrecer
  pestañas para cambiar entre documentos individuales y una vista "Todos"; las pestañas
  son navegación, no entrada de datos, y viven fuera del área de lectura.
- **FR-036**: La cabecera MUST ofrecer un botón de guardar proyecto que fuerza la
  persistencia y confirma visiblemente con la hora del guardado (el autoguardado FR-025
  se mantiene intacto).

**Re-aplicación de códigos y relaciones (cierre v1)**

- **FR-037**: Arrastrar una selección del Canvas y soltarla sobre un código del banco
  MUST crear una nueva cita codificada con el nombre y dominio de ese código.
- **FR-038**: El sistema MUST permitir crear y eliminar relaciones dirigidas entre
  códigos existentes (por nombre) con tipo jerarquía, asociación, causalidad o
  contradicción; una relación cuyos códigos desaparecen del proyecto se elimina sola.
- **FR-039**: Una vista Relaciones MUST visualizar las relaciones como organizador
  (grafo con nodos coloreados por dominio y aristas distinguibles por tipo sin depender
  solo del color) y como árbol construido desde las relaciones de jerarquía.

**Música de foco (v1.1)**

- **FR-040**: Una barra delgada fija al pie MUST ofrecer música de foco con dos fuentes:
  (a) pistas locales del investigador desde la carpeta `musica/` del directorio de datos
  (offline, fuente por defecto, con reproducción continua, siguiente y volumen) y
  (b) Claude FM, el stream lo-fi de Anthropic en YouTube (online, opcional). La música
  nunca MUST bloquear ni interferir el flujo de análisis; si no hay pistas, la barra
  indica dónde depositarlas.

**Persistencia**

- **FR-025**: El sistema MUST persistir automáticamente en disco local todo el estado del
  proyecto (corpus, códigos, resaltados, memos) tras cada cambio, sin botón de guardado.
- **FR-026**: Al abrir la aplicación, el sistema MUST restaurar el último proyecto activo
  con su estado persistido más reciente.
- **FR-032**: El sistema MUST permitir gestionar múltiples proyectos: crear, abrir y
  renombrar proyectos, cada uno con corpus, códigos y memos completamente aislados.

**Identidad visual**

- **FR-027**: La interfaz MUST seguir la estética brutalista definida en la constitución:
  Space Grotesk (títulos), IBM Plex Mono (interfaz), serif (corpus), fondo #FAFAFA, canvas
  #FDFDF7, bordes negros gruesos, acento #FF3300, sombras duras.

**Arquitectura de la experiencia**

- **FR-028**: La aplicación MUST organizarse en las vistas: Pentagrama (Canvas + Paleta),
  NLP, Analytics, Exportar y Literatura, con el importador en la jerarquía superior.
- **FR-029**: La aplicación MUST poder iniciarse con un único comando simple y abrirse en
  el navegador del investigador sin configuración adicional.

### Key Entities

- **Documento**: un archivo importado al corpus; atributos: nombre de archivo, texto
  extraído, fecha de importación, orden dentro del corpus.
- **Corpus**: la concatenación ordenada de los documentos, con separadores que identifican
  el origen; es el contenido del Canvas.
- **Código (registro de codificación)**: unidad central del análisis; atributos:
  identificador, fecha/hora, documento de origen (o "Manual"), dominio, nombre, cita
  textual con su posición en el corpus, memo.
- **Dominio**: una de las 9 categorías fijas con color asociado; clasifica los códigos.
- **Memo**: nota de investigación asociada a un código.
- **Proyecto**: el estado completo persistido (corpus + banco de códigos + memos).
- **Resultado de literatura**: obra devuelta por OpenAlex; título, año, citas, DOI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El ciclo completo de codificación (seleccionar → dominio → nombre → Enter →
  resaltado visible) se completa en menos de 10 segundos por código, sin usar el mouse
  después de la selección salvo para elegir dominio.
- **SC-002**: El 100% de los códigos creados en una sesión sobrevive al cierre y reapertura
  de la aplicación.
- **SC-003**: Cero apariciones de HTML roto o texto ilegible en el Canvas tras codificar
  50 fragmentos, incluyendo 10 citas repetidas y 5 solapadas.
- **SC-004**: El CSV exportado abre en Excel con el 100% de tildes, ñ y columnas intactas.
- **SC-005**: Las Analytics reflejan un nuevo código en menos de 2 segundos tras el Enter.
- **SC-006**: Un corpus de 200 páginas se muestra y permite seleccionar/codificar con
  fluidez (respuesta perceptible < 1 segundo al seleccionar).
- **SC-007**: El investigador (sin conocimientos de programación) inicia la aplicación con
  un único comando y la usa sin instrucciones adicionales.
- **SC-008**: Las 8 funcionalidades del inventario constitucional (importación, Canvas con
  resaltado, Nube Negra, Paleta, NLP triple, Analytics, exportación, OpenAlex) están
  presentes y operativas en la versión entregada.

## Assumptions

- Un solo usuario local (el investigador) por proyecto; no se requiere autenticación ni
  colaboración multiusuario.
- Un solo proyecto activo a la vez en pantalla; se pueden mantener múltiples proyectos
  guardados y cambiar entre ellos mediante el selector.
- Los PDF del corpus tienen capa de texto (no se requiere OCR en esta versión).
- Idiomas del corpus limitados a español e inglés para stopwords de NLP.
- La búsqueda OpenAlex requiere conexión a internet; todo lo demás funciona sin conexión.
- macOS es la plataforma objetivo (Mac del investigador); no se optimiza para Windows/Linux
  en esta versión.
- La aplicación corre localmente y se usa desde un navegador moderno (Safari/Chrome).
