from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional, Union

import httpx

from .auth import TokenProvider, AccessToken


def build_auth_httpx_client_factory(
    org_id: Optional[str],
    token_provider: Optional[TokenProvider],
) -> Callable[..., httpx.AsyncClient]:
    """Return a factory compatible with mcp.streamablehttp_client(httpx_client_factory=...).

    The factory injects x-org-id and Authorization headers and retries once on 401.
    """

    def factory(headers: Optional[Dict[str, str]] = None, timeout: Any = None, auth: Any = None):
        merged_headers: Dict[str, str] = dict(headers or {})
        if org_id:
            merged_headers["x-org-id"] = org_id

        class AuthTransport(httpx.AsyncHTTPTransport):
            async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
                async def set_auth():
                    if token_provider is None:
                        return
                    provided = await token_provider()
                    if isinstance(provided, str):
                        request.headers["Authorization"] = f"Bearer {provided}"
                    else:
                        request.headers["Authorization"] = f"{provided.token_type} {provided.access_token}"

                # First attempt with possible token
                await set_auth()
                response = await super().handle_async_request(request)
                if response.status_code == 401 and token_provider is not None:
                    # refresh and retry once
                    await set_auth()
                    response = await super().handle_async_request(request)
                return response

        return httpx.AsyncClient(headers=merged_headers, timeout=timeout, auth=auth, transport=AuthTransport())

    return factory


