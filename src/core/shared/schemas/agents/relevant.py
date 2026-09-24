"""What the relevance agent returns: does this buyer fit the brief at all?

Four questions and a verdict. The booleans are kept alongside `result` rather than folded
into it, because "excluded on geography" and "excluded on size" are different findings and
the scoring stage reads them differently.
"""

from typing import Any

from pydantic import Field, model_validator

from shared.schemas.blocks.evidence import CheckEvidence
from shared.schemas.common.base import Base
from shared.schemas.common.enums import CheckResult


class RelevanceCheck(Base):
    sector_fits: bool | None = None
    activity_fits: bool | None = None
    size_fits: bool | None = None
    geography_fits: bool | None = None
    evidence: list[CheckEvidence] = Field(default_factory=list)
    result: CheckResult

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


_BOOL = {"anyOf": [{"type": "boolean"}, {"type": "null"}]}
_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}

_EVIDENCE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reason", "text", "url", "retrieved_at"],
    "properties": {
        "reason": {"type": "string", "description": "reason code, e.g. geography_mismatch"},
        "text": {"type": "string", "description": "the quote the finding rests on"},
        "url": _STR,
        "retrieved_at": {"type": "string", "description": "ISO 8601, UTC"},
    },
}

RELEVANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sector_fits", "activity_fits", "size_fits", "geography_fits", "evidence", "result"],
    "properties": {
        "sector_fits": _BOOL,
        "activity_fits": _BOOL,
        "size_fits": _BOOL,
        "geography_fits": _BOOL,
        "evidence": {"type": "array", "items": _EVIDENCE},
        "result": {"enum": ["verified", "excluded"]},
    },
}
