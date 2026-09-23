"""How complete the merged record is, and where the sources disagreed."""

from typing import Any

from pydantic import Field, model_validator

from shared.schemas.common.base import Base


class ConflictingValue(Base):
    """What one source said. `value` is untyped because a conflict can be about any field."""

    source: str
    value: Any


class ConflictRecord(Base):
    """Two or more sources disagreed on one field.

    Kept even after the merge picks a winner: a number that two sources disagree about is
    worth less than one they agree on, and only this record says which is which.
    """

    field: str
    values: list[ConflictingValue] = Field(min_length=2)
    # The source whose value was kept; None while the conflict is still unresolved.
    resolved_to: str | None = None

    @model_validator(mode="after")
    def _resolved_to_is_one_of_the_sources(self) -> "ConflictRecord":
        if self.resolved_to is None:
            return self
        sources = {v.source for v in self.values}
        if self.resolved_to not in sources:
            raise ValueError(f"resolved_to {self.resolved_to!r} is not among the conflicting sources {sorted(sources)}")
        return self


class Quality(Base):
    completeness: float = Field(ge=0.0, le=1.0)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
