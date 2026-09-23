"""
Entra ID bearer-token auth, shared by every route module.

Lives here rather than in api/main.py so a service router can depend on
get_user_context without importing the app (which would be a circular import).
"""

import logging
import time
import uuid

import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from api.analytics import UserContext
from api.config import config

logger = logging.getLogger(__name__)

jwks_client = PyJWKClient(
    f"https://login.microsoftonline.com/{config.azure_tenant_id}/discovery/v2.0/keys",
    cache_keys=True,
    lifespan=86400,
)
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        t = time.time()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        logger.info("jwks_timing", extra={"custom_dimensions": {"duration_seconds": round(time.time() - t, 3)}})
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=f"api://{config.app_client_id}",
        )
        return payload
    except Exception as e:
        print(f"AUTH FAILED: {e}, APP_CLIENT_ID={config.app_client_id}")
        logger.warning(
            "auth_failed",
            extra={"custom_dimensions": {"error": str(e), "app_client_id": config.app_client_id}},
        )
        raise HTTPException(status_code=401, detail=str(e))


def get_user_context(
    request: Request,
    token: dict = Depends(verify_token),
) -> UserContext:
    return UserContext(
        user_id=token.get("oid", ""),
        session_id=str(uuid.uuid4()),
        display_name=token.get("name", ""),
        office_location=request.headers.get("x-office-location", ""),
        job_title=request.headers.get("x-job-title", ""),
    )
