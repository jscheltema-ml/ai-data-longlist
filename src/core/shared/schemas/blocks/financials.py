"""Reported figures for one company."""

from shared.schemas.common.amounts import Headcount, MonetaryAmount
from shared.schemas.common.base import Base


class Financials(Base):
    """Every field is optional: most sources fill in two or three of them, and which value
    survives when they disagree is recorded in `Quality.conflicts` rather than here.
    """

    revenue: MonetaryAmount | None = None
    ebitda: MonetaryAmount | None = None
    ebit: MonetaryAmount | None = None
    enterprise_value: MonetaryAmount | None = None
    equity: MonetaryAmount | None = None
    employees: Headcount | None = None
