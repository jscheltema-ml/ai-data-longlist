from agent_framework import Agent

from clients.llm import foundry_client

# Create web search tool with location context
web_search_tool = foundry_client.get_web_search_tool(
    user_location={"city": "Amsterdam", "country": "NL"},
)

agent = Agent(
    client=foundry_client,
    instructions="You are a helpful assistant that can search the web for current information.",
    tools=[web_search_tool],
)
