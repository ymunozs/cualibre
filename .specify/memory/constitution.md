<!--
Sync Impact Report
==================
Version change: (template) → 1.0.0
Modified principles: n/a (initial ratification)
Added sections:
  - Core Principles (I–VII)
  - Restricciones Técnicas y de Diseño
  - Flujo de Desarrollo y Puertas de Calidad
  - Governance
Removed sections: none (template placeholders replaced)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ compatible (Constitution Check section is generic; gates below apply)
  - .specify/templates/spec-template.md ✅ compatible
  - .specify/templates/tasks-template.md ✅ compatible
Follow-up TODOs: none
-->

# CUA-LIBRE STUDIO Constitution

Herramienta de análisis cualitativo de datos (QDA/CAQDAS) para investigadores en ciencias
sociales, desarrollada y mantenida por un único investigador (Yerko Muñoz-Salinas).

## Core Principles

### I. Preservación Total de Funcionalidades (NON-NEGOTIABLE)

Ninguna iteración, refactorización o corrección puede eliminar ni degradar una funcionalidad
existente. Toda versión N+1 DEBE conservar el 100% de las capacidades de la versión N salvo
instrucción explícita del investigador de remover algo.

- Antes de entregar un cambio, se DEBE verificar contra el inventario de funcionalidades
  (spec.md) que todas las capacidades siguen presentes y operativas.
- Si una corrección exige tocar código de otra funcionalidad, esa funcionalidad se DEBE
  volver a probar antes de la entrega.

Racional: en el desarrollo previo se perdieron repetidamente la integración OpenAlex y
opciones de NLP al "simplificar" el código. Esa pérdida silenciosa destruye la confianza y
el trabajo acumulado.

### II. El Canvas de Lectura es Sagrado

El área donde el investigador lee el corpus es exclusivamente para lectura, selección y
resaltado. NINGÚN control de entrada de datos (inputs de texto, botones, formularios,
bridges ocultos) puede quedar visible sobre, dentro o inmediatamente encima del Canvas.

- La única excepción es la "Nube Negra": el popup efímero de codificación que aparece al
  seleccionar texto y desaparece al confirmar o cancelar.
- Los controles permanentes (códigos manuales, memos, gestión) viven en la Paleta derecha.
- El importador de documentos vive en la jerarquía superior de la página, nunca en la Paleta
  ni sobre el Canvas.

Racional: elementos flotantes permanentes rompen la inmersión de lectura, que es el corazón
del trabajo de análisis cualitativo.

### III. Flujo de Codificación Expedito

El ciclo de codificación DEBE completarse sin fricción:
seleccionar texto → elegir tipo/dominio → nombrar el código → Enter → guardado, resaltado
en color del dominio y actualización de analytics, todo inmediato y en un solo gesto.

- Enter confirma; Escape cancela. Sin clics adicionales obligatorios.
- Al confirmar, el fragmento queda resaltado en el Canvas con el color de su dominio y el
  registro aparece de inmediato en el banco de códigos y en las Analytics.
- El resaltado NUNCA puede corromper la legibilidad del corpus (no HTML roto, no etiquetas
  anidadas visibles).

Racional: el análisis cualitativo requiere fluidez; cada fricción interrumpe el juicio
interpretativo del investigador.

### IV. Tecnología Nativamente Confiable para la Interacción Crítica

La interacción selección→popup→commit→resaltado DEBE implementarse con tecnología donde esa
interacción sea nativa y determinista. Quedan PROHIBIDOS los puentes frágiles entre
contextos aislados (p. ej. inyectar valores en inputs ocultos de un framework desde un
iframe y disparar eventos sintéticos esperando un re-render).

- Si un framework no soporta la interacción de forma nativa, se cambia la arquitectura, no
  se apila otro hack.
- La comunicación entre la capa de interacción (JS/DOM) y la capa de datos (Python) DEBE
  usar un canal soportado oficialmente (HTTP/API, WebSocket, o estado del propio DOM).

Racional: todas las versiones 0.8.6–0.9.1 fallaron por el mismo bridge JS↔Streamlit; el
patrón era el problema, no su afinación.

### V. Integridad de los Datos del Investigador

El trabajo de codificación nunca se pierde.

- Persistencia local automática del proyecto (corpus, códigos, memos) en disco; recargar la
  app o reiniciar la máquina NO puede borrar el trabajo.
- Exportación en UTF-8 con BOM (compatible con Excel) como mínimo; los caracteres del
  español (tildes, ñ) DEBEN sobrevivir el viaje completo.
- Las acciones destructivas (borrar códigos, reiniciar proyecto) DEBEN pedir confirmación
  explícita.

Racional: los datos cualitativos codificados representan horas de juicio experto
irreproducible.

### VI. Estética Brutalista Consistente

La identidad visual es parte del producto y no se negocia por conveniencia técnica:

- Tipografías: Space Grotesk (títulos), IBM Plex Mono (interfaz), serif para el corpus
  (con variante conmutable "máquina de escribir" — Courier — a elección del lector).
- Negro estructural, fondo claro (#FAFAFA / #FDFDF7), acento #FF3300, bordes sólidos
  gruesos, sombras duras sin difuminar. Variante de lectura autorizada: modo oscuro
  conmutable (superficies #141412/#1B1B16, tinta clara, mismo acento y paleta de
  dominios); el organizador y la nube de conceptos permanecen como tarjetas claras.
- Paleta de 9 colores por dominio de código: Emocional #FF3300, Descriptivo #0066FF,
  In Vivo #FFCC00, Tensión/CHAT #FF0066, Proceso #6600CC, Teórico #00CC66,
  Relacional #0099CC, Crítico #CC0000, Método #333333.

Racional: la coherencia estética distingue una herramienta profesional de un prototipo
parchado.

### VII. Verificación Antes de Entrega (NON-NEGOTIABLE)

Ningún cambio se declara funcional sin haberse probado ejecutando la aplicación real.

- El flujo crítico (importar documento → seleccionar → codificar con Enter → ver resaltado
  → ver analytics → exportar) se DEBE ejercitar de punta a punta tras cada cambio que lo
  toque.
- "Debería funcionar" no es un estado entregable. Si no se probó, se dice explícitamente.

Racional: el ciclo anterior de "código completo y corregido" que llegaba roto quemó la
confianza del investigador en cada iteración.

## Restricciones Técnicas y de Diseño

- Aplicación local de escritorio/navegador para macOS; sin dependencia de servicios en la
  nube para el trabajo de análisis (OpenAlex es consulta opcional en línea).
- Python como lenguaje del backend de procesamiento (extracción PDF/DOCX, NLP, datos);
  las bibliotecas ya validadas (PyMuPDF, python-docx, pandas) se prefieren.
- Formatos de corpus soportados: PDF, DOCX, TXT (UTF-8).
- Idiomas del corpus: español e inglés (stopwords y NLP para ambos).
- Inventario de funcionalidades protegidas por el Principio I: importación de corpus,
  Canvas con resaltado por dominio y pestañas de documentos, Nube Negra, Paleta con
  códigos manuales y memos, edición/eliminación de códigos, arrastre de selección a
  códigos existentes, multi-proyecto con guardado explícito, NLP triple (nube de
  palabras + barras + tabla de conteo, con filtro de idioma y longitud mínima),
  Analytics (distribución por dominios + densidad de códigos), relaciones entre códigos
  (jerarquía/asociación/causalidad/contradicción con organizador y árbol), exportación
  CSV UTF-8, búsqueda de literatura OpenAlex, barra de música de foco con las pistas
  locales del investigador (Claude FM retirado por decisión del investigador el
  2026-07-06: embedding restringido), búsqueda en el corpus (⌘F), filtro de resaltados
  por dominio con lectura limpia, matrices de co-ocurrencia (código×código y
  documento×código), modo inmersión, posición de lectura persistente, repetición de la
  última codificación (⌘↵), indicador de autoguardado, exclusiones de palabras en NLP
  por proyecto, exportación del organizador (PNG/SVG) y de la nube de conceptos (PNG),
  deshacer última codificación (⌘Z), manual de uso (MANUAL.md, también dentro de la
  app), sesión de foco con meta y pomodoro omitible, modo oscuro, recuperación de citas
  por código, tipografía del corpus conmutable, numeración de líneas foco gramatical del NLP (verbos/sustantivos/adjetivos con lematización spaCy offline) y análisis de sentimiento por léxico NRC-es (valencia, arco emocional, emociones; auditable y offline).

## Flujo de Desarrollo y Puertas de Calidad

- Todo trabajo nuevo sigue el ciclo spec-kit: specify → clarify → plan → tasks → implement,
  con analyze antes de implementar.
- Puerta de calidad 1 (pre-implementación): el plan DEBE explicar cómo cumple los
  Principios II, III y IV; cualquier desviación se justifica por escrito en el plan.
- Puerta de calidad 2 (pre-entrega): checklist de Principio I (inventario completo) +
  Principio VII (prueba end-to-end ejecutada) antes de declarar una versión lista.
- Los commits describen qué funcionalidad se agregó/corrigió y qué se verificó.

## Governance

Esta constitución prevalece sobre cualquier otra práctica o preferencia de implementación.

- Enmiendas: cualquier cambio a los principios requiere aprobación explícita del
  investigador, actualización de este documento con nueva versión y propagación a las
  plantillas dependientes (plan, spec, tasks).
- Versionado: MAJOR para remociones o redefiniciones incompatibles de principios; MINOR
  para principios o secciones nuevas; PATCH para clarificaciones de redacción.
- Cumplimiento: cada plan de implementación incluye una sección "Constitution Check" que
  se valida contra los Principios I–VII antes de generar tareas y de nuevo antes de
  entregar.

**Version**: 1.7.0 | **Ratified**: 2026-07-06 | **Last Amended**: 2026-07-07
<!-- 1.5.0: Principio VI enmendado por el investigador (modo oscuro y tipografía
Courier como variantes de lectura autorizadas) + inventario ampliado con v1.4. -->
<!-- 1.2.0: inventario ampliado con la barra de música de foco (v1.1 de la app).
1.3.0: inventario ampliado con co-ocurrencia y mejoras de experiencia de lectura
(v1.2 de la app), solicitadas por el investigador el 2026-07-06. -->
<!-- 1.1.0: inventario del Principio I ampliado tras el cierre de v1 (pestañas de
documentos, guardado explícito, arrastre a códigos, relaciones entre códigos),
aprobado por el investigador en sesión del 2026-07-06. -->
