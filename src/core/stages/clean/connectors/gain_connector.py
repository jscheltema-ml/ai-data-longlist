"""Specific connector for the Gain MCP source to the unified Buyer data schema."""

from shared.schemas.buyer import Buyer
from shared.schemas.source_batch import SourceBatch
from stages.clean.utils import to_buyers

CONNECTOR = "gain_connector@0.1"


def standardize(data: SourceBatch) -> tuple[list[Buyer], list[Buyer]]:
    """Turn one batch of Gain records into buyers, and the ones that would not convert.

    Identical to the web-search connector today, because the Gain agent is given the same
    `SEARCH_AGENT_SCHEMA` and so returns the same shape. The two are kept apart because that
    is the thing most likely to stop being true: Gain is a structured provider rather than a
    web search, and the first field it reports differently belongs here.
    """
    return to_buyers(data, CONNECTOR)
