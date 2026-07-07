# CUA-LIBRE STUDIO — Manual de uso (v1.7)

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
- **🎓 DEMO**: crea un proyecto de ejemplo (entrevista ficticia ya codificada, con
  relaciones y exclusiones) para explorar todas las funciones sin riesgo.
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
- **Foco gramatical**: cuenta **todas las palabras**, **solo verbos**, **solo sustantivos** o **solo adjetivos**; al filtrar, las conjugaciones se agrupan bajo su lema (*cantó* y *cantaba* cuentan como *cantar*). Funciona sin internet.
- **Palabras a omitir**: escribe términos separados por coma y presiona **＋ OMITIR** — se **suman** a la lista vigente (chips bajo el campo; ✕ quita una). Ideal para marcas de transcripción como `Entrevistado`. Se guardan por proyecto.
- Tres vistas simultáneas: **nube de conceptos** (exportable con **⬇ PNG**), barras top y tabla de conteo exacto.

## 8. ◫ Analytics

- **Torta** por dominios y **barras** de densidad por código.
- **Co-ocurrencia**: matriz código×código — cuenta las citas que **se solapan** sobre el mismo fragmento (aparece con 2+ códigos anclados; más oscuro = más co-ocurrencias).
- **Códigos por documento**: distribución de cada código a través de tus documentos.

Todo se actualiza solo con cada codificación.

## 9. ◑ Sentimiento

Analiza el **tono emocional** del corpus con un léxico abierto en castellano (NRC EmoLex,
5.094 palabras; uso investigativo con cita a Mohammad & Turney 2013). Todo es **auditable**:
cada puntaje viene acompañado de las palabras que lo produjeron.

- **Tono y arco emocional por documento**: valencia global (−1 a +1) y su trayectoria
  párrafo a párrafo — dónde el relato se oscurece o se ilumina.
- **Tono por dominio y por código**: ¿tus citas de "Tensión/CHAT" son más negativas que
  las de "Relacional"? Barras divergentes desde el eje cero.
- **Emociones detectadas** (8 de NRC: alegría, tristeza, miedo, rabia, confianza,
  anticipación, sorpresa, asco) y **ranking de palabras con carga** (± con conteos).
- Maneja **negación**: "no siento alegría" invierte la polaridad de *alegría*.
- Límites honestos: la ironía y el sarcasmo se le escapan; úsalo como brújula
  exploratoria, no como veredicto.

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
anticipación, sorpresa, asco), del cual Cua-libre incluye las 5.094 entradas en castellano
de la distribución oficial. Uso libre para investigación; **cita**: Mohammad, S. & Turney,
P. (2013). *Crowdsourcing a Word–Emotion Association Lexicon*. Computational
Intelligence, 29(3), 436–465.

**Para seguir leyendo.** Liu, B. (2012), *Sentiment Analysis and Opinion Mining* (el
manual clásico del campo); Jockers, M., viñeta del paquete *syuzhet* (arcos narrativos);
y saifmohammad.com para el léxico NRC y sus actualizaciones.

## 10. ◈ Relaciones

1. Elige código origen → **tipo** → código destino → **◉ CREAR RELACIÓN**.
2. Tipos: **jerarquía** (contiene a), **asociación**, **causalidad** (influye en), **contradicción** (tensiona con).
3. **Organizador (grafo)**: nodos coloreados por dominio, aristas con estilo y letra por tipo (J/A/C/T). Exportable con **⬇ PNG** (para insertar en documentos) o **⬇ SVG** (editable en Illustrator/Inkscape).
4. **Árbol de jerarquía**: se arma solo desde las relaciones "contiene a".
5. Si un código desaparece del proyecto, sus relaciones se limpian automáticamente.

## 11. ⇄ Exportar

Tabla completa del banco y **descarga CSV** en UTF-8 con BOM: abre en Excel con tildes y ñ intactas. Columnas: id, fecha, documento, dominio, código, cita, memo.

**📄 Reporte académico**: genera un documento HTML autocontenido con TODO el proyecto —
nota metodológica con citas formales (y la declaración de análisis 100% humano), libro de
códigos, citas agrupadas por dominio y código con sus memos, gráficos, matrices de
co-ocurrencia, organizador de relaciones y análisis de sentimiento. Se abre en una pestaña
nueva: **⌘P** para guardarlo como PDF (anexo listo para tesis o paper) o **⌘S** para
guardar el HTML.

## 12. 📚 Literatura

Búsqueda por conceptos en **OpenAlex** (título, año, citas, enlace DOI). Única función que requiere internet; si no hay conexión, el resto de la app sigue igual.

## 13. ◷ Sesión de foco

Al abrir la app (o con clic en **◷ sesión** en la barra inferior) puedes fijar una **meta**
("codificar la entrevista 3") y un bloque de **15/25/50/90 minutos** — u **OMITIR**. El
indicador muestra el tiempo restante y cuántos códigos llevas en la sesión; al terminar,
un aviso suave sugiere la pausa (sin alarmas).

## 14. ♫ Música de foco (barra inferior)

Deja tus archivos de audio (mp3, m4a, ogg, wav, flac) en la carpeta `musica/` junto a tus datos — **clic en el título de la barra** te muestra la ruta exacta. `▶` reproduce en bucle, `⏭` salta de pista, y el volumen se recuerda.

## 15. Tabla rápida de atajos

| Atajo | Acción |
|-------|--------|
| `↵` (en la Nube) | Guardar código |
| `⌘↵` (en la Nube) | Repetir última codificación |
| `Esc` | Cancelar Nube / salir de inmersión / limpiar búsqueda |
| `1`–`9` (en la Nube) | Elegir dominio |
| `⌘F` / `Ctrl+F` | Buscar en el corpus |
| `⌘Z` / `Ctrl+Z` | Deshacer última codificación |
| Arrastrar selección → código del banco | Re-aplicar ese código |

## 16. Solución de problemas

- **Mac dice que la app no se puede abrir**: la primera vez, clic derecho → Abrir (la app no está firmada con certificado de Apple).
- **Windows SmartScreen advierte**: "Más información → Ejecutar de todas formas".
- **El navegador no se abre solo**: entra manualmente a `http://127.0.0.1:8734`.
- **"No se pudo conectar con el servidor"**: la app no está corriendo; lánzala de nuevo.
- **Recuperar trabajo**: todo está en `.../cualibre/projects/*.json`; ese archivo es tu proyecto completo, legible y respaldable.
