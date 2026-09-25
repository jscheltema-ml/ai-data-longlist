"""Where an item has got to in the run."""

from pydantic import AwareDatetime, model_validator

from shared.schemas.common.base import Base
from shared.schemas.common.enums import CheckStatus, CleanedStatus, ScoredStatus


class Pipeline(Base):
    """Per-stage status, timestamp and the versioned thing that did the work.

    The check stage is two independent questions, so it is two sets of fields rather than
    one. Relevance asks whether the buyer fits the brief at all: sector, activity, size,
    geography. Availability asks whether they can act right now, which in practice means
    whether they are already in a process. A buyer can be a perfect fit and unavailable, or
    free and irrelevant, and the two are found from different evidence by different agents,
    so collapsing them into one verdict loses which one failed.

    The `*_by` fields carry a version ("relevance_agent@1.0") rather than a bare name, so a
    change in rules or prompt is visible in every record produced after it.

    Each stage writes only its own fields, which is what lets stages run out of step with
    each other on the same record.
    """

    ingested_at: AwareDatetime

    cleaned_status: CleanedStatus = CleanedStatus.PENDING
    cleaned_at: AwareDatetime | None = None
    cleaned_by: str | None = None
    cleaned_reason: str | None = None

    # Fits the brief: sector, activity, size, geography.
    relevant_status: CheckStatus = CheckStatus.PENDING
    relevant_at: AwareDatetime | None = None
    relevant_by: str | None = None
    relevant_reason: str | None = None

    # Free to act, meaning not already in a process.
    available_status: CheckStatus = CheckStatus.PENDING
    available_at: AwareDatetime | None = None
    available_by: str | None = None
    available_reason: str | None = None

    scored_status: ScoredStatus = ScoredStatus.PENDING
    scored_at: AwareDatetime | None = None
    scored_by: str | None = None

    @model_validator(mode="after")
    def _reasons_match_verdicts(self) -> "Pipeline":
        """A buyer that was dropped without a reason is unreviewable, and a reason on one that
        was not dropped is a leftover from an earlier verdict. Both are caught here, for the
        merge and for each of the two checks."""
        if (self.cleaned_status is CleanedStatus.FAILED) != (self.cleaned_reason is not None):
            raise ValueError("cleaned_reason must be set if and only if cleaned_status is 'failed'")

        for status, reason, name in (
            (self.relevant_status, self.relevant_reason, "relevant_reason"),
            (self.available_status, self.available_reason, "available_reason"),
        ):
            if (status is CheckStatus.EXCLUDED) != (reason is not None):
                raise ValueError(f"{name} must be set if and only if its status is 'excluded'")
        return self
