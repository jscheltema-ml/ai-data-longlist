import logging

from posthog import Posthog
from pydantic import BaseModel

from api.config import config

logger = logging.getLogger(__name__)

SERVICE = "long-list"
ENVIRONMENT = config.environment

if config.posthog_api_key:
    posthog = Posthog(project_api_key=config.posthog_api_key, host=config.posthog_host)
else:
    posthog = None
    logger.warning("POSTHOG_API_KEY not set — analytics disabled")


class UserContext(BaseModel):
    user_id: str
    session_id: str
    display_name: str
    office_location: str
    job_title: str


def emit_service_event(
    event_name: str,
    properties: dict | None = None,
):
    """Capture service-level telemetry not tied to a specific user."""
    if posthog is None:
        return
    try:
        posthog.capture(
            distinct_id=f"service:{SERVICE}:{ENVIRONMENT}",
            event=event_name,
            properties={
                "service": SERVICE,
                "environment": ENVIRONMENT,
                **(properties or {}),
            },
        )
    except Exception as e:
        logger.warning(
            "posthog_capture_failed",
            extra={"custom_dimensions": {"error": str(e)}},
        )


def emit_event(
    ctx: UserContext,
    event_name: str,
    resource_type: str = "api",
    resource_name: str | None = None,
    properties: dict | None = None,
):
    if posthog is None:
        return
    try:
        posthog.capture(
            distinct_id=ctx.user_id,
            event=event_name,
            properties={
                "session_id": ctx.session_id,
                "service": SERVICE,
                "environment": ENVIRONMENT,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "display_name": ctx.display_name,
                "office_location": ctx.office_location,
                "job_title": ctx.job_title,
                "schema_version": 1,
                **(properties or {}),
            },
        )
    except Exception as e:
        logger.warning(
            "posthog_capture_failed",
            extra={"custom_dimensions": {"error": str(e)}},
        )


def identify_user(ctx: UserContext):
    if posthog is None:
        return
    try:
        posthog.capture(
            distinct_id=ctx.user_id,
            event="$identify",
            properties={
                "$set": {
                    "display_name": ctx.display_name,
                    "office_location": ctx.office_location,
                    "job_title": ctx.job_title,
                },
            },
        )
    except Exception as e:
        logger.warning(
            "posthog_identify_failed",
            extra={"custom_dimensions": {"error": str(e)}},
        )
