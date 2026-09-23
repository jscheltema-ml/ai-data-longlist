"""Controlled vocabularies used across the schemas."""

from enum import StrEnum


class IdBasis(StrEnum):
    """What `item_id` was derived from.

    Ordered strongest first: an LEI or a registration number identifies a legal entity
    outright, a domain is good enough in practice, and name + country is the last resort
    that the dedupe has to treat as a guess.
    """

    LEI = "lei"
    REGISTRATION = "registration"
    DOMAIN = "domain"
    NAME_COUNTRY = "name_country"


class SourceStatus(StrEnum):
    """How one adapter run ended. `partial` means usable records plus a reported failure."""

    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


class CleanedStatus(StrEnum):
    PENDING = "pending"
    MERGED = "merged"
    FAILED = "failed"


class CheckedStatus(StrEnum):
    """Verdict of the check stage.

    `excluded` and `flagged` are judgements about the company and each carry a reason code;
    `failed` and `skipped` are facts about the run and carry none.
    """

    PENDING = "pending"
    PASSED = "passed"
    EXCLUDED = "excluded"
    FLAGGED = "flagged"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScoredStatus(StrEnum):
    PENDING = "pending"
    SCORED = "scored"
    SKIPPED = "skipped"
    FAILED = "failed"


# ── Open vocabularies ────────────────────────────────────────
#
# The spec leaves these with a trailing "...", so the fields carrying them are plain `str`
# rather than enums. These tuples are the values in use today: documentation, and the lists
# to turn into StrEnums once they stop growing.

KNOWN_SOURCE_KEYS = ("gain", "claude_web", "ml_archive")
KNOWN_BUYER_TYPES = ("pe", "family_office", "strategic")
KNOWN_FUND_TYPES = ("pe",)
KNOWN_STRATEGIES = ("buy_and_build",)
KNOWN_CUSTOMER_TYPES = ("b2b",)
KNOWN_STAKE_PREFERENCES = ("majority",)
