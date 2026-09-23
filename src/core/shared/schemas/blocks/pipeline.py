"""Where an item has got to in the run."""

from pydantic import AwareDatetime, model_validator

from shared.schemas.common.base import Base
from shared.schemas.common.enums import CheckedStatus, CleanedStatus, ScoredStatus


class Pipeline(Base):
    """Per-stage status, timestamp and the versioned thing that did the work.

    The `*_by` fields carry a version ("merge_rules@1.3", "verify_agent@2.1") rather than a
    bare name, so a change in rules or prompt is visible in every record produced after it
    and two records scored differently can be told apart without guessing at dates.

    Each stage writes only its own three fields, which is what lets stages run out of step
    with each other on the same record.
    """

    ingested_at: AwareDatetime

    cleaned_status: CleanedStatus = CleanedStatus.PENDING
    cleaned_at: AwareDatetime | None = None
    cleaned_by: str | None = None

    checked_status: CheckedStatus = CheckedStatus.PENDING
    checked_at: AwareDatetime | None = None
    checked_by: str | None = None
    # Reason codes, each set exactly when its verdict says so — see the validator below.
    exclusion_reason: str | None = None
    flag_reason: str | None = None

    scored_status: ScoredStatus = ScoredStatus.PENDING
    scored_at: AwareDatetime | None = None
    scored_by: str | None = None

    @model_validator(mode="after")
    def _reasons_match_verdict(self) -> "Pipeline":
        """An excluded item without a reason is unreviewable, and a reason on an item that
        was not excluded is a leftover from an earlier verdict. Both are caught here."""
        for status, reason, name in (
            (CheckedStatus.EXCLUDED, self.exclusion_reason, "exclusion_reason"),
            (CheckedStatus.FLAGGED, self.flag_reason, "flag_reason"),
        ):
            if (self.checked_status is status) != (reason is not None):
                raise ValueError(f"{name} must be set if and only if checked_status is {status.value!r}")
        return self
