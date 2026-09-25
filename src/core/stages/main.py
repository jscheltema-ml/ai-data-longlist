"""
Definition of the overall flow and the entry point for the background worker.
"""

from shared.schemas.brief import Brief
from shared.schemas.buyer import Buyer
from shared.schemas.common.enums import CheckStatus
from stages.clean.clean_data import clean_data
from stages.ingest.ingest_data import SourceKey, ingest_data
from stages.verify.verify_availability import verify_availability
from stages.verify.verify_relevance import verify_relevance


async def main(brief: Brief, selected_sources: list[SourceKey]) -> list[Buyer]:

    print(f"[main] brief {brief.brief_id}: {brief.target.identity.name}", flush=True)

    raw_batches = await ingest_data(selected_sources, brief)
    buyers, failed = clean_data(raw_batches)

    buyers = await verify_relevance(buyers, brief)
    relevant = [b for b in buyers if b.pipeline.relevant_status is CheckStatus.VERIFIED]
    rest = [b for b in buyers if b.pipeline.relevant_status is not CheckStatus.VERIFIED]

    print(f"[main] {len(relevant)} relevant of {len(buyers)}; skipping availability for {len(rest)}", flush=True)
    checked = await verify_availability(relevant)

    out = checked + rest + failed
    print(f"[main] done: {len(out)} buyers ({len(failed)} never converted)", flush=True)
    return out
