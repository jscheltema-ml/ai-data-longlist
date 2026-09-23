"""What the buyer says it is looking for."""

from pydantic import Field

from shared.schemas.common.base import Base, CountryCode


class Mandate(Base):
    """The qualitative half of what the buyer wants: where, in what, on what terms.

    The size half lives in `Capacity`, separately, because the two are found in different
    places and are worth different amounts: a mandate is usually published, while the size
    bands are often inferred from deals (see `Capacity.basis`).

    The list fields default to empty rather than None. "Not recorded" and "checked, there is
    none" are not worth distinguishing here, and an empty list saves every consumer a guard.
    """

    countries_active: list[CountryCode] = Field(default_factory=list)
    sectors_of_interest: list[str] = Field(default_factory=list)
    # KNOWN_STRATEGIES / KNOWN_CUSTOMER_TYPES / KNOWN_STAKE_PREFERENCES are open
    # vocabularies — see shared/schemas/common/enums.py.
    strategy: list[str] = Field(default_factory=list)
    customer_type: list[str] = Field(default_factory=list)
    stake_preference: list[str] = Field(default_factory=list)
    # A coded bucket ("5_7_years"), not free text — KNOWN_HOLDING_PERIODS.
    holding_period: str | None = None
