from pydantic import BaseModel, Field


class EmailSyncRequest(BaseModel):
    access_token: str = Field(..., description="Google OAuth2 access token")
    user_id: str = Field(default="me", description="Gmail user id, usually 'me'")
    max_results: int = Field(default=20, ge=1, le=100, description="Unread email fetch count")


class EmailSyncResponse(BaseModel):
    fetched_count: int
    published_count: int
    topic: str
