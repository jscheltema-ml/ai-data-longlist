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
        'default_search_volume': 10},
    SourceKey.GAIN: {
        'function': gain_search,
        'default_search_volume': 10},
}

async def ingest_data(selected_sources: list[SourceKey], brief: Brief) -> dict[str, SourceBatch]:

    chosen = {k: SOURCES[k] for k in selected_sources}

    batches = await asyncio.gather(
        *(source["function"](brief, source["default_search_volume"]) for source in chosen.values()), # Manually add run_id?
        return_exceptions=True,
    )

    return dict(zip(chosen, batches))

    



