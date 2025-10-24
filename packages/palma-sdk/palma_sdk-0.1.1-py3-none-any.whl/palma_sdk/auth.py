from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Union, Dict, Any
import time

import httpx


@dataclass
class AccessToken:
    access_token: str
    token_type: str = "Bearer"
    expires_at_ms: Optional[int] = None


@dataclass
class OIDCClientCredentialsConfig:
    issuer: str  # e.g., https://your-issuer-domain
    client_id: str
    client_secret: str
    audience: Optional[str] = None
    scope: Optional[str] = None
    sub: Optional[str] = None
    min_seconds_left: int = 30


TokenProvider = Callable[[], Awaitable[Union[AccessToken, str]]]


def create_oidc_token_provider(config: OIDCClientCredentialsConfig) -> TokenProvider:
    """Create an async token provider for OIDC client-credentials with simple caching."""
    cached: Optional[AccessToken] = None

    def _should_refresh(token: Optional[AccessToken]) -> bool:
        if token is None or token.expires_at_ms is None:
            return False
        return (time.time() * 1000) + (config.min_seconds_left * 1000) >= token.expires_at_ms

    async def _get() -> Union[AccessToken, str]:
        nonlocal cached
        if cached and not _should_refresh(cached):
            return cached

        data = {
            "grant_type": "client_credentials",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }
        if config.audience:
            data["audience"] = config.audience
        if config.scope:
            data["scope"] = config.scope
        if config.sub:
            data["sub"] = config.sub

        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{config.issuer.rstrip('/')}/oauth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            )
            res.raise_for_status()
            j = res.json()

        expires_in = int(j.get("expires_in", 3600))
        cached = AccessToken(
            access_token=str(j["access_token"]),
            token_type=str(j.get("token_type", "Bearer")),
            expires_at_ms=int(time.time() * 1000) + max(0, (expires_in - config.min_seconds_left) * 1000),
        )
        return cached

    return _get


