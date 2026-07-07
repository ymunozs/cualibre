# CUA-LIBRE STUDIO — Manual de uso (v1.4)

Guía completa de comandos y flujos para el análisis cualitativo.

## 1. Iniciar y salir

| Cómo | Qué hace |
|------|----------|
| `./start.sh` en Terminal, o doble clic en la app instalada | Abre el servidor local y tu navegador en `http://127.0.0.1:8734` |
| `Ctrl-C` en Terminal / cerrar la consola (Windows) / Dock → Salir (app de Mac) | Apaga la aplicación. Tu trabajo ya está guardado |

Si la app ya estaba corriendo y la abres de nuevo, simplemente reutiliza la instancia.

## 2. Proyectos (cabecera)

- **Selector PROYECTO**: cambia entre tus investigaciones; cada proyecto aísla corpus, códigos, memos y relaciones.
- **+ NUEVO** / **✎ RENOMBRAR**: crear o renombrar el proyecto activo.
- **💾 GUARDAR**: fuerza un guardado y confirma la hora. El punto a su lado **pulsa en rojo** con cada guardado automático (que ocurre solo, tras cada acción).
- **❓ MANUAL**: abre este manual dentro de la app. **◐**: alterna modo oscuro/claro.
- Tus datos viven en `~/Library/Application Support/cualibre/` (Mac) o `%APPDATA%\cualibre\` (Windows). Copiar esa carpeta = respaldo completo.

## 3. Importar corpus (franja superior)

Elige archivos **PDF, DOCX o TXT** (puedes seleccionar varios). Cada documento se acumula al corpus con su nombre como encabezado. Errores (archivo dañado, PDF escaneado sin texto) se avisan sin tocar lo ya importado.

## 4. Codificar en el Pentagrama

### La Nube Negra (flujo principal)

1. **Selecciona** un fragmento (3+ caracteres) en el Canvas.
2. Aparece la Nube junto a la selección, con el cursor listo en el nombre.
3. Elige el **dominio** con las teclas **1–9** o el selector.
4. Escribe el nombre del código y presiona **↵ Enter**.

El fragmento queda pintado con el color del dominio, el código entra al banco y las Analytics se actualizan.

| Tecla en la Nube | Acción |
|------------------|--------|
| `↵` | Guardar el código |
| `⌘↵` (Mac) / `Ctrl+↵` | Repetir la **última** codificación (mismo nombre y dominio) sobre esta selección |
| `Esc` o clic fuera | Cancelar sin guardar |
| `1`–`9` | Elegir dominio |

### Otras formas de codificar

- **Arrastrar a un código existente**: selecciona texto y arrástralo sobre un código del banco (Paleta) → se crea otra cita con ese mismo código.
- **Código manual** (Paleta → PALETA DE CONTROL): dominio + etiqueta + memo, sin cita textual. Para códigos teóricos o emergentes.

### Corregir

- **✎** en el banco: editar nombre, dominio (el color del resaltado cambia) y memo.
- **🗑** en el banco: eliminar un código (su resaltado desaparece).
- **⌘Z / Ctrl+Z** (fuera de un campo de texto): deshace la **última** codificación.

## 5. Navegar y leer

| Comando | Acción |
|---------|--------|
| Pestañas sobre el Canvas (`TODOS`, nombres de archivo) | Leer un documento a la vez o el corpus completo |
| **⌘F / Ctrl+F** | Buscar texto en el corpus: coincidencias con borde punteado rojo, navegación **‹ ›** con contador; `Esc` en el buscador limpia |
| Chips **FILTRO DE RESALTADOS** | Apagar/encender los resaltados de cada dominio; **◻ LECTURA LIMPIA** apaga todos (los códigos no se borran, solo se ocultan) |
| **⛶** (junto a "Canvas de Análisis") | **Modo inmersión**: solo el Canvas, centrado. `Esc` sale |
| **Aa** | Alterna la tipografía del corpus: serif ↔ máquina de escribir (Courier) |
| **№** | Muestra/oculta la **numeración de líneas** (los números no se copian al seleccionar) |
| Clic en el **nombre de un código** (banco) | **Todas sus citas** en un panel, con «IR AL CANVAS →» para saltar a cada una |
| Scroll | Tu posición de lectura se recuerda por documento, entre sesiones, y no se pierde al codificar |

## 6. Documentos del corpus (Paleta)

Lista con el número de códigos de cada documento. **🗑** elimina un documento: si tiene códigos, se te advierte cuántos se perderán antes de confirmar.

## 7. ⚡ NLP — análisis léxico

- **Idioma** (español/inglés): aplica las stopwords correctas.
- **Longitud mínima**: descarta palabras cortas.
- **Palabras a omitir**: escribe términos separados por coma (ej. `Entrevistado, Entrevistadora, E1, eh`) y presiona **OMITIR** (o Enter) — ideal para marcas de transcripción. Se guardan por proyecto.
- Tres vistas simultáneas: **nube de conceptos** (exportable con **⬇ PNG**), barras top y tabla de conteo exacto.

## 8. ◫ Analytics

- **Torta** por dominios y **barras** de densidad por código.
- **Co-ocurrencia**: matriz código×código — cuenta las citas que **se solapan** sobre el mismo fragmento (aparece con 2+ códigos anclados; más oscuro = más co-ocurrencias).
- **Códigos por documento**: distribución de cada código a través de tus documentos.

Todo se actualiza solo con cada codificación.

## 9. ◈ Relaciones

1. Elige código origen → **tipo** → código destino → **◉ CREAR RELACIÓN**.
2. Tipos: **jerarquía** (contiene a), **asociación**, **causalidad** (influye en), **contradicción** (tensiona con).
3. **Organizador (grafo)**: nodos coloreados por dominio, aristas con estilo y letra por tipo (J/A/C/T). Exportable con **⬇ PNG** (para insertar en documentos) o **⬇ SVG** (editable en Illustrator/Inkscape).
4. **Árbol de jerarquía**: se arma solo desde las relaciones "contiene a".
5. Si un código desaparece del proyecto, sus relaciones se limpian automáticamente.

## 10. ⇄ Exportar

Tabla completa del banco y **descarga CSV** en UTF-8 con BOM: abre en Excel con tildes y ñ intactas. Columnas: id, fecha, documento, dominio, código, cita, memo.

## 11. 📚 Literatura

Búsqueda por conceptos en **OpenAlex** (título, año, citas, enlace DOI). Única función que requiere internet; si no hay conexión, el resto de la app sigue igual.

## 12. ◷ Sesión de foco

Al abrir la app (o con clic en **◷ sesión** en la barra inferior) puedes fijar una **meta**
("codificar la entrevista 3") y un bloque de **15/25/50/90 minutos** — u **OMITIR**. El
indicador muestra el tiempo restante y cuántos códigos llevas en la sesión; al terminar,
un aviso suave sugiere la pausa (sin alarmas).

## 13. ♫ Música de foco (barra inferior)

Deja tus archivos de audio (mp3, m4a, ogg, wav, flac) en la carpeta `musica/` junto a tus datos — **clic en el título de la barra** te muestra la ruta exacta. `▶` reproduce en bucle, `⏭` salta de pista, y el volumen se recuerda.

## 14. Tabla rápida de atajos

| Atajo | Acción |
|-------|--------|
| `↵` (en la Nube) | Guardar código |
| `⌘↵` (en la Nube) | Repetir última codificación |
| `Esc` | Cancelar Nube / salir de inmersión / limpiar búsqueda |
| `1`–`9` (en la Nube) | Elegir dominio |
| `⌘F` / `Ctrl+F` | Buscar en el corpus |
| `⌘Z` / `Ctrl+Z` | Deshacer última codificación |
| Arrastrar selección → código del banco | Re-aplicar ese código |

## 15. Solución de problemas

- **Mac dice que la app no se puede abrir**: la primera vez, clic derecho → Abrir (la app no está firmada con certificado de Apple).
- **Windows SmartScreen advierte**: "Más información → Ejecutar de todas formas".
- **El navegador no se abre solo**: entra manualmente a `http://127.0.0.1:8734`.
- **"No se pudo conectar con el servidor"**: la app no está corriendo; lánzala de nuevo.
- **Recuperar trabajo**: todo está en `.../cualibre/projects/*.json`; ese archivo es tu proyecto completo, legible y respaldable.
