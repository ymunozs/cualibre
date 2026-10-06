# CUA-LIBRE STUDIO — Manual de uso (v1.13)

Guía completa de comandos y flujos para el análisis cualitativo.

## 1. Iniciar y salir

| Cómo | Qué hace |
|------|----------|
| Doble clic en la app instalada, o `./start.sh` / `start.bat` | Abre Cua-libre en su **propia ventana** |
| Cerrar la ventana (o ⌘Q en Mac) | Apaga la aplicación. Tu trabajo ya está guardado |
| `./start.sh --navegador` | Usa el navegador en vez de la ventana propia (botón **⏻ SALIR** en la cabecera para apagarla) |

Si la ventana propia no puede abrirse (por ejemplo, en un Windows antiguo sin el componente WebView2), Cua-libre usa tu navegador automáticamente. En la ventana propia, exportar un archivo abre el diálogo **Guardar como** del sistema, y el reporte académico se abre en tu navegador para imprimirlo a PDF.

Si la app ya estaba corriendo y la abres de nuevo, simplemente reutiliza la instancia.

## 2. Proyectos (cabecera)

- **Selector PROYECTO**: cambia entre tus investigaciones; cada proyecto aísla corpus, códigos, memos y relaciones.
- **+ NUEVO** / **✎ RENOMBRAR**: crear o renombrar el proyecto activo.
- **⤒ IMPORTAR**: abre un proyecto desde un **respaldo .zip** (el que genera ⇄ Exportar →
  🗄 Respaldo completo) o desde un archivo `.json` de proyecto, o un `.qdpx` de NVivo, ATLAS.ti, MAXQDA o
  QualCoder (ver ⇄ Exportar). Entra como proyecto nuevo,
  sin sobrescribir nada: sirve para mover tu trabajo a otro computador (Mac ↔ Windows) o
  para compartir un proyecto con colegas.
- **🗑** (junto a IMPORTAR): elimina el proyecto activo, previa confirmación. No se borra
  del disco: se mueve a la carpeta `papelera/` de tus datos, desde donde puedes recuperarlo.
- **🎓 DEMO**: crea un proyecto de ejemplo (entrevista ficticia ya codificada, con
  relaciones y exclusiones) para explorar todas las funciones sin riesgo.
- **💾 GUARDAR**: fuerza un guardado y confirma la hora. El punto a su lado **pulsa en rojo** con cada guardado automático (que ocurre solo, tras cada acción).
- **🕐 HISTORIAL**: abre el historial de respaldos de tu proyecto. Cua-libre guarda una
  copia completa cada 10 minutos de trabajo (como máximo) y una copia extra cada vez que
  presionas 💾 GUARDAR. Elige cualquier punto de la lista y pulsa **↺** para restaurar el
  proyecto a ese momento — el estado justo antes de restaurar también se respalda,
  así que nunca pierdes trabajo por equivocarte.
- **ℹ ACERCA DE**: filosofía del proyecto, contacto y agradecimientos.
- **❓ MANUAL**: abre este manual dentro de la app. **◐**: alterna modo oscuro/claro.
- **Selector de idioma** (Español · English · Português): cambia toda la interfaz al
  instante, sin recargar. Tus datos no se traducen: un proyecto se ve igual en cualquier
  idioma (solo cambian las etiquetas de las Categorías Básicas y de los tipos de relación).
  La demo, el manual, el reporte académico y los archivos exportados salen en el idioma
  elegido.
- Tus datos viven en `~/Library/Application Support/cualibre/` (Mac) o `%APPDATA%\cualibre\` (Windows). Copiar esa carpeta = respaldo completo.

## 3. Importar corpus (franja superior)

Elige archivos **PDF, DOCX, DOC o TXT** (puedes seleccionar varios). Cada documento se acumula al corpus con su nombre como encabezado. Errores (archivo dañado, PDF escaneado sin texto) se avisan sin tocar lo ya importado.

- **Word (DOCX y DOC)**: se leen los párrafos y también las **tablas** (muchas
  transcripciones vienen en tablas hablante | intervención), en el orden en que aparecen.
  Al final del documento quedan las **notas** (al pie y finales) y los **cuadros de texto**.
  Encabezados, pies de página y comentarios no se importan.
- **DOC** es el formato de Word 97-2003: se lee directamente, sin tener Word instalado y
  sin convertir nada a mano. También se aceptan los `.doc` que por dentro son RTF. Si el
  archivo tiene **control de cambios** pendiente, acepta o rechaza los cambios en Word
  antes de importarlo: en un `.doc` el texto eliminado todavía aparece. Los documentos
  con contraseña y los anteriores a Word 97 hay que guardarlos primero como `.docx`.
- **TXT**: se aceptan UTF-8 (con o sin BOM) y el formato "ANSI" del Bloc de notas de
  Windows; los saltos de línea de Windows se normalizan solos.
- **PDF escaneados (OCR)**: si una página es solo imagen, Cua-libre reconoce su texto con
  el OCR del propio sistema (Vision en macOS, OCR de Windows), sin internet y sin enviar
  nada fuera del equipo. Tarda unos segundos por página. El documento queda marcado con
  **OCR** (en la lista de documentos y en su encabezado del Canvas) indicando qué páginas
  se leyeron así: el OCR puede equivocarse, así que conviene revisar esas páginas contra el
  original antes de citarlas.

## 4. Codificar en el Pentagrama

### La Nube Negra (flujo principal)

1. **Selecciona** un fragmento (3+ caracteres) en el Canvas.
2. Aparece la Nube junto a la selección, con el cursor listo en el nombre.
3. Elige la **categoría**: haz clic en el selector para abrir el menú, o usa las teclas **1–9** para una Categoría Básica directamente.
4. Escribe el nombre del código y presiona **↵ Enter**.

El fragmento queda pintado con el color de la categoría, el código entra al banco y las Analytics se actualizan.

### Categorías: Básicas y personalizadas

Cua-libre trae **9 Categorías Básicas** de fábrica (Emocional, Descriptivo, In Vivo,
Tensión/CHAT, Proceso, Teórico, Relacional, Crítico, Método) — siempre disponibles, con
sus colores fijos. Al abrir el selector de categoría en la Nube:

- Las **categorías personalizadas** que hayas creado aparecen primero, listas para elegir.
- **"Categorías Básicas ▸"** despliega las 9 de fábrica en un submenú lateral al pasar el
  cursor por encima (como los menús de iOS/Windows) — o con un clic si prefieres no usar hover.
- **"✚ Nueva categoría…"** abre un mini-formulario: nombre + un color (clic en el cuadro
  de color abre el selector nativo) + **✓** para crearla (o Enter en el nombre). Queda
  disponible de inmediato en este proyecto — en el menú y en la Paleta.

Para **eliminar** una categoría personalizada: panel "Categorías personalizadas" en la
Paleta, botón ✕ en su chip. Si hay códigos usándola, se te advierte cuántos antes de
confirmar — el código conserva su nombre de categoría, solo pierde el color propio.

| Tecla en la Nube | Acción |
|------------------|--------|
| `↵` | Guardar el código |
| `⌘↵` (Mac) / `Ctrl+↵` | Repetir la **última** codificación (mismo nombre y categoría) sobre esta selección |
| `Esc` o clic fuera | Cancelar sin guardar |
| `1`–`9` | Elegir una Categoría Básica directamente |

### Otras formas de codificar

- **Arrastrar a un código existente**: selecciona texto y arrástralo sobre un código del
  banco compacto en la Paleta (columna derecha del Pentagrama) → se crea otra cita con
  ese mismo código. El banco completo (con buscador) vive en la pestaña ▤ Códigos, pero
  esta copia compacta en la Paleta existe justamente para poder arrastrar mientras lees
  el Canvas.
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

- **Idioma del corpus** (español, inglés o portugués): aplica las palabras vacías
  (stopwords) y el modelo gramatical correctos. Es un ajuste del proyecto, compartido con
  Sentimiento; se propone solo al importar el primer documento y puedes cambiarlo cuando
  quieras. Es independiente del idioma de la interfaz.
- **Longitud mínima**: descarta palabras cortas.
- **Foco gramatical**: cuenta **todas las palabras**, **solo verbos**, **solo sustantivos** o **solo adjetivos**; al filtrar, las conjugaciones se agrupan bajo su lema (*cantó* y *cantaba* cuentan como *cantar*). Funciona sin internet, en español, inglés y portugués.
- **Palabras a omitir**: escribe términos separados por coma y presiona **＋ OMITIR** — se **suman** a la lista vigente (chips bajo el campo; ✕ quita una). Ideal para marcas de transcripción como `Entrevistado`. Se guardan por proyecto.
- Tres vistas simultáneas: **nube de conceptos** (exportable con **⬇ PNG**), barras top y tabla de conteo exacto.
- **Concordancias (KWIC)**: haz clic en cualquier palabra —de la nube, las barras o la
  tabla— para ver **todas sus ocurrencias en el corpus**, cada una con el texto que la
  rodea. Con foco gramatical activo, busca por su **lema**: al pedir "cantar" también
  encuentra "cantó" y "cantaba", mostrando la forma real en el texto. Cada ocurrencia
  tiene un botón **«IR AL CANVAS →»** que salta directo a leerla en su contexto completo.

## 8. ◫ Analytics

- **Torta** por dominios y **barras** de densidad por código.
- **Co-ocurrencia**: matriz código×código — cuenta las citas que **se solapan** sobre el mismo fragmento (aparece con 2+ códigos anclados; más oscuro = más co-ocurrencias).
- **Códigos por documento**: distribución de cada código a través de tus documentos.

Todo se actualiza solo con cada codificación.

## 9. ◑ Sentimiento

Analiza el **tono emocional** del corpus con el léxico abierto NRC EmoLex en el idioma del
corpus (uso investigativo con cita a Mohammad & Turney 2013).

- **Instalación única del léxico**: los términos de uso del NRC no permiten redistribuir
  el léxico dentro de Cua-libre, así que cada equipo lo obtiene **una sola vez** desde el
  sitio oficial: botón **⬇ DESCARGAR DESDE EL NRC** (≈ 25 MB; instala castellano, inglés
  y portugués). Sin internet, **ELEGIR .ZIP OFICIAL** acepta el archivo
  NRC-Emotion-Lexicon.zip descargado en otro equipo. Después funciona siempre sin
  conexión.
- Las versiones en castellano y portugués son **traducciones automáticas** del inglés
  hechas por los autores del léxico: revisa en contexto las palabras con carga.

Todo es **auditable**: cada puntaje viene acompañado de las palabras que lo produjeron.

- **Tono y arco emocional por documento**: valencia global (−1 a +1) y su trayectoria
  párrafo a párrafo — dónde el relato se oscurece o se ilumina.
- **Tono por dominio y por código**: ¿tus citas de "Tensión/CHAT" son más negativas que
  las de "Relacional"? Barras divergentes desde el eje cero.
- **Emociones detectadas** (8 de NRC: alegría, tristeza, miedo, rabia, confianza,
  anticipación, sorpresa, asco) y **ranking de palabras con carga** (± con conteos).
- **Auditar cada clasificación**: haz clic en una **emoción** para ver exactamente qué
  palabras la dispararon en tu corpus; haz clic en una **palabra con carga** (positiva o
  negativa) para lo mismo. Desde ahí, clic en cualquier palabra abre sus **concordancias**
  (todas sus menciones en contexto, con salto directo al Canvas) — para verificar con tus
  propios ojos si la clasificación automática tiene sentido en tu corpus.
- Maneja **negación**: "no siento alegría" invierte la polaridad de *alegría*.
- Límites honestos: la ironía y el sarcasmo se le escapan; úsalo como brújula
  exploratoria, no como veredicto. Usa siempre el léxico del idioma del corpus: un
  corpus en inglés analizado con el léxico castellano no es interpretable.
- Los **negadores** (*no, nada, nunca*…) solo invierten la palabra que sigue; nunca
  cuentan como palabras con carga.
- **Corpus grandes**: la primera vez que abres Sentimiento (o el foco gramatical) sobre
  un corpus voluminoso, Cua-libre analiza cada documento una sola vez y muestra el avance
  ("Analizando el corpus: 12 de 60 documentos…"). El resultado queda guardado: las
  siguientes consultas, incluso en otra sesión, son inmediatas.

### Cómo se produce el análisis (racionalidad y método)

Cua-libre está diseñado para **promover decisiones 100% humanas**: el análisis de
sentimiento no interpreta por ti ni escribe nada en tu banco de códigos — es una brújula
exploratoria que señala zonas del corpus donde tu lectura atenta puede rendir más.

**Racionalidad.** El análisis usa un método **basado en léxico**: una lista fija y pública
de palabras, cada una con su polaridad y sus emociones asociadas, elaborada y validada por
investigadores. Se eligió este método (y no redes neuronales) por tres razones que importan
en investigación cualitativa:

1. **Auditabilidad**: cada puntaje puede reconstruirse a mano. Si un documento marca −0.4,
   la vista te muestra exactamente qué palabras lo produjeron y cuántas veces; puedes ir a
   verlas en contexto y juzgar si el número dice algo o no. Nada queda dentro de una caja
   negra.
2. **Replicabilidad**: con el mismo texto y el mismo léxico, el resultado es siempre el
   mismo, en cualquier máquina, sin conexión a internet. Otro investigador puede repetir tu
   análisis y obtener idénticos valores.
3. **Defensa metodológica**: en un apartado de métodos puedes describir el procedimiento
   completo en un párrafo y citar la fuente del léxico. Con un modelo neuronal solo podrías
   decir "el modelo lo clasificó así".

El costo de esta transparencia es conocido: el léxico no capta ironía, sarcasmo ni dobles
sentidos. Por eso los puntajes son **insumo para tu interpretación**, nunca su reemplazo.

**Procesamiento, paso a paso.**
1. Cada texto se tokeniza y **lematiza** con spaCy (*lloraba* → *llorar*), para que las
   conjugaciones encuentren su entrada en el léxico.
2. Cada palabra (por su forma o su lema) se busca en el léxico: si existe, aporta su
   polaridad (+1 o −1) y sus emociones asociadas.
3. **Negación**: si en las 3 palabras anteriores hay un negador (*no, nunca, sin, jamás,
   ni, tampoco, nada, nadie, ninguno/a*), la polaridad de esa palabra se invierte.
4. La **valencia** de un texto es el promedio de los aportes: (positivas − negativas) /
   total de palabras con carga → un valor entre −1 y +1.
5. El **arco emocional** repite el cálculo párrafo a párrafo (hasta 40 tramos), siguiendo
   la idea del paquete *syuzhet* de M. Jockers para trayectorias narrativas.

**Fuentes.** El léxico es el **NRC Word–Emotion Association Lexicon (EmoLex)** de Saif
Mohammad y Peter Turney (National Research Council Canada): ~14.000 palabras anotadas por
crowdsourcing con polaridad y 8 emociones (alegría, tristeza, miedo, rabia, confianza,
anticipación, sorpresa, asco), con traducciones automáticas a más de cien idiomas.
Cua-libre usa las entradas de una sola palabra en castellano, inglés y portugués,
convertidas en tu equipo a partir del archivo oficial. Uso libre para investigación; **cita**: Mohammad, S. & Turney,
P. (2013). *Crowdsourcing a Word–Emotion Association Lexicon*. Computational
Intelligence, 29(3), 436–465.

**Para seguir leyendo.** Liu, B. (2012), *Sentiment Analysis and Opinion Mining* (el
manual clásico del campo); Jockers, M., viñeta del paquete *syuzhet* (arcos narrativos);
y saifmohammad.com para el léxico NRC y sus actualizaciones.

## 10. ▤ Códigos

El banco de códigos completo, con buscador y fusión (antes vivía dentro de la Paleta).

- **Buscar en el banco**: filtra por nombre de código, categoría o texto de la cita, sin
  tocar el Canvas ni el backend.
- **⇄ Fusionar códigos** (codificación axial): elige un código de origen, escribe el
  nombre destino (uno existente o nuevo) y confirma. Si el destino ya existía, todas las
  citas fusionadas adoptan su categoría; si es un nombre nuevo, cada cita conserva la
  suya. Las relaciones que involucraban al código de origen migran solas al nuevo
  nombre — nunca se pierden por fusionar.
- Editar (✎) y eliminar (🗑) funcionan igual que en la Paleta — es el mismo banco, visto
  con más espacio.
- Con miles de códigos, el banco se dibuja por tandas: **Mostrar más** al final de la
  lista carga la siguiente.

## 11. ◈ Relaciones

1. Elige código origen → **tipo** → código destino → **◉ CREAR RELACIÓN**.
2. Tipos: **jerarquía** (contiene a), **asociación**, **causalidad** (influye en), **contradicción** (tensiona con).
3. **Organizador (grafo)**: nodos coloreados por dominio, aristas con estilo y letra por tipo (J/A/C/T). Exportable con **⬇ PNG** (para insertar en documentos) o **⬇ SVG** (editable en Illustrator/Inkscape).
4. **Árbol de jerarquía**: se arma solo desde las relaciones "contiene a".
5. Si un código desaparece del proyecto, sus relaciones se limpian automáticamente.

## 12. ⚖ Acuerdo entre codificadores

Compara la codificación de dos personas sobre el mismo corpus, como apoyo a la discusión
metodológica del equipo.

1. Quien prepara el corpus exporta el **🗄 Respaldo completo (.zip)**.
2. La otra persona lo abre con **⤒ IMPORTAR** y codifica en su propia copia.
3. Quien compara importa el proyecto de su colega (o su .zip), vuelve a su propio proyecto
   (A), abre **⚖ ACUERDO**, elige el proyecto del colega (B) y presiona **⚖ CALCULAR ACUERDO**.

Los documentos se emparejan por su **texto** (aunque el archivo tenga otro nombre). Para
cada código se informa el **porcentaje de acuerdo**, la **kappa de Cohen** y el **alfa de
Krippendorff**, con el **carácter** como unidad de análisis (el criterio de NVivo), más
la kappa media y los valores globales. Los tramos de Landis y Koch (1977) son solo
orientativos. Clic en un código muestra los **fragmentos en desacuerdo** (quién los
codificó y dónde), con salto al Canvas para discutirlos. **⬇ CSV** exporta la tabla.
Nada de esto modifica el banco de códigos: las decisiones siguen siendo del equipo.

## 13. ⇄ Exportar

Tabla completa del banco y **descarga CSV** en UTF-8 con BOM: abre en Excel con tildes y ñ intactas. Columnas: id, fecha, documento, dominio, código, cita, memo.

**📄 Reporte académico**: genera un documento HTML autocontenido con TODO el proyecto —
nota metodológica con citas formales (y la declaración de análisis 100% humano), libro de
códigos, citas agrupadas por dominio y código con sus memos, gráficos, matrices de
co-ocurrencia, organizador de relaciones y análisis de sentimiento. Se abre en una pestaña
nueva: **⌘P** para guardarlo como PDF (anexo listo para tesis o paper) o **⌘S** para
guardar el HTML.

**⇆ REFI-QDA (.qdpx)**: el proyecto en el estándar abierto de intercambio entre programas
de análisis cualitativo. Ábrelo en **NVivo, ATLAS.ti, MAXQDA o QualCoder** para trabajar
con colegas que usan otro software. Las categorías pasan como códigos padre (con su
color), cada código con sus citas y memos, y las relaciones como vínculos. El selector
junto al botón elige el destino: **Estándar** (ATLAS.ti, MAXQDA, QualCoder) o **NVivo**,
porque NVivo para Windows cuenta las posiciones del texto de otra forma. **⤒ IMPORTAR**
también abre archivos .qdpx de esos programas: la jerarquía de códigos se conserva como
categorías y relaciones de jerarquía, la convención de posiciones se detecta sola, y se
informa si hubo fuentes que no son texto (imagen, audio, video) y quedaron fuera.

**🗄 Respaldo completo (.zip)**: un archivo autocontenido con el proyecto entero —
`proyecto.json` (fidelidad total: corpus, códigos, relaciones, memos, categorías propias;
se reabre con **⤒ IMPORTAR**), `codigos.csv` y el texto de cada
documento en `.txt`. Pensado para depositar como evidencia de reproducibilidad al
publicar, o como copia portable independiente de la app.

## 14. 📚 Literatura

Búsqueda por conceptos en **OpenAlex** (título, año, citas, enlace DOI). Junto con la descarga única del léxico de sentimiento, es lo único que requiere internet; si no hay conexión, el resto de la app sigue igual.

## 15. ◷ Sesión de foco

Al abrir la app (o con clic en **◷ sesión** en la barra inferior) puedes fijar una **meta**
("codificar la entrevista 3") y un bloque de **15/25/50/90 minutos** — u **OMITIR**. El
indicador muestra el tiempo restante y cuántos códigos llevas en la sesión; al terminar,
un aviso suave sugiere la pausa (sin alarmas).

## 16. ♫ Música de foco (barra inferior)

Deja tus archivos de audio (mp3, m4a, ogg, wav, flac) en la carpeta `musica/` junto a tus datos — **clic en el título de la barra** te muestra la ruta exacta. `▶` reproduce en bucle, `⏭` salta de pista, y el volumen se recuerda.

## 17. Tabla rápida de atajos

| Atajo | Acción |
|-------|--------|
| `↵` (en la Nube) | Guardar código |
| `⌘↵` (en la Nube) | Repetir última codificación |
| `Esc` | Cancelar Nube / salir de inmersión / limpiar búsqueda |
| `1`–`9` (en la Nube) | Elegir dominio |
| `⌘F` / `Ctrl+F` | Buscar en el corpus |
| `⌘Z` / `Ctrl+Z` | Deshacer última codificación |
| Arrastrar selección → código del banco | Re-aplicar ese código |

## 18. Solución de problemas

- **Mac dice que la app no se puede abrir**: pasa solo la primera vez, porque la app no está firmada con certificado de Apple. En macOS 15 (Sequoia) o posterior: *Configuración del Sistema → Privacidad y seguridad → Abrir de todos modos*. En macOS 14 o anterior: clic derecho sobre la app → Abrir.
- **En otra Mac no abre / no dice nada**: lo más probable es que sea el **DMG equivocado para su chip**. Hay dos instaladores: uno para Mac **Intel** y otro para Mac **Apple Silicon (M1/M2/M3/M4)** — no son intercambiables (a diferencia de Rosetta, que solo traduce Intel→Apple Silicon, nunca al revés). En esa Mac, ve a menú  → *Acerca de esta Mac* para ver qué chip tiene, y descarga el DMG correspondiente. Además, se necesita **macOS 10.15 (Catalina) o superior**.
- **Windows SmartScreen advierte**: "Más información → Ejecutar de todas formas".
- **El navegador no se abre solo**: entra manualmente a `http://127.0.0.1:8734`.
- **"No se pudo conectar con el servidor"**: la app no está corriendo; lánzala de nuevo.
- **Recuperar trabajo**: todo está en `.../cualibre/projects/*.json`; ese archivo es tu proyecto completo, legible y respaldable. Un proyecto eliminado queda en `.../cualibre/papelera/`: impórtalo con **⤒ IMPORTAR** para recuperarlo.
- **La primera apertura de Sentimiento tarda con un corpus muy grande**: es el análisis
  inicial de cada documento (se hace una sola vez y queda guardado en `.../cualibre/cache/`,
  carpeta que se puede borrar sin riesgo).
- **Windows**: los atajos usan `Ctrl` donde el manual dice `⌘`.
- **La ventana propia no abre en Windows**: falta el componente WebView2 (viene con Windows
  11 y con Windows 10 actualizado). Cua-libre se abre entonces en el navegador; puedes
  instalar WebView2 desde el sitio de Microsoft. Los mensajes técnicos quedan en
  `%APPDATA%\cualibre\logs\cualibre.log`.
- **Un PDF escaneado no se lee**: el equipo no tiene OCR disponible (Windows sin idioma de
  OCR instalado, o macOS anterior a 10.15). En macOS, el OCR en castellano y portugués
  requiere macOS 11 o superior.
