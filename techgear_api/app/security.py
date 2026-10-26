import secrets

from fastapi import Depends, Header, HTTPException, status

from app.config import settings


async def require_admin(
    token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    if not settings.admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API token is not configured",
        )
    if token is None or not secrets.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator credentials are required",
        )


async def require_client(
    token: str | None = Header(default=None, alias="X-Client-Token"),
) -> None:
    if not settings.admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client API token is not configured",
        )
    if token is None or not secrets.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client credentials are required",
        )
