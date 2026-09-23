"""The ranking stage's output."""

from pydantic import Field

from shared.schemas.common.base import Base


class ScoreComponent(Base):
    """One weighted term of the total.

    `contribution` is stored rather than recomputed from `raw * weight` so that a record
    scored under one config still explains itself after the weights have moved on.
    """

    raw: float
    weight: float = Field(ge=0.0, le=1.0)
    contribution: float


class Scoring(Base):
    total: float
    # 1 is the best tier.
    tier: int = Field(ge=1)
    # Keyed by component name ("sector_fit"), so the set of components is a property of the
    # ranking config rather than of this schema.
    components: dict[str, ScoreComponent] = Field(default_factory=dict)
    rationale: str | None = None
