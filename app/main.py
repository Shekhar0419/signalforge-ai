from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.cleaned_files import (
    router as cleaned_files_router,
)
from app.api.routes.cleaning import (
    router as cleaning_router,
)
from app.api.routes.datasets import (
    router as datasets_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.version_compare import (
    router as version_compare_router,
)
from app.api.routes.versioning import (
    router as versioning_router,
)
from app.core.config import Settings


settings = Settings()

logging.basicConfig(
    level=getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    ),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    logger.info(
        "signalforge_started environment=%s",
        settings.app_env,
    )

    yield

    logger.info("signalforge_stopped")


app = FastAPI(
    title="SignalForge AI",
    version="1.0.0",
    description=(
        "AI-powered Dataset Quality "
        "Intelligence Platform"
    ),
    lifespan=lifespan,
)

app.state.settings = settings


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "https://signalforge-ai-two.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_metadata(
    request: Request,
    call_next,
):
    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid4())
    )

    started_at = perf_counter()

    response = await call_next(request)

    process_time_ms = (
        perf_counter() - started_at
    ) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers[
        "X-Process-Time-Ms"
    ] = f"{process_time_ms:.2f}"

    return response


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "SignalForge AI",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
        "ready": "/api/v1/ready",
    }


app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    datasets_router,
    prefix="/api/v1",
)

app.include_router(
    cleaning_router,
    prefix="/api/v1",
)

app.include_router(
    cleaned_files_router,
    prefix="/api/v1",
)

app.include_router(
    versioning_router,
    prefix="/api/v1",
)

app.include_router(
    version_compare_router,
    prefix="/api/v1",
)