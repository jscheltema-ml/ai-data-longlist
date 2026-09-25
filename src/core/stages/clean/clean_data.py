"""The data cleaning step, where we define the normalisation, deduplication and merging mechanisms.
"""

import json
from collections import defaultdict
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from shared.schemas.blocks.quality import ConflictingValue, ConflictRecord, Quality
from shared.schemas.buyer import Buyer
from shared.schemas.common.enums import CleanedStatus
from shared.schemas.source_batch import SourceBatch
from stages.clean.connectors.gain_connector import standardize as gain_standardize
from stages.clean.connectors.web_search_connector import standardize as web_search_standardize
from stages.ingest.ingest_data import SourceKey

MERGER = "merge_rules@0.1"

CONNECTORS = {
    SourceKey.WEB_SEARCH: web_search_standardize,
    SourceKey.GAIN: gain_standardize,
}

BLOCKS = ("identity", "classification", "mandate", "capacity", "financial_buyer", "strategic_buyer", "track_record")


def clean_data(batches: dict[SourceKey, SourceBatch]) -> tuple[list[Buyer], list[Buyer]]:
    """Standardise every batch, then merge the buyers that turn out to be the same company.

    Returns the merged buyers and, separately, the records that would not convert. A source
    that failed during ingest arrives here as an exception rather than a batch and is skipped:
    it is already on the record in the run, and nothing here can improve on that.
    """
    print(f"[clean] standardising {len(batches)} batch(es)", flush=True)
    cleaned: list[Buyer] = []
    failed: list[Buyer] = []

    for source, batch in batches.items():
        if not isinstance(batch, SourceBatch) or not batch.records:
            continue
        converted, unconvertible = CONNECTORS[source](batch)
        print(f"[clean]   {source.value}: {len(converted)} converted, {len(unconvertible)} failed", flush=True)
        cleaned.extend(converted)
        failed.extend(unconvertible)

    merged = _merge(cleaned)
    print(f"[clean] {len(cleaned)} buyers -> {len(merged)} after dedupe", flush=True)
    return merged, failed


def _merge(buyers: list[Buyer]) -> list[Buyer]:
    """Group by `item_id` and reconcile each group into one buyer."""
    groups: dict[str, list[Buyer]] = defaultdict(list)
    for buyer in buyers:
        groups[buyer.item_id].append(buyer)

    return [_merge_group(group) for group in groups.values()]



# NEED TO CHECK IF I AGREE WITH THIS APPROACH
def _merge_group(group: list[Buyer]) -> Buyer:
    """Reconcile buyers that share an id into one.

    Works on dumps rather than models so that a conflict can hold whatever the field was,
    whether a string or a nested amount, and the result is validated back into a `Buyer` at
    the end rather than assembled field by field.

    First-in wins, which makes source order the tie-break. That is a placeholder for a real
    rule, and the honest version of it is that every loss is recorded: `quality.conflicts`
    holds what the other sources said, so a better rule can be applied later without going
    back to the batches.
    """
    dumps = [buyer.model_dump(mode="json") for buyer in group]
    merged = deepcopy(dumps[0])

    provenance: dict[str, str] = {}
    conflicts: list[ConflictRecord] = []
    filled = total = 0

    for block in BLOCKS:
        present = [(dump, dump[block]) for dump in dumps if isinstance(dump.get(block), dict)]
        if not present:
            continue
        if not isinstance(merged.get(block), dict):
            merged[block] = deepcopy(present[0][1])

        for field in present[0][1]:
            total += 1
            stated = [(dump["found_by"][0], values[field]) for dump, values in present if _is_filled(values.get(field))]
            if not stated:
                continue

            filled += 1
            winner, value = stated[0]
            merged[block][field] = value
            provenance[f"{block}.{field}"] = winner

            if conflict := _conflict(f"{block}.{field}", stated, winner):
                conflicts.append(conflict)

    merged["found_by"] = list(dict.fromkeys(source for dump in dumps for source in dump["found_by"]))
    merged["external_ids"] = {k: v for dump in dumps for k, v in dump["external_ids"].items()}
    merged["evidence"] = [item for dump in dumps for item in dump["evidence"]]
    merged["provenance"] = provenance
    merged["quality"] = Quality(
        completeness=round(filled / total, 4) if total else 0.0,
        conflicts=conflicts,
    ).model_dump(mode="json")
    merged["pipeline"] |= {
        "cleaned_status": CleanedStatus.MERGED.value,
        "cleaned_at": datetime.now(UTC).isoformat(),
        "cleaned_by": MERGER,
    }

    return Buyer.model_validate(merged)


def _conflict(field: str, stated: list[tuple[str, Any]], winner: str) -> ConflictRecord | None:
    """A record of the disagreement, or nothing if the sources agreed.

    Compared as JSON so that two equal nested amounts count as agreement rather than as two
    different objects.
    """
    if len({json.dumps(value, sort_keys=True) for _, value in stated}) < 2:
        return None
    return ConflictRecord(
        field=field,
        values=[ConflictingValue(source=source, value=value) for source, value in stated],
        resolved_to=winner,
    )


def _is_filled(value: Any) -> bool:
    """`False` and `0` are answers; None and emptiness are not."""
    return value is not None and value != [] and value != {}
