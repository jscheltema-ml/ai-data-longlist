"""Shared configuration and primitive types for every schema in this package."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# ISO 3166-1 alpha-2, upper case ("NL", "BE").
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]


class Base(BaseModel):
    """Every model below inherits this.

    `extra="forbid"` is deliberate: these models are the contract between the stages, so a
    key nobody declared is a bug in the producer rather than data worth carrying along.
    Where a payload genuinely is source-shaped it gets an untyped dict instead, which is
    why `SourceEnvelope.records` is typed the way it is.

    Assignment is not revalidated: stages fill a record in over several steps, and
    validating each field as it is set would reject legal intermediate states (a status
    written before the reason that has to accompany it). Validation happens when a model
    is constructed, so a stage that changes a record rebuilds it — `model_copy(update=...)`
    followed by a re-validate, or a fresh constructor call.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
