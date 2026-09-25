"""Specific connector for web_search to the unified Buyer data schema."""

from shared.schemas.buyer import Buyer
from shared.schemas.source_batch import SourceBatch
from stages.clean.utils import to_buyers

CONNECTOR = "web_search_connector@0.1"


def standardize(data: SourceBatch) -> tuple[list[Buyer], list[Buyer]]:
    """Turn one batch of web-search records into buyers, and the ones that would not convert.

    Nothing source-specific yet: the search agent is given `SEARCH_AGENT_SCHEMA`, so its
    records are already the blocks a `Buyer` is made of. This file is where a web-search
    quirk goes when one turns up, rather than into the shared conversion.
    """
    return to_buyers(data, CONNECTOR)
