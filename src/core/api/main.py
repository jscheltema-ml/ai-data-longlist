# General imports
import uuid

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from api.analytics import logger
from api.config import config

# ── Observability ────────────────────────────────────────────

_connection_string = config.applicationinsights_connection_string
if _connection_string:
    configure_azure_monitor(connection_string=_connection_string)
    HTTPXClientInstrumentor().instrument()

# ── App ──────────────────────────────────────────────────────

app = FastAPI()


@app.middleware("http")
async def catch_unhandled(request: Request, call_next):
    """Turn any unhandled exception into a real 500 response with CORS headers.

    Deliberate HTTPExceptions never reach this — Starlette's ExceptionMiddleware
    sits further in and converts those first.
    """
    try:
        return await call_next(request)
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception(
            "unhandled_error",
            extra={"custom_dimensions": {"path": request.url.path, "error_id": error_id}},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": f"{type(e).__name__}: {e}", "error_id": error_id},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if _connection_string:
    FastAPIInstrumentor.instrument_app(app)

# ── Service routers ──────────────────────────────────────────
#
# Each service lives in its own package under `services/` and owns its router, auth
# and analytics; this module only wires them onto the app. Add a service by importing
# its router and including it here:
#
#     from services.<name> import routes as <name>_routes
#     app.include_router(<name>_routes.router)
#
# A service that needs work done once at startup (building a client, warming a cache)
# should do it in a `lifespan` handler passed to FastAPI() rather than at import time,
# so importing the module does not reach out to Azure.

# ── Endpoints ────────────────────────────────────────────────


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
