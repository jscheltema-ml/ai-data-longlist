"""
Agent endpoint.

This module owns the wire format and nothing else: it turns an A2A `message/send` request
into a plain string, hands that to the runner, and wraps the reply back up. The agents are
built at startup and read off `app.state`.

One route serves every agent, addressed by the `slug` from its spec, so adding an agent to
the registry gives it an endpoint with no change here.
"""

import base64
import binascii
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from services.agents.documents import UnsupportedDocument, render
from services.agents.runner import run_turn
from services.agents.shared_utils import serialize_messages
from services.agents.streaming import sse_events

from api.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Matches the prompt playground, so a prompt tested there sees the same framing here.
_DATA_HEADER = "## Widget data"

# Bodies are parsed into memory before the handler runs, so this only bounds the conversion,
# not the upload. A real ceiling belongs at ingress.
_MAX_FILE_BYTES = 10 * 1024 * 1024


class A2ARequestError(ValueError):
    """The payload is not a request this endpoint can serve."""


async def _parse_message_send(payload: dict[str, Any]) -> tuple[Any, str, str | None]:
    """Pull the request id, user text and conversation id out of an A2A `message/send`.

    Returns `(request_id, user_text, context_id)`. Raises A2ARequestError if the payload
    does not carry the parts a turn needs.
    """
    params = payload.get("params")
    if not isinstance(params, dict):
        raise A2ARequestError("`params` is missing or not an object.")

    message = params.get("message")
    if not isinstance(message, dict):
        raise A2ARequestError("`params.message` is missing or not an object.")

    # Accept both spellings: the A2A JSON wire format is camelCase, while some clients send
    # snake_case.
    context_id = message.get("contextId") or message.get("context_id")

    user_text = ""
    data: Any = None
    file: dict[str, Any] | None = None
    for part in message.get("parts") or []:
        if not isinstance(part, dict):
            continue
        if not user_text and "text" in part:
            user_text = str(part.get("text", ""))
        elif data is None and "data" in part:
            data = part["data"]
        elif file is None and ("file" in part or part.get("kind") == "file"):
            if not isinstance(part.get("file"), dict):
                raise A2ARequestError("A file part needs `file` as an object with `bytes`.")
            file = part["file"]

    if not user_text:
        raise A2ARequestError("`params.message.parts` carries no text part.")

    blocks = []
    if file is not None:
        blocks.append(await _render_file(file))
    if data is not None:
        blocks.append(f"{_DATA_HEADER}\n{json.dumps(data, ensure_ascii=False, separators=(',', ':'))}")

    return payload.get("id"), "\n\n".join([*blocks, user_text]), context_id


async def _render_file(file: dict[str, Any]) -> str:
    """Decode an A2A file part and render it into prompt text."""
    if "uri" in file and "bytes" not in file:
        raise A2ARequestError("`file.uri` is not supported; send the document as `file.bytes`.")

    try:
        raw = base64.b64decode(str(file.get("bytes", "")), validate=True)
    except (binascii.Error, ValueError) as e:
        raise A2ARequestError(f"`file.bytes` is not valid base64: {e}") from e

    if not raw:
        raise A2ARequestError("`file.bytes` is empty.")
    if len(raw) > _MAX_FILE_BYTES:
        raise A2ARequestError(f"The document is {len(raw)} bytes; the limit is {_MAX_FILE_BYTES}.")

    try:
        return await render(str(file.get("name", "document")), file.get("mimeType"), raw)
    except UnsupportedDocument as e:
        raise A2ARequestError(str(e)) from e


def _error(request_id: Any, code: int, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}},
    )


@router.get("")
def list_agents(request: Request) -> dict[str, list[str]]:
    """The agents this service is serving, by slug.

    Worth keeping because one parameterized route means OpenAPI cannot name them.
    """
    return {"agents": sorted(request.app.state.agents)}


@router.post("/{agent_slug}/interact")
async def handle_message(
    agent_slug: str,
    request: Request,
    payload: dict[str, Any],
    claims: dict[str, Any] = Depends(verify_token),
) -> Any:
    """Run one turn of `agent_slug`. `message/send` returns JSON, `message/stream` returns SSE."""
    agent = request.app.state.agents.get(agent_slug)
    if agent is None:
        known = ", ".join(sorted(request.app.state.agents)) or "none"
        return _error(payload.get("id"), -32601, f"Unknown agent '{agent_slug}'. Known agents: {known}.", 404)

    method = payload.get("method")
    if method not in ("message/send", "message/stream"):
        return _error(payload.get("id"), -32601, "Only 'message/send' and 'message/stream' are supported.", 400)

    try:
        request_id, user_text, context_id = await _parse_message_send(payload)
    except A2ARequestError as e:
        return _error(payload.get("id"), -32602, f"Invalid request: {e}", 400)

    # A user token carries `oid`; a service principal token carries `appid` instead.
    caller = claims.get("oid") or claims.get("appid")

    if method == "message/stream":
        return StreamingResponse(
            sse_events(agent, user_text, context_id, caller),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    result = await run_turn(
        agent,
        user_text,
        conversation_id=context_id,
        caller=caller,
    )

    # contextId must be returned: without it the caller cannot continue the conversation.
    # `messages` is the whole run, for a caller that wants to show more than the final text.
    return JSONResponse(
        {
            "id": request_id,
            "result": result.text,
            "contextId": result.conversation_id,
            "messages": serialize_messages(result.messages),
        }
    )
