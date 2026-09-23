"""Shape a streaming agent turn into Server-Sent Events."""

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from agents.runner import TurnResult, stream_turn

logger = logging.getLogger(__name__)

# A tool call can hold the model silent for minutes, which an idle proxy may read as a dead
# connection. Anything quieter than this gets a comment frame to keep the socket warm.
_HEARTBEAT_SECONDS = 15.0


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"


def _tool_call(call_id: str, buffered: dict[str, Any]) -> str:
    return _sse("tool_call", {"callId": call_id, "name": buffered["name"], "arguments": buffered["args"]})


async def _with_heartbeat(items: AsyncIterator[Any]) -> AsyncIterator[Any]:
    """Yield from `items`, standing in None when it goes quiet and the exception if it fails.

    A background task does the pulling so the timeout lands on `queue.get()`. Timing out the
    iterator directly would cancel it mid-suspension and lose the run.
    """
    queue: asyncio.Queue[Any] = asyncio.Queue()
    finished = object()

    async def pump() -> None:
        try:
            async for item in items:
                await queue.put(item)
        except Exception as e:  # noqa: BLE001 - handed to the consumer, which reports it in-band
            await queue.put(e)
        finally:
            await queue.put(finished)

    task = asyncio.create_task(pump())
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), _HEARTBEAT_SECONDS)
            except TimeoutError:
                yield None
                continue

            if item is finished:
                return
            yield item
    finally:
        # The caller may have hung up; stop the run rather than leaving it pumping.
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def sse_events(agent: Any, user_text: str, context_id: str | None, caller: str | None) -> AsyncIterator[str]:
    """One turn as SSE frames: `update`, `tool_call`, then either `done` or `error`."""
    # A tool call arrives as argument fragments, so hold each one by call_id and emit it only
    # once the arguments parse. Text is passed straight through, chunk by chunk.
    pending: dict[str, dict[str, Any]] = {}

    async for item in _with_heartbeat(stream_turn(agent, user_text, context_id, caller)):
        if item is None:
            yield ": keep-alive\n\n"
            continue

        if isinstance(item, Exception):
            # The 200 went out with the first frame, so a failure can only be reported in-band.
            logger.error("agent_stream_failed", exc_info=item)
            yield _sse("error", {"message": f"{type(item).__name__}: {item}"})
            return

        if isinstance(item, TurnResult):
            for call_id, buffered in pending.items():
                yield _tool_call(call_id, buffered)
            yield _sse("done", {"result": item.text, "contextId": item.conversation_id})
            return

        update = item.to_dict()
        passthrough = []

        for content in update.get("contents", []):
            if content.get("type") != "function_call":
                passthrough.append(content)
                continue

            call_id = str(content.get("call_id") or "")
            fragment = content.get("arguments")
            buffered = pending.setdefault(call_id, {"name": "", "args": ""})
            buffered["name"] = content.get("name")

            # Already whole when the model emitted it in one piece.
            if isinstance(fragment, dict):
                buffered["args"] = fragment
                yield _tool_call(call_id, pending.pop(call_id))
                continue

            buffered["args"] += str(fragment or "")
            try:
                buffered["args"] = json.loads(buffered["args"])
            except ValueError:
                continue
            yield _tool_call(call_id, pending.pop(call_id))

        if passthrough:
            yield _sse("update", {**update, "contents": passthrough})
