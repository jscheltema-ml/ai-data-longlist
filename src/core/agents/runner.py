"""One turn of an agent run, as a single reply or as a stream of updates."""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from agent_framework import Agent, AgentResponseUpdate, AgentSession
from clients.foundry_session import resolve_conversation_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TurnResult:
    text: str
    conversation_id: str | None
    messages: list[Any]


async def _start(agent: Agent, conversation_id: str | None, caller: str | None) -> tuple[AgentSession, str | None]:
    resume_id = await resolve_conversation_id(agent.client, conversation_id, caller)

    logger.info(
        "agent_run_starting",
        extra={"custom_dimensions": {"agent": agent.name, "caller": caller, "conversation_id": resume_id}},
    )

    return AgentSession(service_session_id=resume_id), resume_id


def _finish(
    agent: Agent,
    result: Any,
    session: AgentSession,
    resume_id: str | None,
    conversation_id: str | None,
    caller: str | None,
) -> TurnResult:
    # Only valid once the stream is drained: the session carries the id we started with until then.
    resolved_id = getattr(session, "service_session_id", None) or resume_id or conversation_id

    logger.info(
        "agent_run_complete",
        extra={"custom_dimensions": {"agent": agent.name, "caller": caller, "conversation_id": resolved_id}},
    )

    return TurnResult(text=result.text, conversation_id=resolved_id, messages=list(result.messages))


async def run_turn(
    agent: Agent,
    user_text: str,
    conversation_id: str | None = None,
    caller: str | None = None,
) -> TurnResult:
    """Run one turn and wait for the whole reply."""
    session, resume_id = await _start(agent, conversation_id, caller)

    # stream=True returns a ResponseStream, not an awaitable reply.
    stream = agent.run(user_text, stream=True, session=session)
    result = await stream.get_final_response()

    return _finish(agent, result, session, resume_id, conversation_id, caller)


async def stream_turn(
    agent: Agent,
    user_text: str,
    conversation_id: str | None = None,
    caller: str | None = None,
) -> AsyncIterator[AgentResponseUpdate | TurnResult]:
    """Run one turn, yielding updates and then a final TurnResult carrying the conversation id."""
    session, resume_id = await _start(agent, conversation_id, caller)

    stream = agent.run(user_text, stream=True, session=session)
    async for update in stream:
        yield update

    result = await stream.get_final_response()

    yield _finish(agent, result, session, resume_id, conversation_id, caller)
