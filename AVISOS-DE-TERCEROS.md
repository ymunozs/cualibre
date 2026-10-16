# Avisos de terceros · Third-party notices · Avisos de terceiros

CUA-LIBRE STUDIO se distribuye bajo la licencia **GNU Affero General Public License,
versión 3 o (a tu elección) cualquier versión posterior** (AGPL-3.0-or-later). Ver
`LICENSE`. Incluye o usa los siguientes componentes de terceros, cada uno bajo su propia
licencia, todas compatibles con la AGPL-3.0.

| Componente | Uso en Cua-libre | Licencia |
|---|---|---|
| PyMuPDF (Artifex) | Lectura de PDF, OCR de páginas escaneadas | AGPL-3.0 (o comercial de Artifex) |
| PDF.js 3.11.174 (Mozilla), en `frontend/vendor/pdfjs/` | Lector de PDF de la biblioteca | Apache-2.0 (`licencias/pdfjs-Apache-2.0.txt`) |
| Fuentes estándar de PDF.js: Liberation Sans (Red Hat) | Dibujar PDF sin fuentes incrustadas | SIL Open Font License 1.1 (`frontend/vendor/pdfjs/standard_fonts/LICENSE_LIBERATION`) |
| Fuentes estándar de PDF.js: Foxit (PDFium Authors) | Dibujar PDF sin fuentes incrustadas | BSD-3-Clause (`frontend/vendor/pdfjs/standard_fonts/LICENSE_FOXIT`) |
| spaCy (Explosion) | Análisis lingüístico | MIT |
| Modelo `es_core_news_sm` 3.8.0 (Explosion) | Castellano | GPL-3.0 |
| Modelo `en_core_web_sm` 3.8.0 (Explosion) | Inglés | MIT |
| Modelo `pt_core_news_sm` 3.8.0 (Explosion) | Portugués | CC BY-SA 4.0 |
| FastAPI, Pydantic | Servidor local | MIT |
| Uvicorn, Starlette, HTTPX | Servidor local y consultas web | BSD-3-Clause |
| python-docx | Lectura de .docx | MIT |
| python-multipart | Subida de archivos | Apache-2.0 |
| olefile | Lectura de Word 97-2003 (.doc) | BSD-2-Clause |
| NumPy | Cálculo | BSD-3-Clause |
| pywebview | Ventana propia | BSD-3-Clause |
| PyObjC (Vision) · winrt | OCR del sistema (Mac · Windows) | MIT |
| Space Grotesk (fuente) | Títulos | SIL Open Font License 1.1 (`licencias/SpaceGrotesk-OFL.txt`) |
| IBM Plex Mono (fuente) | Interfaz | SIL Open Font License 1.1 (`licencias/IBMPlexMono-OFL.txt`) |

## Datos que NO vienen incluidos

- **NRC Word-Emotion Association Lexicon (EmoLex)**, de Saif M. Mohammad y Peter Turney
  (National Research Council Canada). Sus términos de uso no permiten redistribuirlo:
  cada equipo lo descarga una vez desde el sitio oficial y se rige por esos términos.

## Servicios en línea opcionales

OpenAlex (CC0) y Crossref (metadatos de uso libre) solo se consultan cuando la persona
busca literatura o completa la ficha de un documento por su DOI; todo lo demás funciona
sin conexión.
