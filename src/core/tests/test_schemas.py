"""The spec payloads, validated end to end, plus the rules the models are there to enforce."""

import pytest
from conftest_payloads import (
    CAPACITY,
    CLASSIFICATION,
    ENVELOPE,
    FINANCIAL_BUYER,
    IDENTITY,
    ITEM,
    STRATEGIC_BUYER,
)
from pydantic import ValidationError

from shared.schemas import (
    BuyerType,
    CapacityBasis,
    CheckStatus,
    CompanyItem,
    IdBasis,
    Magnitude,
    SourceEnvelope,
    SourceStatus,
)

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
    assert item.pipeline.relevant_status is CheckStatus.VERIFIED
    assert item.pipeline.available_status is CheckStatus.VERIFIED
    assert item.identity.country == "NL"
    assert item.classification.buyer_type is BuyerType.FINANCIAL
    assert item.quality.conflicts[0].resolved_to == "gain"
    assert item.scoring.components["track_record_fit"].contribution == 0.140
    # external_ids keeps the key it has no value for.
    assert item.external_ids["lei"] is None


def test_capacity_is_bands_and_keeps_the_three_apart():
    """Ticket size is equity written, EV is deal size: matching a target against the wrong
    one puts the buyer in the wrong tier."""
    item = CompanyItem.model_validate(ITEM)

    assert (item.capacity.ticket_size.min, item.capacity.ticket_size.max) == (10, 60)
    assert (item.capacity.target_ev_range.min, item.capacity.target_ev_range.max) == (20, 150)
    assert item.capacity.target_ebitda_range.unit is Magnitude.MILLIONS
    assert item.capacity.basis is CapacityBasis.STATED


def test_a_band_may_be_open_at_either_end():
    capacity = {**CAPACITY, "ticket_size": {"min": None, "max": 50, "currency": "EUR", "unit": "M"}}
    item = CompanyItem.model_validate({**ITEM, "capacity": capacity})

    assert item.capacity.ticket_size.min is None


def test_a_band_that_runs_backwards_is_rejected():
    capacity = {**CAPACITY, "ticket_size": {"min": 60, "max": 10, "currency": "EUR", "unit": "M"}}
    with pytest.raises(ValidationError, match="min 60.0 is above max 10.0"):
        CompanyItem.model_validate({**ITEM, "capacity": capacity})


def test_the_buyer_itself_is_described_by_the_block_its_type_calls_for():
    item = CompanyItem.model_validate(ITEM)

    assert item.financial_buyer.dry_powder.value == 120
    assert item.financial_buyer.current_fund.vintage == 2023
    assert item.strategic_buyer is None


def test_a_strategic_buyer_carries_its_own_figures_instead():
    item = CompanyItem.model_validate(
        {
            **ITEM,
            "classification": {**CLASSIFICATION, "buyer_type": "strategic"},
            "financial_buyer": None,
            "strategic_buyer": STRATEGIC_BUYER,
        }
    )

    assert item.strategic_buyer.revenue.value == 820
    assert item.strategic_buyer.listed is True
    assert item.financial_buyer is None


def test_item_round_trips_through_json():
    item = CompanyItem.model_validate(ITEM)

    assert CompanyItem.model_validate(item.model_dump(mode="json")) == item


def test_item_defaults_the_blocks_later_stages_fill():
    """Ingestion writes a buyer before cleaning, check or scoring have run."""
    bare = CompanyItem.model_validate(
        {
            "item_id": "cmp_new",
            "id_basis": "name_country",
            "identity": {"name": "Nog Onbekend B.V."},
            "pipeline": {"ingested_at": "2026-09-22T10:15:41Z"},
        }
    )

    assert bare.pipeline.relevant_status is CheckStatus.PENDING
    assert bare.pipeline.available_status is CheckStatus.PENDING
    assert bare.quality is None and bare.scoring is None
    assert bare.mandate.countries_active == []
    assert bare.capacity.ticket_size is None
    assert bare.track_record.recent_deals == []


def test_item_rejects_an_unknown_field():
    """extra="forbid": a stray key is a bug in the producer, not data to carry along."""
    with pytest.raises(ValidationError, match="ticket_sizes"):
        CompanyItem.model_validate({**ITEM, "capacity": {**CAPACITY, "ticket_sizes": None}})


def test_item_rejects_a_country_that_is_not_alpha_2():
    with pytest.raises(ValidationError):
        CompanyItem.model_validate({**ITEM, "identity": {**IDENTITY, "country": "Netherlands"}})


# ── The buyer blocks follow buyer_type ───────────────────────


def test_a_financial_buyer_may_not_carry_strategic_figures():
    with pytest.raises(ValidationError, match="strategic_buyer must be null"):
        CompanyItem.model_validate({**ITEM, "strategic_buyer": STRATEGIC_BUYER})


def test_a_strategic_buyer_may_not_carry_fund_figures():
    with pytest.raises(ValidationError, match="financial_buyer must be null"):
        CompanyItem.model_validate(
            {
                **ITEM,
                "classification": {**CLASSIFICATION, "buyer_type": "strategic"},
                "strategic_buyer": STRATEGIC_BUYER,
            }
        )


def test_an_unclassified_buyer_carries_neither_block():
    """Nothing says which block the figures belong in yet, so they cannot be there."""
    unclassified = {**CLASSIFICATION, "buyer_type": None}
    with pytest.raises(ValidationError, match="buyer_type is not"):
        CompanyItem.model_validate({**ITEM, "classification": unclassified})

    ok = CompanyItem.model_validate({**ITEM, "classification": unclassified, "financial_buyer": None})
    assert ok.classification.buyer_type is None


def test_buyer_type_is_closed_to_the_two_kinds():
    with pytest.raises(ValidationError):
        CompanyItem.model_validate({**ITEM, "classification": {**CLASSIFICATION, "buyer_type": "pe"}})


def test_fund_type_still_subdivides_the_financial_side():
    item = CompanyItem.model_validate(
        {**ITEM, "financial_buyer": {**FINANCIAL_BUYER, "fund_type": "family_office"}}
    )

    assert item.classification.buyer_type is BuyerType.FINANCIAL
    assert item.financial_buyer.fund_type == "family_office"


# ── The two checks are independent ───────────────────────────


def test_relevance_and_availability_are_separate_verdicts():
    """A buyer can fit the brief perfectly and still be unreachable, so one excluded check
    must not drag the other with it."""
    item = CompanyItem.model_validate(
        {
            **ITEM,
            "pipeline": {
                **ITEM["pipeline"],
                "available_status": "excluded",
                "available_reason": "in_active_process",
            },
        }
    )

    assert item.pipeline.relevant_status is CheckStatus.VERIFIED
    assert item.pipeline.available_status is CheckStatus.EXCLUDED
    assert item.pipeline.available_reason == "in_active_process"


@pytest.mark.parametrize("check", ["relevant", "available"])
def test_excluded_without_a_reason_is_rejected(check):
    with pytest.raises(ValidationError, match=f"{check}_reason must be set"):
        CompanyItem.model_validate({**ITEM, "pipeline": {**ITEM["pipeline"], f"{check}_status": "excluded"}})


@pytest.mark.parametrize("check", ["relevant", "available"])
def test_a_reason_left_behind_by_an_earlier_verdict_is_rejected(check):
    """The buyer passed this time, so last run's reason must not still be there."""
    with pytest.raises(ValidationError, match=f"{check}_reason must be set"):
        CompanyItem.model_validate({**ITEM, "pipeline": {**ITEM["pipeline"], f"{check}_reason": "stale"}})


def test_a_check_that_never_ran_is_pending_and_carries_no_reason():
    item = CompanyItem.model_validate(
        {**ITEM, "pipeline": {**ITEM["pipeline"], "available_status": "skipped", "available_at": None}}
    )

    assert item.pipeline.available_status is CheckStatus.SKIPPED
    assert item.pipeline.available_reason is None


# ── Conflicts ────────────────────────────────────────────────


def test_conflict_resolved_to_a_source_that_did_not_take_part_is_rejected():
    conflict = {
        "field": "financial_buyer.aum",
        "values": [{"source": "gain", "value": 450}, {"source": "ml_archive", "value": 420}],
        "resolved_to": "claude_web",
    }
    with pytest.raises(ValidationError, match="not among the conflicting sources"):
        CompanyItem.model_validate({**ITEM, "quality": {"completeness": 0.72, "conflicts": [conflict]}})
