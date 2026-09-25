"""Quotes backing what the record claims."""

from pydantic import AwareDatetime, HttpUrl

from shared.schemas.common.base import Base


class Evidence(Base):
    """One quote backing one field.

    `claim` is a dotted path into the item ("buyer_profile.aum"), the same key space
    `Buyer.provenance` uses, so a field, the source it came from and the text that
    supports it all line up on one key.
    """

    claim: str
    text: str
    url: HttpUrl | None = None
    source_key: str
    retrieved_at: AwareDatetime


class CheckEvidence(Base):
    """Why a check agent reached its verdict.

    Keyed by reason code rather than by field, because it backs a verdict rather than a
    value. It does not appear on `Buyer`: the surviving reason code is already in
    `pipeline.relevant_reason` / `available_reason`, and keeping the quotes there too would
    say the same thing twice. The agent output schemas carry it, and whatever a run needs to
    keep of it belongs with that run's record.
    """

    reason: str
    text: str
    url: HttpUrl | None = None
    retrieved_at: AwareDatetime
