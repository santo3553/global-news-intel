"""
Central Redis Caching Engine for Global News Intelligence API.
Provides sub-millisecond hot-path caching for executive briefings and event queries.
Fails open gracefully if Redis is temporarily disconnected.
"""

import json
import logging
import time
from typing import Any, Optional, List, Dict, Tuple
from redis import asyncio as aioredis
from apps.api.app.config import settings

logger = logging.getLogger("gni.cache")

_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    """Returns the shared async Redis connection pool."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=1.5,
            socket_connect_timeout=1.5
        )
    return _redis_client


async def close_redis():
    """Gracefully closes the Redis connection pool on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None


async def get_cache(key: str) -> Optional[str]:
    """Retrieves raw string value from Redis cache. Returns None on cache miss or error."""
    try:
        client = get_redis_client()
        return await client.get(key)
    except Exception as e:
        logger.debug("Redis get_cache miss/error [%s]: %s", key, e)
        return None


async def set_cache(key: str, value: str, ttl_seconds: int = 60) -> bool:
    """Sets raw string value with TTL in Redis cache."""
    try:
        client = get_redis_client()
        await client.set(key, value, ex=ttl_seconds)
        return True
    except Exception as e:
        logger.debug("Redis set_cache error [%s]: %s", key, e)
        return False


async def get_json_cache(key: str) -> Optional[Any]:
    """Retrieves and deserializes JSON object from Redis cache."""
    raw = await get_cache(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception as e:
        logger.warning("Failed to deserialize JSON cache [%s]: %s", key, e)
        return None


async def set_json_cache(key: str, data: Any, ttl_seconds: int = 60) -> bool:
    """Serializes and sets JSON object with TTL in Redis cache."""
    try:
        # Default serializer for pydantic models or datetimes
        def default_serializer(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump(mode="json")
            if hasattr(obj, "dict"):
                return obj.dict()
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            return str(obj)

        serialized = json.dumps(data, default=default_serializer)
        return await set_cache(key, serialized, ttl_seconds=ttl_seconds)
    except Exception as e:
        logger.debug("Redis set_json_cache error [%s]: %s", key, e)
        return False


async def delete_cache(key: str) -> bool:
    """Deletes a single cache key."""
    try:
        client = get_redis_client()
        await client.delete(key)
        return True
    except Exception as e:
        logger.debug("Redis delete_cache error [%s]: %s", key, e)
        return False


async def invalidate_patterns(patterns: List[str]) -> int:
    """
    Invalidates all keys matching the provided glob patterns (e.g. ['briefing:*', 'events:*']).
    Returns total count of deleted keys.
    """
    total_deleted = 0
    try:
        client = get_redis_client()
        for pat in patterns:
            keys = await client.keys(pat)
            if keys:
                deleted = await client.delete(*keys)
                total_deleted += deleted
        if total_deleted > 0:
            logger.info("Invalidated %d cache keys matching %s", total_deleted, patterns)
    except Exception as e:
        logger.debug("Redis invalidate_patterns error %s: %s", patterns, e)
    return total_deleted


async def ping_redis() -> Tuple[bool, float]:
    """Pings Redis and measures latency in milliseconds."""
    start = time.perf_counter()
    try:
        client = get_redis_client()
        pong = await client.ping()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return bool(pong), latency_ms
    except Exception:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return False, latency_ms
