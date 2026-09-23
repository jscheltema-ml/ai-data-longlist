"""What kind of buyer this is."""

from shared.schemas.common.base import Base
from shared.schemas.common.enums import BuyerType


class Classification(Base):
    """`buyer_type` decides which of the two buyer blocks the record carries, so it is the
    one field here the rest of the schema reacts to.

    Sector wording is kept as the source phrased it rather than mapped onto a taxonomy: the
    scoring stage decides what "industrial automation" is worth against the mandate, and it
    can only do that if the original wording survives.
    """

    # None until the buyer has been classified; see common/validators.check_buyer_blocks.
    buyer_type: BuyerType | None = None
    sector_text: str | None = None
    description: str | None = None
