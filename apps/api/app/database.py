import time
from typing import AsyncGenerator, Dict, Any
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from apps.api.app.config import settings

# Determine database dialect
is_sqlite = "sqlite" in settings.DATABASE_URL

# Async Engine for FastAPI operations
connect_args = {"check_same_thread": False} if is_sqlite else {}
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Synchronous Engine for migrations and scripts
sync_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_SYNC_URL else {}
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=False,
    connect_args=sync_connect_args,
    pool_pre_ping=True
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connectivity() -> Dict[str, Any]:
    """Health check utility to verify database connectivity and measure latency."""
    start_time = time.perf_counter()
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            
            # Check PostGIS extension if PostgreSQL
            has_postgis = False
            if not is_sqlite:
                try:
                    result = await conn.execute(text("SELECT PostGIS_Version()"))
                    row = result.scalar_one_or_none()
                    if row:
                        has_postgis = True
                except Exception:
                    has_postgis = False
                    
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "status": "connected",
                "dialect": "sqlite" if is_sqlite else "postgresql",
                "postgis_enabled": has_postgis,
                "latency_ms": latency_ms
            }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "disconnected",
            "error": str(e),
            "latency_ms": latency_ms
        }
