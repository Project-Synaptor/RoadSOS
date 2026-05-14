"""FastAPI application entry point.

Sets up the app with lifespan management (Redis connect/disconnect),
CORS middleware, health check endpoint, and webhook routes.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import webhook
from app.services.session import close_redis, get_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown.

    On startup: verify Redis connectivity.
    On shutdown: close the Redis connection.
    """
    logger.info("Starting RoadSOS...")
    try:
        r = await get_redis()
        await r.ping()
        logger.info("Redis connected successfully")
    except Exception as exc:
        logger.error("Redis connection failed: %s", exc)
        raise

    yield

    logger.info("Shutting down RoadSOS...")
    await close_redis()
    logger.info("Redis connection closed")


app = FastAPI(
    title="RoadSOS",
    description="WhatsApp-based AI emergency response agent for road accident victims",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint. Returns service status."""
    try:
        r = await get_redis()
        await r.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "error"

    return {"status": "ok", "redis": redis_status}
