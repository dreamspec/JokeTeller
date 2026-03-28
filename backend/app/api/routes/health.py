"""Health and status endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from backend.app.models.status import HealthResponse, StatusResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Return backend health without querying LM Studio."""

    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/status", response_model=StatusResponse)
async def status(request: Request) -> StatusResponse:
    """Return backend status plus LM Studio reachability details."""

    settings = request.app.state.settings
    lm_studio_service = request.app.state.lm_studio_service
    lm_status = await lm_studio_service.probe()
    return StatusResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        lm_studio=lm_status,
    )

