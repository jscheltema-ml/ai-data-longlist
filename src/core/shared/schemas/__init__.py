"""Schemas shared by the ingestion, cleaning, check and scoring stages.

Two records matter, and they sit at the top of this package:

- `SourceEnvelope` (`envelope.py`) — one adapter's raw output for one run, source-shaped.
- `CompanyItem` (`item.py`) — the merged record every later stage reads and writes.

Underneath them, `blocks/` holds the nested models `CompanyItem` is assembled from, and
`common/` holds what both build on: the shared model config, primitive types and controlled
vocabularies. Imports run one way only, common → blocks → records.

Import from this package rather than from the modules underneath, so the layout stays an
implementation detail.
"""

from shared.schemas.blocks import (
    BuyerProfile,
    CheckEvidence,
    Classification,
    ConflictingValue,
    ConflictRecord,
    Evidence,
    Financials,
    Identity,
    Pipeline,
    Quality,
    ScoreComponent,
    Scoring,
)
from shared.schemas.common import (
    KNOWN_BUYER_TYPES,
    KNOWN_CUSTOMER_TYPES,
    KNOWN_FUND_TYPES,
    KNOWN_SOURCE_KEYS,
    KNOWN_STAKE_PREFERENCES,
    KNOWN_STRATEGIES,
    Base,
    CheckedStatus,
    CleanedStatus,
    CountryCode,
    CurrencyCode,
    Headcount,
    IdBasis,
    Magnitude,
    MonetaryAmount,
    ScoredStatus,
    SourceStatus,
)
from shared.schemas.envelope import SourceEnvelope
from shared.schemas.item import CompanyItem

__all__ = [
    "KNOWN_BUYER_TYPES",
    "KNOWN_CUSTOMER_TYPES",
    "KNOWN_FUND_TYPES",
    "KNOWN_SOURCE_KEYS",
    "KNOWN_STAKE_PREFERENCES",
    "KNOWN_STRATEGIES",
    "Base",
    "BuyerProfile",
    "CheckEvidence",
    "CheckedStatus",
    "Classification",
    "CleanedStatus",
    "CompanyItem",
    "ConflictRecord",
    "ConflictingValue",
    "CountryCode",
    "CurrencyCode",
    "Evidence",
    "Financials",
    "Headcount",
    "IdBasis",
    "Identity",
    "Magnitude",
    "MonetaryAmount",
    "Pipeline",
    "Quality",
    "ScoreComponent",
    "ScoredStatus",
    "Scoring",
    "SourceEnvelope",
    "SourceStatus",
]
