from agent_framework import Agent

from clients.llm import foundry_client
from shared.schemas.agents.available import AVAILABILITY_SCHEMA

# Create web search tool with location context
web_search_tool = foundry_client.get_web_search_tool(
    user_location={"city": "Amsterdam", "country": "NL"},
)

availability_agent = Agent(
    client=foundry_client,
    instructions=(
        "You are a critical M&A long-list verification agent that searches the web to verify if a "
        "potential buyer is currently not involved in an M&A process as target."
    ),
    tools=[web_search_tool],
    default_options={
        "include": ["web_search_call.action.sources"],
        "response_format": AVAILABILITY_SCHEMA,
    },
)
