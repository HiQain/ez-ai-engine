"""Caller authentication for the AI Takeoff service.

The service is an internal engine: only trusted backends (today the Laravel
API at api.ezestimater.com) should reach its endpoints. Callers prove they are
trusted by sending a shared secret in the X-Engine-Key header, which this
dependency compares against ``settings.engine_api_key``.

Behaviour when no key is configured on the server:
- development / test: auth is skipped, so local runs and the test suite work
  without extra setup;
- production: every request is refused, so a deployment that forgets to set
  ENGINE_API_KEY fails closed instead of running wide open.
"""

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings

API_KEY_HEADER = "X-Engine-Key"


def require_engine_key(
    x_engine_key: str | None = Header(default=None, alias=API_KEY_HEADER),
) -> None:
    configured = settings.engine_api_key

    if not configured:
        if settings.app_env == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Engine API key is not configured on the server.",
            )
        # Dev/test convenience: no key set means auth is intentionally off.
        return

    if not x_engine_key or not hmac.compare_digest(x_engine_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
