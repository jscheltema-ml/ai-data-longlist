"""What the buyer has actually bought."""

# Aliased because `Deal.date` shadows the name inside the class body.
from datetime import date as date_

from pydantic import Field, HttpUrl

from shared.schemas.common.amounts import MonetaryAmount
from shared.schemas.common.base import Base, CountryCode


class Deal(Base):
    """One acquisition. `url` is what makes it checkable, so a deal without one is hearsay."""

    target: str | None = None
    date: date_ | None = None
    country: CountryCode | None = None
    sector: str | None = None
    # KNOWN_STAKE_PREFERENCES — the same vocabulary as Mandate.stake_preference.
    stake: str | None = None
    ev: MonetaryAmount | None = None
    url: HttpUrl | None = None


class TrackRecord(Base):
    """What the buyer has done, as against what it says it wants in `Mandate`.

    This is the block that catches a stated mandate nobody acts on: a fund claiming to look
    at industrial automation in the Benelux, with no deal in five years, scores differently
    from one that closed three. `last_deal_at` carries most of that on its own.

    `sectors_acquired` and `countries_acquired` are summaries over the deals, kept alongside
    `recent_deals` because sources often give the summary without the underlying list.
    """

    deal_count_5y: int | None = Field(default=None, ge=0)
    last_deal_at: date_ | None = None
    sectors_acquired: list[str] = Field(default_factory=list)
    countries_acquired: list[CountryCode] = Field(default_factory=list)
    recent_deals: list[Deal] = Field(default_factory=list)
