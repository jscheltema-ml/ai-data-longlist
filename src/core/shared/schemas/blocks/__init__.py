"""The nested models `CompanyItem` is assembled from, one file per block.

Each is a field of `CompanyItem` and means little on its own. They are grouped here so the
records stay at the top of the package and the pieces do not compete with them for
attention. The search agent composes the same blocks, so a change here reaches both.
"""

from shared.schemas.blocks.capacity import Capacity
from shared.schemas.blocks.classification import Classification
from shared.schemas.blocks.evidence import CheckEvidence, Evidence
from shared.schemas.blocks.financial_buyer import FinancialBuyer, Fund
from shared.schemas.blocks.financials import Financials
from shared.schemas.blocks.identity import Identity
from shared.schemas.blocks.mandate import Mandate
from shared.schemas.blocks.pipeline import Pipeline
from shared.schemas.blocks.quality import ConflictingValue, ConflictRecord, Quality
from shared.schemas.blocks.scoring import ScoreComponent, Scoring
from shared.schemas.blocks.strategic_buyer import StrategicBuyer
from shared.schemas.blocks.target import Target
from shared.schemas.blocks.track_record import Deal, TrackRecord

__all__ = [
    "Capacity",
    "CheckEvidence",
    "Classification",
    "ConflictRecord",
    "ConflictingValue",
    "Deal",
    "Evidence",
    "Financials",
    "FinancialBuyer",
    "Fund",
    "Identity",
    "Mandate",
    "Pipeline",
    "Quality",
    "ScoreComponent",
    "Scoring",
    "StrategicBuyer",
    "Target",
    "TrackRecord",
]
