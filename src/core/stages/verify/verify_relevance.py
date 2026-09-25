"""Check whether a buyer fits the brief at all: sector, activity, size, geography."""

from agents.agents.verify_relevance_agent import relevance_agent
from shared.schemas.agents.relevant import RelevanceCheck
from shared.schemas.brief import Brief
from shared.schemas.buyer import Buyer
from stages.verify.utils import Check, candidate, run_check

AGENT = "relevance_agent@0.1"

# Which dimension failed, when the agent excludes a buyer without citing a finding. Ordered,
# so the first failing dimension is the one reported.
MISMATCH_REASONS = {
    "sector_fits": "sector_mismatch",
    "activity_fits": "activity_mismatch",
    "size_fits": "size_mismatch",
    "geography_fits": "geography_mismatch",
}
DEFAULT_REASON = "not_relevant"


async def verify_relevance(buyers: list[Buyer], brief: Brief) -> list[Buyer]:
    """Check every buyer against the brief and return them all, each carrying its verdict."""
    return await run_check(
        buyers,
        Check(
            agent=relevance_agent,
            result=RelevanceCheck,
            # Closes over the brief: relevance is a comparison, so it needs both sides.
            prompt=lambda buyer: _prompt(buyer, brief),
            reason=_reason,
            field="relevant",
            by=AGENT,
        ),
    )


def _prompt(buyer: Buyer, brief: Brief) -> str:
    """Both sides of the comparison, in the shape each already has.

    The brief and the buyer state the same things in the same blocks, so the agent is handed
    two records rather than a sentence assembled from them.
    """
    return (
        "Decide whether this buyer fits the brief, on each of sector, activity, size and "
        "geography. The brief describes the company being sold and the buyer we want; the "
        "candidate describes one buyer that was found.\n\n"
        f"BRIEF:\n{brief.model_dump_json(indent=2, exclude_none=True)}\n\n"
        f"CANDIDATE:\n{candidate(buyer)}"
    )


def _reason(check: RelevanceCheck) -> str:
    """The agent's own finding where it gave one. Otherwise the first dimension it marked as
    not fitting, because "excluded on geography" and "excluded on size" are different findings
    and the booleans are the only place that distinction survives."""
    if check.evidence:
        return check.evidence[0].reason
    for dimension, reason in MISMATCH_REASONS.items():
        if getattr(check, dimension) is False:
            return reason
    return DEFAULT_REASON
