"""Pydantic models for health, status, and error responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic backend health information."""

    status: str
    app_name: str
    version: str
    timestamp: datetime


class LMStudioStatus(BaseModel):
    """Detailed LM Studio connectivity status."""

    reachable: bool
    base_url: str
    default_model: str | None = None
    available_models: list[str] = Field(default_factory=list)
    error: str | None = None


class StatusResponse(BaseModel):
    """Combined backend and LM Studio status payload."""

    status: str
    app_name: str
    version: str
    lm_studio: LMStudioStatus


class ErrorResponse(BaseModel):
    """Structured error payload returned by the backend."""

    code: str
    message: str
    suggestion: str | None = None

