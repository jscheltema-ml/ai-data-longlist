"""What the search agent is instructed to return, and how little is left for the connector."""

import pytest
from conftest_payloads import (
    CAPACITY,
    CLASSIFICATION,
    EVIDENCE,
    FINANCIAL_BUYER,
    IDENTITY,
    ITEM,
    MANDATE,
    STRATEGIC_BUYER,
    TRACK_RECORD,
)
from pydantic import ValidationError

from shared.schemas import (
    SEARCH_AGENT_SCHEMA,
    WIP_SEARCH_SCHEMA,
    BuyerType,
    Capacity,
    Classification,
    CompanyItem,
    Deal,
    Evidence,
    FinancialBuyer,
    Fund,
    Headcount,
    Identity,
    Mandate,
    MonetaryAmount,
    MonetaryRange,
    SearchAgentCompany,
    SearchAgentOutput,
    StrategicBuyer,
    TrackRecord,
    WIPSearchCompany,
    WIPSearchOutput,
)

FOUND = {
    "identity": IDENTITY,
    "classification": CLASSIFICATION,
    "mandate": MANDATE,
    "capacity": CAPACITY,
    "financial_buyer": FINANCIAL_BUYER,
    "strategic_buyer": None,
    "track_record": TRACK_RECORD,
    "evidence": EVIDENCE,
}


def test_the_agent_emits_the_blocks_the_merged_record_uses():
    output = SearchAgentOutput.model_validate({"companies": [FOUND]})

    (found,) = output.companies
    assert found.identity.domain == "voorbeeldcapital.nl"
    assert found.classification.buyer_type is BuyerType.FINANCIAL
    assert found.capacity.ticket_size.max == 60
    assert found.financial_buyer.current_fund.name == "Fund IV"
    assert found.track_record.deal_count_5y == 6


def test_the_blocks_it_emits_are_the_same_objects_the_item_holds():
    """The point of controlling the output format: no reshaping between the two, so the
    connector copies blocks across rather than mapping field by field."""
    found = SearchAgentCompany.model_validate(FOUND)
    item = CompanyItem.model_validate(ITEM)

    assert found.identity == item.identity
    assert found.mandate == item.mandate
    assert found.capacity == item.capacity
    assert found.financial_buyer == item.financial_buyer
    assert found.track_record == item.track_record


def test_a_found_company_becomes_an_item_by_adding_what_only_the_stage_knows():
    """Everything the connector has to supply, in one place: an identity for the buyer and
    a record of where it came from. No block is rebuilt."""
    found = SearchAgentCompany.model_validate(FOUND)

    item = CompanyItem.model_validate(
        {
            **found.model_dump(mode="json"),
            "item_id": "cmp_8f3a",
            "id_basis": "domain",
            "external_ids": {"gain": None},
            "found_by": ["claude_web"],
            "pipeline": {"ingested_at": "2026-09-22T10:15:41Z"},
            "provenance": {"capacity.ticket_size": "claude_web"},
        }
    )

    assert item.capacity == found.capacity
    assert item.evidence == found.evidence


def test_a_bare_hit_is_a_normal_result():
    """A name and a domain is worth keeping; another pass fills the rest in."""
    found = SearchAgentCompany.model_validate({"identity": {"name": "Onbekend Capital"}})

    assert found.classification.buyer_type is None
    assert found.capacity.ticket_size is None
    assert found.evidence == []


def test_an_empty_run_is_not_an_error():
    assert SearchAgentOutput.model_validate({"companies": []}).companies == []


def test_the_agent_output_obeys_the_same_buyer_type_rule_as_the_item():
    """Caught at the agent's output rather than one stage later."""
    with pytest.raises(ValidationError, match="strategic_buyer must be null"):
        SearchAgentCompany.model_validate({**FOUND, "strategic_buyer": STRATEGIC_BUYER})


def test_the_agent_may_not_invent_a_field():
    with pytest.raises(ValidationError, match="confidence"):
        SearchAgentCompany.model_validate({**FOUND, "confidence": 0.8})


# ── The JSON schema handed to the API ────────────────────────

# Every $def and the model whose field names it has to match. The schema is written by hand,
# so this mapping is the only thing standing between a renamed field and a silent mismatch.
SCHEMA_MODELS = {
    "Money": MonetaryAmount,
    "MoneyRange": MonetaryRange,
    "Headcount": Headcount,
    "Identity": Identity,
    "Classification": Classification,
    "Mandate": Mandate,
    "Capacity": Capacity,
    "Fund": Fund,
    "FinancialBuyer": FinancialBuyer,
    "StrategicBuyer": StrategicBuyer,
    "Deal": Deal,
    "TrackRecord": TrackRecord,
    "Evidence": Evidence,
    "Company": SearchAgentCompany,
}


def _walk(node, path="$"):
    """Every (path, schema node) pair, stepping over the name level in $defs and properties
    so that model and field names are not mistaken for keywords."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("$defs", "properties"):
                for name, sub in value.items():
                    yield from _walk(sub, f"{path}.{key}.{name}")
            else:
                yield from _walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


@pytest.mark.parametrize("name", sorted(SCHEMA_MODELS))
def test_each_def_matches_the_model_it_stands_for(name):
    """The drift guard. A field added to a block without being added here fails right here."""
    assert set(SEARCH_AGENT_SCHEMA["$defs"][name]["properties"]) == set(SCHEMA_MODELS[name].model_fields)


def test_every_def_is_accounted_for():
    assert set(SEARCH_AGENT_SCHEMA["$defs"]) == set(SCHEMA_MODELS)


def test_the_schema_holds_nothing_outside_the_strict_dialect():
    supported = {
        "$defs", "$ref", "additionalProperties", "anyOf", "description",
        "enum", "items", "properties", "required", "title", "type",
    }
    used = {key for _, node in _walk(SEARCH_AGENT_SCHEMA) if isinstance(node, dict) for key in node}

    assert used <= supported


def test_every_object_requires_all_its_properties_and_is_closed():
    seen = 0
    for path, node in _walk(SEARCH_AGENT_SCHEMA):
        if isinstance(node, dict) and "properties" in node:
            assert node["properties"], path
            assert set(node["required"]) == set(node["properties"]), path
            assert node["additionalProperties"] is False, path
            seen += 1
    assert seen == len(SCHEMA_MODELS) + 1  # the defs, plus the root


def test_every_ref_resolves_and_every_def_is_reached():
    refs = {node["$ref"] for _, node in _walk(SEARCH_AGENT_SCHEMA) if isinstance(node, dict) and "$ref" in node}
    defs = {f"#/$defs/{name}" for name in SEARCH_AGENT_SCHEMA["$defs"]}

    assert refs <= defs, "a $ref points at a def that does not exist"
    assert defs <= refs, "a def is never referenced"


def test_a_reply_full_of_nulls_parses_to_the_defaults_it_meant():
    """What a model actually returns under strict output: every key present, most of them
    null. A null for `evidence` cannot reach `list[Evidence]`, so it has to become the
    default instead."""
    reply = {
        "companies": [
            {
                "identity": {
                    "name": "Onbekend Capital",
                    "country": None,
                    "domain": None,
                    "website": None,
                    "hq_city": None,
                },
                "classification": {"buyer_type": None, "sector_text": None, "description": None},
                "mandate": None,
                "capacity": None,
                "financial_buyer": None,
                "strategic_buyer": None,
                "track_record": None,
                "evidence": None,
            }
        ]
    }

    (found,) = SearchAgentOutput.model_validate(reply).companies

    assert found.identity.name == "Onbekend Capital"
    assert found.evidence == []
    assert found.mandate.countries_active == []
    assert found.capacity.ticket_size is None


def test_the_constraints_the_schema_cannot_carry_are_enforced_on_the_way_in():
    """Strict output has no `pattern`, so nothing stops the model returning a country name.
    Pydantic is what catches it."""
    bad = {**FOUND, "identity": {**IDENTITY, "country": "Netherlands"}}

    with pytest.raises(ValidationError):
        SearchAgentOutput.model_validate({"companies": [bad]})


def test_parsing_still_enforces_the_buyer_type_rule():
    bad = {**FOUND, "strategic_buyer": STRATEGIC_BUYER}

    with pytest.raises(ValidationError, match="strategic_buyer must be null"):
        SearchAgentOutput.model_validate({"companies": [bad]})


# ── The cut-down WIP schema ──────────────────────────────────


def test_the_wip_company_stays_small():
    """The whole point of it: if this grows past ten fields it is no longer the cheap one."""
    assert len(WIPSearchCompany.model_fields) <= 10


def test_the_wip_schema_matches_its_model():
    assert set(WIP_SEARCH_SCHEMA["$defs"]["Company"]["properties"]) == set(WIPSearchCompany.model_fields)


def test_the_wip_schema_is_strict_valid():
    supported = {
        "$defs", "$ref", "additionalProperties", "anyOf", "description",
        "enum", "items", "properties", "required", "title", "type",
    }
    used = {key for _, node in _walk(WIP_SEARCH_SCHEMA) if isinstance(node, dict) for key in node}
    assert used <= supported

    for path, node in _walk(WIP_SEARCH_SCHEMA):
        if isinstance(node, dict) and "properties" in node:
            assert set(node["required"]) == set(node["properties"]), path
            assert node["additionalProperties"] is False, path


def test_the_wip_output_parses_a_reply_full_of_nulls():
    reply = {
        "companies": [
            {
                "name": "Voorbeeld Capital",
                "website": None,
                "country": "NL",
                "buyer_type": "financial",
                "sector_text": None,
                "countries_active": None,
                "ticket_size_min_eur_m": 10,
                "ticket_size_max_eur_m": None,
                "source_url": "https://example.invalid",
            }
        ]
    }

    (found,) = WIPSearchOutput.model_validate(reply).companies

    assert found.name == "Voorbeeld Capital"
    assert found.countries_active == []
    assert found.ticket_size_min_eur_m == 10
    assert found.ticket_size_max_eur_m is None


def test_the_wip_schema_stays_loose_about_country():
    """Deliberate: a test run should show what the agent returned, not fail on it."""
    reply = {"companies": [{"name": "X", "country": "Netherlands"}]}

    assert WIPSearchOutput.model_validate(reply).companies[0].country == "Netherlands"
