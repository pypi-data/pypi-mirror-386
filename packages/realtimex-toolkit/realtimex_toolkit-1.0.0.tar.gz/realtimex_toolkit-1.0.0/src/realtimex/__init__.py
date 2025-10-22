"""RealtimeX Internal Utilities - Lightweight library for LLM and credential management."""

__version__ = "0.1.0"

from realtimex.credentials import (
    CredentialBundle,
    CredentialManager,
    CredentialType,
    get_credential,
)
from realtimex.exceptions import (
    ApiError,
    AuthenticationError,
    ConnectionError,
    CredentialError,
    ProviderError,
    RateLimitError,
    RealtimeXError,
    ResourceNotFoundError,
    ServerError,
)
from realtimex.llm import LLMProviderManager, configure_provider, get_provider_env_vars

__all__ = [
    # Version
    "__version__",
    # Exceptions
    "ApiError",
    "AuthenticationError",
    "ConnectionError",
    "CredentialError",
    "ProviderError",
    "RateLimitError",
    "RealtimeXError",
    "ResourceNotFoundError",
    "ServerError",
    # LLM
    "LLMProviderManager",
    "configure_provider",
    "get_provider_env_vars",
    # Credentials
    "CredentialBundle",
    "CredentialManager",
    "CredentialType",
    "get_credential",
]
