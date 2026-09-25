"""The spec payloads the schemas were written from, shared by the schema tests.

Kept verbatim so that renaming or retyping a field fails here before it fails anywhere that
matters.
"""

BATCH = {
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

IDENTITY = {
    "name": "Voorbeeld Capital B.V.",
    "country": "NL",
    "domain": "voorbeeldcapital.nl",
    "website": "https://voorbeeldcapital.nl",
    "hq_city": "Amsterdam",
}

CLASSIFICATION = {
    "buyer_type": "financial",
    "sector_text": "industrial automation",
    "description": "...",
}

MANDATE = {
    "countries_active": ["NL", "BE", "DE"],
    "sectors_of_interest": ["industrial automation", "machining"],
    "strategy": ["buy_and_build"],
    "customer_type": ["b2b"],
    "stake_preference": ["majority"],
    "holding_period": "5_7_years",
}

CAPACITY = {
    "ticket_size": {"min": 10, "max": 60, "currency": "EUR", "unit": "M"},
    "target_ev_range": {"min": 20, "max": 150, "currency": "EUR", "unit": "M"},
    "target_ebitda_range": {"min": 3, "max": 20, "currency": "EUR", "unit": "M"},
    "basis": "stated",
}

FINANCIAL_BUYER = {
    "fund_type": "pe",
    "aum": {"value": 450, "currency": "EUR", "unit": "M", "as_of": "2025-12-31"},
    "dry_powder": {"value": 120, "currency": "EUR", "unit": "M", "as_of": "2025-12-31"},
    "current_fund": {
        "name": "Fund IV",
        "vintage": 2023,
        "size": {"value": 300, "currency": "EUR", "unit": "M"},
    },
    "portfolio_count": 14,
}

FINANCIALS = {
    "revenue": {"value": 820, "currency": "EUR", "unit": "M", "as_of": "2024-12-31"},
    "ebitda": {"value": 96, "currency": "EUR", "unit": "M", "as_of": "2024-12-31"},
    "ebit": None,
    "enterprise_value": {"value": 1150, "currency": "EUR", "unit": "M"},
    "equity": {"value": 430, "currency": "EUR", "unit": "M", "as_of": "2024-12-31"},
    "employees": {"value": 3400, "as_of": "2025-06-30"},
}

STRATEGIC_BUYER = {
    "financials": FINANCIALS,
    "listed": True,
    "ticker": "AMS:VBI",
    "parent": None,
}

BRIEF = {
    "brief_id": "brief_01",
    "target": {
        "identity": {"name": "Te Koop Industrials B.V.", "country": "NL", "hq_city": "Eindhoven"},
        "sector_text": "industrial automation",
        "activity": "retrofits control systems for food processing lines",
        "description": "...",
        "financials": {
            "revenue": {"value": 42.0, "currency": "EUR", "unit": "M", "as_of": "2025-12-31"},
            "ebitda": {"value": 6.5, "currency": "EUR", "unit": "M", "as_of": "2025-12-31"},
            "enterprise_value": {"value": 55.0, "currency": "EUR", "unit": "M"},
            "equity": {"value": 18.0, "currency": "EUR", "unit": "M", "as_of": "2025-12-31"},
            "employees": {"value": 180, "as_of": "2025-06-30"},
        },
    },
    "thesis": "A bolt-on for a European automation group wanting food-sector exposure.",
    "mandate": {
        "countries_active": ["NL", "BE", "DE"],
        "sectors_of_interest": ["industrial automation"],
        "stake_preference": ["majority"],
    },
    "capacity": {
        "target_ev_range": {"min": 40, "max": 80, "currency": "EUR", "unit": "M"},
    },
    "buyer_types": ["financial", "strategic"],
    "exclusions": ["direct_competitor"],
}

TRACK_RECORD = {
    "deal_count_5y": 6,
    "last_deal_at": "2025-03-11",
    "sectors_acquired": ["industrial automation", "machining"],
    "countries_acquired": ["NL", "DE"],
    "recent_deals": [
        {
            "target": "...",
            "date": "2025-03-11",
            "country": "NL",
            "sector": "...",
            "stake": "majority",
            "ev": {"value": 45, "currency": "EUR", "unit": "M"},
            "url": "https://example.invalid/deal",
        }
    ],
}

EVIDENCE = [
    {
        "claim": "capacity.ticket_size",
        "text": "...",
        "url": "https://example.invalid/mandate",
        "source_key": "claude_web",
        "retrieved_at": "2026-09-22T10:17:02Z",
    }
]

ITEM = {
    "item_id": "cmp_8f3a",
    "id_basis": "domain",
    "external_ids": {
        "gain": "A-10293",
        "ml_archive": "bv-88214",
        "kvk": "12345678",
        "lei": None,
    },
    "found_by": ["gain", "claude_web"],
    "pipeline": {
        "ingested_at": "2026-09-22T10:15:41Z",
        "cleaned_status": "merged",
        "cleaned_at": "2026-09-22T10:17:12Z",
        "cleaned_by": "merge_rules@1.3",
        "relevant_status": "verified",
        "relevant_at": "2026-09-22T10:18:02Z",
        "relevant_by": "relevance_agent@1.0",
        "relevant_reason": None,
        "available_status": "verified",
        "available_at": "2026-09-22T10:18:30Z",
        "available_by": "availability_agent@1.0",
        "available_reason": None,
        "scored_status": "scored",
        "scored_at": "2026-09-22T10:19:47Z",
        "scored_by": "ranking_config@0.4",
    },
    "identity": IDENTITY,
    "classification": CLASSIFICATION,
    "mandate": MANDATE,
    "capacity": CAPACITY,
    "financial_buyer": FINANCIAL_BUYER,
    "strategic_buyer": None,
    "track_record": TRACK_RECORD,
    "evidence": EVIDENCE,
    "provenance": {
        "identity.name": "gain",
        "capacity.ticket_size": "claude_web",
        "financial_buyer.aum": "gain",
    },
    "quality": {
        "completeness": 0.72,
        "conflicts": [
            {
                "field": "financial_buyer.aum",
                "values": [
                    {"source": "gain", "value": 450},
                    {"source": "ml_archive", "value": 420},
                ],
                "resolved_to": "gain",
            }
        ],
    },
    "scoring": {
        "total": 0.78,
        "tier": 1,
        "components": {
            "sector_fit": {"raw": 0.9, "weight": 0.30, "contribution": 0.270},
            "size_fit": {"raw": 0.6, "weight": 0.20, "contribution": 0.120},
            "geography_fit": {"raw": 1.0, "weight": 0.15, "contribution": 0.150},
            "track_record_fit": {"raw": 0.7, "weight": 0.20, "contribution": 0.140},
            "thesis_fit": {"raw": 0.6, "weight": 0.15, "contribution": 0.090},
        },
        "rationale": "...",
    },
}
