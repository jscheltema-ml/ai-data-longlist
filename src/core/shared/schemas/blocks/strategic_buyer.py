"""The buyer's own position, when it is an operating company."""

from pydantic import Field

from shared.schemas.blocks.financials import Financials
from shared.schemas.common.base import Base


class StrategicBuyer(Base):
    """Set only when `classification.buyer_type` is `strategic`.

    The figures sit in a `Financials` block rather than inline, so a strategic buyer's size
    and the target's size are the same shape and can be compared directly. They stand in for
    the capacity a fund gets from `dry_powder`: an acquirer's own earnings are what say
    whether a deal is within reach.

    `listed` and `ticker` are here because a listed acquirer's numbers are public and
    verifiable, which changes how much the rest of the record can be trusted. `parent` names
    the group above this entity, where there is one: an approach is wasted on a subsidiary
    that does not decide its own acquisitions.
    """

    financials: Financials = Field(default_factory=Financials)
    listed: bool | None = None
    ticker: str | None = None
    parent: str | None = None
