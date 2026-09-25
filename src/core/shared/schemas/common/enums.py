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


class Stage(StrEnum):
    """The stages a run can be asked for, in the order they run.

    The same five the per-item `Pipeline` tracks, plus ingestion, which has no per-item
    status because an item does not exist until it has happened.
    """

    INGESTION = "ingestion"
    CLEANING = "cleaning"
    RELEVANCE = "relevance"
    AVAILABILITY = "availability"
    SCORING = "scoring"


class RunStatus(StrEnum):
    """How a run as a whole is going.

    `partial` is the common ending rather than an edge case: one source failing while the
    others returned usable buyers is a result worth keeping, not a failed run.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class StageStatus(StrEnum):
    """How one stage of a run went. `skipped` means it was not among the stages requested."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SourceStatus(StrEnum):
    """How one adapter run ended. `partial` means usable records plus a reported failure."""

    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


class CleanedStatus(StrEnum):
    PENDING = "pending"
    MERGED = "merged"
    FAILED = "failed"


class CheckResult(StrEnum):
    """What a check agent can conclude.

    Only two outcomes, because an agent either found enough to keep the buyer or enough to
    drop it. The pipeline's own states (pending, failed, skipped) are facts about the run
    and are not the agent's to report, which is why `CheckStatus` is a separate enum.
    """

    VERIFIED = "verified"
    EXCLUDED = "excluded"


class CheckStatus(StrEnum):
    """Where one check has got to, for both relevance and availability.

    `verified` and `excluded` are the agent's verdict carried over; `failed` and `skipped`
    are what happened to the run. Only `excluded` carries a reason code.
    """

    PENDING = "pending"
    VERIFIED = "verified"
    EXCLUDED = "excluded"
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
