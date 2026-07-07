"""Modelos de datos de CUA-LIBRE STUDIO.

Fuente de verdad de validación (data-model.md). Los offsets start/end son
unidades UTF-16 calculadas en el frontend; el backend los valida contra la
longitud UTF-16 del texto pero jamás rebana texto con ellos (research.md D2).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# Paleta de 9 dominios fijos (Constitución, Principio VI / FR-016)
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


class Document(BaseModel):
    id: str = Field(default_factory=new_id)
    filename: str
    text: str
    imported_at: str = Field(default_factory=now_iso)


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


class Relation(BaseModel):
    id: int
    source: str  # nombre de código
    target: str  # nombre de código
    type: str
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
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v


class CodeCreate(BaseModel):
    doc_id: Optional[str] = None
    domain: str
    name: str = Field(max_length=200)
    quote: str = ""
    start: Optional[int] = None
    end: Optional[int] = None
    memo: str = ""

    @field_validator("domain")
    @classmethod
    def valid_domain(cls, v: str) -> str:
        if v not in DOMAINS:
            raise ValueError(f"Dominio inválido: {v!r}. Debe ser uno de: {', '.join(DOMAINS)}")
        return v

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre del código no puede estar vacío")
        return v

    @model_validator(mode="after")
    def anchored_or_manual(self) -> "CodeCreate":
        if self.doc_id is None:
            if self.start is not None or self.end is not None:
                raise ValueError("Un código manual no puede llevar offsets")
            self.quote = ""
        else:
            if self.start is None or self.end is None:
                raise ValueError("Un código anclado requiere offsets start y end")
            if self.start < 0 or self.end <= self.start:
                raise ValueError("Offsets incoherentes: se requiere 0 <= start < end")
        return self


class CodeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    domain: Optional[str] = None
    memo: Optional[str] = None

    @field_validator("domain")
    @classmethod
    def valid_domain(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in DOMAINS:
            raise ValueError(f"Dominio inválido: {v!r}")
        return v

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre del código no puede estar vacío")
        return v


class RelationCreate(BaseModel):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    type: str

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if v not in RELATION_TYPES:
            raise ValueError(
                f"Tipo de relación inválido: {v!r}. Usa: {', '.join(RELATION_TYPES)}"
            )
        return v

    @model_validator(mode="after")
    def distinct_ends(self) -> "RelationCreate":
        if self.source == self.target:
            raise ValueError("Una relación requiere dos códigos distintos")
        return self


class ConfirmPayload(BaseModel):
    confirm: bool = False
