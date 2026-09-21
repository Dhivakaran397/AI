from .base import AIProvider
from .openai_provider import OpenAIProvider
from .google_provider import GoogleProvider
from app.config import settings

_providers = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
}


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Get an AI provider instance by name. Defaults to configured provider."""
    name = provider_name or settings.AI_PROVIDER
    provider_cls = _providers.get(name.lower())
    if not provider_cls:
        raise ValueError(f"AI provider '{name}' not found. Available: {list(_providers.keys())}")
    return provider_cls()
