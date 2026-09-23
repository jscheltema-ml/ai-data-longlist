"""What kind of company or investor this is."""

from shared.schemas.common.base import Base


class Classification(Base):
    """Free-text sector wording is kept as the source phrased it rather than mapped onto a
    taxonomy here: the scoring stage decides what "industrial automation" is worth, and it
    can only do that if the original wording survives.
    """

    # One of KNOWN_BUYER_TYPES, an open vocabulary — see shared/schemas/common/enums.py.
    buyer_type: str | None = None
    sector_text: str | None = None
    description: str | None = None
