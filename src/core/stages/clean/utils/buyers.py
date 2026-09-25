"""Turning agent-shaped records into buyers.

Every source whose agent is given `SEARCH_AGENT_SCHEMA` hands back the same blocks a `Buyer`
is made of, so the conversion is the same whoever fetched it and lives here. What a
connector supplies is its own name, for the record of what did the converting.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ValidationError

from shared.schemas.agents.search import SearchAgentCompany
from shared.schemas.blocks.identity import Identity
from shared.schemas.blocks.pipeline import Pipeline
from shared.schemas.buyer import Buyer
from shared.schemas.common.enums import CleanedStatus, IdBasis
from shared.schemas.source_batch import SourceBatch
from stages.clean.utils.normalise import normalise

# The blocks a found company hands over untouched, in the order they read on a Buyer.
CARRIED = ("identity", "classification", "mandate", "capacity", "financial_buyer", "strategic_buyer", "track_record")


def to_buyers(batch: SourceBatch, connector: str) -> tuple[list[Buyer], list[Buyer]]:
    """Convert one batch into buyers: the ones that converted, and the ones that did not.

    A record that will not validate is not dropped and does not take the batch down with it.
    It comes back as a buyer carrying `cleaned_status: failed` and the reason, so a bad record
    is something you can count, review and re-run rather than something that vanished. The raw
    record is still in the batch, which is where to look once the reason names the field.
    """
    if not batch.records:
        raise ValueError("No records included in source batch")

    cleaned: list[Buyer] = []
    failed: list[Buyer] = []
    for index, record in enumerate(batch.records):
        try:
            cleaned.append(_to_buyer(record, batch))
        except ValidationError as error:
            failed.append(_to_failed(record, batch, index, error, connector))
    return cleaned, failed


def _to_buyer(record: dict[str, Any], batch: SourceBatch) -> Buyer:
    """The near-identity mapping the agent's output format was chosen to allow.

    The blocks move across untouched; only what the agent cannot know is added here.
    """
    found = SearchAgentCompany.model_validate(normalise(record))
    carried = {name: getattr(found, name) for name in CARRIED}

    return Buyer(
        item_id=_item_id(found),
        id_basis=IdBasis.DOMAIN if found.identity.domain else IdBasis.NAME_COUNTRY,
        found_by=[batch.source_key],
        pipeline=Pipeline(ingested_at=batch.finished_at),
        evidence=found.evidence,
        provenance=_provenance(carried, batch.source_key),
        **carried,
    )


def _item_id(found: SearchAgentCompany) -> str:
    """The dedupe key, derived rather than generated.

    The same buyer found by two sources has to land on the same id, or the merge has nothing
    to merge on. A domain identifies a company well enough in practice; without one, name and
    country is the guess `IdBasis.NAME_COUNTRY` admits to being.
    """
    identity = found.identity
    seed = identity.domain or f"{identity.name.strip().casefold()}|{identity.country or ''}"
    return f"cmp_{hashlib.sha1(seed.encode()).hexdigest()[:12]}"


def _provenance(carried: dict[str, BaseModel | None], source_key: str) -> dict[str, str]:
    """Which source each value came from, one entry per filled field.

    Two levels deep ("capacity.ticket_size", not "capacity.ticket_size.min") because that is
    the grain the merge resolves conflicts at. Only filled fields appear: an empty entry would
    claim this source said something about a field it never mentioned.
    """
    provenance = {}
    for block_name, block in carried.items():
        if block is None:
            continue
        for field, value in block:
            if value is None or value == [] or value == {}:
                continue
            provenance[f"{block_name}.{field}"] = source_key
    return provenance


def _to_failed(
    record: dict[str, Any],
    batch: SourceBatch,
    index: int,
    error: ValidationError,
    connector: str,
) -> Buyer:
    """The least a buyer can be and still be on the record.

    Only the name survives, and only if it was usable; everything else failed to parse and is
    deliberately not guessed at. The id is a hash of the raw record, so re-running the stage on
    the same batch produces the same buyer rather than a second one.
    """
    identity = record.get("identity")
    name = identity.get("name") if isinstance(identity, dict) else None
    seed = json.dumps(record, sort_keys=True, default=str)

    return Buyer(
        item_id=f"cmp_{hashlib.sha1(seed.encode()).hexdigest()[:12]}",
        id_basis=IdBasis.NAME_COUNTRY,
        found_by=[batch.source_key],
        pipeline=Pipeline(
            ingested_at=batch.finished_at,
            cleaned_status=CleanedStatus.FAILED,
            cleaned_at=datetime.now(UTC),
            cleaned_by=connector,
            cleaned_reason=_reason(error),
        ),
        identity=Identity(name=name if isinstance(name, str) and name.strip() else f"(unparsed record {index})"),
    )


def _reason(error: ValidationError) -> str:
    """The first failure, as a field path and a message.

    One line rather than pydantic's full report: this is read in a list of failures, and the
    batch still holds the record for anyone who needs the rest.
    """
    first = error.errors()[0]
    location = ".".join(str(part) for part in first["loc"]) or "(root)"
    return f"{location}: {first['msg']}"
