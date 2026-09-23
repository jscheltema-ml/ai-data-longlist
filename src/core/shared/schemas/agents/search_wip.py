"""Cut-down search output, for testing throughput before the full schema is worth paying for.

Nine flat fields, one nesting level, one enum. Types are deliberately loose — `country` is a
plain string, not the alpha-2 pattern — so a test run shows what the agent actually returns
instead of failing validation on it.
"""

from typing import Any

from pydantic import Field, model_validator

from shared.schemas.common.base import Base
from shared.schemas.common.enums import BuyerType


class WIPSearchCompany(Base):
    name: str
    website: str | None = None
    country: str | None = None
    buyer_type: BuyerType | None = None
    sector_text: str | None = None
    countries_active: list[str] = Field(default_factory=list)
    ticket_size_min_eur_m: float | None = None
    ticket_size_max_eur_m: float | None = None
    source_url: str | None = None


class WIPSearchOutput(Base):
    companies: list[WIPSearchCompany] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _drop_nulls(cls, data: Any) -> Any:
        return _without_nulls(data)


def _without_nulls(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: _without_nulls(value) for key, value in node.items() if value is not None}
    if isinstance(node, list):
        return [_without_nulls(item) for item in node]
    return node


_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}
_NUM = {"anyOf": [{"type": "number"}, {"type": "null"}]}

_COMPANY_PROPERTIES: dict[str, Any] = {
    "name": {"type": "string"},
    "website": _STR,
    "country": _STR | {"description": "ISO 3166-1 alpha-2, e.g. NL"},
    "buyer_type": {"anyOf": [{"enum": ["financial", "strategic"]}, {"type": "null"}]},
    "sector_text": _STR | {"description": "the sector in the source's own words"},
    "countries_active": {"type": "array", "items": {"type": "string"}, "description": "ISO 3166-1 alpha-2"},
    "ticket_size_min_eur_m": _NUM | {"description": "equity per deal, EUR millions"},
    "ticket_size_max_eur_m": _NUM | {"description": "equity per deal, EUR millions"},
    "source_url": _STR | {"description": "a page backing the entry"},
}

WIP_SEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["companies"],
    "properties": {"companies": {"type": "array", "items": {"$ref": "#/$defs/Company"}}},
    "$defs": {
        "Company": {
            "type": "object",
            "additionalProperties": False,
            "required": list(_COMPANY_PROPERTIES),
            "properties": _COMPANY_PROPERTIES,
        }
    },
}
