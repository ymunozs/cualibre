"""Modelos de datos de CUA-LIBRE STUDIO.

Fuente de verdad de validación (data-model.md). Los offsets start/end son
unidades UTF-16 calculadas en el frontend; el backend los valida contra la
longitud UTF-16 del texto pero jamás rebana texto con ellos (research.md D2).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

import re

from pydantic import BaseModel, Field, field_validator, model_validator

from .i18n import tr

# Categorías Básicas: los 9 dominios de fábrica de Cua-libre, fijos e
# inmutables (Constitución, Principio VI / FR-016). El investigador puede
# además crear sus propias categorías personalizadas por proyecto (FR-064);
# ambas conviven — "DOMAINS" es solo el conjunto de fábrica.
DOMAINS: dict[str, str] = {
    "Emocional": "#FF3300",
    "Descriptivo": "#0066FF",
    "In Vivo": "#FFCC00",
    "Tensión/CHAT": "#FF0066",
    "Proceso": "#6600CC",
    "Teórico": "#00CC66",
    "Relacional": "#0099CC",
    "Crítico": "#CC0000",
    "Método": "#333333",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_id() -> str:
    return uuid.uuid4().hex


def utf16_len(text: str) -> int:
    """Longitud del texto en unidades UTF-16 (la que ve JavaScript)."""
    return len(text.encode("utf-16-le")) // 2


HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Document(BaseModel):
    id: str = Field(default_factory=new_id)
    filename: str
    text: str
    imported_at: str = Field(default_factory=now_iso)
    # Páginas cuyo texto se obtuvo por OCR (FR-080): transparencia sobre qué
    # parte del corpus es lectura automática de una imagen y no texto original
    ocr_pages: list[int] = Field(default_factory=list)


class Code(BaseModel):
    id: int
    created_at: str = Field(default_factory=now_iso)
    doc_id: Optional[str] = None  # None ⇔ código manual
    domain: str
    name: str
    quote: str = ""
    start: Optional[int] = None
    end: Optional[int] = None
    memo: str = ""


# Tipos de relación entre códigos (FR-038)
RELATION_TYPES: dict[str, str] = {
    "jerarquía": "contiene a",
    "asociación": "se asocia con",
    "causalidad": "influye en",
    "contradicción": "tensiona con",
}


# Extremos de una relación (FR-085): un código (por nombre) o una categoría
# (por su clave: Básica en castellano o nombre de la personalizada)
NODE_KINDS = ("code", "category")


class Relation(BaseModel):
    id: int
    source: str  # nombre de código o clave de categoría
    target: str
    type: str
    created_at: str = Field(default_factory=now_iso)
    source_kind: str = "code"  # proyectos anteriores a v1.14: siempre códigos
    target_kind: str = "code"


class CodebookEntry(BaseModel):
    """Descripción cualitativa de un código o categoría (FR-084): la estructura
    clásica de un libro de códigos. Texto libre, escrito solo por el investigador."""

    definition: str = ""
    inclusion: str = ""  # cuándo aplicarlo
    exclusion: str = ""  # cuándo no aplicarlo
    example: str = ""
    updated_at: str = Field(default_factory=now_iso)

    def is_empty(self) -> bool:
        return not any(f.strip() for f in (self.definition, self.inclusion,
                                           self.exclusion, self.example))


# Formas de nodo (FR-087). None = simbología nativa de Cua-libre: círculo para
# los códigos y cuadrado para las categorías
NODE_SHAPES = ("circle", "square", "diamond", "hexagon", "box")


class BoardNode(BaseModel):
    kind: str = "code"
    name: str
    x: Optional[float] = None  # None = ubicación automática (círculo)
    y: Optional[float] = None
    color: Optional[str] = None  # None = color de su categoría
    shape: Optional[str] = None  # None = forma nativa (FR-087)
    locked: bool = False  # fijo: no se arrastra ni se reordena (FR-087)


class Board(BaseModel):
    """Cuadro organizador (FR-085): una vista de las relaciones del proyecto.

    El cuadro general (id 0) muestra siempre todas las relaciones, como el
    organizador de siempre; sus nodos solo guardan posición y color. Los
    cuadros propios muestran únicamente los nodos que el investigador puso en
    ellos y las relaciones entre esos nodos."""

    id: int
    name: str = ""
    nodes: list[BoardNode] = Field(default_factory=list)
    edge_colors: dict[str, str] = Field(default_factory=dict)  # id de relación -> #hex
    show_tone: bool = False  # tono emocional sobre los nodos (FR-086)
    locked: bool = False  # cuadro bloqueado: nada se mueve (FR-087)


class LexiconOverrides(BaseModel):
    """Ajustes del investigador al léxico de sentimiento (FR-086), por idioma:
    palabras descartadas de una emoción o polaridad, y palabras sumadas."""

    removed: dict[str, list[str]] = Field(default_factory=dict)  # categoría -> palabras
    added: dict[str, list[str]] = Field(default_factory=dict)

    def is_empty(self) -> bool:
        return not any(self.removed.values()) and not any(self.added.values())


class LitCoding(BaseModel):
    """Pasaje de la biblioteca codificado con un código del proyecto (FR-091).
    Vive aparte de los códigos del corpus: no entra en Analytics, co-ocurrencia,
    sentimiento, acuerdo ni exportaciones del corpus (decisión del investigador)."""

    id: int
    item_id: str  # documento de la biblioteca (común a todos los proyectos)
    name: str  # nombre de un código del proyecto
    domain: str
    quote: str = ""
    memo: str = ""
    page: Optional[int] = None  # PDF: página (desde 1) y rectángulos en fracciones
    rects: list[list[float]] = Field(default_factory=list)
    start: Optional[int] = None  # texto (Word/TXT): offsets UTF-16, como el Canvas
    end: Optional[int] = None
    created_at: str = Field(default_factory=now_iso)


class Project(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    documents: list[Document] = Field(default_factory=list)
    codes: list[Code] = Field(default_factory=list)
    next_code_id: int = 1
    relations: list[Relation] = Field(default_factory=list)
    next_relation_id: int = 1
    nlp_exclusions: list[str] = Field(default_factory=list)
    custom_domains: dict[str, str] = Field(default_factory=dict)  # nombre -> #hex (FR-064)
    corpus_lang: Optional[str] = None  # es/en/pt (FR-077); None = aún no definido
    # v1.14 (todos con valor por omisión: los proyectos anteriores abren igual)
    codebook: dict[str, CodebookEntry] = Field(default_factory=dict)  # nombre de código
    category_notes: dict[str, CodebookEntry] = Field(default_factory=dict)  # clave de categoría
    general_board: Board = Field(default_factory=lambda: Board(id=0))
    boards: list[Board] = Field(default_factory=list)
    next_board_id: int = 1
    sentiment_overrides: dict[str, LexiconOverrides] = Field(default_factory=dict)  # idioma
    lit_codings: list[LitCoding] = Field(default_factory=list)  # literatura (FR-091)
    next_lit_id: int = 1

    def summary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_count": len(self.documents),
            "code_count": len(self.codes),
        }


# ----- Payloads de la API -----

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("project_name_empty"))
        return v


class CodeCreate(BaseModel):
    doc_id: Optional[str] = None
    domain: str
    name: str = Field(max_length=200)
    quote: str = ""
    start: Optional[int] = None
    end: Optional[int] = None
    memo: str = ""

    # La pertenencia real del dominio (¿existe entre las Categorías Básicas o
    # las personalizadas del proyecto?) se valida en el endpoint, que es quien
    # tiene acceso al proyecto activo (FR-064) — aquí solo se exige no-vacío.
    @field_validator("domain")
    @classmethod
    def non_empty_domain(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("domain_empty"))
        return v

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("code_name_empty"))
        return v

    @model_validator(mode="after")
    def anchored_or_manual(self) -> "CodeCreate":
        if self.doc_id is None:
            if self.start is not None or self.end is not None:
                raise ValueError(tr("manual_no_offsets"))
            self.quote = ""
        else:
            if self.start is None or self.end is None:
                raise ValueError(tr("anchored_needs_offsets"))
            if self.start < 0 or self.end <= self.start:
                raise ValueError(tr("offsets_incoherent"))
        return self


class CodeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    domain: Optional[str] = None
    memo: Optional[str] = None

    @field_validator("domain")
    @classmethod
    def non_empty_domain(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError(tr("domain_empty"))
        return v

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError(tr("code_name_empty"))
        return v


class CodeMerge(BaseModel):
    """Fusión/renombre en bloque (FR-068): todas las citas de from_name pasan
    a llamarse to_name. Si to_name ya existe, es una fusión real: adoptan su
    dominio (o el explícito, si se da). Si to_name es nuevo, es un renombre
    puro y cada instancia conserva su dominio original."""

    from_name: str = Field(min_length=1, max_length=200)
    to_name: str = Field(min_length=1, max_length=200)
    domain: Optional[str] = None

    @field_validator("from_name", "to_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("name_empty"))
        return v

    @model_validator(mode="after")
    def distinct_names(self) -> "CodeMerge":
        if self.from_name == self.to_name:
            raise ValueError(tr("merge_same_names"))
        return self


class CustomDomainCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    color: str

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("category_name_empty"))
        return v

    @field_validator("color")
    @classmethod
    def valid_hex(cls, v: str) -> str:
        if not HEX_COLOR_RE.match(v):
            raise ValueError(tr("invalid_color", value=v))
        return v.upper()


def _valid_kind(v: str) -> str:
    if v not in NODE_KINDS:
        raise ValueError(tr("invalid_node_kind", value=v))
    return v


class RelationCreate(BaseModel):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    type: str
    source_kind: str = "code"
    target_kind: str = "code"
    board_id: Optional[int] = None  # cuadro activo: recibe ambos extremos

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if v not in RELATION_TYPES:
            raise ValueError(tr("invalid_relation_type", value=v))
        return v

    @field_validator("source_kind", "target_kind")
    @classmethod
    def valid_kind(cls, v: str) -> str:
        return _valid_kind(v)

    @model_validator(mode="after")
    def distinct_ends(self) -> "RelationCreate":
        if (self.source_kind, self.source) == (self.target_kind, self.target):
            raise ValueError(tr("relation_same_ends"))
        return self


class CodebookUpdate(BaseModel):
    kind: str  # "code" | "category"
    name: str = Field(min_length=1, max_length=200)
    definition: str = Field(default="", max_length=20000)
    inclusion: str = Field(default="", max_length=20000)
    exclusion: str = Field(default="", max_length=20000)
    example: str = Field(default="", max_length=20000)

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v: str) -> str:
        return _valid_kind(v)


class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("name_empty"))
        return v


class BoardNodeIn(BaseModel):
    kind: str = "code"
    name: str = Field(min_length=1, max_length=200)
    x: Optional[float] = None
    y: Optional[float] = None
    color: Optional[str] = None
    shape: Optional[str] = None
    locked: bool = False

    @field_validator("shape")
    @classmethod
    def valid_shape(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in NODE_SHAPES:
            raise ValueError(tr("invalid_node_shape", value=v))
        return v

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v: str) -> str:
        return _valid_kind(v)

    @field_validator("color")
    @classmethod
    def valid_hex(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not HEX_COLOR_RE.match(v):
            raise ValueError(tr("invalid_color", value=v))
        return v.upper() if v else v


class BoardUpdate(BaseModel):
    """Reemplazo completo de un cuadro (posiciones, colores, nombre, tono)."""

    name: Optional[str] = Field(default=None, max_length=80)
    nodes: list[BoardNodeIn] = Field(default_factory=list, max_length=2000)
    edge_colors: dict[str, str] = Field(default_factory=dict)
    show_tone: bool = False
    locked: bool = False

    @field_validator("edge_colors")
    @classmethod
    def valid_colors(cls, v: dict[str, str]) -> dict[str, str]:
        for color in v.values():
            if not HEX_COLOR_RE.match(color):
                raise ValueError(tr("invalid_color", value=color))
        return {k: c.upper() for k, c in v.items()}


# Categorías del léxico que el investigador puede ajustar (FR-086): las ocho
# emociones del NRC (claves en castellano, como en lexicons.EMOTIONS) y las
# dos polaridades
SENTIMENT_CATEGORIES = ("alegría", "confianza", "miedo", "sorpresa", "tristeza", "asco",
                        "rabia", "anticipación", "positivo", "negativo")
LEXICON_WORD_RE = re.compile(r"^[^\W\d_]+(?:['’-][^\W\d_]+)*$")


class LexiconOverridesUpdate(BaseModel):
    lang: str
    removed: dict[str, list[str]] = Field(default_factory=dict)
    added: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("removed", "added")
    @classmethod
    def clean(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        cleaned: dict[str, list[str]] = {}
        for category, words in v.items():
            if category not in SENTIMENT_CATEGORIES:
                raise ValueError(tr("invalid_sentiment_category", value=category))
            normalized = set()
            for word in words:
                word = word.strip().lower()
                if not word:
                    continue
                if len(word) > 60 or not LEXICON_WORD_RE.match(word):
                    raise ValueError(tr("lexicon_word_invalid", value=word))
                normalized.add(word)
            if normalized:
                cleaned[category] = sorted(normalized)
        return cleaned


class ConfirmPayload(BaseModel):
    confirm: bool = False


# ----- Biblioteca de literatura (FR-089..092) -----

LIT_TYPES = ("article", "book", "chapter", "thesis", "report", "other")
ANNOTATION_KINDS = ("highlight", "underline", "strike", "note")


class Person(BaseModel):
    family: str = Field(default="", max_length=200)
    given: str = Field(default="", max_length=200)


class LitMeta(BaseModel):
    """Metadatos bibliográficos (para la lista de referencias en APA 7)."""

    type: str = "article"
    title: str = Field(default="", max_length=1000)
    authors: list[Person] = Field(default_factory=list)
    editors: list[Person] = Field(default_factory=list)  # capítulos de libro
    year: str = Field(default="", max_length=20)
    container: str = Field(default="", max_length=500)  # revista o libro
    volume: str = Field(default="", max_length=40)
    issue: str = Field(default="", max_length=40)
    pages: str = Field(default="", max_length=40)
    publisher: str = Field(default="", max_length=300)
    doi: str = Field(default="", max_length=300)
    url: str = Field(default="", max_length=1000)
    isbn: str = Field(default="", max_length=40)

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        return v if v in LIT_TYPES else "other"


class LibraryItem(BaseModel):
    id: str = Field(default_factory=new_id)
    kind: str = "pdf"  # pdf | text (Word/TXT) | ref (solo la referencia, sin archivo)
    filename: str = ""
    file: str = ""  # nombre del archivo guardado en biblioteca/archivos/
    sha1: str = ""
    pages: int = 0
    added_at: str = Field(default_factory=now_iso)
    meta: LitMeta = Field(default_factory=LitMeta)
    note: str = ""


class Annotation(BaseModel):
    """Anotación de lectura (de la persona, no de un proyecto): resaltar,
    subrayar, tachar o nota, sobre un PDF (página + rectángulos) o un texto
    (offsets UTF-16). El archivo original nunca se modifica."""

    id: str = Field(default_factory=new_id)
    item_id: str
    kind: str = "highlight"
    color: str = "#FFCC00"
    page: Optional[int] = None
    rects: list[list[float]] = Field(default_factory=list)
    start: Optional[int] = None
    end: Optional[int] = None
    quote: str = ""
    comment: str = ""
    created_at: str = Field(default_factory=now_iso)


class Library(BaseModel):
    items: list[LibraryItem] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)


def _clean_rects(v: list[list[float]]) -> list[list[float]]:
    if len(v) > 400:
        raise ValueError(tr("invalid_field", field="rects"))
    out = []
    for r in v:
        if len(r) != 4 or not all(-0.01 <= x <= 1.01 for x in r):
            raise ValueError(tr("invalid_field", field="rects"))
        out.append([round(float(x), 5) for x in r])
    return out


class AnchorIn(BaseModel):
    """Dónde está un pasaje: página + rectángulos (PDF) u offsets (texto)."""

    item_id: str = Field(min_length=1, max_length=64)
    quote: str = Field(default="", max_length=20000)
    page: Optional[int] = Field(default=None, ge=1)
    rects: list[list[float]] = Field(default_factory=list)
    start: Optional[int] = Field(default=None, ge=0)
    end: Optional[int] = Field(default=None, ge=0)

    @field_validator("rects")
    @classmethod
    def valid_rects(cls, v):
        return _clean_rects(v)

    @model_validator(mode="after")
    def anchored(self):
        pdf = self.page is not None and bool(self.rects)
        text = self.start is not None and self.end is not None and self.end > self.start
        if not (pdf or text):
            raise ValueError(tr("offsets_incoherent"))
        return self


class AnnotationCreate(AnchorIn):
    kind: str = "highlight"
    color: str = "#FFCC00"
    comment: str = Field(default="", max_length=20000)

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v: str) -> str:
        if v not in ANNOTATION_KINDS:
            raise ValueError(tr("invalid_field", field="kind"))
        return v

    @field_validator("color")
    @classmethod
    def valid_hex(cls, v: str) -> str:
        if not HEX_COLOR_RE.match(v):
            raise ValueError(tr("invalid_color", value=v))
        return v.upper()


class AnnotationUpdate(BaseModel):
    kind: Optional[str] = None
    color: Optional[str] = None
    comment: Optional[str] = Field(default=None, max_length=20000)

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v):
        if v is not None and v not in ANNOTATION_KINDS:
            raise ValueError(tr("invalid_field", field="kind"))
        return v

    @field_validator("color")
    @classmethod
    def valid_hex(cls, v):
        if v is not None and not HEX_COLOR_RE.match(v):
            raise ValueError(tr("invalid_color", value=v))
        return v.upper() if v else v


class LitCodingCreate(AnchorIn):
    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1)
    memo: str = Field(default="", max_length=20000)

    @field_validator("name", "domain")
    @classmethod
    def strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(tr("code_name_empty"))
        return v


class LitItemUpdate(BaseModel):
    meta: Optional[LitMeta] = None
    note: Optional[str] = Field(default=None, max_length=20000)


class DoiLookup(BaseModel):
    doi: str = Field(default="", max_length=300)
