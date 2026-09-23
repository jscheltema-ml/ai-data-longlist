"""
Shared Azure OpenAI client.

One client per process, imported by every route module that needs it. Lives here
rather than in api/main.py so a service router can use it without importing the app.
"""

from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from api.config import config

# Base LLM client
llm_client = AsyncAzureOpenAI(
    api_key=config.azure_api_key,
    azure_endpoint=config.azure_endpoint,
    api_version=config.azure_api_version,
)

credential = DefaultAzureCredential()
# Specific Foundry chat client
foundry_client = FoundryChatClient(
    project_endpoint=config.foundry_endpoint,
    model=config.foundry_deployment,
    credential=credential,
)
