"""Thin async client for the photo frame's local REST API (see HomeAssistant.md)."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class PhotoFrameError(Exception):
    """Base error talking to a photo frame."""


class PhotoFrameAuthError(PhotoFrameError):
    """Raised on HTTP 401 — wrong username/password."""


class PhotoFrameConnectionError(PhotoFrameError):
    """Raised when the frame can't be reached at all."""


class PhotoFrameClient:
    """Talks to one frame's embedded HTTPS server.

    The frame always serves a self-signed certificate (there's no public DNS
    name to get a real one for), so callers must hand in a session created
    with ``verify_ssl=False``. The connection is still encrypted — this only
    skips validating who signed the certificate.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._base_url = f"https://{host}:{port}"
        self._auth = aiohttp.BasicAuth(username, password)

    async def async_get_status(self) -> dict[str, Any]:
        return await self._request("GET", "/api/status") or {}

    async def async_get_settings(self) -> dict[str, Any]:
        return await self._request("GET", "/api/settings") or {}

    async def async_set_brightness(self, value: float) -> None:
        await self._request("POST", "/api/brightness", params={"value": f"{value:.3f}"})

    async def async_set_settings(self, payload: dict[str, Any]) -> None:
        await self._request("POST", "/api/settings", json=payload)

    async def async_ping_presence(self) -> None:
        await self._request("POST", "/api/presence")

    async def async_set_display(self, action: str) -> None:
        await self._request("POST", "/api/display", params={"action": action})

    async def async_set_playback(self, action: str) -> None:
        await self._request("POST", "/api/playback", params={"action": action})

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=10),
                **kwargs,
            ) as response:
                if response.status == 401:
                    raise PhotoFrameAuthError("Invalid username or password")
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return None
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise PhotoFrameAuthError("Invalid username or password") from err
            raise PhotoFrameConnectionError(str(err)) from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PhotoFrameConnectionError(str(err)) from err
