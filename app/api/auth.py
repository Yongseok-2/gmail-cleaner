# -*- coding: utf-8 -*-
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


@router.get(
    "/google/authorize",
    response_model=GoogleAuthorizeResponse,
    summary="Google OAuth 동의 URL 생성",
)
async def get_google_authorization_url(
    redirect_uri: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> GoogleAuthorizeResponse:
    """Google OAuth2 authorization URL을 반환한다."""
    auth_url = google_oauth_service.build_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
    )
    return GoogleAuthorizeResponse(authorization_url=auth_url)


@router.post(
    "/google/token",
    response_model=ManagedGoogleTokenResponse,
    summary="인가 코드로 토큰 발급",
    description="Google authorization code를 access/refresh token으로 교환한다.",
)
async def exchange_google_token(payload: TokenExchangeRequest) -> ManagedGoogleTokenResponse:
    """인가 코드를 토큰으로 교환한다."""
    token_data = await google_oauth_service.exchange_code_for_tokens(
        code=payload.code,
        redirect_uri=payload.redirect_uri,
    )
    return ManagedGoogleTokenResponse(**token_data)


@router.post(
    "/google/refresh",
    response_model=ManagedGoogleTokenResponse,
    summary="Access Token 갱신",
    description="refresh token으로 access token을 갱신한다.",
)
async def refresh_google_token(payload: TokenRefreshRequest) -> ManagedGoogleTokenResponse:
    """refresh token 기반으로 access token을 갱신한다."""
    token_data = await google_oauth_service.refresh_access_token(
        refresh_token=payload.refresh_token
    )
    return ManagedGoogleTokenResponse(**token_data)


@router.post(
    "/google/token/ensure",
    response_model=ManagedGoogleTokenResponse,
    summary="유효 토큰 보장",
    description="현재 토큰 만료 여부를 확인하고 필요 시 자동 갱신한다.",
)
async def ensure_google_token(payload: EnsureTokenRequest) -> ManagedGoogleTokenResponse:
    """토큰이 만료 임박이면 갱신하고 아니면 기존 값을 반환한다."""
    token_data = await google_oauth_service.ensure_valid_access_token(
        access_token=payload.access_token,
        refresh_token=payload.refresh_token,
        expires_at=payload.expires_at,
    )
    return ManagedGoogleTokenResponse(**token_data)
