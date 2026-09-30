from abc import ABC, abstractmethod
from typing import List
from ai.schemas.extraction import ExtractedEventData


class AIProvider(ABC):
    """
    Abstract AI Provider interface ensuring inference engine replaceability.
    Allows swapping between Local CPU, AMD/ROCm, Ollama, GGUF, or Cloud providers
    without architectural redesign (Sections 4 & 6).
    """

    @abstractmethod
    async def extract_event(self, title: str, text: str) -> ExtractedEventData:
        """
        Extracts structured event intelligence from article title and body text.
        Must return validated ExtractedEventData Pydantic model.
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a dense semantic vector representation (384-dim) for text clustering.
        """
        pass

    @abstractmethod
    async def summarize_event(self, prompt: str) -> str:
        """
        Generates text summaries and briefings for events.
        """
        pass
