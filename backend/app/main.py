from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.trace import TraceIdMiddleware


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.add_middleware(TraceIdMiddleware)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
