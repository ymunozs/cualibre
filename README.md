# CUA-LIBRE STUDIO

Estudio local de análisis cualitativo de datos (QDA/CAQDAS) para investigación en
ciencias sociales. Todo tu trabajo vive en tu Mac; no depende de la nube.

**Manual completo de comandos y atajos: [MANUAL.md](MANUAL.md)**

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
5. **◫ Analytics**: distribución por dominios, densidad de códigos, y las matrices de
   **co-ocurrencia** (qué códigos se solapan sobre las mismas citas) y **códigos por
   documento** — al día con cada codificación.
   - En el Pentagrama además: **⌘F** busca en el corpus (con navegación ‹ ›), los chips
     de la Paleta **filtran resaltados** por dominio («lectura limpia» los apaga todos),
     **⛶** activa el modo inmersión (Esc sale), **⌘↵** en la Nube repite tu última
     codificación, y tu posición de lectura se conserva siempre.
6. **◈ Relaciones**: vincula códigos entre sí (jerarquía «contiene a», asociación,
   causalidad, contradicción/tensión) y míralos como organizador gráfico y como árbol
   de jerarquía. Si un código desaparece, sus relaciones se limpian solas.
7. **⇄ Exportar**: tabla completa y descarga CSV en UTF-8 que abre perfecto en Excel
   (tildes y ñ intactas).
8. **📚 Literatura**: búsqueda de papers en OpenAlex (título, año, citas, DOI). Es lo
   único que requiere internet.

El proyecto se guarda solo tras cada acción; el botón **💾 GUARDAR** de la cabecera
fuerza un guardado y te confirma la hora, para trabajar tranquilo.

**♫ Música de foco**: la barra al pie reproduce tu propia música — deja tus archivos
(mp3, m4a, ogg, wav, flac) en la carpeta `musica/` junto a tus datos (clic en el título
de la barra te muestra la ruta exacta) y suenan en bucle mientras codificas.

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

## Instaladores

No necesitas Terminal si usas la app instalada:

- **macOS**: `packaging/build_mac.sh` genera `dist/CUA-LIBRE-Studio-<v>-mac.dmg`.
  Abre el DMG, arrastra la app a Aplicaciones. Como no está firmada con certificado de
  Apple, **la primera vez ábrela con clic derecho → Abrir**. Para salir: clic derecho en
  el ícono del Dock → Salir.
- **Windows**: se construye en una máquina Windows con `packaging/windows/build_windows.bat`
  (requiere Python 3.12+ e Inno Setup 6), **o automáticamente en GitHub**: sube este
  repositorio a GitHub y ejecuta el workflow *Installers* (pestaña Actions), que produce
  el `.dmg` de Mac y el `CUA-LIBRE-Studio-…-windows-setup.exe` de Windows como artefactos;
  si además publicas un tag `v1.0`, quedan adjuntos a un Release. La app de Windows
  muestra una ventana de consola mientras corre: ciérrala para apagar el servidor.

En ambos casos la app instalada abre el navegador sola y usa la misma carpeta de datos,
así que tus proyectos se comparten con la versión de desarrollo.

### Compatibilidad del instalador de macOS

- **Sistema mínimo: macOS 10.15 Catalina o superior** — incluye Big Sur, Monterey,
  Ventura, Sonoma, Sequoia y Tahoe. (Verificado con `otool -l` sobre los binarios
  empaquetados: numpy, thinc, blis, PyMuPDF y Python mismo.)
- **Arquitectura: Intel (x86_64)**. En Macs con Apple Silicon (M1/M2/M3/M4) corre vía
  **Rosetta 2** — macOS lo ofrece instalar automáticamente la primera vez (requiere
  internet esa única vez). Si una Mac Apple Silicon la rechaza sin pedir instalar
  Rosetta, revisa Preferencias → Privacidad y Seguridad → permite la app ahí.
- Nota técnica: `numpy>=2` exige macOS 14 (Sonoma) como mínimo — por eso el proyecto
  fija `numpy==1.26.4` en `pyproject.toml` y en los scripts de empaquetado; no lo subas
  de versión sin volver a verificar el piso de compatibilidad con `otool -l`.

## Para desarrollo

- Tests: `uv run -m pytest backend/tests/ -v`
- Documentación de diseño: `specs/001-cualibre-studio/` (spec, plan, research, tasks)
- Reglas del proyecto: `.specify/memory/constitution.md`
