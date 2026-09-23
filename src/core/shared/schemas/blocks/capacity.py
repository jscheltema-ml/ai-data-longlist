"""What size of target the buyer can and will take on."""

from shared.schemas.common.amounts import MonetaryRange
from shared.schemas.common.base import Base
from shared.schemas.common.enums import CapacityBasis


class Capacity(Base):
    """Bands, not figures: this is what the buyer is shopping for, not what it reports.

    Three bands because they are not interchangeable. `ticket_size` is the equity the buyer
    writes, `target_ev_range` is the enterprise value of the deals it does, and
    `target_ebitda_range` is the earnings band it screens on. A buyer writing EUR 10-60M of
    equity can be in a EUR 150M deal alongside co-investors, so matching a target against
    the wrong band puts the buyer in the wrong tier.

    `basis` says how much any of it can be trusted.
    """

    ticket_size: MonetaryRange | None = None
    target_ev_range: MonetaryRange | None = None
    target_ebitda_range: MonetaryRange | None = None
    basis: CapacityBasis | None = None
