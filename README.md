# CUA-LIBRE STUDIO

Estudio local de análisis cualitativo de datos (QDA/CAQDAS) para investigación en
ciencias sociales. Todo tu trabajo vive en tu Mac; no depende de la nube.

## Cómo iniciar

Abre la Terminal en esta carpeta y ejecuta:

```bash
./start.sh
```

La primera vez tardará un poco (descarga Python y las dependencias automáticamente con
`uv`). Después, el navegador se abre solo en `http://127.0.0.1:8734`. Para salir,
presiona `Ctrl-C` en la Terminal.

## Cómo se usa

1. **Importa tu corpus** (PDF, DOCX o TXT) desde la franja superior. Los documentos se
   acumulan y el Canvas identifica de cuál proviene cada sección.
2. **Codifica**: selecciona un fragmento en el Canvas → aparece la **Nube Negra** →
   elige el dominio (teclas 1–9 o el selector) → escribe el nombre del código →
   **Enter**. El fragmento queda resaltado con el color de su dominio.
   `Esc` o un clic fuera cancelan.
   - Con más de un documento, usa las **pestañas** sobre el Canvas para leer uno a la
     vez o todos juntos.
   - Para **re-aplicar un código existente**: selecciona el fragmento y **arrástralo**
     sobre ese código en el banco de la Paleta.
3. **Paleta derecha**: códigos manuales con memo, lista de documentos (con eliminación
   protegida), banco de códigos con edición ✎ y eliminación 🗑, y reinicio del proyecto
   (siempre con confirmación).
4. **⚡ NLP**: frecuencias del corpus con nube de palabras, barras y tabla; filtros de
   idioma (español/inglés) y longitud mínima.
5. **◫ Analytics**: distribución por dominios y densidad de códigos, al día con cada
   codificación.
6. **◈ Relaciones**: vincula códigos entre sí (jerarquía «contiene a», asociación,
   causalidad, contradicción/tensión) y míralos como organizador gráfico y como árbol
   de jerarquía. Si un código desaparece, sus relaciones se limpian solas.
7. **⇄ Exportar**: tabla completa y descarga CSV en UTF-8 que abre perfecto en Excel
   (tildes y ñ intactas).
8. **📚 Literatura**: búsqueda de papers en OpenAlex (título, año, citas, DOI). Es lo
   único que requiere internet.

El proyecto se guarda solo tras cada acción; el botón **💾 GUARDAR** de la cabecera
fuerza un guardado y te confirma la hora, para trabajar tranquilo.

## Proyectos y respaldo

- Puedes tener **varios proyectos** (selector arriba a la derecha: crear, renombrar,
  cambiar). Cada uno aísla su corpus, códigos y memos.
- Todo se **guarda solo** tras cada acción; al reabrir la app encuentras tu último
  proyecto tal como lo dejaste.
- Tus datos viven en `~/Library/Application Support/cualibre/projects/` (un archivo
  JSON legible por proyecto). Para respaldar, copia esa carpeta.

## Los 9 dominios de codificación

Emocional · Descriptivo · In Vivo · Tensión/CHAT · Proceso · Teórico · Relacional ·
Crítico · Método — cada uno con su color fijo en toda la aplicación.

## Para desarrollo

- Tests: `uv run -m pytest backend/tests/ -v`
- Documentación de diseño: `specs/001-cualibre-studio/` (spec, plan, research, tasks)
- Reglas del proyecto: `.specify/memory/constitution.md`
