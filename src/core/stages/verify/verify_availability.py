"""Check if a company is currently or was recently a target in a separate M&A process and thus unavailable."""

from agents.agents.verify_available_agent import availability_agent
from shared.schemas.agents.available import AvailabilityCheck
from shared.schemas.buyer import Buyer
from stages.verify.utils import Check, run_check

AGENT = "availability_agent@0.1"

# Used when the agent excludes a buyer without saying which finding did it.
DEFAULT_REASON = "in_active_process"


async def verify_availability(buyers: list[Buyer]) -> list[Buyer]:
    """Check every buyer and return them all, each carrying its verdict."""
    return await run_check(
        buyers,
        Check(
            agent=availability_agent,
            result=AvailabilityCheck,
            prompt=_prompt,
            reason=_reason,
            field="available",
            by=AGENT,
        ),
    )


def _prompt(buyer: Buyer) -> str:
    """Only the identity: this asks about the company, not about its fit with anything."""
    identity = buyer.identity
    known = ", ".join(part for part in (identity.country, identity.domain) if part)
    return (
        "Determine whether this company is currently, or was recently, a target in an M&A "
        "process and therefore unavailable to act as a buyer.\n\n"
        f"Company: {identity.name}" + (f" ({known})" if known else "")
    )


def _reason(check: AvailabilityCheck) -> str:
    """The agent's own finding where it gave one, since that is what a reviewer looks up. Its
    evidence does not survive onto the buyer: the code is what the pipeline keeps."""
    if check.evidence:
        return check.evidence[0].reason
    return DEFAULT_REASON
