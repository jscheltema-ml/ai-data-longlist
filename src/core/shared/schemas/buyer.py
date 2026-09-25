"""The merged buyer record, written by every stage."""

from pydantic import Field, model_validator

from shared.schemas.blocks.capacity import Capacity
from shared.schemas.blocks.classification import Classification
from shared.schemas.blocks.evidence import Evidence
from shared.schemas.blocks.financial_buyer import FinancialBuyer
from shared.schemas.blocks.identity import Identity
from shared.schemas.blocks.mandate import Mandate
from shared.schemas.blocks.pipeline import Pipeline
from shared.schemas.blocks.quality import Quality
from shared.schemas.blocks.scoring import Scoring
from shared.schemas.blocks.strategic_buyer import StrategicBuyer
from shared.schemas.blocks.track_record import TrackRecord
from shared.schemas.common.base import Base
from shared.schemas.common.enums import IdBasis
from shared.schemas.common.validators import check_buyer_blocks


class Buyer(Base):
    """One potential buyer, as it stands after however many stages have run.

    These are acquirers, not targets. Nothing here describes a company for sale: `mandate`
    and `capacity` are what the buyer is looking for, `track_record` is what it has bought,
    and only `financial_buyer` / `strategic_buyer` describe the buyer itself — and then only
    as far as it says whether they can act.

    One record per buyer rather than one per stage: ingestion creates it, cleaning merges the
    sources into it, check and scoring fill their own blocks, and `pipeline` is the only
    thing that says which of those have happened. `quality` and `scoring` are None until the
    stage that owns them runs.

    Three fields describe where the content came from, answering different questions:
    `found_by` is which sources returned the buyer at all, `external_ids` is what each one
    calls it, and `provenance` is which source each surviving field value came from.
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

    # What the buyer wants.
    mandate: Mandate = Field(default_factory=Mandate)
    capacity: Capacity = Field(default_factory=Capacity)

    # What the buyer is. Exactly one of these is set once `classification.buyer_type` is
    # known, and neither before then — see common/validators.check_buyer_blocks.
    financial_buyer: FinancialBuyer | None = None
    strategic_buyer: StrategicBuyer | None = None

    # What the buyer has done.
    track_record: TrackRecord = Field(default_factory=TrackRecord)

    evidence: list[Evidence] = Field(default_factory=list)

    # Dotted field path → the source key its value came from, e.g.
    # {"capacity.ticket_size": "claude_web"}. Only fields that were filled appear.
    provenance: dict[str, str] = Field(default_factory=dict)

    quality: Quality | None = None
    scoring: Scoring | None = None

    @model_validator(mode="after")
    def _buyer_block_matches_type(self) -> "Buyer":
        check_buyer_blocks(self.classification.buyer_type, self.financial_buyer, self.strategic_buyer)
        return self
