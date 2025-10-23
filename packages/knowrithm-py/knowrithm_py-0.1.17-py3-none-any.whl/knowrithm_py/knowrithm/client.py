



import time
import urllib.parse
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
        headers: Optional[Dict] = None
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
                    return {"success": True}
                
                try:
                    return response.json()
                except ValueError:
                    # Non-JSON responses are returned as raw text or bytes
                    return response.content if files else response.text
                
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

        while True:
            endpoint = self._normalize_status_endpoint(status_url)
            task_response = self._make_request("GET", endpoint, headers=poll_headers)

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
            if time.monotonic() >= deadline:
                raise KnowrithmAPIError(
                    "Timed out while waiting for asynchronous task to complete.",
                    response_data=task_response,
                )

            # Default to polling even when the status field is absent — older
            # implementations may omit it while the task is in-flight.
            time.sleep(poll_interval)

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
