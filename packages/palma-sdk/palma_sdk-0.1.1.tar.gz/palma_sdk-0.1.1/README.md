# Palma AI SDK (Python)

High-level Python SDK for the MCP Gateway. Provides an async context-managed client over HTTP that handles connection lifecycle, optional OIDC client-credentials tokens, and simple tool/resource calls.

## Installation

```bash
pip install palma-sdk
```

## Usage

```python
import os
from dotenv import load_dotenv
from palma_sdk import (
    PalmaHttpClient,
    PalmaHttpClientConfig,
    OIDCClientCredentialsConfig,
    create_oidc_token_provider,
)

load_dotenv()

token_provider = None
if os.getenv("AUTH0_DOMAIN"):
    token_provider = create_oidc_token_provider(
        OIDCClientCredentialsConfig(
            issuer=f"https://{os.getenv('AUTH0_DOMAIN')}",
            client_id=os.getenv("AUTH0_CLIENT_ID", ""),
            client_secret=os.getenv("AUTH0_CLIENT_SECRET", ""),
            audience=os.getenv("AUTH0_AUDIENCE"),
            scope=os.getenv("AUTH0_SCOPE"),
            sub=os.getenv("AUTH0_SUB"),
        )
    )

cfg = PalmaHttpClientConfig(
    endpoint=os.getenv("MCP_ENDPOINT", "http://localhost:3000/mcp"),
    org_id=os.getenv("MCP_ORG_ID"),
    token_provider=token_provider,
)

async def main():
    async with PalmaHttpClient(cfg) as client:
        tools = await client.list_tools()
        print("tools:", tools)
```

## Features

- Async context manager handles connect/initialize/cleanup
- Optional OIDC client-credentials token provider
- Tool and resource APIs (list, call, read)
- Type hints throughout

## License

MIT
