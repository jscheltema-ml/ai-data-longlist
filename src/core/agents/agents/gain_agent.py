from agent_framework import Agent

from clients.gain_auth import gain_mcp_tools
from clients.llm import foundry_client
from shared.schemas.agents.search_wip import WIP_SEARCH_SCHEMA

gain_tools = gain_mcp_tools()

gain_mcp_agent = Agent(
    client=foundry_client,
    instructions="You are an M&A long-list generator that searches Gain for potential buyers for a company.",
    tools=gain_tools,
    default_options={"response_format": WIP_SEARCH_SCHEMA},
)
