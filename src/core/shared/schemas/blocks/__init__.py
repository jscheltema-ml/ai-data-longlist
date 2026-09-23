"""The nested models `CompanyItem` is assembled from, one file per block.

Each is a field of `CompanyItem` and means nothing on its own. They are grouped here so the
two records stay at the top of the package and the pieces do not compete with them for
attention.
"""

from shared.schemas.blocks.buyer_profile import BuyerProfile
from shared.schemas.blocks.classification import Classification
from shared.schemas.blocks.evidence import CheckEvidence, Evidence
from shared.schemas.blocks.financials import Financials
from shared.schemas.blocks.identity import Identity
from shared.schemas.blocks.pipeline import Pipeline
from shared.schemas.blocks.quality import ConflictingValue, ConflictRecord, Quality
from shared.schemas.blocks.scoring import ScoreComponent, Scoring

__all__ = [
    "BuyerProfile",
    "CheckEvidence",
    "Classification",
    "ConflictRecord",
    "ConflictingValue",
    "Evidence",
    "Financials",
    "Identity",
    "Pipeline",
    "Quality",
    "ScoreComponent",
    "Scoring",
]
