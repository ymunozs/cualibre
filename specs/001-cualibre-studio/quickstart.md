# Quickstart & Validación end-to-end — CUA-LIBRE STUDIO

**Purpose**: recorrido obligatorio de verificación (Principio VII) antes de declarar
cualquier versión funcional. Referencias: [spec.md](./spec.md), [contracts/api.md](./contracts/api.md).

## Prerrequisitos

- macOS con `uv` instalado (`uv --version`); uv aprovisiona Python y dependencias solo
- Navegador moderno (Safari o Chrome)

## Arranque

```bash
./start.sh
```

Esperado: se crea `.venv` (solo la primera vez), se instalan dependencias, Uvicorn arranca
en `http://127.0.0.1:8734` y el navegador se abre solo (SC-007).

## Tests de backend

```bash
uv run -m pytest backend/tests/ -v
```

Esperado: todos verdes (contrato API, extracción, NLP, CSV, persistencia).

## Recorrido de validación manual (orden obligatorio)

1. **Importar** (US2): cargar un TXT con tildes/ñ desde el importador superior → el texto
   aparece en el Canvas encabezado por el nombre del archivo, caracteres intactos.
   Cargar un PDF → se acumula debajo sin borrar el anterior.
2. **Canvas sagrado** (US1/FR-005): inspeccionar visualmente: ningún campo de texto ni
   botón sobre o inmediatamente encima del Canvas.
3. **Codificar con la Nube Negra** (US1): seleccionar una frase → la Nube aparece junto a
   la selección con el campo de nombre enfocado → elegir dominio → escribir nombre →
   **Enter** → popup desaparece, la frase queda resaltada con el color del dominio.
   Repetir con: (a) una cita repetida en el texto (solo se pinta la ocurrencia
   seleccionada), (b) una selección solapada con la anterior (ambas visibles, texto
   legible, sin HTML roto), (c) **Escape** (cierra sin guardar), (d) nombre vacío + Enter
   (no guarda, lo indica).
4. **Paleta** (US4): crear un código manual con memo → aparece en el banco de códigos con
   origen "Manual".
5. **Editar/eliminar** (FR-030/031): renombrar un código y cambiarle el dominio → el color
   del resaltado cambia. Eliminar un código → su resaltado desaparece.
6. **Analytics** (US6): abrir la vista → torta por dominios y barras por código con los
   colores oficiales, incluyendo el código recién creado (< 2 s, SC-005).
7. **NLP** (US5): abrir la vista → nube de palabras empaquetada + barras + tabla,
   coherentes; cambiar idioma y longitud mínima → resultados cambian.
8. **Exportar** (US7): descargar el CSV → abrirlo (Excel o `cat`) → tildes/ñ intactas,
   columnas íntegras aun con comas/comillas en las citas.
9. **Persistencia** (US3): cerrar el servidor (Ctrl-C) → `./start.sh` de nuevo → corpus,
   resaltados y códigos restaurados al 100% (SC-002).
10. **Proyectos** (FR-032): crear un segundo proyecto → corpus vacío; volver al primero →
    todo intacto.
11. **Eliminar documento** (FR-033): eliminar el documento con códigos → advertencia con
    el número de códigos a perder → confirmar → documento y resaltados fuera.
12. **Literatura** (US8): buscar "Vygotsky emotions education" → resultados con título,
    año, citas y DOI clicable (requiere internet).
13. **Reiniciar** (FR-014): botón reiniciar → pide confirmación; cancelar no borra nada.

## Inventario constitucional (Principio I — SC-008)

Antes de entregar, confirmar presencia y operación de las 8 funcionalidades:
importación ☑ · Canvas+resaltado ☑ · Nube Negra ☑ · Paleta+memos ☑ · NLP triple ☑ ·
Analytics ☑ · Exportación CSV ☑ · OpenAlex ☑ — validado por el investigador el 2026-07-06
