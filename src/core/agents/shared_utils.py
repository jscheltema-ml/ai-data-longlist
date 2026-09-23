from pathlib import Path
from typing import Any


def read_prompt(path: str | Path) -> str:
    with open(path, encoding="utf-8") as prompt:
        return prompt.read()


def serialize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    """Render the framework's messages for the wire, in order.

    Everything the run produced, not a projection of it: assistant text, reasoning items,
    tool calls and their results, each keyed by `type` under `contents`. A caller that only
    wants tool calls filters on that, and one that wants to replay the whole run can.

    `to_dict()` already drops `raw_representation`, so the SDK objects underneath never
    reach the wire and the result is plain JSON.
    """
    return [msg.to_dict() for msg in messages]
