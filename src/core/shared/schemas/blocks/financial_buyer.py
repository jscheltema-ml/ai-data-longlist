"""The buyer's own position, when it is a fund rather than a company."""

from pydantic import Field

from shared.schemas.common.amounts import MonetaryAmount
from shared.schemas.common.base import Base


class Fund(Base):
    """The vehicle currently being deployed.

    `vintage` matters as much as `size`: a fund raised five years ago is near the end of its
    investment period and unlikely to start something new, however much is left in it.
    """

    name: str | None = None
    vintage: int | None = Field(default=None, ge=1900, le=2100)
    size: MonetaryAmount | None = None


class FinancialBuyer(Base):
    """Set only when `classification.buyer_type` is `financial`.

    `dry_powder` is the one that says whether they can act now; `aum` only says how big they
    are. Both are kept because sources give one or the other and the merge should not have
    to choose.
    """

    # KNOWN_FUND_TYPES is an open vocabulary — see shared/schemas/common/enums.py.
    fund_type: str | None = None
    aum: MonetaryAmount | None = None
    dry_powder: MonetaryAmount | None = None
    current_fund: Fund | None = None
    portfolio_count: int | None = Field(default=None, ge=0)
