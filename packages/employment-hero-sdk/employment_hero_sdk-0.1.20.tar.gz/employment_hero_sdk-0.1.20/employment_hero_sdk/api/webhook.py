from typing import Any, Dict, List, Optional

from .base import EmploymentHeroBase
from ..client import EmploymentHeroClient, EmploymentHeroAsyncClient
from ..models import WebHook


class Webhook(EmploymentHeroBase):
    """
    Manage webhook registrations for a business.

    Endpoint base:
      /api/v2/business/{businessId}/webhookregistrations
    """

    # Explicitly set endpoint to match Employment Hero API path
    endpoint: str = "webhookregistrations"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = WebHook(**self.data)

    # ---------- Convenience helpers (sync) ----------
    def find_by_uri(self, web_hook_uri: str) -> Optional["Webhook"]:
        """
        Return the first webhook registration that matches the given URI, if any.
        """
        uri_lower = (web_hook_uri or "").strip().lower()
        for item in self.list():
            candidate = (item.data or {}).get("webHookUri") or (item.data or {}).get("webhookUri")
            if isinstance(candidate, str) and candidate.strip().lower() == uri_lower:
                return item
        return None

    def ensure(
        self,
        *,
        web_hook_uri: str,
        description: str = "",
        secret: Optional[str] = None,
        is_paused: bool = False,
        headers: Optional[Dict[str, str]] = None,
        filters: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        """
        Ensure a webhook registration exists for the given URI. If it exists, update its
        settings; otherwise create it.
        """
        existing = self.find_by_uri(web_hook_uri)
        payload: Dict[str, Any] = {
            "description": description,
            # API docs show both minimal and full payloads; the server ignores unknowns
            "isPaused": is_paused,
            "secret": secret or "",
            "webHookUri": web_hook_uri,
        }
        if headers is not None:
            payload["headers"] = headers
        if filters is not None:
            payload["filters"] = filters
        if properties is not None:
            payload["properties"] = properties

        if existing and getattr(existing, "id", None):
            return self.update(existing.id, payload)
        return self.create(payload)

    def pause(self, resource_id: str) -> "Webhook":
        current = self.fetch(resource_id)
        body = dict(current.data)
        body["isPaused"] = True
        return self.update(resource_id, body)

    def resume(self, resource_id: str) -> "Webhook":
        current = self.fetch(resource_id)
        body = dict(current.data)
        body["isPaused"] = False
        return self.update(resource_id, body)

    def test(self, resource_id: str, *, filter: Optional[str] = None) -> Any:  # noqa: A002 (shadow builtins)
        """
        Trigger a webhook test for a registration id with an optional filter string.
        """
        url = self._build_url(resource_id=resource_id, suffix="test")
        params = {"filter": filter} if filter else None
        response = self.client._request("GET", url, params=params)  # type: ignore[arg-type]
        return response.json()

    def delete_all(self) -> None:
        """Delete all webhook registrations for the current business."""
        url = self._build_url()
        # DELETE without resource id clears all registrations
        self.client._request("DELETE", url)

    # ---------- Convenience helpers (async) ----------
    async def find_by_uri_async(self, web_hook_uri: str) -> Optional["Webhook"]:
        uri_lower = (web_hook_uri or "").strip().lower()
        for item in await self.list_async():
            candidate = (item.data or {}).get("webHookUri") or (item.data or {}).get("webhookUri")
            if isinstance(candidate, str) and candidate.strip().lower() == uri_lower:
                return item
        return None

    async def ensure_async(
        self,
        *,
        web_hook_uri: str,
        description: str = "",
        secret: Optional[str] = None,
        is_paused: bool = False,
        headers: Optional[Dict[str, str]] = None,
        filters: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        existing = await self.find_by_uri_async(web_hook_uri)
        payload: Dict[str, Any] = {
            "description": description,
            "isPaused": is_paused,
            "secret": secret or "",
            "webHookUri": web_hook_uri,
        }
        if headers is not None:
            payload["headers"] = headers
        if filters is not None:
            payload["filters"] = filters
        if properties is not None:
            payload["properties"] = properties

        if existing and getattr(existing, "id", None):
            return await self.update_async(existing.id, payload)
        return await self.create_async(payload)

    async def pause_async(self, resource_id: str) -> "Webhook":
        current = await self.fetch_async(resource_id)
        body = dict(current.data)
        body["isPaused"] = True
        return await self.update_async(resource_id, body)

    async def resume_async(self, resource_id: str) -> "Webhook":
        current = await self.fetch_async(resource_id)
        body = dict(current.data)
        body["isPaused"] = False
        return await self.update_async(resource_id, body)

    async def test_async(self, resource_id: str, *, filter: Optional[str] = None) -> Any:  # noqa: A002
        url = self._build_url(resource_id=resource_id, suffix="test")
        params = {"filter": filter} if filter else None
        response = await self.client._request("GET", url, params=params)  # type: ignore[arg-type]
        return response.json()

    async def delete_all_async(self) -> None:
        url = self._build_url()
        await self.client._request("DELETE", url)


