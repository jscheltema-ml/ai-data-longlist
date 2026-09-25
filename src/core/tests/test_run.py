"""The run record: what was asked for, as against what happened."""

import pytest
from conftest_payloads import BRIEF
from pydantic import ValidationError

from shared.schemas import Run, RunStatus, Stage, StageStatus

RUN = {
    "run_id": "run_01JBQ",
    "brief": BRIEF,
    "status": "partial",
    "created_at": "2026-09-22T10:15:00Z",
    "started_at": "2026-09-22T10:15:02Z",
    "finished_at": "2026-09-22T10:19:47Z",
    "requested_sources": ["gain", "claude_web", "ml_archive"],
    "requested_stages": ["ingestion", "cleaning", "relevance", "availability", "scoring"],
    "search_volume": 50,
    "sources": {
        "gain": {"status": "ok", "record_count": 412},
        "claude_web": {"status": "ok", "record_count": 38},
        "ml_archive": {"status": "failed", "record_count": 0, "error": "auth expired"},
    },
    "stages": {
        "ingestion": {"status": "completed", "items_in": 0, "items_out": 450},
        "cleaning": {"status": "completed", "version": "merge_rules@1.3", "items_in": 450, "items_out": 301},
        "relevance": {"status": "completed", "version": "relevance_agent@1.0", "items_in": 301, "items_out": 140},
        "availability": {"status": "failed", "error": "rate limited"},
        "scoring": {"status": "skipped"},
    },
}


def test_run_example_validates():
    run = Run.model_validate(RUN)

    assert run.status is RunStatus.PARTIAL
    assert run.sources["gain"].record_count == 412
    assert run.stages[Stage.CLEANING].version == "merge_rules@1.3"


def test_the_brief_is_frozen_into_the_run():
    """Embedded rather than referenced, so the run stays readable after the brief changes."""
    run = Run.model_validate(RUN)

    assert run.brief.target.identity.name == "Te Koop Industrials B.V."
    assert run.brief.brief_id == "brief_01"


def test_a_source_that_returned_nothing_is_still_on_the_record():
    """The reason SourceRun exists: no batch was written for ml_archive, so nothing else
    in the system knows it was ever asked."""
    run = Run.model_validate(RUN)

    assert "ml_archive" in run.requested_sources
    assert run.sources["ml_archive"].record_count == 0
    assert run.sources["ml_archive"].error == "auth expired"


def test_a_stage_that_never_ran_is_distinguishable_from_one_that_failed():
    run = Run.model_validate(RUN)

    assert run.stages[Stage.AVAILABILITY].status is StageStatus.FAILED
    assert run.stages[Stage.SCORING].status is StageStatus.SKIPPED


def test_results_may_lag_the_request_because_a_run_can_still_be_going():
    run = Run.model_validate({**RUN, "status": "running", "sources": {}, "stages": {}})

    assert run.requested_sources == ["gain", "claude_web", "ml_archive"]
    assert run.sources == {}


def test_a_result_for_a_source_nobody_asked_for_is_rejected():
    """A runner writing to the wrong key would quietly widen what the run claims to have
    done."""
    with pytest.raises(ValidationError, match=r"source results for \['kvk'\]"):
        Run.model_validate({**RUN, "sources": {**RUN["sources"], "kvk": {"status": "ok"}}})


def test_a_result_for_a_stage_nobody_asked_for_is_rejected():
    trimmed = {**RUN, "requested_stages": ["ingestion", "cleaning"]}
    with pytest.raises(ValidationError, match="stage results for"):
        Run.model_validate(trimmed)


def test_a_run_must_ask_for_something():
    for field in ("requested_sources", "requested_stages"):
        with pytest.raises(ValidationError, match=field):
            Run.model_validate({**RUN, field: [], "sources": {}, "stages": {}})


def test_run_round_trips_through_json():
    run = Run.model_validate(RUN)

    assert Run.model_validate(run.model_dump(mode="json")) == run
