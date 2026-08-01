import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import datasets, health
from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings
    logger.info(
        "signalforge_started environment=%s",
        settings.app_env,
    )
    yield
    logger.info("signalforge_stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI data reliability and decision intelligence API",
    lifespan=lifespan,
)

# ----------------------------
# CORS Configuration
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517\d",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid4()),
    )

    started = time.perf_counter()

    response = await call_next(request)

    duration_ms = (
        time.perf_counter() - started
    ) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = (
        f"{duration_ms:.2f}"
    )

    logger.info(
        "request_completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )

    return response


app.include_router(
    health.router,
    prefix="/api/v1",
)

app.include_router(
    datasets.router,
    prefix="/api/v1",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/v1/health",
    }