



import time
import urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional

import requests
from knowrithm_py.config.config import Config
from knowrithm_py.dataclass.config import KnowrithmConfig
from knowrithm_py.dataclass.error import KnowrithmAPIError

class KnowrithmClient:
    """
    Main client for interacting with the Knowrithm API using API Key authentication
    
    Example usage:
        # Initialize with API credentials
        client = KnowrithmClient(
            api_key="your_api_key_here",
            api_secret="your_api_secret_here",
            base_url="https://app.knowrithm.org"
        )
        
        # Create a company
        company = client.companies.create({
            "name": "Acme Corp",
            "email": "contact@acme.com"
        })
        
        # Create an agent
        agent = client.agents.create({
            "name": "Customer Support Bot",
            "company_id": company["id"]
        })
    """
    
    def __init__(self, api_key: str, api_secret: str, config: Optional[KnowrithmConfig] = None):
        """
        Initialize the client with API key and secret
        
        Args:
            api_key: Your API key
            api_secret: Your API secret
            config: Optional configuration object
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or KnowrithmConfig(base_url=Config.KNOWRITHM_BASE_URL)
        self._session = requests.Session()
        
        # Set up authentication headers
        self._setup_authentication()
        
        # Initialize service modules
        from knowrithm_py.services.address import AddressService
        from knowrithm_py.services.admin import AdminService
        from knowrithm_py.services.agent import AgentService
        from knowrithm_py.services.auth import ApiKeyService, AuthService, UserService
        from knowrithm_py.services.company import CompanyService
        from knowrithm_py.services.conversation import ConversationService, MessageService
        from knowrithm_py.services.dashboard import AnalyticsService
        from knowrithm_py.services.database import DatabaseService
        from knowrithm_py.services.document import DocumentService
        from knowrithm_py.services.settings import SettingsService
        from knowrithm_py.services.lead import LeadService
        from knowrithm_py.services.website import WebsiteService
        
        self.auth = AuthService(self)
        self.api_keys = ApiKeyService(self)
        self.users = UserService(self)
        self.companies = CompanyService(self)
        self.agents = AgentService(self)
        self.leads = LeadService(self)
        self.documents = DocumentService(self)
        self.databases = DatabaseService(self)
        self.websites = WebsiteService(self)
        self.conversations = ConversationService(self)
        self.messages = MessageService(self)
        self.analytics = AnalyticsService(self)
        self.settings = SettingsService(self)
        self.addresses = AddressService(self)
        self.admin = AdminService(self)
    
    def _setup_authentication(self):
        """Set up API key authentication headers"""
        self._session.headers.update({
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
        })
    
    @property
    def base_url(self) -> str:
        return f"{self.config.base_url}/{self.config.api_version}"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Any] = None,
        headers: Optional[Dict] = None,
        *,
        return_response: bool = False,
    ) -> Any:
        """Make HTTP request with error handling and retries"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Add content type for JSON requests
        if data and not files and "Content-Type" not in request_headers:
            request_headers['Content-Type'] = 'application/json'
        if files:
            # Let requests set the multipart boundary automatically.
            request_headers.pop("Content-Type", None)
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=data if data and not files else None,
                    data=data if files else None,
                    params=params,
                    files=files,
                    headers=request_headers,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                
                if response.status_code >= 400:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except ValueError:
                        error_data = {"detail": response.text}
                    
                    raise KnowrithmAPIError(
                        message=error_data.get("detail", error_data.get("message", f"HTTP {response.status_code}")),
                        status_code=response.status_code,
                        response_data=error_data,
                        error_code=error_data.get("error_code")
                    )
                
                # Return empty dict for successful requests with no content
                if not response.content:
                    payload: Any = {"success": True}
                else:
                    try:
                        payload = response.json()
                    except ValueError:
                        # Non-JSON responses are returned as raw text or bytes
                        payload = response.content if files else response.text

                if return_response:
                    return payload, response
                return payload
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise KnowrithmAPIError(f"Request failed after {self.config.max_retries} attempts: {str(e)}")
                time.sleep(self.config.retry_backoff_factor ** attempt)
        
        raise KnowrithmAPIError("Max retries exceeded")

    def _resolve_async_response(
        self,
        response: Any,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Resolve asynchronous task responses into their final payloads.

        Many POST/PUT/PATCH/DELETE endpoints now queue Celery tasks and return an
        acknowledgement payload shaped like::

            {
                "message": "...",
                "status": "accepted",
                "task_id": "...",
                "status_url": "/api/v1/tasks/<task_id>/status"
            }

        This helper polls ``status_url`` until the task completes (or fails) so
        that calling code continues to behave as it did when the APIs were
        synchronous.
        """
        if not isinstance(response, dict):
            return response

        status = str(response.get("status", "")).lower()
        status_url = response.get("status_url") or response.get("poll_url")
        if not status_url:
            task_id = response.get("task_id")
            if task_id:
                status_url = f"/{self.config.api_version}/tasks/{task_id}/status"

        if status_url and status in {"accepted", "queued", "pending"}:
            return self._poll_task_status(status_url, headers=headers)

        return response

    def _poll_task_status(
        self,
        status_url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Poll a Celery task status endpoint until completion or failure.
        """
        poll_interval = getattr(self.config, "task_poll_interval", 1.5)
        timeout_seconds = getattr(self.config, "task_poll_timeout", 180)
        deadline = time.monotonic() + timeout_seconds

        poll_headers: Optional[Dict[str, str]] = None
        if headers:
            poll_headers = dict(headers)
            poll_headers.pop("Content-Type", None)

        adaptive_interval = max(poll_interval, 0.1)
        max_interval = max(poll_interval * 6, poll_interval + 10.0)

        while True:
            endpoint = self._normalize_status_endpoint(status_url)
            task_response, http_response = self._make_request(
                "GET",
                endpoint,
                headers=poll_headers,
                return_response=True,
            )

            if not isinstance(task_response, dict):
                return task_response

            task_status = str(task_response.get("status", "")).lower()

            if task_status in {"completed", "success", "succeeded", "finished", "done"}:
                if "result" in task_response and task_response["result"] is not None:
                    return task_response["result"]
                if "data" in task_response and task_response["data"] is not None:
                    return task_response["data"]
                # Some task endpoints return the payload in ``response`` or reuse
                # the full dictionary.
                if "response" in task_response and task_response["response"] is not None:
                    return task_response["response"]
                return task_response

            if task_status in {"failed", "error", "rejected"}:
                error_payload = task_response.get("error")
                message = None
                error_code = None
                if isinstance(error_payload, dict):
                    message = error_payload.get("message")
                    error_code = error_payload.get("code")
                elif isinstance(error_payload, str):
                    message = error_payload
                raise KnowrithmAPIError(
                    message or "Asynchronous task failed.",
                    response_data=task_response,
                    error_code=error_code,
                )

            # If the task is still running, ensure we have not exceeded the timeout.
            now = time.monotonic()
            if now >= deadline:
                raise KnowrithmAPIError(
                    "Timed out while waiting for asynchronous task to complete.",
                    response_data=task_response,
                )

            next_status_url = task_response.get("status_url") or task_response.get("poll_url")
            if next_status_url:
                status_url = str(next_status_url)

            wait_seconds = self._determine_poll_delay(task_response, http_response)

            if wait_seconds is None:
                wait_seconds = adaptive_interval
                adaptive_interval = min(max_interval, max(poll_interval, adaptive_interval * 1.5))
            else:
                adaptive_interval = max(poll_interval, 0.1)
                wait_seconds = max(wait_seconds, 0.1)

            time_remaining = deadline - now
            if time_remaining <= 0:
                raise KnowrithmAPIError(
                    "Timed out while waiting for asynchronous task to complete.",
                    response_data=task_response,
                )

            # Default to polling even when the status field is absent — older
            # implementations may omit it while the task is in-flight.
            time.sleep(min(wait_seconds, time_remaining))

    def _normalize_status_endpoint(self, status_url: str) -> str:
        """
        Convert a status URL (absolute or relative) into a client-relative endpoint.
        """
        if not status_url:
            raise ValueError("status_url is required to poll task status.")

        parsed = urllib.parse.urlsplit(status_url)
        path = parsed.path or status_url

        # Remove any leading base URL components.
        for prefix in (
            self.base_url,
            self.config.base_url,
            f"{self.config.base_url.rstrip('/')}/{self.config.api_version}",
        ):
            if prefix and path.startswith(prefix):
                path = path[len(prefix):]

        if path.startswith("/"):
            cleaned = path
        else:
            cleaned = f"/{path}"

        api_prefix = f"/api/{self.config.api_version}"
        version_prefix = f"/{self.config.api_version}"

        if cleaned.startswith(api_prefix):
            cleaned = cleaned[len(f"/api"):]
        if cleaned.startswith(version_prefix):
            cleaned = cleaned[len(version_prefix):]
            if not cleaned.startswith("/"):
                cleaned = f"/{cleaned}"

        return cleaned or "/"

    def _determine_poll_delay(
        self,
        task_response: Dict[str, Any],
        http_response: Optional[requests.Response],
    ) -> Optional[float]:
        """
        Inspect server responses for an explicit polling cadence.
        """
        hints: list[float] = []

        if http_response is not None:
            header_hint = self._parse_retry_after_header(http_response.headers.get("Retry-After"))
            if header_hint is not None:
                hints.append(header_hint)

        containers = [task_response]
        for key in ("meta", "metadata", "details", "info"):
            value = task_response.get(key)
            if isinstance(value, dict):
                containers.append(value)

        duration_keys = (
            "retry_after",
            "retry_after_seconds",
            "retry_after_ms",
            "poll_after",
            "poll_after_seconds",
            "poll_after_ms",
            "poll_in",
            "poll_interval",
            "refresh_in",
            "wait_for",
            "wait_for_seconds",
            "next_poll_in",
        )

        datetime_keys = (
            "retry_at",
            "next_poll_at",
            "eta",
            "available_at",
            "scheduled_for",
        )

        for container in containers:
            for key in duration_keys:
                seconds = self._coerce_duration_seconds(container.get(key) if isinstance(container, dict) else None, key)
                if seconds is not None:
                    hints.append(seconds)
            for key in datetime_keys:
                seconds = self._seconds_until(container.get(key) if isinstance(container, dict) else None)
                if seconds is not None:
                    hints.append(seconds)

        if hints:
            return max(0.0, max(hints))
        return None

    @staticmethod
    def _parse_retry_after_header(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        try:
            return max(0.0, float(text))
        except ValueError:
            moment = KnowrithmClient._parse_datetime_string(text)
            if moment is None:
                return None
            now = datetime.now(tz=moment.tzinfo or timezone.utc)
            return max(0.0, (moment - now).total_seconds())

    @staticmethod
    def _coerce_duration_seconds(value: Any, field_name: Optional[str] = None) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            seconds = float(value)
        elif isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                seconds = float(stripped)
            except ValueError:
                return None
        else:
            return None

        key_hint = (field_name or "").lower()
        if "ms" in key_hint or "millis" in key_hint:
            seconds /= 1000.0
        return max(0.0, seconds)

    @staticmethod
    def _seconds_until(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, datetime):
            target = value
        elif isinstance(value, (int, float)):
            target = datetime.fromtimestamp(float(value), tz=timezone.utc)
        elif isinstance(value, str):
            target = KnowrithmClient._parse_datetime_string(value)
            if target is None:
                return None
        else:
            return None

        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=target.tzinfo or timezone.utc)
        return max(0.0, (target - now).total_seconds())

    @staticmethod
    def _parse_datetime_string(value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        try:
            iso_candidate = text.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_candidate)
        except ValueError:
            try:
                dt = parsedate_to_datetime(text)
            except (TypeError, ValueError):
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
