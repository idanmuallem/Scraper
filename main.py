import os
from fastapi import FastAPI, Depends
from core.database import engine, Base
from db import models
from routers import entities, ingestion
from core.security import get_api_key, RateLimitMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

# Database tables are now managed by Alembic.
# Base.metadata.create_all(bind=engine) has been removed.

# Initialize FastAPI application
app = FastAPI(
    title="Alternative Financial Data API",
    description="B2B API for extracting and serving structured financial data via GenAI.",
    version="0.1.0"
)

@app.on_event("startup")
async def startup():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="api-cache")

# Add Rate Limiting Middleware globally (60 requests/minute limit)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Include API Routers
app.include_router(entities.router, dependencies=[Depends(get_api_key)])
app.include_router(ingestion.router, dependencies=[Depends(get_api_key)])

@app.get("/")
def health_check():
    """
    Root health-check endpoint to verify the API is running correctly.
    """
    return {"status": "ok", "message": "Alternative Financial Data API is online."}