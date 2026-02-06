"""
Pydantic schemas for Authentication API requests and responses.
"""
from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Schema for simple password authentication."""
    password: str = Field(..., min_length=1, description="Authentication password")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Health status: healthy | unhealthy")
    services: dict = Field(..., description="Status of dependent services")
    version: str = Field(..., description="API version")
