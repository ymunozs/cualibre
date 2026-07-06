# Checklist de Calidad de Requisitos: Interacción Crítica del Pentagrama

**Purpose**: Validar que los requisitos de la experiencia seleccionar→Nube Negra→Enter→resaltado
están completos, claros, consistentes y medibles antes y durante la implementación — el área
donde fallaron las nueve versiones anteriores.
**Created**: 2026-07-06
**Feature**: [spec.md](../spec.md)

## Flujo de codificación expedita (Requirement Completeness)

- [x] CHK001 - ¿Está especificado el umbral exacto de selección que activa la Nube Negra (≥3 caracteres)? [Completeness, Spec §FR-009]
- [x] CHK002 - ¿Están definidos los tres desenlaces posibles del popup (Enter guarda, Escape cancela, clic fuera cancela) sin ambigüedad? [Completeness, Spec §FR-010/FR-011]
- [x] CHK003 - ¿Está especificado el comportamiento con nombre de código vacío (no guardar + indicación al usuario)? [Completeness, Spec §FR-012]
- [x] CHK004 - ¿Está definido dónde queda el foco del teclado al abrir la Nube (campo de nombre, foco automático)? [Clarity, Spec §FR-009]
- [x] CHK005 - ¿Se especifica qué debe actualizarse tras el Enter y con qué inmediatez (resaltado, banco, Analytics < 2 s)? [Measurability, Spec §FR-010, §SC-005]
- [x] CHK006 - ¿Está definida la posición del popup relativa a la selección de forma verificable ("adyacente")? [Clarity, Spec §FR-009]

## Pureza del Canvas — Principio II (Requirement Consistency)

- [x] CHK007 - ¿Prohíbe la spec explícitamente todo control de entrada sobre/dentro del Canvas, con la Nube Negra como única excepción efímera? [Consistency, Spec §FR-005, Constitución §II]
- [x] CHK008 - ¿Queda la gestión de documentos (lista/eliminar) fuera del Canvas en todos los artefactos (spec, plan, tasks T018–T019)? [Consistency, tasks.md Fase 3]
- [x] CHK009 - ¿Está definida la ubicación de cada control permanente (importador arriba, gestión en Paleta derecha) sin contradicciones entre secciones? [Consistency, Spec §FR-001/FR-013/FR-028]
- [x] CHK010 - ¿Existe un criterio de aceptación que permita verificar objetivamente la ausencia de controles sobre el Canvas? [Measurability, Spec §US1-AC5]

## Estabilidad del resaltado (Edge Case Coverage)

- [x] CHK011 - ¿Está especificado el anclaje por posición (documento + offsets) y no por búsqueda de cadena? [Clarity, Spec §FR-007]
- [x] CHK012 - ¿Están cubiertas las citas repetidas (solo la ocurrencia seleccionada se pinta)? [Edge Case, Spec §Edge Cases]
- [x] CHK013 - ¿Están cubiertas las citas solapadas (ambas persisten, legibilidad intacta, sin HTML roto)? [Edge Case, Spec §FR-006]
- [x] CHK014 - ¿Está definido el comportamiento de la selección que cruza dos documentos (no codificable, la Nube no se abre)? [Edge Case, Spec §Edge Cases]
- [x] CHK015 - ¿Existe un criterio medible de estabilidad del resaltado (SC-003: 50 fragmentos, 10 repetidos, 5 solapados, cero HTML roto)? [Measurability, Spec §SC-003]
- [x] CHK016 - ¿Está especificado qué ocurre con el resaltado al editar el dominio de un código (cambio de color) y al eliminarlo (desaparece)? [Completeness, Spec §FR-030/FR-031]
- [x] CHK017 - ¿Está definido cómo se muestra el nombre del código al pasar el cursor sobre un resaltado? [Completeness, Spec §FR-008]

## Integridad de datos en el ciclo de codificación (Non-Functional)

- [x] CHK018 - ¿Está especificado el momento exacto de la persistencia (tras cada mutación, antes de responder, sin botón de guardado)? [Clarity, Spec §FR-025, contracts/api.md]
- [x] CHK019 - ¿Está definido el contenido completo del registro de codificación (id, fecha, documento, dominio, nombre, cita, memo)? [Completeness, Spec §FR-015]
- [x] CHK020 - ¿Están definidos los requisitos de recuperación tras cierre abrupto (estado más reciente sin corrupción)? [Edge Case, Spec §Edge Cases, research.md D4]
- [x] CHK021 - ¿Es medible la supervivencia de los datos (SC-002: 100% de códigos tras cierre y reapertura)? [Measurability, Spec §SC-002]
- [x] CHK022 - ¿Exigen los requisitos confirmación explícita para toda acción destructiva (reset, eliminar documento con códigos, eliminar código)? [Coverage, Spec §FR-014/FR-031/FR-033]
- [x] CHK023 - ¿Está documentada la decisión sobre offsets UTF-16 (calculados/consumidos solo en JS; backend opaco) para que la implementación no los reinterprete? [Assumption, research.md D2, data-model.md]

## Inventario constitucional pre-entrega (Traceability)

- [x] CHK024 - ¿Existe un criterio de éxito que exija las 8 funcionalidades del inventario presentes y operativas (SC-008)? [Traceability, Spec §SC-008, Constitución §I]
- [x] CHK025 - ¿Cada funcionalidad del inventario tiene requisitos propios rastreables (importación FR-001..004, Canvas FR-005..008, Nube FR-009..012, Paleta FR-013..014, NLP FR-017..018/034, Analytics FR-019..020, Exportar FR-021..022, OpenAlex FR-023..024)? [Traceability]
- [x] CHK026 - ¿Está definida la verificación end-to-end obligatoria antes de declarar la versión funcional (quickstart 13 pasos, Principio VII)? [Completeness, quickstart.md]
- [x] CHK027 - ¿Queda rastreable que ningún requisito habilita eliminar funcionalidades al iterar (Principio I reflejado en spec/tasks)? [Consistency, Constitución §I]
