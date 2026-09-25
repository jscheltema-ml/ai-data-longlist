"""One run of the long list: what was asked for, and what came of it."""

from pydantic import AwareDatetime, Field, model_validator

from shared.schemas.brief import Brief
from shared.schemas.common.base import Base
from shared.schemas.common.enums import RunStatus, SourceStatus, Stage, StageStatus


class SourceRun(Base):
    """What one source did for this run.

    Exists because a `SourceBatch` only exists if the adapter got far enough to produce
    one. A source that was asked for and never answered leaves nothing behind, and that is
    the failure most worth seeing, so it is recorded here rather than inferred from an
    absence.
    """

    status: SourceStatus = SourceStatus.FAILED
    record_count: int = Field(default=0, ge=0)
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    error: str | None = None


class StageRun(Base):
    """What one stage did for this run.

    `version` is the same versioned identifier the per-item `Pipeline` records
    ("merge_rules@1.3"), stated once here rather than read off an arbitrary item.
    """

    status: StageStatus = StageStatus.PENDING
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    version: str | None = None
    items_in: int | None = Field(default=None, ge=0)
    items_out: int | None = Field(default=None, ge=0)
    error: str | None = None


class Run(Base):
    """The job record, one level above `SourceBatch`.

    A run asks several sources for buyers against one brief, then puts the results through
    several stages. The envelopes hold what each source returned, and each `Buyer`
    holds its own `Pipeline` saying which stages have touched it. This holds neither of
    those: it holds what was *requested*, which is the one thing nothing else records.

    That distinction is the whole point. An item's pipeline says cleaning ran on it; only
    this says cleaning was asked for at all, and so only this can tell you that a stage you
    expected never ran, or that a source you asked for returned nothing.

    The brief is embedded rather than referenced, so a run stays readable after the brief it
    came from has been edited or deleted.
    """

    run_id: str = Field(min_length=1)
    brief: Brief

    status: RunStatus = RunStatus.PENDING
    created_at: AwareDatetime
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None

    # ── What was asked for ───────────────────────────────────
    requested_sources: list[str] = Field(min_length=1)
    requested_stages: list[Stage] = Field(min_length=1)
    # How many buyers each source was asked for. Per run rather than per source, until a
    # reason appears to vary it.
    search_volume: int | None = Field(default=None, ge=1)

    # ── What came of it ──────────────────────────────────────
    # Keyed by source key and stage, so a requested one that never reported is a missing key
    # rather than a silent absence; see the validator below.
    sources: dict[str, SourceRun] = Field(default_factory=dict)
    stages: dict[Stage, StageRun] = Field(default_factory=dict)

    error: str | None = None

    @model_validator(mode="after")
    def _outcomes_belong_to_the_request(self) -> "Run":
        """A run may report on fewer sources or stages than it was asked for, because it may
        still be going. It may not report on ones nobody asked for: that is a runner writing
        to the wrong key, and it would quietly widen what the run claims to have done."""
        for reported, requested, what in (
            (set(self.sources), set(self.requested_sources), "source"),
            (set(self.stages), set(self.requested_stages), "stage"),
        ):
            unasked = reported - requested
            if unasked:
                raise ValueError(f"{what} results for {sorted(str(u) for u in unasked)}, which were not requested")
        return self
