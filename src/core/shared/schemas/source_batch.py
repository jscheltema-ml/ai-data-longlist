"""What one adapter hands back for one run."""

from typing import Any

from pydantic import AwareDatetime, Field, model_validator

from shared.schemas.common.base import Base
from shared.schemas.common.enums import SourceStatus


class SourceBatch(Base):
    """One source's output for one run, before anything is normalised.

    The envelope is the unit that gets stored and retried: it says what was asked, how the
    call went and what came back, while `records` stays in whatever shape that source uses.
    Turning those into `Buyer` is a separate, deterministic connector per source, so
    a parser that cannot cope with a new field does not also lose the fetch.
    """

    run_id: str = Field(min_length=1)
    source_key: str = Field(min_length=1)
    # The adapter's own version, so a change in what it asks for is visible per batch.
    adapter_version: str = Field(min_length=1)
    # The query as the adapter actually issued it, not the user's request: the shape differs
    # per source and it is kept verbatim so a run can be explained or replayed.
    query: dict[str, Any] = Field(default_factory=dict)

    status: SourceStatus
    # Set exactly when the run did not fully succeed — see the validator below.
    error: str | None = None

    record_count: int = Field(ge=0)
    started_at: AwareDatetime
    finished_at: AwareDatetime

    # Source-shaped and deliberately untyped: see the class docstring.
    records: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _envelope_is_self_consistent(self) -> "SourceBatch":
        if (self.status is SourceStatus.OK) == (self.error is not None):
            raise ValueError("error must be set for a 'partial' or 'failed' run and absent for an 'ok' one")
        # Carried alongside the records rather than derived from them, so a mismatch means
        # records were dropped somewhere between the adapter and here.
        if self.record_count != len(self.records):
            raise ValueError(f"record_count is {self.record_count} but records holds {len(self.records)}")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at is before started_at")
        return self
