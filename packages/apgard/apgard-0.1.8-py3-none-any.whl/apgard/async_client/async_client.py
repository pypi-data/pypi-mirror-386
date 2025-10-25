import logging
import httpx
from typing import Optional
from ..errors import APIError, ValidationError
from .async_moderation import AsyncModerationClient
from .async_breaks import AsyncBreakClient

logger = logging.getLogger("apgard")


class AsyncApgardClient:
    """Root client coordinating all Apgard API services."""

    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.apgardai.com",
        break_interval_minutes: int = 180,
        timeout: float = 30.0,
    ):
        if not api_key:
            raise ValidationError("API key required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.break_interval = break_interval_minutes

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        # Feature subclients
        self.moderation = AsyncModerationClient(self._client)
        self.breaks = AsyncBreakClient(self._client, break_interval_minutes)

    async def __aenter__(self):
        await self.verify()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def verify(self):
        """Verify API key validity."""
        try:
            resp = await self._client.get("/api/auth/verify")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise APIError("Invalid API key", 401)
            raise APIError(f"Verification failed: {e}", e.response.status_code)

    async def close(self):
        """Close the HTTP session."""
        await self._client.aclose()

    async def get_or_create_user(self, external_user_id: Optional[str] = None) -> str:
        payload = {
            "external_user_id": str(external_user_id) if external_user_id else None,
        }
        resp = await self._client.post("/api/end-users/get-or-create", json=payload)
        resp.raise_for_status()
        return resp.json()["user_id"]