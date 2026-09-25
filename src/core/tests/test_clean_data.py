"""Cleaning: standardise each batch, then reconcile buyers that are the same company."""

from shared.schemas import Buyer, CleanedStatus, SourceBatch
from stages.clean.clean_data import clean_data
from stages.ingest.ingest_data import SourceKey

WEB = [
    {
        "identity": {"name": "Kroket Capital", "website": "kroketcapital.nl", "country": "NL"},
        "classification": {"buyer_type": "financial", "sector_text": "food service"},
        "capacity": {"ticket_size": {"min": 2, "max": 10, "currency": "EUR", "unit": "M"}},
    },
    {"identity": {"name": "Web Only B.V.", "website": "webonly.nl"}},
]

GAIN = [
    {
        # the same company: different spelling, a www, and one extra fact
        "identity": {
            "name": "Kroket Capital B.V.",
            "website": "www.kroketcapital.nl",
            "country": "NL",
            "hq_city": "Amsterdam",
        },
        "classification": {"buyer_type": "financial", "sector_text": "quick service restaurants"},
        "capacity": {"ticket_size": {"min": 3, "max": 10, "currency": "EUR", "unit": "M"}},
        "financial_buyer": {"fund_type": "pe", "portfolio_count": 11},
    },
]


def _batch(source_key: str, records: list[dict]) -> SourceBatch:
    return SourceBatch(
        run_id="r",
        source_key=source_key,
        adapter_version="0.2",
        status="ok",
        record_count=len(records),
        started_at="2026-09-25T10:00:00Z",
        finished_at="2026-09-25T10:02:00Z",
        records=records,
    )


def _both() -> dict:
    return {SourceKey.WEB_SEARCH: _batch("web_search", WEB), SourceKey.GAIN: _batch("gain_mcp", GAIN)}


def _by_name(buyers: list[Buyer], fragment: str) -> Buyer:
    return next(b for b in buyers if fragment in b.identity.name)


def test_the_same_company_from_two_sources_becomes_one_buyer():
    """Three records in, two buyers out: the dedupe matched on domain despite the name being
    spelled differently and one side carrying a www."""
    merged, _ = clean_data(_both())

    assert len(merged) == 2
    assert _by_name(merged, "Kroket").found_by == ["web_search", "gain_mcp"]


def test_a_gap_in_one_source_is_filled_from_the_other():
    merged, _ = clean_data(_both())
    kroket = _by_name(merged, "Kroket")

    assert kroket.identity.hq_city == "Amsterdam"  # only gain had it
    assert kroket.financial_buyer.fund_type == "pe"  # a whole block only one side had


def test_disagreements_are_kept_rather_than_quietly_resolved():
    """A number two sources argue about is worth less than one they agree on, and only this
    record says which is which."""
    merged, _ = clean_data(_both())
    conflicts = {c.field: c for c in _by_name(merged, "Kroket").quality.conflicts}

    assert "classification.sector_text" in conflicts
    assert "capacity.ticket_size" in conflicts
    sector = conflicts["classification.sector_text"]
    assert {v.source for v in sector.values} == {"web_search", "gain_mcp"}
    assert sector.resolved_to == "web_search"
    # and the winner is what the merged record actually carries
    assert _by_name(merged, "Kroket").classification.sector_text == "food service"


def test_agreement_is_not_a_conflict():
    """Both sources said NL and both said buyer_type financial."""
    merged, _ = clean_data(_both())
    fields = {c.field for c in _by_name(merged, "Kroket").quality.conflicts}

    assert "identity.country" not in fields
    assert "classification.buyer_type" not in fields


def test_provenance_names_the_source_each_surviving_value_came_from():
    merged, _ = clean_data(_both())
    kroket = _by_name(merged, "Kroket")

    assert kroket.provenance["classification.sector_text"] == "web_search"
    assert kroket.provenance["identity.hq_city"] == "gain_mcp"
    assert kroket.provenance["financial_buyer.fund_type"] == "gain_mcp"


def test_a_merged_buyer_says_so():
    merged, _ = clean_data(_both())

    for buyer in merged:
        assert buyer.pipeline.cleaned_status is CleanedStatus.MERGED
        assert buyer.pipeline.cleaned_by == "merge_rules@0.1"
        assert buyer.pipeline.cleaned_reason is None


def test_evidence_from_every_source_is_kept():
    def quote(text: str, source: str) -> dict:
        return {"claim": "identity.name", "text": text, "source_key": source, "retrieved_at": "2026-09-25T10:01:00Z"}

    web = [{**WEB[0], "evidence": [quote("a", "web_search")]}]
    gain = [{**GAIN[0], "evidence": [quote("b", "gain_mcp")]}]

    merged, _ = clean_data({SourceKey.WEB_SEARCH: _batch("web_search", web), SourceKey.GAIN: _batch("gain_mcp", gain)})

    assert len(merged[0].evidence) == 2


def test_records_that_would_not_convert_come_back_separately():
    bad = [
        {
            "identity": {"name": "Broken NV"},
            "classification": {"buyer_type": "financial"},
            "strategic_buyer": {"listed": True},
        }
    ]

    merged, failed = clean_data({SourceKey.GAIN: _batch("gain_mcp", bad)})

    assert merged == []
    assert len(failed) == 1
    assert failed[0].pipeline.cleaned_status is CleanedStatus.FAILED
    assert "strategic_buyer" in failed[0].pipeline.cleaned_reason


def test_a_source_that_failed_during_ingest_is_skipped():
    """asyncio.gather(return_exceptions=True) puts an exception where a batch would be. It is
    already recorded on the run, and nothing here can improve on it."""
    merged, failed = clean_data(
        {SourceKey.WEB_SEARCH: _batch("web_search", WEB), SourceKey.GAIN: RuntimeError("auth expired")}
    )

    assert len(merged) == 2
    assert failed == []


def test_completeness_reflects_how_much_was_actually_found():
    merged, _ = clean_data(_both())

    kroket = _by_name(merged, "Kroket")
    sparse = _by_name(merged, "Web Only")
    assert 0.0 < sparse.quality.completeness < kroket.quality.completeness <= 1.0
