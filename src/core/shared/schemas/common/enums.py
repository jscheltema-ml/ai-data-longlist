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


class BuyerType(StrEnum):
    """Which kind of buyer this is, and with it which of the two buyer blocks the record
    carries: a financial buyer has funds and dry powder, a strategic buyer has a P&L.

    Closed on purpose. `fund_type` below subdivides the financial side further and is where
    new kinds of investor go, so this stays a two-way split that the scoring can rely on.
    """

    FINANCIAL = "financial"
    STRATEGIC = "strategic"


class CapacityBasis(StrEnum):
    """Where the size bands came from.

    A band the buyer publishes is worth more than one derived from the deals they have done,
    so scoring needs to be able to tell them apart. `mixed` is the common case: a stated
    ticket size alongside an EV range inferred from their track record.
    """

    STATED = "stated"
    INFERRED = "inferred"
    MIXED = "mixed"


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

    `excluded` and `flagged` are judgements about the buyer and each carry a reason code;
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
# The spec leaves these open, so the fields carrying them are plain `str`. These tuples are
# the values seen so far: documentation, and the lists to turn into StrEnums once they stop
# growing. `holding_period` and `stake` in particular read as coded buckets rather than free
# text, so they are the first candidates to close.

KNOWN_SOURCE_KEYS = ("gain", "claude_web", "ml_archive")
KNOWN_FUND_TYPES = ("pe", "family_office", "search_fund", "holding")
KNOWN_STRATEGIES = ("buy_and_build",)
KNOWN_CUSTOMER_TYPES = ("b2b",)
KNOWN_STAKE_PREFERENCES = ("majority",)
KNOWN_HOLDING_PERIODS = ("5_7_years",)
