from .client_http import PalmaHttpClient, PalmaHttpClientConfig
from .auth import AccessToken, OIDCClientCredentialsConfig, create_oidc_token_provider

# Advanced exports of underlying MCP pieces for power users
try:
    from mcp import ClientSession  # type: ignore
    from mcp.client.streamable_http import streamablehttp_client  # type: ignore
except Exception:  # pragma: no cover
    ClientSession = None  # type: ignore
    streamablehttp_client = None  # type: ignore

__all__ = [
    "PalmaHttpClient",
    "PalmaHttpClientConfig",
    "AccessToken",
    "OIDCClientCredentialsConfig",
    "create_oidc_token_provider",
    "ClientSession",
    "streamablehttp_client",
]
