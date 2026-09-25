from agent_framework import Agent

from clients.llm import foundry_client
from shared.schemas.agents.relevant import RELEVANCE_SCHEMA

# Create web search tool with location context
web_search_tool = foundry_client.get_web_search_tool(
    user_location={"city": "Amsterdam", "country": "NL"},
)

relevance_agent = Agent(
    client=foundry_client,
    instructions=(
        "You are a critical M&A long-list verification agent that searches the web to verify if a "
        "potential buyer is relevant on the following dimensions: sector/activity fits investment "
        "thesis, size fits targeted deal size, geography fits mandate."
    ),
    tools=[web_search_tool],
    default_options={
        "include": ["web_search_call.action.sources"],
        "response_format": RELEVANCE_SCHEMA,
    },
)
