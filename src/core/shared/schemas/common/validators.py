"""Cross-field rules that more than one model needs.

Kept out of the models themselves because the same rule holds for the merged record and for
what an agent hands back, and a rule enforced in one place but not the other is worse than
no rule at all.
"""

from typing import Any

from shared.schemas.common.enums import BuyerType


def check_buyer_blocks(
    buyer_type: BuyerType | None,
    financial_buyer: Any,
    strategic_buyer: Any,
) -> None:
    """A record carries the buyer block its `buyer_type` calls for, and only that one.

    Both blocks empty is legal while the buyer is still unclassified. A block filled in for
    the wrong type is not: it is either a mislabelled buyer or a leftover from before the
    classification changed, and both make the size scoring read the wrong numbers.
    """
    allowed = {
        BuyerType.FINANCIAL: ("financial_buyer", financial_buyer, "strategic_buyer", strategic_buyer),
        BuyerType.STRATEGIC: ("strategic_buyer", strategic_buyer, "financial_buyer", financial_buyer),
    }

    if buyer_type is None:
        for name, block in (("financial_buyer", financial_buyer), ("strategic_buyer", strategic_buyer)):
            if block is not None:
                raise ValueError(f"{name} is set but buyer_type is not, so there is nothing saying it belongs here")
        return

    _, _, wrong_name, wrong_block = allowed[buyer_type]
    if wrong_block is not None:
        raise ValueError(f"{wrong_name} must be null when buyer_type is {buyer_type.value!r}")
