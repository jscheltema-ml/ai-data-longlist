"""How a buyer invests — populated for buyers, empty for plain targets."""

from pydantic import Field

from shared.schemas.common.amounts import MonetaryAmount
from shared.schemas.common.base import Base, CountryCode


class BuyerProfile(Base):
    """The list fields default to empty rather than None: "no strategy recorded" and "we
    checked and there is none" are not worth distinguishing here, and an empty list keeps
    every consumer from having to guard before iterating.
    """

    countries_active: list[CountryCode] = Field(default_factory=list)
    # KNOWN_STRATEGIES / KNOWN_CUSTOMER_TYPES / KNOWN_STAKE_PREFERENCES / KNOWN_FUND_TYPES
    # are open vocabularies — see shared/schemas/common/enums.py.
    strategy: list[str] = Field(default_factory=list)
    # Free text until the vocabulary is settled: sources phrase it as "3-5 years", as a
    # single number of years, or not at all.
    holding_period: str | None = None
    customer_type: list[str] = Field(default_factory=list)
    stake_preference: list[str] = Field(default_factory=list)
    fund_type: str | None = None
    aum: MonetaryAmount | None = None
    dry_powder: MonetaryAmount | None = None
