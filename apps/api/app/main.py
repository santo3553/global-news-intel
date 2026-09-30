from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.config import settings
from apps.api.app.database import async_engine, Base
from apps.api.app.routes.health import router as health_router
from apps.api.app.routes.sources import router as sources_router
from apps.api.app.routes.articles import router as articles_router
from apps.api.app.routes.extraction import router as extraction_router
from apps.api.app.routes.events import router as events_router
import logging

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("gni.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Global News Intelligence API [%s]...", settings.ENVIRONMENT)
    # Ensure database schema is created on startup (safe for development & tests)
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified.")
    except Exception as e:
        logger.error("Failed to auto-create database tables on startup: %s", e)
    yield
    logger.info("Shutting down Global News Intelligence API...")
    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Local-first Global News Intelligence & Geospatial Event Analysis API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(sources_router)
app.include_router(articles_router)
app.include_router(extraction_router)
app.include_router(events_router)


@app.get("/", tags=["General"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
