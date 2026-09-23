"""Búsqueda de literatura científica en OpenAlex (FR-023/024, research.md D7).

Funcionalidad protegida por el Principio I de la constitución.
"""

from __future__ import annotations

import httpx

from .i18n import tr

OPENALEX_URL = "https://api.openalex.org/works"
MAILTO = "ymunozsalinas@gmail.com"  # cortesía requerida por la API pública
MAX_RESULTS = 10


class LiteratureError(Exception):
    """Fallo de red o de la API, con mensaje apto para el usuario."""


def search_works(query: str, client: httpx.Client | None = None) -> list[dict]:
    params = {"search": query, "per-page": MAX_RESULTS, "mailto": MAILTO}
    own_client = client is None
    client = client or httpx.Client(timeout=10.0)
    try:
        response = client.get(OPENALEX_URL, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
    except (httpx.HTTPError, ValueError) as exc:
        raise LiteratureError(tr("openalex_error")) from exc
    finally:
        if own_client:
            client.close()

    return [
        {
            "title": work.get("display_name") or tr("untitled"),
            "year": work.get("publication_year"),
            "cited_by_count": work.get("cited_by_count", 0),
            "doi": work.get("doi"),
        }
        for work in results[:MAX_RESULTS]
    ]
