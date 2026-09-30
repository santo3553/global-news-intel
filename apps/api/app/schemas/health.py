from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def utc_now_str():
    return datetime.now(timezone.utc).isoformat()


class ComponentHealth(BaseModel):
    status: str = Field(..., description="'connected', 'disconnected', or 'degraded'")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional component metadata")


class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Runtime environment")
    timestamp: str = Field(default_factory=utc_now_str, description="ISO-8601 UTC timestamp")
    database: ComponentHealth
    redis: ComponentHealth
