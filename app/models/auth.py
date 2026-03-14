from pydantic import BaseModel, Field
from datetime import datetime


class GoogleAuthorizeResponse(BaseModel):
    authorization_url: str


class TokenExchangeRequest(BaseModel):
    code: str = Field(..., description="Google OAuth2 authorization code")
    redirect_uri: str | None = Field(
        default=None,
        description="Redirect URI used during OAuth consent; falls back to credentials.json value",
    )


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Google OAuth2 refresh token")


class GoogleTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    scope: str | None = None
    token_type: str
    refresh_token: str | None = None
    id_token: str | None = None


class ManagedGoogleTokenResponse(GoogleTokenResponse):
    expires_at: datetime
    refreshed: bool = False


class EnsureTokenRequest(BaseModel):
    access_token: str | None = Field(
        default=None,
        description="Current access token if available",
    )
    refresh_token: str = Field(..., description="Google OAuth2 refresh token")
    expires_at: datetime | None = Field(
        default=None,
        description="Access token expiry time in ISO-8601 (UTC recommended)",
    )
