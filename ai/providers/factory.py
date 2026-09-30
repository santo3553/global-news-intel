from apps.api.app.config import settings
from ai.providers.base import AIProvider
from ai.providers.mock_provider import MockAIProvider
from ai.providers.local_llm import LocalLLMProvider


def get_ai_provider() -> AIProvider:
    """
    Factory function returning configured AIProvider based on environment configuration.
    Defaults to MockAIProvider in development/mock mode, or LocalLLMProvider when configured.
    """
    provider_type = settings.LLM_PROVIDER.lower().strip()
    if provider_type in ("local_llm", "ollama", "llamacpp"):
        return LocalLLMProvider()
    return MockAIProvider()
