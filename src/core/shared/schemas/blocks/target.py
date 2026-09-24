"""The company being sold: the subject of the search, not a result of it."""

from pydantic import Field

from shared.schemas.blocks.financials import Financials
from shared.schemas.blocks.identity import Identity
from shared.schemas.common.base import Base


class Target(Base):
    """What a buyer is being matched against.

    `sector_text` and `activity` are kept apart because they answer different questions and
    the relevance agent checks them separately. The sector is the label an industry list
    would give ("industrial automation"); the activity is what the company actually does
    ("retrofits control systems for food processing lines"). A buyer can be right on the
    sector and wrong on the activity, and only splitting them shows which.
    """

    identity: Identity
    sector_text: str | None = None
    activity: str | None = None
    description: str | None = None
    financials: Financials = Field(default_factory=Financials)
