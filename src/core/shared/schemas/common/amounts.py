"""Quantities that carry their own units, shared by several blocks."""

from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import Field, StringConstraints, model_validator

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
    """A single figure with its currency and scale.

    No default magnitude on purpose: a missing unit silently meaning millions is the kind of
    bug that only shows up once it has moved a buyer up the ranking.
    """

    value: float
    currency: CurrencyCode
    unit: Magnitude
    # Absent on figures that carry no reporting date of their own, such as a fund's size.
    as_of: date | None = None


class MonetaryRange(Base):
    """A band, which is how a buyer states what it will look at.

    Either end may be open: "up to EUR 50M" is a real mandate and arrives as min=None. The
    currency and magnitude are on the range rather than on each end, because a band whose
    ends disagreed about either would be nonsense.
    """

    min: float | None = None
    max: float | None = None
    currency: CurrencyCode
    unit: Magnitude

    @model_validator(mode="after")
    def _min_not_above_max(self) -> "MonetaryRange":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"min {self.min} is above max {self.max}")
        return self


class Headcount(Base):
    """People, not money — hence no currency or magnitude."""

    value: int = Field(ge=0)
    as_of: date | None = None
