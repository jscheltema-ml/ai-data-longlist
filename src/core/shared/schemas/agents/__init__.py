"""Output formats for the agents, one module per agent.

Each is the shape its agent is instructed to return, composed of the same `blocks` models as
the merged record, so the connector into `CompanyItem` is a near-identity mapping.
"""

from shared.schemas.agents.search import SEARCH_AGENT_SCHEMA, SearchAgentCompany, SearchAgentOutput
from shared.schemas.agents.search_wip import WIP_SEARCH_SCHEMA, WIPSearchCompany, WIPSearchOutput

__all__ = [
    "SEARCH_AGENT_SCHEMA",
    "WIP_SEARCH_SCHEMA",
    "SearchAgentCompany",
    "SearchAgentOutput",
    "WIPSearchCompany",
    "WIPSearchOutput",
]
