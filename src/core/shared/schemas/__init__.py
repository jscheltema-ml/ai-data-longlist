"""Schemas for the long list: the buyers it collects and what each stage adds to them.

The records that get stored sit at the top of this package:

- `SourceBatch` (`batch.py`) — one adapter's raw output for one run, source-shaped.
- `Buyer` (`item.py`) — the merged buyer record every later stage reads and writes.

Underneath, `blocks/` holds the nested models `Buyer` is assembled from, `agents/`
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
from shared.schemas.brief import Brief
from shared.schemas.buyer import Buyer
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
    RunStatus,
    ScoredStatus,
    SourceStatus,
    Stage,
    StageStatus,
)
from shared.schemas.run import Run, SourceRun, StageRun
from shared.schemas.source_batch import SourceBatch

__all__ = [
    "AVAILABILITY_SCHEMA",
    "AvailabilityCheck",
    "Base",
    "BuyerType",
    "Capacity",
    "CapacityBasis",
    "CheckEvidence",
    "CheckResult",
    "CheckStatus",
    "Classification",
    "CleanedStatus",
    "Buyer",
    "ConflictRecord",
    "ConflictingValue",
    "CountryCode",
    "CurrencyCode",
    "Deal",
    "Evidence",
    "FinancialBuyer",
    "Financials",
    "Fund",
    "Headcount",
    "IdBasis",
    "Identity",
    "KNOWN_CUSTOMER_TYPES",
    "KNOWN_FUND_TYPES",
    "KNOWN_HOLDING_PERIODS",
    "KNOWN_SOURCE_KEYS",
    "KNOWN_STAKE_PREFERENCES",
    "KNOWN_STRATEGIES",
    "Magnitude",
    "Mandate",
    "MonetaryAmount",
    "MonetaryRange",
    "Pipeline",
    "Quality",
    "RELEVANCE_SCHEMA",
    "RelevanceCheck",
    "Run",
    "RunStatus",
    "SEARCH_AGENT_SCHEMA",
    "ScoreComponent",
    "ScoredStatus",
    "Scoring",
    "SearchAgentCompany",
    "SearchAgentOutput",
    "Brief",
    "SourceBatch",
    "SourceRun",
    "SourceStatus",
    "Stage",
    "StageRun",
    "StageStatus",
    "StrategicBuyer",
    "Target",
    "TrackRecord",
    "WIPSearchCompany",
    "WIPSearchOutput",
    "WIP_SEARCH_SCHEMA",
]
