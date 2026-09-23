import pytest

pytest.importorskip("fastapi")  # skips under bare `uvx pytest` (no app deps)

# Dummy Azure config is set in conftest.py before any test module imports api.main.
from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

ORIGIN = "http://localhost:5173"


# Routes exist for these tests only: the middleware is app-wide, so it needs some
# endpoint to fail behind, and pinning that to a real service route would tie this
# file to whichever service happens to exist.
@app.get("/__test__/boom")
async def _boom():
    raise RuntimeError("endpoint exploded")


@app.get("/__test__/teapot")
async def _teapot():
    raise HTTPException(status_code=418, detail="deliberate")


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_exception_returns_500_with_cors_headers(client):
    """The bug this guards: an unhandled 500 escaping CORSMiddleware makes the
    browser report a bogus 'missing Access-Control-Allow-Origin' instead of the
    actual error."""
    resp = client.get("/__test__/boom", headers={"Origin": ORIGIN})

    assert resp.status_code == 500
    assert resp.headers["access-control-allow-origin"] == "*"


def test_unhandled_exception_body_names_the_error(client):
    """
    Test that the error body includes error details and identifier.
    """
    resp = client.get("/__test__/boom", headers={"Origin": ORIGIN})

    body = resp.json()
    assert body["detail"] == "RuntimeError: endpoint exploded"
    assert body["error_id"]  # correlates the response with the logged traceback


def test_http_exceptions_are_left_alone(client):
    """
    Test that the error middleware doesn't override deliberate HTTPExceptions raised by endpoints.

    A deliberate 418 must not get rewritten as a 500. Deliberate HTTPExceptions are handled
    further in by ExceptionMiddleware and must keep their own status code and detail.
    """
    resp = client.get("/__test__/teapot", headers={"Origin": ORIGIN})

    assert resp.status_code == 418
    assert resp.json()["detail"] == "deliberate"
