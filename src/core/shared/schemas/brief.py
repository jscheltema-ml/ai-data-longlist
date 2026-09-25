"""What we are looking for: the input to a run."""

from pydantic import Field

from shared.schemas.blocks.capacity import Capacity
from shared.schemas.blocks.mandate import Mandate
from shared.schemas.blocks.target import Target
from shared.schemas.common.base import Base
from shared.schemas.common.enums import BuyerType


class Brief(Base):
    """The search parameters for one long list, and the other half of every comparison.

    A `Buyer` says what a buyer is and what it covers. This says what we want covered.
    Both sides use the same two blocks on purpose: `mandate` and `capacity` here are the
    buyer we are hoping to find, and on a `Buyer` they are the buyer we found, so
    relevance is a comparison of like with like rather than a translation between two
    vocabularies.

    Read the two halves as facts and wishes. `target` is fact: the company being sold, its
    sector, what it does, its numbers. Everything else is a wish about who should buy it,
    and `thesis` is where the reasoning goes that no field can hold.
    """

    brief_id: str = Field(min_length=1)
    #created_at: AwareDatetime

    # The company being sold.
    target: Target

    # Why a buyer would want it: the angle, in prose, for the agents to reason from. The
    # structured fields below say who to look for; this says why they would be interested,
    # which is the part that decides a borderline case.
    thesis: str | None = None

    # The buyer we are hoping to find. `mandate` is where and in what, `capacity` is at what
    # size, `buyer_types` is what kind. Empty means unconstrained, not "none apply".
    mandate: Mandate = Field(default_factory=Mandate)
    capacity: Capacity = Field(default_factory=Capacity)
    buyer_types: list[BuyerType] = Field(default_factory=list)

    # Reason codes a buyer is out on regardless of fit, e.g. a competitor the seller refuses
    # to approach. Applied by the check stage before anything is scored.
    exclusions: list[str] = Field(default_factory=list)
