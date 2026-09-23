"""Quantities that carry their own units, shared by financials and buyer profile."""

from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import Field, StringConstraints

from shared.schemas.common.base import Base

# ISO 4217, upper case ("EUR").
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class Magnitude(StrEnum):
    """The multiplier `value` is expressed in, so 82.0 EUR M reads as EUR 82 million."""

    UNITS = "1"
    THOUSANDS = "K"
    MILLIONS = "M"
    BILLIONS = "B"


class MonetaryAmount(Base):
    """A figure with its currency and scale.

    No default magnitude on purpose: a missing unit silently meaning millions is the kind
    of bug that only shows up in a ranking, so it has to be stated.
    """

    value: float
    currency: CurrencyCode
    unit: Magnitude
    # Absent on figures that carry no reporting date of their own, such as fund AUM.
    as_of: date | None = None


class Headcount(Base):
    """People, not money — hence no currency or magnitude."""

    value: int = Field(ge=0)
    as_of: date | None = None
