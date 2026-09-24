"""What the availability agent returns: can this buyer act right now?

One question. A buyer already in a process is out however well they fit, so this is kept
apart from relevance rather than folded into a single verdict.
"""

from typing import Any

from pydantic import Field, model_validator

from shared.schemas.blocks.evidence import CheckEvidence
from shared.schemas.common.base import Base
from shared.schemas.common.enums import CheckResult


class AvailabilityCheck(Base):
    in_process: bool | None = None
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


_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}

_EVIDENCE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reason", "text", "url", "retrieved_at"],
    "properties": {
        "reason": {"type": "string", "description": "reason code, e.g. in_active_process"},
        "text": {"type": "string", "description": "the quote the finding rests on"},
        "url": _STR,
        "retrieved_at": {"type": "string", "description": "ISO 8601, UTC"},
    },
}

AVAILABILITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["in_process", "evidence", "result"],
    "properties": {
        "in_process": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
        "evidence": {"type": "array", "items": _EVIDENCE},
        "result": {"enum": ["verified", "excluded"]},
    },
}
