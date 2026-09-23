"""Quotes backing what the record claims."""

from pydantic import AwareDatetime, HttpUrl

from shared.schemas.common.base import Base


class Evidence(Base):
    """One quote backing one field.

    `claim` is a dotted path into the item ("buyer_profile.aum"), the same key space
    `CompanyItem.provenance` uses, so a field, the source it came from and the text that
    supports it all line up on one key.
    """

    claim: str
    text: str
    url: HttpUrl | None = None
    source_key: str
    retrieved_at: AwareDatetime


class CheckEvidence(Base):
    """Why the check stage reached its verdict.

    Keyed by reason code rather than by field, because it backs
    `pipeline.exclusion_reason` / `flag_reason` instead of a value in the record.
    """

    reason: str
    text: str
    url: HttpUrl | None = None
    retrieved_at: AwareDatetime
