from fastapi import APIRouter, Query

from app.models.auth import (
    EnsureTokenRequest,
    GoogleAuthorizeResponse,
    ManagedGoogleTokenResponse,
    TokenExchangeRequest,
    TokenRefreshRequest,
)
from app.services.auth import google_oauth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/authorize", response_model=GoogleAuthorizeResponse)
async def get_google_authorization_url(
    redirect_uri: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> GoogleAuthorizeResponse:
    auth_url = google_oauth_service.build_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
    )
    return GoogleAuthorizeResponse(authorization_url=auth_url)


@router.post("/google/token", response_model=ManagedGoogleTokenResponse)
async def exchange_google_token(payload: TokenExchangeRequest) -> ManagedGoogleTokenResponse:
    token_data = await google_oauth_service.exchange_code_for_tokens(
        code=payload.code,
        redirect_uri=payload.redirect_uri,
    )
    return ManagedGoogleTokenResponse(**token_data)


@router.post("/google/refresh", response_model=ManagedGoogleTokenResponse)
async def refresh_google_token(payload: TokenRefreshRequest) -> ManagedGoogleTokenResponse:
    token_data = await google_oauth_service.refresh_access_token(
        refresh_token=payload.refresh_token
    )
    return ManagedGoogleTokenResponse(**token_data)


@router.post("/google/token/ensure", response_model=ManagedGoogleTokenResponse)
async def ensure_google_token(payload: EnsureTokenRequest) -> ManagedGoogleTokenResponse:
    token_data = await google_oauth_service.ensure_valid_access_token(
        access_token=payload.access_token,
        refresh_token=payload.refresh_token,
        expires_at=payload.expires_at,
    )
    return ManagedGoogleTokenResponse(**token_data)
