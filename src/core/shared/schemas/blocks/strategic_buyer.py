"""The buyer's own position, when it is an operating company."""

from shared.schemas.common.amounts import Headcount, MonetaryAmount
from shared.schemas.common.base import Base


class StrategicBuyer(Base):
    """Set only when `classification.buyer_type` is `strategic`.

    These are the buyer's reported figures, and they stand in for the capacity a fund gets
    from `dry_powder`: an acquirer's own earnings are what says whether a deal is within
    reach. `listed` and `ticker` are here because a listed acquirer's numbers are public and
    verifiable, which changes how much the rest of the record can be trusted.

    `parent` names the group above this entity, where there is one — an approach is wasted
    on a subsidiary that does not decide its own acquisitions.
    """

    revenue: MonetaryAmount | None = None
    ebitda: MonetaryAmount | None = None
    employees: Headcount | None = None
    listed: bool | None = None
    ticker: str | None = None
    parent: str | None = None
