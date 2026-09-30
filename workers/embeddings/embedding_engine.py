import math
from typing import List
from ai.providers.factory import get_ai_provider


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    sim = dot / (norm_a * norm_b)
    # Clamp to [-1.0, 1.0] to prevent floating point rounding drift
    return max(-1.0, min(1.0, round(sim, 5)))


class EmbeddingEngine:
    """
    Semantic embedding engine supporting local dense vector generation and vector distance calculations.
    """

    def __init__(self):
        self.provider = get_ai_provider()

    async def embed_text(self, text: str) -> List[float]:
        """Generates 384-dimensional unit vector representation."""
        return await self.provider.generate_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation."""
        return [await self.embed_text(t) for t in texts]
