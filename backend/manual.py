"""Manual en la app (FR-052): convierte MANUAL.md a HTML con un conversor
mínimo sin dependencias (títulos, tablas, listas, negritas, código, enlaces)."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path


def manual_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "MANUAL.md"
    return Path(__file__).resolve().parent.parent / "MANUAL.md"


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text


def manual_html() -> str:
    lines = manual_path().read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_list = in_table = False

    def close_blocks() -> None:
        nonlocal in_list, in_table
        if in_list:
            out.append("</ul>")
            in_list = False
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

        heading = re.match(r"(#{1,3})\s+(.*)", stripped)
        if heading:
            close_blocks()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        item = re.match(r"(?:-|\d+\.)\s+(.*)", stripped)
        if item:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(item.group(1))}</li>")
            continue
        close_blocks()
        if stripped:
            out.append(f"<p>{_inline(stripped)}</p>")

    close_blocks()
    return "\n".join(out)
