"""The merged company record, written by every stage."""

from pydantic import Field

from shared.schemas.blocks.buyer_profile import BuyerProfile
from shared.schemas.blocks.classification import Classification
from shared.schemas.blocks.evidence import CheckEvidence, Evidence
from shared.schemas.blocks.financials import Financials
from shared.schemas.blocks.identity import Identity
from shared.schemas.blocks.pipeline import Pipeline
from shared.schemas.blocks.quality import Quality
from shared.schemas.blocks.scoring import Scoring
from shared.schemas.common.base import Base
from shared.schemas.common.enums import IdBasis


class CompanyItem(Base):
    """One company, as it stands after however many stages have run.

    There is one record per company rather than one per stage: ingestion creates it,
    cleaning merges the sources into it, check and scoring fill their own blocks, and
    `pipeline` is the only thing that says which of those have happened. `quality` and
    `scoring` are None until the stage that owns them runs.

    Three fields describe where the content came from and they answer different questions:
    `found_by` is which sources returned the company at all, `external_ids` is what each
    one calls it, and `provenance` is which source each surviving field value came from.
    """

    item_id: str = Field(min_length=1)
    id_basis: IdBasis
    # Keyed by source or registry ("gain", "kvk", "lei"). A null value means the key was
    # looked for and not found, which is worth keeping so it is not looked for again.
    external_ids: dict[str, str | None] = Field(default_factory=dict)
    found_by: list[str] = Field(default_factory=list)

    pipeline: Pipeline

    identity: Identity
    classification: Classification = Field(default_factory=Classification)
    financials: Financials = Field(default_factory=Financials)
    buyer_profile: BuyerProfile = Field(default_factory=BuyerProfile)

    evidence: list[Evidence] = Field(default_factory=list)
    check_evidence: list[CheckEvidence] = Field(default_factory=list)

    # Dotted field path → the source key its value came from, e.g.
    # {"financials.revenue": "gain"}. Only fields that were actually filled appear.
    provenance: dict[str, str] = Field(default_factory=dict)

    quality: Quality | None = None
    scoring: Scoring | None = None
