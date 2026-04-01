import time
from typing import Any, Dict, Optional

import requests
from rich.console import Console

from meta_cli.models.responses import GraphError

BASE_URL = "https://graph.facebook.com/v20.0"
RATE_LIMIT_CODES = {4, 17, 613}

console = Console(stderr=True)


class GraphAPIError(Exception):
    def __init__(self, message: str, code: int, error_type: str, fbtrace_id: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_type = error_type
        self.fbtrace_id = fbtrace_id


class AuthError(GraphAPIError):
    pass


class RateLimitError(GraphAPIError):
    def __init__(self, message: str, code: int, error_type: str,
                 fbtrace_id: Optional[str] = None, retry_after: Optional[float] = None):
        super().__init__(message, code, error_type, fbtrace_id)
        self.retry_after = retry_after


class NotFoundError(GraphAPIError):
    pass


class GraphClient:
    def __init__(self, access_token: str, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

    def _build_url(self, path: str) -> str:
        return f"{BASE_URL}{path}" if path.startswith("/") else f"{BASE_URL}/{path}"

    def _parse_error(self, response: requests.Response) -> GraphAPIError:
        retry_after = None
        try:
            raw = response.json().get("error", {})
            error = GraphError.model_validate(raw)
        except Exception:
            return GraphAPIError(
                message=f"HTTP {response.status_code}",
                code=response.status_code,
                error_type="HTTPError",
            )

        if response.status_code == 404:
            return NotFoundError(error.message, error.code, error.type, error.fbtrace_id)

        if error.code == 190:
            return AuthError(error.message, error.code, error.type, error.fbtrace_id)

        if error.code in RATE_LIMIT_CODES:
            raw_retry = response.headers.get("Retry-After")
            if raw_retry:
                try:
                    retry_after = float(raw_retry)
                except ValueError:
                    pass
            return RateLimitError(error.message, error.code, error.type, error.fbtrace_id, retry_after)

        return GraphAPIError(error.message, error.code, error.type, error.fbtrace_id)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            body = response.json()
        except Exception:
            response.raise_for_status()
            return {}

        if "error" in body:
            raise self._parse_error(response)

        if not response.ok:
            raise self._parse_error(response)

        return body

    def _request_with_retry(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = self._build_url(path)
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                return self._handle_response(response)
            except RateLimitError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = e.retry_after or min(2 ** attempt * 2.0, 60.0)
                with console.status(f"[yellow]Rate limited. Retrying in {wait:.0f}s...[/yellow]"):
                    time.sleep(wait)

        raise GraphAPIError("Max retries exceeded", code=0, error_type="RetryError")

    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self._request_with_retry("GET", path, params=params)

    def post(self, path: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        return self._request_with_retry("POST", path, json=json)
