"""The two payloads the schemas were written from, validated end to end.

These are the spec examples verbatim. If a field is renamed or retyped, one of these fails
before anything downstream does.
"""

import pytest
from pydantic import ValidationError

from shared.schemas import (
    CheckedStatus,
    CompanyItem,
    IdBasis,
    Magnitude,
    SourceEnvelope,
    SourceStatus,
)

ENVELOPE = {
    "run_id": "01JBQ000000000000000000000",
    "source_key": "gain",
    "adapter_version": "1.0",
    "query": {"sector": "industrial automation", "country": "NL"},
    "status": "ok",
    "error": None,
    "record_count": 2,
    "started_at": "2026-09-22T10:15:02Z",
    "finished_at": "2026-09-22T10:15:41Z",
    "records": [{"id": "A-10293"}, {"id": "A-10294"}],
}

ITEM = {
    "item_id": "cmp_8f3a",
    "id_basis": "domain",
    "external_ids": {"gain": "A-10293", "ml_archive": "bv-88214", "kvk": "12345678", "lei": None},
    "found_by": ["gain", "claude_web"],
    "pipeline": {
        "ingested_at": "2026-09-22T10:15:41Z",
        "cleaned_status": "merged",
        "cleaned_at": "2026-09-22T10:17:12Z",
        "cleaned_by": "merge_rules@1.3",
        "checked_status": "passed",
        "checked_at": "2026-09-22T10:18:02Z",
        "checked_by": "verify_agent@2.1",
        "exclusion_reason": None,
        "flag_reason": None,
        "scored_status": "scored",
        "scored_at": "2026-09-22T10:19:47Z",
        "scored_by": "ranking_config@0.4",
    },
    "identity": {
        "name": "Voorbeeld Industrials B.V.",
        "country": "NL",
        "domain": "voorbeeld-industrials.nl",
        "website": "https://voorbeeld-industrials.nl",
        "hq_city": "Eindhoven",
    },
    "classification": {
        "buyer_type": "pe",
        "sector_text": "industrial automation",
        "description": "...",
    },
    "financials": {
        "revenue": {"value": 82.0, "currency": "EUR", "unit": "M", "as_of": "2024-12-31"},
        "ebitda": None,
        "ebit": None,
        "enterprise_value": None,
        "equity": None,
        "employees": {"value": 340, "as_of": "2025-06-30"},
    },
    "buyer_profile": {
        "countries_active": ["NL", "BE"],
        "strategy": ["buy_and_build"],
        "holding_period": None,
        "customer_type": ["b2b"],
        "stake_preference": ["majority"],
        "fund_type": "pe",
        "aum": {"value": 450, "currency": "EUR", "unit": "M"},
        "dry_powder": None,
    },
    "evidence": [
        {
            "claim": "buyer_profile.aum",
            "text": "...",
            "url": "https://example.invalid/fund",
            "source_key": "claude_web",
            "retrieved_at": "2026-09-22T10:17:02Z",
        }
    ],
    "check_evidence": [
        {
            "reason": "in_active_process",
            "text": "...",
            "url": "https://example.invalid/news",
            "retrieved_at": "2026-09-22T10:18:01Z",
        }
    ],
    "provenance": {
        "identity.name": "gain",
        "financials.revenue": "gain",
        "buyer_profile.aum": "claude_web",
    },
    "quality": {
        "completeness": 0.72,
        "conflicts": [
            {
                "field": "financials.revenue",
                "values": [
                    {"source": "gain", "value": 82.0},
                    {"source": "ml_archive", "value": 79.5},
                ],
                "resolved_to": "gain",
            }
        ],
    },
    "scoring": {
        "total": 0.78,
        "tier": 1,
        "components": {
            "sector_fit": {"raw": 0.9, "weight": 0.3, "contribution": 0.27},
            "size_fit": {"raw": 0.6, "weight": 0.2, "contribution": 0.12},
        },
        "rationale": "...",
    },
}


# ── SourceEnvelope ───────────────────────────────────────────


def test_envelope_example_validates():
    envelope = SourceEnvelope.model_validate(ENVELOPE)

    assert envelope.status is SourceStatus.OK
    assert envelope.record_count == len(envelope.records)
    # Records stay source-shaped rather than being coerced into anything.
    assert envelope.records[0] == {"id": "A-10293"}


def test_envelope_rejects_an_ok_run_that_also_reports_an_error():
    with pytest.raises(ValidationError, match="error must be set"):
        SourceEnvelope.model_validate(ENVELOPE | {"error": "rate limited"})


def test_envelope_rejects_a_failed_run_with_no_error():
    with pytest.raises(ValidationError, match="error must be set"):
        SourceEnvelope.model_validate(ENVELOPE | {"status": "failed"})


def test_envelope_rejects_a_record_count_that_does_not_match_the_records():
    with pytest.raises(ValidationError, match="record_count is 99"):
        SourceEnvelope.model_validate(ENVELOPE | {"record_count": 99})


def test_envelope_rejects_finishing_before_it_started():
    with pytest.raises(ValidationError, match="finished_at is before started_at"):
        SourceEnvelope.model_validate(ENVELOPE | {"finished_at": "2026-09-22T10:00:00Z"})


# ── CompanyItem ──────────────────────────────────────────────


def test_item_example_validates():
    item = CompanyItem.model_validate(ITEM)

    assert item.id_basis is IdBasis.DOMAIN
    assert item.pipeline.checked_status is CheckedStatus.PASSED
    assert item.identity.country == "NL"
    assert item.financials.revenue.unit is Magnitude.MILLIONS
    assert item.financials.employees.value == 340
    assert item.quality.conflicts[0].resolved_to == "gain"
    assert item.scoring.components["sector_fit"].contribution == 0.27
    # external_ids keeps the key it has no value for.
    assert item.external_ids["lei"] is None


def test_item_round_trips_through_json():
    item = CompanyItem.model_validate(ITEM)

    assert CompanyItem.model_validate(item.model_dump(mode="json")) == item


def test_item_defaults_the_blocks_later_stages_fill():
    """Ingestion writes an item before cleaning, check or scoring have run."""
    bare = CompanyItem.model_validate(
        {
            "item_id": "cmp_new",
            "id_basis": "name_country",
            "identity": {"name": "Nog Onbekend B.V."},
            "pipeline": {"ingested_at": "2026-09-22T10:15:41Z"},
        }
    )

    assert bare.pipeline.checked_status is CheckedStatus.PENDING
    assert bare.quality is None and bare.scoring is None
    assert bare.buyer_profile.countries_active == []


def test_item_rejects_an_unknown_field():
    """extra="forbid": a stray key is a bug in the producer, not data to carry along."""
    with pytest.raises(ValidationError, match="revenu"):
        CompanyItem.model_validate(
            {**ITEM, "financials": {**ITEM["financials"], "revenu": None}},
        )


def test_item_rejects_a_country_that_is_not_alpha_2():
    with pytest.raises(ValidationError):
        CompanyItem.model_validate({**ITEM, "identity": {**ITEM["identity"], "country": "Netherlands"}})


# ── Pipeline reason codes ────────────────────────────────────


def test_excluded_without_a_reason_is_rejected():
    with pytest.raises(ValidationError, match="exclusion_reason must be set"):
        CompanyItem.model_validate({**ITEM, "pipeline": {**ITEM["pipeline"], "checked_status": "excluded"}})


def test_a_reason_left_behind_by_an_earlier_verdict_is_rejected():
    """The item passed this time, so last run's exclusion reason must not still be there."""
    with pytest.raises(ValidationError, match="exclusion_reason must be set"):
        CompanyItem.model_validate(
            {**ITEM, "pipeline": {**ITEM["pipeline"], "exclusion_reason": "in_active_process"}},
        )


def test_flagged_with_a_reason_is_accepted():
    item = CompanyItem.model_validate(
        {
            **ITEM,
            "pipeline": {**ITEM["pipeline"], "checked_status": "flagged", "flag_reason": "stale_financials"},
        }
    )

    assert item.pipeline.flag_reason == "stale_financials"


# ── Conflicts ────────────────────────────────────────────────


def test_conflict_resolved_to_a_source_that_did_not_take_part_is_rejected():
    conflict = {
        "field": "financials.revenue",
        "values": [{"source": "gain", "value": 82.0}, {"source": "ml_archive", "value": 79.5}],
        "resolved_to": "claude_web",
    }
    with pytest.raises(ValidationError, match="not among the conflicting sources"):
        CompanyItem.model_validate({**ITEM, "quality": {"completeness": 0.72, "conflicts": [conflict]}})
