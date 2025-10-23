from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union, Awaitable, Callable

from .auth import TokenProvider, OIDCClientCredentialsConfig, create_oidc_token_provider
from .http_client import build_auth_httpx_client_factory


@dataclass
class PalmaHttpClientConfig:
    endpoint: str  # e.g., https://api.example.com/mcp
    org_id: Optional[str] = None
    token_provider: Optional[TokenProvider] = None
    auth: Optional[OIDCClientCredentialsConfig] = None


class PalmaHttpClient:
    """High-level Palma client using MCP streamable HTTP transport.

    Users interact via simple methods and can ignore MCP entirely.
    """

    def __init__(self, config: PalmaHttpClientConfig):
        self.config = config
        self._session = None
        self._close_streams: Optional[Callable[[], Awaitable[None]]] = None
        self._token_provider = config.token_provider or (
            create_oidc_token_provider(config.auth) if config.auth else None
        )

    async def __aenter__(self):
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        httpx_factory = build_auth_httpx_client_factory(self.config.org_id, self._token_provider)
        self._stream_ctx = streamablehttp_client(self.config.endpoint, httpx_client_factory=httpx_factory)
        read_stream, write_stream, _get_session_id = await self._stream_ctx.__aenter__()
        self._close_streams = self._stream_ctx.__aexit__
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc, tb)
        if self._close_streams:
            await self._close_streams(exc_type, exc, tb)
        self._session = None
        self._close_streams = None

    # Public API
    async def list_tools(self):
        return await self._session.list_tools()

    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        return await self._session.call_tool(name, arguments)

    async def list_resources(self):
        return await self._session.list_resources()

    async def read_resource(self, uri: str):
        return await self._session.read_resource(uri)

    # Advanced access
    def get_mcp_session(self):
        return self._session


