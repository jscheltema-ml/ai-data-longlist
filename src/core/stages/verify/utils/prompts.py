"""Rendering a buyer for a check's prompt."""

from shared.schemas.buyer import Buyer

# What an agent needs to judge a buyer. The pipeline, provenance, quality and scoring blocks
# say nothing about the buyer itself and would only be noise in the prompt.
CANDIDATE_BLOCKS = {
    "identity",
    "classification",
    "mandate",
    "capacity",
    "financial_buyer",
    "strategic_buyer",
    "track_record",
}


def candidate(buyer: Buyer) -> str:
    """The buyer as JSON, carrying only what is known about the company."""
    return buyer.model_dump_json(indent=2, exclude_none=True, include=CANDIDATE_BLOCKS)
