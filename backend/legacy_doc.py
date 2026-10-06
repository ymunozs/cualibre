"""Texto de documentos Word antiguos (.doc), sin Word ni programas externos (FR-082).

Un archivo «.doc» puede ser tres cosas distintas, y Word abre las tres sin
avisar, así que aquí se decide por el contenido y no por la extensión:

- el formato binario de Word 97-2003 (contenedor OLE2), que es el caso normal;
- RTF con extensión cambiada (lo producen varios programas de transcripción);
- un .docx renombrado (lo resuelve extraction.py con python-docx).

Del binario se lee lo mismo que de un .docx: el cuerpo y, al final, las notas
(al pie y finales) y los cuadros de texto. Encabezados, pies de página y
comentarios quedan fuera. El texto vive repartido en «piezas» (unas en 8 bits,
otras en UTF-16) cuya tabla está en el flujo 0Table/1Table; se sigue la
especificación pública [MS-DOC] de Microsoft.

Límite conocido: en el binario, el texto borrado con control de cambios todavía
sin aceptar aparece junto al resto (en .docx y RTF no), porque distinguirlo
exige leer las propiedades de carácter. Conviene aceptar o rechazar los cambios
antes de importar.
"""

from __future__ import annotations

import io
import re
import struct

import olefile

from .i18n import tr

OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP_MAGIC = b"PK\x03\x04"

# Marca interna de «fin de celda»: un carácter de uso privado que no aparece
# en textos reales; desaparece al armar las filas.
_CELL = "\ue000"

# Word guarda las piezas de 8 bits en Windows-1252, salvo los cinco bytes que
# esa tabla deja sin definir, que valen su propio número ([MS-DOC] 2.9.73).
_ANSI_TABLE = {
    b: bytes([b]).decode("cp1252")
    for b in range(0x80, 0xA0) if b not in (0x81, 0x8D, 0x8F, 0x90, 0x9D)
}

_FIELD_MARKS = re.compile("([\x13\x14\x15])")
# Anclas de imágenes y objetos, marcas de nota y de comentario, guion opcional
# y demás caracteres de control que no son texto
_INVISIBLE = re.compile("[\x00-\x08\x0e-\x1d\x1f\x7f]")


class LegacyDocError(Exception):
    """Error con mensaje apto para el usuario final."""


def sniff(data: bytes) -> str:
    """Qué hay de verdad dentro del archivo: 'ole', 'zip', 'rtf' o 'unknown'."""
    if data.startswith(OLE_MAGIC):
        return "ole"
    if data.startswith(ZIP_MAGIC):
        return "zip"
    if data[:64].lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"{\\rtf"):
        return "rtf"
    return "unknown"


def extract(data: bytes, filename: str) -> str:
    """Texto de un .doc binario o de un RTF. Lanza LegacyDocError si no se puede."""
    kind = sniff(data)
    if kind == "ole":
        stories = (_layout(_strip_fields(story)) for story in _word_binary_stories(data, filename))
        return "\n\n".join(story for story in stories if story.strip())
    if kind == "rtf":
        return _layout(_rtf_text(data))
    raise LegacyDocError(tr("doc_unrecognised", filename=filename))


# ----- Word 97-2003 -----

def _word_binary_stories(data: bytes, filename: str) -> list[str]:
    """Cuerpo, notas al pie, notas finales y cuadros de texto, en ese orden."""
    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
    except Exception as exc:
        raise LegacyDocError(tr("unreadable_file", filename=filename)) from exc
    try:
        if ole.exists("EncryptedPackage"):  # .docx con contraseña: viene dentro de un OLE
            raise LegacyDocError(tr("doc_encrypted", filename=filename))
        if not ole.exists("WordDocument"):  # Excel, PowerPoint u otro contenedor OLE
            raise LegacyDocError(tr("doc_unrecognised", filename=filename))
        main = ole.openstream("WordDocument").read()
        if len(main) < 0x0C:
            raise LegacyDocError(tr("unreadable_file", filename=filename))
        ident, version = struct.unpack_from("<HH", main, 0)
        flags = struct.unpack_from("<H", main, 0x0A)[0]
        if flags & 0x0100:
            raise LegacyDocError(tr("doc_encrypted", filename=filename))
        if ident != 0xA5EC or version < 0xC1:  # Word 6/95 y anteriores: otra estructura
            raise LegacyDocError(tr("doc_too_old", filename=filename))
        table_name = "1Table" if flags & 0x0200 else "0Table"
        if len(main) < 0x1AA or not ole.exists(table_name):
            raise LegacyDocError(tr("unreadable_file", filename=filename))
        table = ole.openstream(table_name).read()
    finally:
        ole.close()

    # El texto de todas las «historias» viene seguido, en este orden y con
    # estos largos: cuerpo, notas al pie, encabezados y pies, macros,
    # comentarios, notas finales, cuadros de texto, cuadros de los encabezados
    lengths = [max(n, 0) for n in struct.unpack_from("<8i", main, 0x4C)]
    clx_offset, clx_size = struct.unpack_from("<II", main, 0x1A2)
    text = _pieces_text(main, table[clx_offset:clx_offset + clx_size], filename)
    starts = [sum(lengths[:i]) for i in range(len(lengths))]
    return [text[starts[i]:starts[i] + lengths[i]] for i in (0, 1, 5, 6)]


def _pieces_text(main: bytes, clx: bytes, filename: str) -> str:
    """Recorre la tabla de piezas (Clx → PlcPcd) y arma el texto en orden."""
    pos = 0
    while pos + 3 <= len(clx) and clx[pos] == 0x01:  # bloques de formato previos: se saltan
        pos += 3 + struct.unpack_from("<H", clx, pos + 1)[0]
    if pos + 5 > len(clx) or clx[pos] != 0x02:
        raise LegacyDocError(tr("unreadable_file", filename=filename))
    size = struct.unpack_from("<I", clx, pos + 1)[0]
    plc = clx[pos + 5:pos + 5 + size]
    count = (len(plc) - 4) // 12
    if count < 1:
        raise LegacyDocError(tr("unreadable_file", filename=filename))
    starts = struct.unpack_from(f"<{count + 1}I", plc, 0)
    chunks: list[str] = []
    for i in range(count):
        length = starts[i + 1] - starts[i]
        where = struct.unpack_from("<I", plc, 4 * (count + 1) + 8 * i + 2)[0]
        offset = where & 0x3FFFFFFF
        if where & 0x40000000:  # pieza «comprimida»: un byte por carácter
            raw = main[offset // 2:offset // 2 + length]
            chunks.append(raw.decode("latin-1").translate(_ANSI_TABLE))
        else:
            chunks.append(main[offset:offset + 2 * length].decode("utf-16-le", "replace"))
    return "".join(chunks)


def _strip_fields(text: str) -> str:
    """Los campos (hipervínculos, índices, referencias) guardan su instrucción
    entre \\x13 y \\x14 y el resultado visible entre \\x14 y \\x15: queda solo
    el resultado. Los campos pueden anidarse."""
    if "\x13" not in text:
        return text
    out: list[str] = []
    stack: list[bool] = []  # por cada campo abierto: ¿sigue en la instrucción?
    hidden = 0
    for part in _FIELD_MARKS.split(text):
        if part == "\x13":
            stack.append(True)
            hidden += 1
        elif part == "\x14":
            if stack and stack[-1]:
                stack[-1] = False
                hidden -= 1
        elif part == "\x15":
            if stack and stack.pop():
                hidden -= 1
        elif not hidden:
            out.append(part)
    return "".join(out)


def _layout(text: str) -> str:
    """De los caracteres de control de Word a texto corrido, con el mismo
    criterio que los .docx: un párrafo por línea y las filas de tabla como
    «celda | celda» (muchas transcripciones vienen en tablas).

    \\x07 cierra una celda y dos seguidos cierran la fila. Una celda vacía
    también deja dos seguidos, así que una fila con celdas vacías puede quedar
    en dos líneas: se conserva todo el texto, que es lo que importa."""
    text = re.sub("\x07(\x07?)", lambda m: "\r" if m.group(1) else _CELL, text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x0b", "\n").replace("\x0c", "\n").replace("\x1e", "-")
    text = _INVISIBLE.sub("", text)
    lines: list[str] = []
    for line in text.split("\n"):
        if _CELL in line:
            cells = [cell.strip() for cell in line.split(_CELL)]
            line = " | ".join(cell for cell in cells if cell)
        lines.append(line)
    return "\n".join(lines).strip("\n")


# ----- RTF -----

_RTF_TOKEN = re.compile(
    r"\\([a-zA-Z]{1,32})(-?\d{1,10})?[ ]?"  # palabra de control, con número opcional
    r"|\\'([0-9a-fA-F]{2})"                 # byte en la página de códigos
    r"|\\(.)"                               # símbolo de control
    r"|([{}])"
    r"|([\r\n]+)"                           # saltos del archivo: no son texto
    r"|([^\\{}\r\n]+)",                     # texto
    re.DOTALL,
)

# Grupos que no son texto del cuerpo: tablas de fuentes y estilos, metadatos,
# imágenes, objetos, encabezados y pies, notas, viñetas automáticas, formas
_RTF_SKIP = frozenset("""
fonttbl colortbl stylesheet info pict object objdata objclass header headerl headerr
headerf footer footerl footerr footerf footnote annotation atnid atnauthor atnref
fldinst datafield themedata colorschememapping latentstyles datastore listtable
listoverridetable rsidtbl generator xmlnstbl pntext listtext shpinst shppict nonshppict
filetbl revtbl template bkmkstart bkmkend tc xe pgptbl
""".split())

_RTF_WORDS = {
    "par": "\r", "sect": "\r", "page": "\r", "line": "\x0b", "row": "\r", "nestrow": "\r",
    "cell": _CELL, "nestcell": _CELL, "tab": "\t",
    "emdash": "\u2014", "endash": "\u2013", "emspace": " ", "enspace": " ", "qmspace": " ",
    "bullet": "\u2022", "lquote": "\u2018", "rquote": "\u2019",
    "ldblquote": "\u201c", "rdblquote": "\u201d",
}

_RTF_SYMBOLS = {
    "~": "\u00a0", "_": "-", "{": "{", "}": "}", "\\": "\\", "\n": "\r", "\r": "\r",
}

_RTF_CODEPAGES = {"ansi": "cp1252", "mac": "mac_roman", "pc": "cp437", "pca": "cp850"}


def _rtf_text(data: bytes) -> str:
    """Texto visible de un RTF, con los mismos caracteres de control que usa
    Word (los ordena _layout). Respeta \\uN con sus caracteres de respaldo,
    \\'hh en la página de códigos declarada, y omite lo borrado con control
    de cambios (\\deleted)."""
    source = data.decode("latin-1")
    out: list[str] = []
    stack: list[tuple[bool, int, bool]] = []
    skip, fallback, deleted = False, 1, False  # estado del grupo actual
    codepage = "cp1252"
    pending = 0  # caracteres de respaldo que faltan por saltar tras un \uN
    high = None  # mitad alta de un par sustituto (caracteres fuera del plano básico)
    raw = bytearray()  # bytes \'hh seguidos: se decodifican juntos (páginas de 2 bytes)
    opening = False  # ¿lo anterior fue «{»? Ahí se decide si el grupo se omite
    pos, end = 0, len(source)

    while pos < end:
        match = _RTF_TOKEN.match(source, pos)
        if match is None:  # una barra invertida al final del archivo
            break
        pos = match.end()
        word, arg, hexa, symbol, brace, newline, chars = match.groups()
        if newline:
            continue
        if hexa is None and raw:
            out.append(bytes(raw).decode(codepage, "replace"))
            raw.clear()
        if brace:
            if brace == "{":
                stack.append((skip, fallback, deleted))
            elif stack:
                skip, fallback, deleted = stack.pop()
            opening = brace == "{"
            pending = 0
            continue
        was_opening, opening = opening, False

        if word:
            if word == "bin":  # datos binarios incrustados: se saltan tal cual
                pos += max(int(arg or 0), 0)
            elif was_opening and word in _RTF_SKIP:
                skip = True
            elif word == "uc":
                fallback = max(int(arg or 1), 0)
            elif word == "u" and arg is not None:
                pending = fallback
                code = int(arg) & 0xFFFF
                if skip or deleted:
                    pass
                elif 0xD800 <= code < 0xDC00:
                    high = code
                elif 0xDC00 <= code < 0xE000:
                    if high is not None:
                        out.append(chr(0x10000 + ((high - 0xD800) << 10) + (code - 0xDC00)))
                    high = None
                else:
                    out.append(chr(code))
            elif pending:
                pending -= 1
            elif word in _RTF_CODEPAGES:
                codepage = _RTF_CODEPAGES[word]
            elif word == "ansicpg":
                codepage = _known_codepage(f"cp{arg}", codepage)
            elif word == "deleted":
                deleted = arg != "0"
            elif word == "plain":
                deleted = False
            elif word in _RTF_WORDS and not skip and not deleted:
                out.append(_RTF_WORDS[word])
            continue

        if symbol == "*" and was_opening:  # {\*\destino …}: opcional por definición
            skip = True
            opening = True  # la palabra que sigue todavía abre el grupo
            continue
        if pending:
            if chars and len(chars) > pending:
                chars, pending = chars[pending:], 0
            else:
                pending -= len(chars) if chars else 1
                continue
        if skip or deleted:
            continue
        if hexa:
            raw.append(int(hexa, 16))
        elif symbol:
            out.append(_RTF_SYMBOLS.get(symbol, ""))
        elif chars:
            out.append(chars)
    if raw:
        out.append(bytes(raw).decode(codepage, "replace"))
    return "".join(out)


def _known_codepage(name: str, default: str) -> str:
    try:
        "".encode(name)
        return name
    except LookupError:
        return default
