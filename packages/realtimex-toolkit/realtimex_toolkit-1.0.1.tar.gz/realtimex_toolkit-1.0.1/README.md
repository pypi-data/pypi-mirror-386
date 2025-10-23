# RealtimeX Internal Utilities

Lightweight internal library providing utilities for LLM provider configuration and credential management across RealtimeX internal services.

## Installation

```bash
# Using uv (recommended)
uv pip install -e /path/to/realtimex-toolkit

# Using pip
pip install -e /path/to/realtimex-toolkit
```

## Quick Start

### LLM Provider Configuration

```python
from realtimex import configure_provider, get_provider_env_vars

# Configure provider (sets environment variables)
env_vars = configure_provider("openai")

# Get provider env vars without setting them
env_vars = get_provider_env_vars("openai")

# With explicit providers
env_vars = configure_provider(
    "openai",
    providers={"openai": {"OPEN_AI_KEY": "sk-..."}}
)
```

### Credential Management

Retrieve encrypted credentials from the RealtimeX app backend and decrypt them for use across RealtimeX ecosystem services.

```python
from realtimex import get_credential

# Simplest usage - just the credential ID
# Connects to local RealtimeX backend (http://localhost:3001) by default
credential = await get_credential("credential-id")
print(credential["payload"])  # {"name": "API_KEY", "value": "secret-value"}

# With API key for authenticated requests
credential = await get_credential("credential-id", api_key="service-api-key")

# With custom backend URL (for non-default configurations)
credential = await get_credential(
    "credential-id",
    api_key="service-api-key",
    base_url="http://custom-host:3001"  # Override default localhost:3001
)

# For long-running services, use CredentialManager directly
from realtimex import CredentialManager

# Connects to http://localhost:3001 by default
manager = CredentialManager(api_key="service-api-key")
try:
    bundle = await manager.get("credential-id")
    # Credentials are cached automatically
    bundle_again = await manager.get("credential-id")  # Returns cached

    # Force refresh from backend
    fresh_bundle = await manager.get("credential-id", force_refresh=True)
finally:
    await manager.close()
```

**Configuration:**
- `base_url`: Base URL of the RealtimeX app backend (default: `http://localhost:3001`)
- `api_key`: Authentication token for backend API requests (optional)
- Credentials are encrypted using AES-256-CBC and decrypted using keys from `~/.realtimex.ai/Resources/server/.env.development`

**Return shape (`get_credential`):**

```python
{
    "credential_id": str,
    "name": str,
    "credential_type": str,
    "payload": dict[str, str],
    "metadata": dict | None,
    "updated_at": str | None,
}
```

## Supported LLM Providers

- **Major Providers**: OpenAI, Anthropic, Azure OpenAI
- **Cloud AI**: Google Gemini, AWS Bedrock
- **Alternative APIs**: Groq, Cohere, Mistral, Perplexity
- **Open Source Aggregators**: Open Router, Together AI, Fireworks AI
- **Emerging**: DeepSeek, xAI, Novita
- **Local Deployment**: Ollama, LocalAI, LM Studio, KoboldCPP
- **Custom**: Generic OpenAI, LiteLLM, Nvidia NIM, Hugging Face

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy src/realtimex

# Format & lint
ruff check src/realtimex tests
ruff format src/realtimex tests
```

## Architecture

- **`realtimex.llm`**: LLM provider configuration utilities
- **`realtimex.credentials`**: Secure credential retrieval and decryption
- **`realtimex.api`**: HTTP client with retry logic and error mapping
- **`realtimex.utils`**: Internal utilities (path resolution, logging)

## License

Proprietary - Internal use only
