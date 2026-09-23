"""Manual en la app (FR-052): convierte MANUAL.md a HTML con un conversor
mínimo sin dependencias (títulos, tablas, listas, negritas, código, enlaces)."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path


def manual_path(lang: str = "es") -> Path:
    """MANUAL.md (español) o su traducción MANUAL.en.md / MANUAL.pt.md."""
    if getattr(sys, "frozen", False):
        folder = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        folder = Path(__file__).resolve().parent.parent
    translated = folder / f"MANUAL.{lang}.md"
    if lang != "es" and translated.exists():
        return translated
    return folder / "MANUAL.md"


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*\s][^*]*?)\*(?![*\w])", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text


def manual_html(lang: str = "es") -> str:
    lines = manual_path(lang).read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    list_tag: str | None = None  # "ul" u "ol" abierta
    in_table = False
    paragraph: list[str] = []  # líneas del párrafo en curso
    item: list[str] = []  # líneas del ítem de lista en curso

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_item() -> None:
        if item:
            out.append(f"<li>{_inline(' '.join(item))}</li>")
            item.clear()

    def close_blocks() -> None:
        nonlocal list_tag, in_table
        flush_paragraph()
        flush_item()
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                continue  # separador de cabecera
            if not in_table:
                close_blocks()
                out.append('<table class="data-table"><thead><tr>'
                           + "".join(f"<th>{_inline(c)}</th>" for c in cells)
                           + "</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</tbody></table>")
            in_table = False

        if not stripped:
            close_blocks()
            continue
        heading = re.match(r"(#{1,3})\s+(.*)", stripped)
        if heading:
            close_blocks()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        bullet = re.match(r"(-|\d+\.)\s+(.*)", stripped)
        if bullet:
            flush_paragraph()
            flush_item()
            tag = "ol" if bullet.group(1)[0].isdigit() else "ul"
            if list_tag != tag:
                if list_tag:
                    out.append(f"</{list_tag}>")
                out.append(f"<{tag}>")
                list_tag = tag
            item.append(bullet.group(2))
            continue
        if item and line[:1].isspace():  # continuación del ítem (línea sangrada)
            item.append(stripped)
            continue
        if list_tag:
            close_blocks()
        paragraph.append(stripped)  # párrafo de varias líneas

    close_blocks()
    return "\n".join(out)
