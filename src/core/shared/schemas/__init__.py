"""Schemas for the long list: the buyers it collects and what each stage adds to them.

The records that get stored sit at the top of this package:

- `SourceEnvelope` (`envelope.py`) — one adapter's raw output for one run, source-shaped.
- `CompanyItem` (`item.py`) — the merged buyer record every later stage reads and writes.

Underneath, `blocks/` holds the nested models `CompanyItem` is assembled from, `agents/`
holds what each agent is instructed to return, and `common/` holds what all of them build
on: the shared model config, primitive types and controlled vocabularies. Imports run one
way only, common → blocks → records and agents.

Import from this package rather than from the modules underneath, so the layout stays an
implementation detail.
"""

from shared.schemas.agents import (
    AVAILABILITY_SCHEMA,
    RELEVANCE_SCHEMA,
    SEARCH_AGENT_SCHEMA,
    WIP_SEARCH_SCHEMA,
    AvailabilityCheck,
    RelevanceCheck,
    SearchAgentCompany,
    SearchAgentOutput,
    WIPSearchCompany,
    WIPSearchOutput,
)
from shared.schemas.blocks import (
    Capacity,
    CheckEvidence,
    Classification,
    ConflictingValue,
    ConflictRecord,
    Deal,
    Evidence,
    FinancialBuyer,
    Financials,
    Fund,
    Identity,
    Mandate,
    Pipeline,
    Quality,
    ScoreComponent,
    Scoring,
    StrategicBuyer,
    Target,
    TrackRecord,
)
from shared.schemas.brief import SearchBrief
from shared.schemas.common import (
    KNOWN_CUSTOMER_TYPES,
    KNOWN_FUND_TYPES,
    KNOWN_HOLDING_PERIODS,
    KNOWN_SOURCE_KEYS,
    KNOWN_STAKE_PREFERENCES,
    KNOWN_STRATEGIES,
    Base,
    BuyerType,
    CapacityBasis,
    CheckResult,
    CheckStatus,
    CleanedStatus,
    CountryCode,
    CurrencyCode,
    Headcount,
    IdBasis,
    Magnitude,
    MonetaryAmount,
    MonetaryRange,
    ScoredStatus,
    SourceStatus,
)
from shared.schemas.envelope import SourceEnvelope
from shared.schemas.item import CompanyItem

__all__ = [
    "AVAILABILITY_SCHEMA",
    "RELEVANCE_SCHEMA",
    "SEARCH_AGENT_SCHEMA",
    "WIP_SEARCH_SCHEMA",
    "KNOWN_CUSTOMER_TYPES",
    "KNOWN_FUND_TYPES",
    "KNOWN_HOLDING_PERIODS",
    "KNOWN_SOURCE_KEYS",
    "KNOWN_STAKE_PREFERENCES",
    "KNOWN_STRATEGIES",
    "Base",
    "BuyerType",
    "Capacity",
    "CapacityBasis",
    "CheckEvidence",
    "CheckResult",
    "CheckStatus",
    "Classification",
    "CleanedStatus",
    "CompanyItem",
    "ConflictRecord",
    "ConflictingValue",
    "CountryCode",
    "CurrencyCode",
    "Deal",
    "Evidence",
    "Financials",
    "FinancialBuyer",
    "Fund",
    "Headcount",
    "IdBasis",
    "Identity",
    "Magnitude",
    "Mandate",
    "MonetaryAmount",
    "MonetaryRange",
    "Pipeline",
    "Quality",
    "ScoreComponent",
    "ScoredStatus",
    "Scoring",
    "AvailabilityCheck",
    "RelevanceCheck",
    "SearchAgentCompany",
    "SearchAgentOutput",
    "SourceEnvelope",
    "SourceStatus",
    "SearchBrief",
    "StrategicBuyer",
    "Target",
    "TrackRecord",
    "WIPSearchCompany",
    "WIPSearchOutput",
]
