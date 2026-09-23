"""Acuerdo entre codificadores (FR-078).

Dos personas codifican copias del mismo corpus en proyectos separados (una
exporta el respaldo .zip, la otra lo importa y codifica). Cua-libre compara
ambos proyectos sobre los documentos que comparten (mismo texto exacto,
aunque cambie el nombre del archivo) y calcula, para cada nombre de código:

- porcentaje de acuerdo,
- kappa de Cohen,
- alfa de Krippendorff (datos nominales, dos codificadores),

con el carácter como unidad de análisis (como NVivo): cada carácter del
documento está codificado o no con ese código por cada persona. Además lista
los fragmentos en desacuerdo, para discutirlos: el cálculo es una ayuda para
la conversación metodológica entre codificadores, nunca un veredicto
automático (Principio VIII). Nada se escribe en el banco de códigos.

Las posiciones son unidades UTF-16 (las del Canvas), idénticas en ambas copias
porque el texto es el mismo.
"""

from __future__ import annotations

import hashlib

from .models import Project

MAX_DISAGREEMENTS = 150  # fragmentos por código en la respuesta


def _merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Unión de intervalos [inicio, fin): los solapamientos se cuentan una vez."""
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


def _intersect(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        start, end = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if start < end:
            out.append((start, end))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _subtract(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Partes de a que no están en b (ambas ya unidas y ordenadas)."""
    out, j = [], 0
    for start, end in a:
        cursor = start
        while j < len(b) and b[j][1] <= cursor:
            j += 1
        k = j
        while k < len(b) and b[k][0] < end:
            if b[k][0] > cursor:
                out.append((cursor, b[k][0]))
            cursor = max(cursor, b[k][1])
            k += 1
        if cursor < end:
            out.append((cursor, end))
    return out


def _length(intervals) -> int:
    return sum(e - s for s, e in intervals)


def statistics(both: int, only_a: int, only_b: int, total: int) -> dict:
    """Tabla 2×2 (unidades codificadas por ambos / solo A / solo B / ninguno)
    → porcentaje de acuerdo, kappa de Cohen y alfa de Krippendorff."""
    neither = total - both - only_a - only_b
    if total <= 0:
        return {"agreement": None, "kappa": None, "alpha": None}
    po = (both + neither) / total
    pa, pb = (both + only_a) / total, (both + only_b) / total
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe) if pe < 1 else (1.0 if po == 1 else None)
    # Krippendorff, nominal, 2 codificadores sin datos faltantes
    ones = 2 * both + only_a + only_b
    zeros = 2 * neither + only_a + only_b
    n = 2 * total
    expected = 2 * ones * zeros / (n * (n - 1)) if n > 1 else 0
    observed = (only_a + only_b) / total
    alpha = 1 - observed / expected if expected > 0 else (1.0 if observed == 0 else None)
    round3 = lambda v: None if v is None else round(v, 3)
    return {"agreement": round3(po), "kappa": round3(kappa), "alpha": round3(alpha)}


def band(kappa: float | None) -> str:
    """Tramo de Landis y Koch (1977), solo orientativo."""
    if kappa is None:
        return "na"
    if kappa < 0:
        return "poor"
    for limit, name in ((0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial")):
        if kappa <= limit:
            return name
    return "almost_perfect"


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def compare(a: Project, b: Project) -> dict:
    """Compara la codificación de a (este proyecto) con la de b (el otro)."""
    b_docs = {_digest(d.text): d for d in b.documents}
    pairs = [(da, b_docs[_digest(da.text)]) for da in a.documents if _digest(da.text) in b_docs]
    names = sorted({c.name for c in a.codes if c.doc_id} | {c.name for c in b.codes if c.doc_id})

    def spans(project: Project, doc_id: str, name: str) -> list[tuple[int, int]]:
        return _merge([(c.start, c.end) for c in project.codes
                       if c.doc_id == doc_id and c.name == name and c.start is not None])

    codes_out = []
    totals = {"both": 0, "only_a": 0, "only_b": 0, "units": 0}
    for name in names:
        row = {"name": name, "both": 0, "only_a": 0, "only_b": 0, "units": 0,
               "count_a": 0, "count_b": 0, "documents": [], "disagreements": []}
        for da, db in pairs:
            sa, sb = spans(a, da.id, name), spans(b, db.id, name)
            row["count_a"] += sum(1 for c in a.codes if c.doc_id == da.id and c.name == name)
            row["count_b"] += sum(1 for c in b.codes if c.doc_id == db.id and c.name == name)
            if not sa and not sb:
                continue
            units = _utf16_len(da.text)
            both = _length(_intersect(sa, sb))
            only_a_spans, only_b_spans = _subtract(sa, sb), _subtract(sb, sa)
            only_a, only_b = _length(only_a_spans), _length(only_b_spans)
            doc_stats = statistics(both, only_a, only_b, units)
            row["documents"].append({"doc_id": da.id, "filename": da.filename,
                                     "both": both, "only_a": only_a, "only_b": only_b,
                                     **doc_stats})
            for who, fragments in (("a", only_a_spans), ("b", only_b_spans)):
                for start, end in fragments:
                    if len(row["disagreements"]) >= MAX_DISAGREEMENTS:
                        break
                    row["disagreements"].append({
                        "who": who, "doc_id": da.id, "filename": da.filename,
                        "start": start, "end": end, "quote": _slice_utf16(da.text, start, end),
                    })
            row["both"] += both
            row["only_a"] += only_a
            row["only_b"] += only_b
            row["units"] += units
        if row["count_a"] == 0 and row["count_b"] == 0:
            continue
        # Kappa del código sobre los documentos donde alguien lo usó (criterio de NVivo)
        row.update(statistics(row["both"], row["only_a"], row["only_b"], row["units"]))
        row["band"] = band(row["kappa"])
        for key in totals:
            totals[key] += row[key]
        codes_out.append(row)

    kappas = [r["kappa"] for r in codes_out if r["kappa"] is not None]
    overall = statistics(totals["both"], totals["only_a"], totals["only_b"], totals["units"])
    return {
        "project_a": {"id": a.id, "name": a.name, "codes": sum(1 for c in a.codes if c.doc_id)},
        "project_b": {"id": b.id, "name": b.name, "codes": sum(1 for c in b.codes if c.doc_id)},
        "shared_documents": [{"doc_id": da.id, "filename": da.filename} for da, _ in pairs],
        "only_in_a": [d.filename for d in a.documents if _digest(d.text) not in b_docs],
        "only_in_b": [d.filename for d in b.documents
                      if _digest(d.text) not in {_digest(x.text) for x in a.documents}],
        "codes": codes_out,
        "mean_kappa": round(sum(kappas) / len(kappas), 3) if kappas else None,
        "pooled": overall,
    }


def _slice_utf16(text: str, start: int, end: int) -> str:
    raw = text.encode("utf-16-le")
    return raw[start * 2:end * 2].decode("utf-16-le", errors="replace")


def to_csv_rows(result: dict, labels: dict[str, str]) -> list[list]:
    """Tabla por código para exportar (encabezados ya traducidos en labels)."""
    rows = [[labels[k] for k in ("code", "count_a", "count_b", "agreement", "kappa", "alpha", "band")]]
    for r in result["codes"]:
        rows.append([r["name"], r["count_a"], r["count_b"], r["agreement"], r["kappa"],
                     r["alpha"], labels.get("band_" + r["band"], r["band"])])
    return rows
