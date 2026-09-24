"""Output formats for the agents, one module per agent.

Each is the shape its agent is instructed to return, composed of the same `blocks` models as
the merged record, so the connector into `CompanyItem` is a near-identity mapping.
"""

from shared.schemas.agents.available import AVAILABILITY_SCHEMA, AvailabilityCheck
from shared.schemas.agents.relevant import RELEVANCE_SCHEMA, RelevanceCheck
from shared.schemas.agents.search import SEARCH_AGENT_SCHEMA, SearchAgentCompany, SearchAgentOutput
from shared.schemas.agents.search_wip import WIP_SEARCH_SCHEMA, WIPSearchCompany, WIPSearchOutput

__all__ = [
    "AVAILABILITY_SCHEMA",
    "RELEVANCE_SCHEMA",
    "SEARCH_AGENT_SCHEMA",
    "WIP_SEARCH_SCHEMA",
    "AvailabilityCheck",
    "RelevanceCheck",
    "SearchAgentCompany",
    "SearchAgentOutput",
    "WIPSearchCompany",
    "WIPSearchOutput",
]
