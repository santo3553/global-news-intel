import re
import json
import logging
from typing import List, Optional
import httpx

from apps.api.app.config import settings
from ai.providers.base import AIProvider
from ai.providers.mock_provider import MockAIProvider
from ai.schemas.extraction import ExtractedEventData

logger = logging.getLogger("gni.ai.local_llm")

EXTRACTION_SYSTEM_PROMPT = """You are a senior news intelligence analyst. Analyze the provided news report and extract structured event intelligence.
You MUST output ONLY valid JSON matching this exact structure:
{
  "event_title": "Concise, factual title of the real-world event",
  "category": "natural_disaster|politics|security|economy|science|health|environment|society",
  "subcategory": "specific subcategory (e.g. earthquake, diplomacy, trade)",
  "location": {
    "name": "Specific place name (e.g. Kyushu, Japan)",
    "country": "Country name or ISO code",
    "admin_region": "State, province, or prefecture",
    "city": "City name if specified",
    "latitude": 32.8,
    "longitude": 131.4,
    "precision": "city|region|country|global",
    "location_confidence": 0.85
  },
  "entities": [
    {"name": "Entity Name", "type": "country|location|person|organization|concept"}
  ],
  "claims": [
    "Factual claim 1",
    "Factual claim 2"
  ],
  "severity": 0.85,
  "novelty": 0.70,
  "confidence": 0.90,
  "human_impact_estimate": 7.5,
  "global_impact_estimate": 6.0
}
Never include preamble or conversational filler. Output only raw JSON.
"""


class LocalLLMProvider(AIProvider):
    """
    Local LLM provider connecting to Ollama, llama.cpp, or local OpenAI-compatible endpoints.
    Employs structured JSON schema enforcement, regex recovery, and fallback to MockProvider
    if local server is unreachable (guaranteeing zero crashed runs).
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.endpoint = endpoint or "http://localhost:11434/api/generate"
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout
        self.fallback = MockAIProvider()

    def _extract_json_block(self, text: str) -> str:
        """Extracts JSON object from text, stripping markdown code fences if present."""
        text = text.strip()
        # Look for markdown ```json ... ``` block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        # Look for raw outermost {...}
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            return brace_match.group(1)
        return text

    async def extract_event(self, title: str, text: str) -> ExtractedEventData:
        prompt = f"Title: {title}\n\nArticle Content:\n{text[:3000]}"
        payload = {
            "model": self.model,
            "prompt": f"{EXTRACTION_SYSTEM_PROMPT}\n\n{prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": settings.LLM_TEMPERATURE,
                "num_ctx": settings.LLM_CONTEXT_SIZE
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint, json=payload)
                if response.status_code == 200:
                    res_json = response.json()
                    raw_output = res_json.get("response", "")
                    clean_json_str = self._extract_json_block(raw_output)
                    data = ExtractedEventData.model_validate_json(clean_json_str)
                    return data
                else:
                    logger.warning("Local LLM returned HTTP %s, using fallback", response.status_code)
        except Exception as e:
            logger.info("Local LLM not reached (%s), using resilient rule-based extraction", e)

        # Resilient fallback
        return await self.fallback.extract_event(title, text)

    async def generate_embedding(self, text: str) -> List[float]:
        # Embeddings generated locally
        return await self.fallback.generate_embedding(text)

    async def summarize_event(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception:
            pass
        return await self.fallback.summarize_event(prompt)
