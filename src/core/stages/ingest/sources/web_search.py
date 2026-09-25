"""Web search as a data source."""

import uuid
from datetime import UTC, datetime

from agents.agents.web_search_agent import web_search_agent
from shared.schemas.brief import Brief
from shared.schemas.source_batch import SourceBatch

SOURCE_KEY = "web_search"
ADAPTER_VERSION = "0.1"


async def web_search(brief: Brief, search_volume: int, run_id: str | None = None) -> SourceBatch:
    """Ask the search agent for buyers matching `brief`, as one batch.

    Returns a batch either way: a run that comes back with nothing is a `failed` record
    of an attempt, not an exception, because the point of the batch is that a bad parse
    cannot lose the fact that the fetch happened.
    """
    run_id = run_id or uuid.uuid4().hex
    prompt = (
        f"Find at least {search_volume} potential buyers for the company described by this "
        f"brief. Return only buyers that plausibly fit it.\n\n{brief.model_dump_json(indent=2)}"
    )

    started_at = datetime.now(UTC)
    response = await web_search_agent.run(prompt)
    finished_at = datetime.now(UTC)
    records = (response.value or {}).get("companies") or []
    failed = not records

    return SourceBatch(
        run_id=run_id,
        source_key=SOURCE_KEY,
        adapter_version=ADAPTER_VERSION,
        query={"brief_id": brief.brief_id, "search_volume": search_volume, "prompt": prompt},
        status="failed" if failed else "ok",
        error="the agent returned no companies" if failed else None,
        record_count=len(records),
        started_at=started_at,
        finished_at=finished_at,
        records=records,
    )

# Needs turn and cost capping.
