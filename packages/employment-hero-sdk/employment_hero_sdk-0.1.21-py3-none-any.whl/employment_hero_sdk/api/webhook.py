from typing import Any, Dict, List, Optional, Sequence, Union

from .base import EmploymentHeroBase
from ..client import EmploymentHeroClient, EmploymentHeroAsyncClient
from ..models import WebHook


class WebhookEvents:
    """Known webhook event names and helpers."""
    BANK_ACCOUNT_DELETED = "BankAccountDeleted"
    BANK_ACCOUNT_UPDATED = "BankAccountUpdated"
    EMPLOYEE_CREATED = "EmployeeCreated"
    EMPLOYEE_RECURRING_DEDUCTION_DELETED = "EmployeeRecurringDeductionDeleted"
    EMPLOYEE_RECURRING_DEDUCTION_UPDATED = "EmployeeRecurringDeductionUpdated"
    EMPLOYEE_TERMINATED = "EmployeeTerminated"
    EMPLOYEE_UPDATED = "EmployeeUpdated"
    LEAVE_ENTITLEMENT_BALANCE_UPDATED = "LeaveEntitlementBalanceUpdated"
    LEAVE_REQUEST_APPROVED = "LeaveRequestApproved"
    LEAVE_REQUEST_CANCELLED = "LeaveRequestCancelled"
    LEAVE_REQUEST_CREATED = "LeaveRequestCreated"
    LEAVE_REQUEST_DECLINED = "LeaveRequestDeclined"
    LEAVE_REQUEST_UPDATED = "LeaveRequestUpdated"
    PAY_RUN_DELETED = "PayRunDeleted"
    PAY_RUN_FINALISED = "PayRunFinalised"
    PAY_RUN_INITIALISED = "PayRunInitialised"
    PAYMENT_SUMMARIES_PUBLISHED = "PaymentSummariesPublished"
    PAYMENT_SUMMARIES_UNPUBLISHED = "PaymentSummariesUnpublished"
    TIMESHEET_APPROVED = "TimesheetApproved"
    TIMESHEET_CREATED = "TimesheetCreated"
    TIMESHEET_DELETED = "TimesheetDeleted"
    TIMESHEET_REJECTED = "TimesheetRejected"
    TIMESHEET_UPDATED = "TimesheetUpdated"
    ALL = "*"

    @classmethod
    def all_events(cls) -> List[str]:
        return [
            cls.BANK_ACCOUNT_DELETED,
            cls.BANK_ACCOUNT_UPDATED,
            cls.EMPLOYEE_CREATED,
            cls.EMPLOYEE_RECURRING_DEDUCTION_DELETED,
            cls.EMPLOYEE_RECURRING_DEDUCTION_UPDATED,
            cls.EMPLOYEE_TERMINATED,
            cls.EMPLOYEE_UPDATED,
            cls.LEAVE_ENTITLEMENT_BALANCE_UPDATED,
            cls.LEAVE_REQUEST_APPROVED,
            cls.LEAVE_REQUEST_CANCELLED,
            cls.LEAVE_REQUEST_CREATED,
            cls.LEAVE_REQUEST_DECLINED,
            cls.LEAVE_REQUEST_UPDATED,
            cls.PAY_RUN_DELETED,
            cls.PAY_RUN_FINALISED,
            cls.PAY_RUN_INITIALISED,
            cls.PAYMENT_SUMMARIES_PUBLISHED,
            cls.PAYMENT_SUMMARIES_UNPUBLISHED,
            cls.TIMESHEET_APPROVED,
            cls.TIMESHEET_CREATED,
            cls.TIMESHEET_DELETED,
            cls.TIMESHEET_REJECTED,
            cls.TIMESHEET_UPDATED,
        ]


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
    @staticmethod
    def _normalize_filters(filters: Optional[Union[str, Sequence[str]]]) -> Optional[List[str]]:
        if filters is None:
            return None
        if isinstance(filters, str):
            if filters.strip() == WebhookEvents.ALL:
                return [WebhookEvents.ALL]
            return [filters.strip()]
        normalized: List[str] = []
        for f in filters:
            if isinstance(f, str) and f.strip():
                if f.strip() == WebhookEvents.ALL:
                    return [WebhookEvents.ALL]
                normalized.append(f.strip())
        return normalized
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
        filters: Optional[Union[str, Sequence[str]]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        """
        Ensure a webhook registration exists for the given URI. If it exists, update its
        settings; otherwise create it.
        """
        existing = self.find_by_uri(web_hook_uri)
        normalized_filters = self._normalize_filters(filters)

        if existing and getattr(existing, "id", None):
            # Preserve existing values when not provided
            payload: Dict[str, Any] = dict(existing.data)
            payload["description"] = description if description is not None else payload.get("description", "")
            payload["isPaused"] = is_paused if is_paused is not None else payload.get("isPaused", False)
            payload["webHookUri"] = web_hook_uri
            if secret is not None and secret != "":
                payload["secret"] = secret
            # Merge or replace filters/headers/properties only if provided
            if normalized_filters is not None:
                payload["filters"] = normalized_filters
            if headers is not None:
                payload["headers"] = headers
            if properties is not None:
                payload["properties"] = properties
            return self.update(existing.id, payload)

        # Create new registration
        payload: Dict[str, Any] = {
            "description": description,
            "isPaused": is_paused,
            "secret": secret or "",
            "webHookUri": web_hook_uri,
            "headers": headers or {},
            "properties": properties or {},
        }
        if normalized_filters is not None:
            payload["filters"] = normalized_filters
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

    def update_filters(self, resource_id: str, filters: Union[str, Sequence[str]]) -> "Webhook":
        current = self.fetch(resource_id)
        body = dict(current.data)
        body["filters"] = self._normalize_filters(filters)
        return self.update(resource_id, body)

    def ensure_all(
        self,
        *,
        web_hook_uri: str,
        description: str = "",
        secret: Optional[str] = None,
        is_paused: bool = False,
        headers: Optional[Dict[str, str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        return self.ensure(
            web_hook_uri=web_hook_uri,
            description=description,
            secret=secret,
            is_paused=is_paused,
            headers=headers,
            filters=WebhookEvents.ALL,
            properties=properties,
        )

    def ensure_events(
        self,
        *,
        web_hook_uri: str,
        events: Sequence[str],
        description: str = "",
        secret: Optional[str] = None,
        is_paused: bool = False,
        headers: Optional[Dict[str, str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        return self.ensure(
            web_hook_uri=web_hook_uri,
            description=description,
            secret=secret,
            is_paused=is_paused,
            headers=headers,
            filters=list(events),
            properties=properties,
        )

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
        filters: Optional[Union[str, Sequence[str]]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        existing = await self.find_by_uri_async(web_hook_uri)
        normalized_filters = self._normalize_filters(filters)

        if existing and getattr(existing, "id", None):
            payload: Dict[str, Any] = dict(existing.data)
            payload["description"] = description if description is not None else payload.get("description", "")
            payload["isPaused"] = is_paused if is_paused is not None else payload.get("isPaused", False)
            payload["webHookUri"] = web_hook_uri
            if secret is not None and secret != "":
                payload["secret"] = secret
            if normalized_filters is not None:
                payload["filters"] = normalized_filters
            if headers is not None:
                payload["headers"] = headers
            if properties is not None:
                payload["properties"] = properties
            return await self.update_async(existing.id, payload)

        payload = {
            "description": description,
            "isPaused": is_paused,
            "secret": secret or "",
            "webHookUri": web_hook_uri,
            "headers": headers or {},
            "properties": properties or {},
        }
        if normalized_filters is not None:
            payload["filters"] = normalized_filters
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

    async def update_filters_async(self, resource_id: str, filters: Union[str, Sequence[str]]) -> "Webhook":
        current = await self.fetch_async(resource_id)
        body = dict(current.data)
        body["filters"] = self._normalize_filters(filters)
        return await self.update_async(resource_id, body)

    async def ensure_all_async(
        self,
        *,
        web_hook_uri: str,
        description: str = "",
        secret: Optional[str] = None,
        is_paused: bool = False,
        headers: Optional[Dict[str, str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        return await self.ensure_async(
            web_hook_uri=web_hook_uri,
            description=description,
            secret=secret,
            is_paused=is_paused,
            headers=headers,
            filters=WebhookEvents.ALL,
            properties=properties,
        )

    async def ensure_events_async(
        self,
        *,
        web_hook_uri: str,
        events: Sequence[str],
        description: str = "",
        secret: Optional[str] = None,
        is_paused: bool = False,
        headers: Optional[Dict[str, str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> "Webhook":
        return await self.ensure_async(
            web_hook_uri=web_hook_uri,
            description=description,
            secret=secret,
            is_paused=is_paused,
            headers=headers,
            filters=list(events),
            properties=properties,
        )

    async def test_async(self, resource_id: str, *, filter: Optional[str] = None) -> Any:  # noqa: A002
        url = self._build_url(resource_id=resource_id, suffix="test")
        params = {"filter": filter} if filter else None
        response = await self.client._request("GET", url, params=params)  # type: ignore[arg-type]
        return response.json()

    async def delete_all_async(self) -> None:
        url = self._build_url()
        await self.client._request("DELETE", url)


