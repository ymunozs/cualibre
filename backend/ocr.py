"""OCR para PDF escaneados con el motor nativo del sistema (FR-080).

- macOS: framework Vision de Apple (VNRecognizeTextRequest), macOS 10.15+;
  español y portugués desde macOS 11.
- Windows: Windows.Media.Ocr (Windows 10/11), con los idiomas de OCR que
  tenga instalados el sistema (vienen con cada idioma de Windows).

Sin modelos que empaquetar, sin internet: el texto reconocido nunca sale del
equipo. El OCR es una lectura automática de una imagen y puede equivocarse;
por eso cada documento guarda qué páginas se leyeron así (Document.ocr_pages)
y la interfaz lo muestra.
"""

from __future__ import annotations

import sys

OCR_DPI = 220  # resolución de renderizado de cada página escaneada

# Etiquetas de idioma preferidas por cada motor
_VISION_TAGS = {"es": "es-ES", "en": "en-US", "pt": "pt-BR"}
_WINDOWS_TAGS = {"es": "es", "en": "en", "pt": "pt"}


class OcrError(Exception):
    """El OCR no está disponible o falló; mensaje apto para el usuario."""


def engine_name() -> str | None:
    if sys.platform == "darwin":
        try:
            import Vision  # noqa: F401

            return "Apple Vision"
        except ImportError:
            return None
    if sys.platform == "win32":
        try:
            from winrt.windows.media.ocr import OcrEngine

            return "Windows OCR" if OcrEngine.available_recognizer_languages.size else None
        except Exception:
            return None
    return None


def available() -> bool:
    return engine_name() is not None


def _language_order(langs: list[str]) -> list[str]:
    order = [lang for lang in langs if lang in _VISION_TAGS]
    return order + [lang for lang in ("es", "pt", "en") if lang not in order]


# ----- macOS: Vision -----

def _vision_supported(request, level) -> set[str]:
    import Vision

    try:  # macOS 12+
        langs, _err = request.supportedRecognitionLanguagesAndReturnError_(None)
    except Exception:
        try:  # macOS 10.15/11
            langs, _err = Vision.VNRecognizeTextRequest \
                .supportedRecognitionLanguagesForTextRecognitionLevel_revision_error_(
                    level, Vision.VNRecognizeTextRequestRevision1, None)
        except Exception:
            langs = None
    return set(langs or [])


def _recognize_vision(png: bytes, langs: list[str]) -> str:
    import Vision
    from Foundation import NSData

    data = NSData.dataWithBytes_length_(png, len(png))
    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(data, None)
    request = Vision.VNRecognizeTextRequest.alloc().init()
    level = Vision.VNRequestTextRecognitionLevelAccurate
    request.setRecognitionLevel_(level)
    request.setUsesLanguageCorrection_(True)
    supported = _vision_supported(request, level)
    tags = [_VISION_TAGS[lang] for lang in _language_order(langs)]
    tags = [t for t in tags if not supported or t in supported] or ["en-US"]
    request.setRecognitionLanguages_(tags)
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise OcrError(str(error))
    lines = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if not candidates:
            continue
        box = observation.boundingBox()  # normalizado, origen abajo a la izquierda
        top = box.origin.y + box.size.height
        lines.append((top, box.origin.x, box.size.height, candidates[0].string()))
    return _join_lines(lines)


def _join_lines(lines: list[tuple[float, float, float, str]]) -> str:
    """Ordena las líneas de arriba abajo y separa párrafos por saltos verticales."""
    lines.sort(key=lambda item: (-round(item[0], 3), item[1]))
    out: list[str] = []
    previous_top = previous_height = None
    for top, _x, height, text in lines:
        if previous_top is not None and previous_top - top > 1.9 * max(height, previous_height):
            out.append("")  # espacio vertical grande → nuevo párrafo
        out.append(text)
        previous_top, previous_height = top, height
    return "\n".join(out)


# ----- Windows: Windows.Media.Ocr -----

async def _recognize_windows_async(png: bytes, langs: list[str]) -> str:
    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import BitmapDecoder, BitmapPixelFormat, SoftwareBitmap
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(png)
    await writer.store_async()
    await writer.flush_async()
    writer.detach_stream()
    stream.seek(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    bitmap = SoftwareBitmap.convert(bitmap, BitmapPixelFormat.BGRA8)

    engine = None
    for lang in _language_order(langs):
        language = Language(_WINDOWS_TAGS[lang])
        if OcrEngine.is_language_supported(language):
            engine = OcrEngine.try_create_from_language(language)
            break
    engine = engine or OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise OcrError("Windows no tiene ningún idioma de OCR instalado")
    result = await engine.recognize_async(bitmap)
    return "\n".join(line.text for line in result.lines)


def _recognize_windows(png: bytes, langs: list[str]) -> str:
    import asyncio

    return asyncio.run(_recognize_windows_async(png, langs))


def recognize_png(png: bytes, langs: list[str]) -> str:
    """Texto de una imagen PNG. langs: idiomas probables del corpus, en orden."""
    if sys.platform == "darwin":
        return _recognize_vision(png, langs)
    if sys.platform == "win32":
        return _recognize_windows(png, langs)
    raise OcrError("OCR no disponible en este sistema")


def render_page_png(page) -> bytes:
    """Página de PyMuPDF → PNG a OCR_DPI (acotado para el límite de Windows OCR)."""
    import fitz

    dpi = OCR_DPI
    longest = max(page.rect.width, page.rect.height) / 72  # pulgadas
    if longest * dpi > 9500:
        dpi = int(9500 / longest)
    return page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY).tobytes("png")
