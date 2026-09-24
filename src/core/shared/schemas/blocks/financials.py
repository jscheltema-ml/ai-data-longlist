"""A company's own reported numbers.

Deliberately used by both sides: the company being sold carries one of these, and so does a
strategic buyer. They are the same idea, and holding one definition means a size comparison
between brief and buyer compares like with like.

Not to be confused with `Capacity`, which is a band a buyer will *pay*, not a figure anyone
reports.
"""

from shared.schemas.common.amounts import Headcount, MonetaryAmount
from shared.schemas.common.base import Base


class Financials(Base):
    """All optional: sources fill in two or three, and the merge records the rest."""

    revenue: MonetaryAmount | None = None
    ebitda: MonetaryAmount | None = None
    ebit: MonetaryAmount | None = None
    enterprise_value: MonetaryAmount | None = None
    equity: MonetaryAmount | None = None
    employees: Headcount | None = None
