import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Article
from ai.providers.factory import get_ai_provider
from workers.extraction.geocoder import Geocoder
from workers.embeddings.embedding_engine import EmbeddingEngine

logger = logging.getLogger("gni.worker.extraction")


class ExtractionWorker:
    """
    Worker pipeline orchestrating:
    1. AI structured event extraction (Title, Category, Claims, Entities)
    2. Geocoder coordinate verification & precision protection
    3. Dense semantic vector embedding calculation
    4. Database article status transition from 'pending' -> 'extracted'
    """

    def __init__(self):
        self.ai_provider = get_ai_provider()
        self.geocoder = Geocoder()
        self.embedding_engine = EmbeddingEngine()

    async def process_article(
        self,
        session: AsyncSession,
        article: Article
    ) -> Dict[str, Any]:
        """
        Executes full extraction pipeline on a single Article entity.
        """
        content_for_ai = article.cleaned_content or article.raw_content or article.title

        # 1. AI Extraction
        extracted_data = await self.ai_provider.extract_event(
            title=article.title,
            text=content_for_ai
        )

        # 2. Geocoding Grounding (Never trust raw LLM coordinates blindly)
        resolved_loc = self.geocoder.resolve(
            raw_name=extracted_data.location.name,
            country_hint=extracted_data.location.country,
            text_context=content_for_ai[:1000],
            llm_lat=extracted_data.location.latitude,
            llm_lng=extracted_data.location.longitude
        )

        # 3. Dense Semantic Vector Embedding
        embedding_text = f"{article.title} {extracted_data.category} {resolved_loc.name} {content_for_ai[:500]}"
        embedding = await self.embedding_engine.embed_text(embedding_text)

        # 4. Update Database Record
        article.embedding = embedding
        article.processing_status = "extracted"
        article.updated_at = datetime.now(timezone.utc)
        await session.commit()

        logger.info(
            "Extracted article [%s]: category=%s, location=%s (lat=%.2f, lng=%.2f, prec=%s)",
            article.id,
            extracted_data.category,
            resolved_loc.name,
            resolved_loc.latitude,
            resolved_loc.longitude,
            resolved_loc.precision
        )

        return {
            "article_id": article.id,
            "status": "extracted",
            "event_title": extracted_data.event_title,
            "category": extracted_data.category,
            "subcategory": extracted_data.subcategory,
            "location": resolved_loc.to_dict(),
            "entities": [e.model_dump() for e in extracted_data.entities],
            "claims": extracted_data.claims,
            "severity": extracted_data.severity,
            "novelty": extracted_data.novelty,
            "confidence": extracted_data.confidence,
            "embedding_dims": len(embedding)
        }

    async def process_pending_batch(
        self,
        session: AsyncSession,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Scans for pending articles and processes them sequentially or concurrently.
        """
        stmt = select(Article).where(Article.processing_status == "pending").limit(limit)
        result = await session.execute(stmt)
        articles = result.scalars().all()

        processed = 0
        errors = 0

        for art in articles:
            try:
                await self.process_article(session, art)
                processed += 1
            except Exception as e:
                errors += 1
                logger.error("Failed extracting article [%s]: %s", art.id, e)

        return {
            "pending_found": len(articles),
            "processed": processed,
            "errors": errors
        }
