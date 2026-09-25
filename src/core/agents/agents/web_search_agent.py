from agent_framework import Agent

from clients.llm import foundry_client
from shared.schemas.agents.search_wip import WIP_SEARCH_SCHEMA

# Create web search tool with location context
web_search_tool = foundry_client.get_web_search_tool(
    user_location={"city": "Amsterdam", "country": "NL"},
)

#### IS THIS THE RIGHT WEB SEARCH TOOL??? USES BING FOR EXAMPLE #######

web_search_agent = Agent(
    client=foundry_client,
    instructions="You are an M&A long-list generator that searches the web for potential buyers for a company.",
    tools=[web_search_tool],
    default_options={
        "include": ["web_search_call.action.sources"],
        "response_format": WIP_SEARCH_SCHEMA,
    },
)
