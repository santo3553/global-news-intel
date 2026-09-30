from apps.api.app.routes.health import router as health_router
from apps.api.app.routes.sources import router as sources_router
from apps.api.app.routes.articles import router as articles_router
from apps.api.app.routes.extraction import router as extraction_router
from apps.api.app.routes.events import router as events_router

__all__ = [
    "health_router",
    "sources_router",
    "articles_router",
    "extraction_router",
    "events_router"
]
