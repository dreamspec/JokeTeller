"""FastAPI entrypoint for the JokeTeller backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.services.lm_studio import LMStudioService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and clean up shared application resources."""

    settings = get_settings()
    lm_studio_service = LMStudioService(settings=settings)
    app.state.settings = settings
    app.state.lm_studio_service = lm_studio_service
    try:
        yield
    finally:
        await lm_studio_service.aclose()


def create_app() -> FastAPI:
    """Create the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
