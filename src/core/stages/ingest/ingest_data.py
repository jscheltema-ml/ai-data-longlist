from stages.ingest.sources.web_search import web_search
from stages.ingest.sources.gain import gain_search

from shared.schemas.brief import Brief
from shared.schemas.source_batch import SourceBatch

from typing import Literal
import asyncio
from enum import StrEnum

class SourceKey(StrEnum):
    WEB_SEARCH = "web_search"
    GAIN = "gain"

SOURCES = {
    SourceKey.WEB_SEARCH: {
        'function': web_search,
        'default_search_volume': 5},
    SourceKey.GAIN: {
        'function': gain_search,
        'default_search_volume': 5},
}

async def ingest_data(selected_sources: list[SourceKey], brief: Brief) -> dict[str, SourceBatch]:

    chosen = {k: SOURCES[k] for k in selected_sources}
    print(f"[ingest] asking {len(chosen)} source(s): {[k.value for k in chosen]}", flush=True)

    batches = await asyncio.gather(
        *(source["function"](brief, source["default_search_volume"]) for source in chosen.values()), # Manually add run_id?
        return_exceptions=True,
    )

    for key, batch in zip(chosen, batches):
        if isinstance(batch, Exception):
            print(f"[ingest]   {key.value}: FAILED {type(batch).__name__}: {batch}", flush=True)
        else:
            print(f"[ingest]   {key.value}: {batch.status.value}, {batch.record_count} records", flush=True)

    return dict(zip(chosen, batches))

    



