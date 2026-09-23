"""Search agent output: the models it is parsed into, and the JSON schema it is asked for.

The schema below is maintained by hand and must stay in step with the models; the drift
guard is in tests/test_agent_schemas.py.
"""

from typing import Any

from pydantic import Field, model_validator

from shared.schemas.blocks.capacity import Capacity
from shared.schemas.blocks.classification import Classification
from shared.schemas.blocks.evidence import Evidence
from shared.schemas.blocks.financial_buyer import FinancialBuyer
from shared.schemas.blocks.identity import Identity
from shared.schemas.blocks.mandate import Mandate
from shared.schemas.blocks.strategic_buyer import StrategicBuyer
from shared.schemas.blocks.track_record import TrackRecord
from shared.schemas.common.base import Base
from shared.schemas.common.validators import check_buyer_blocks


class SearchAgentCompany(Base):
    """One buyer the agent found. Only `identity` has to be filled."""

    identity: Identity
    classification: Classification = Field(default_factory=Classification)
    mandate: Mandate = Field(default_factory=Mandate)
    capacity: Capacity = Field(default_factory=Capacity)
    financial_buyer: FinancialBuyer | None = None
    strategic_buyer: StrategicBuyer | None = None
    track_record: TrackRecord = Field(default_factory=TrackRecord)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def _buyer_block_matches_type(self) -> "SearchAgentCompany":
        check_buyer_blocks(self.classification.buyer_type, self.financial_buyer, self.strategic_buyer)
        return self


class SearchAgentOutput(Base):
    companies: list[SearchAgentCompany] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _drop_nulls(cls, data: Any) -> Any:
        """The schema makes every field required, so "not found" comes back as null. Dropping
        the key lets the field's default stand in, which is what the null meant."""
        return _without_nulls(data)


def _without_nulls(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: _without_nulls(value) for key, value in node.items() if value is not None}
    if isinstance(node, list):
        return [_without_nulls(item) for item in node]
    return node


_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}
_NUM = {"anyOf": [{"type": "number"}, {"type": "null"}]}
_INT = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
_STRS = {"type": "array", "items": {"type": "string"}}
_UNIT = {"enum": ["1", "K", "M", "B"], "description": "multiplier for value"}


def _opt(ref: str, description: str | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"anyOf": [{"$ref": f"#/$defs/{ref}"}, {"type": "null"}]}
    return schema | {"description": description} if description else schema


def _obj(properties: dict[str, Any], description: str | None = None) -> dict[str, Any]:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }
    return schema | {"description": description} if description else schema


SEARCH_AGENT_SCHEMA: dict[str, Any] = _obj(
    {"companies": {"type": "array", "items": {"$ref": "#/$defs/Company"}}}
) | {
    "$defs": {
        "Money": _obj(
            {
                "value": {"type": "number"},
                "currency": {"type": "string", "description": "ISO 4217, e.g. EUR"},
                "unit": _UNIT,
                "as_of": _STR | {"description": "YYYY-MM-DD"},
            }
        ),
        "MoneyRange": _obj(
            {
                "min": _NUM,
                "max": _NUM,
                "currency": {"type": "string", "description": "ISO 4217, e.g. EUR"},
                "unit": _UNIT,
            },
            "a band; either end may be null when the buyer states only one side",
        ),
        "Headcount": _obj({"value": {"type": "integer"}, "as_of": _STR | {"description": "YYYY-MM-DD"}}),
        "Identity": _obj(
            {
                "name": {"type": "string"},
                "country": _STR | {"description": "ISO 3166-1 alpha-2, e.g. NL"},
                "domain": _STR | {"description": "bare domain, no scheme and no www"},
                "website": _STR,
                "hq_city": _STR,
            }
        ),
        "Classification": _obj(
            {
                "buyer_type": {"anyOf": [{"enum": ["financial", "strategic"]}, {"type": "null"}]},
                "sector_text": _STR | {"description": "the sector in the source's own words"},
                "description": _STR,
            }
        ),
        "Mandate": _obj(
            {
                "countries_active": _STRS | {"description": "ISO 3166-1 alpha-2"},
                "sectors_of_interest": _STRS,
                "strategy": _STRS | {"description": "e.g. buy_and_build"},
                "customer_type": _STRS | {"description": "e.g. b2b"},
                "stake_preference": _STRS | {"description": "e.g. majority"},
                "holding_period": _STR | {"description": "coded bucket, e.g. 5_7_years"},
            },
            "what the buyer says it is looking for",
        ),
        "Capacity": _obj(
            {
                "ticket_size": _opt("MoneyRange", "equity the buyer writes per deal"),
                "target_ev_range": _opt("MoneyRange", "enterprise value of the deals it does"),
                "target_ebitda_range": _opt("MoneyRange", "earnings band it screens on"),
                "basis": {
                    "anyOf": [{"enum": ["stated", "inferred", "mixed"]}, {"type": "null"}],
                    "description": "stated by the buyer, or inferred from its deals",
                },
            },
            "what size of target the buyer takes on; bands, not the buyer's own figures",
        ),
        "Fund": _obj({"name": _STR, "vintage": _INT | {"description": "year raised"}, "size": _opt("Money")}),
        "FinancialBuyer": _obj(
            {
                "fund_type": _STR | {"description": "pe, family_office, search_fund, holding"},
                "aum": _opt("Money"),
                "dry_powder": _opt("Money"),
                "current_fund": _opt("Fund"),
                "portfolio_count": _INT,
            },
            "the buyer's own position; only when buyer_type is financial",
        ),
        "StrategicBuyer": _obj(
            {
                "revenue": _opt("Money"),
                "ebitda": _opt("Money"),
                "employees": _opt("Headcount"),
                "listed": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                "ticker": _STR,
                "parent": _STR | {"description": "group above this entity, if any"},
            },
            "the buyer's own figures; only when buyer_type is strategic",
        ),
        "Deal": _obj(
            {
                "target": _STR,
                "date": _STR | {"description": "YYYY-MM-DD"},
                "country": _STR | {"description": "ISO 3166-1 alpha-2"},
                "sector": _STR,
                "stake": _STR | {"description": "e.g. majority"},
                "ev": _opt("Money"),
                "url": _STR,
            }
        ),
        "TrackRecord": _obj(
            {
                "deal_count_5y": _INT,
                "last_deal_at": _STR | {"description": "YYYY-MM-DD"},
                "sectors_acquired": _STRS,
                "countries_acquired": _STRS | {"description": "ISO 3166-1 alpha-2"},
                "recent_deals": {"type": "array", "items": {"$ref": "#/$defs/Deal"}},
            },
            "what the buyer has actually bought",
        ),
        "Evidence": _obj(
            {
                "claim": {"type": "string", "description": "dotted field path, e.g. capacity.ticket_size"},
                "text": {"type": "string", "description": "the quote the claim rests on"},
                "url": _STR,
                "source_key": {"type": "string"},
                "retrieved_at": {"type": "string", "description": "ISO 8601, UTC"},
            }
        ),
        "Company": _obj(
            {
                "identity": {"$ref": "#/$defs/Identity"},
                "classification": {"$ref": "#/$defs/Classification"},
                "mandate": {"$ref": "#/$defs/Mandate"},
                "capacity": {"$ref": "#/$defs/Capacity"},
                "financial_buyer": _opt("FinancialBuyer", "null unless buyer_type is financial"),
                "strategic_buyer": _opt("StrategicBuyer", "null unless buyer_type is strategic"),
                "track_record": {"$ref": "#/$defs/TrackRecord"},
                "evidence": {"type": "array", "items": {"$ref": "#/$defs/Evidence"}},
            }
        ),
    }
}
