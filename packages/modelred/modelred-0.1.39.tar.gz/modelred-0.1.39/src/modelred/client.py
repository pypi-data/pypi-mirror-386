from __future__ import annotations
import time
from typing import Any, Dict, Iterator, List, Literal, Optional
import httpx

from .errors import (
    APIError,
    Conflict,
    Forbidden,
    LimitExceeded,
    NotAllowedForApiKey,
    NotFound,
    RateLimited,
    ServerError,
    Unauthorized,
    ValidationFailed,
)
from . import __version__

# --- internals / constants ---
RETRYABLE_STATUSES = {429, 502, 503, 504}
BASE_URL = "https://www.app.modelred.ai"


def _user_agent(version: str) -> str:
    return f"modelred-python-sdk/{version}"


def _backoff_delays(max_retries: int, base: float = 0.5, cap: float = 8.0):
    import random

    for i in range(max_retries):
        delay = min(cap, base * (2**i))
        yield random.uniform(0, delay)


def _build_headers(
    api_key: Optional[str], ua: str, extra: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    h: Dict[str, str] = {"Accept": "application/json", "User-Agent": ua}
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
        h["x-api-key"] = api_key
    if extra:
        h.update(extra)
    return h


def _normalize_error_payload(data: Any):
    if not isinstance(data, dict):
        return ("Unknown error", None, None)
    message = str(data.get("error") or data.get("message") or "Unknown error")
    code = data.get("code")
    details = data.get("details")
    return (message, code, details)


def _compact(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys whose values are None (avoid sending nulls for optional fields)."""
    return {k: v for k, v in d.items() if v is not None}


# ----- public typing -----
StatusFilter = Literal["all", "QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
ProviderFilter = Literal[
    "all",
    "openai",
    "anthropic",
    "azure",
    "huggingface",
    "rest",
    "bedrock",
    "sagemaker",
    "google",
    "grok",
    "openrouter",
]
SortDir = Literal["asc", "desc"]


class ModelRed:
    """
    Synchronous ModelRed client (base URL fixed to https://www.app.modelred.ai).

    Args:
        api_key: Your ModelRed API key (mr_...).
        timeout: Request timeout (seconds).
        max_retries: Automatic retries for 429/5xx/transient transport issues.
        transport: Optional httpx transport for testing.
        extra_headers: Extra headers to include on all requests.

    Notes:
        • Do NOT pass organization id; backend derives it from the API key.
        • When creating assessments, you MUST provide:
            - detector_provider ("openai" | "anthropic")
            - detector_api_key (string)
            - detector_model (string)
          (base_url & organization are optional and only relevant for OpenAI edge cases)
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 20.0,
        max_retries: int = 3,
        transport: Optional[httpx.BaseTransport] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        if not api_key or not api_key.startswith("mr_"):
            raise ValueError("Valid API key (mr_...) is required")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._headers = _build_headers(api_key, _user_agent(__version__), extra_headers)
        self._client = httpx.Client(
            base_url=BASE_URL, timeout=self.timeout, transport=transport
        )

    # --- internals ---
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        json: Dict[str, Any] | None = None,
    ) -> Any:
        url = path if path.startswith("/") else f"/{path}"
        last_exc: Optional[Exception] = None
        for delay in [0.0, *list(_backoff_delays(self.max_retries))]:
            if delay:
                time.sleep(delay)
            try:
                resp = self._client.request(
                    method, url, headers=self._headers, params=params, json=json
                )
            except Exception as exc:
                last_exc = exc
                if isinstance(exc, httpx.TransportError):
                    continue
                raise
            if resp.status_code in RETRYABLE_STATUSES:
                continue
            if resp.status_code >= 400:
                self._raise_for_status(resp)
            if resp.headers.get("content-type", "").startswith("application/json"):
                return resp.json()
            return resp.text
        if isinstance(last_exc, Exception):
            raise last_exc
        raise RateLimited(429, "Request retry limit reached")

    def _raise_for_status(self, resp: httpx.Response) -> None:
        try:
            payload = resp.json()
        except Exception:
            payload = {"error": resp.text or resp.reason_phrase}
        message, code, details = _normalize_error_payload(payload)
        status = resp.status_code
        if status in (400, 422):
            raise ValidationFailed(status, message, code, details)
        if status == 401:
            raise Unauthorized(status, message, code, details)
        if status == 403:
            ml = (message or "").lower()
            if "plan" in ml or "limit" in ml:
                raise LimitExceeded(status, message, code, details)
            if "web ui" in ml or "requires web ui" in ml or "apikey" in ml:
                raise NotAllowedForApiKey(status, message, code, details)
            raise Forbidden(status, message, code, details)
        if status == 404:
            raise NotFound(status, message, code, details)
        if status == 409:
            raise Conflict(status, message, code, details)
        if status == 429:
            raise RateLimited(status, message, code, details)
        if 500 <= status <= 599:
            raise ServerError(status, message, code, details)
        raise APIError(status, message, code, details)

    # --- Assessments ---

    def _build_detector_payload(
        self,
        *,
        detector_provider: Literal["openai", "anthropic"],
        detector_api_key: str,
        detector_model: str,
        detector_base_url: Optional[str],
        detector_organization: Optional[str],
    ) -> Dict[str, Any]:
        if not detector_api_key:
            raise ValueError("detector_api_key is required")
        if detector_provider not in ("openai", "anthropic"):
            raise ValueError("detector_provider must be 'openai' or 'anthropic'")
        if not detector_model or not isinstance(detector_model, str):
            raise ValueError("detector_model is required (string)")

        if detector_provider == "openai":
            payload: Dict[str, Any] = {
                "provider": "openai",
                "model": detector_model,
                "apiKey": detector_api_key,
            }
            if detector_base_url:
                payload["baseUrl"] = detector_base_url
            if detector_organization:
                payload["organization"] = detector_organization
            return payload

        # anthropic
        return {
            "provider": "anthropic",
            "model": detector_model,
            "apiKey": detector_api_key,
        }

    def create_assessment(
        self,
        *,
        model: Optional[str] = None,
        model_id: Optional[str] = None,
        probe_pack_ids: List[str],
        priority: Literal["low", "normal", "high", "critical"] = "normal",
        # REQUIRED detector settings:
        detector_provider: Literal["openai", "anthropic"],
        detector_api_key: str,
        detector_model: str,
        # Optional detector fine-tuning (OpenAI edge cases):
        detector_base_url: Optional[str] = None,
        detector_organization: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an assessment.

        Provide either `model` (recommended) or `model_id`.
        You MUST provide:
          • detector_provider ("openai" | "anthropic")
          • detector_api_key
          • detector_model
        """
        if not (model or model_id):
            raise ValueError("Provide `model` (recommended) or `model_id`")
        if not probe_pack_ids:
            raise ValueError("At least one probe_pack_id is required")

        det_payload = self._build_detector_payload(
            detector_provider=detector_provider,
            detector_api_key=detector_api_key,
            detector_model=detector_model,
            detector_base_url=detector_base_url,
            detector_organization=detector_organization,
        )

        body = _compact(
            {
                "model": model,  # drop if None (avoid "model": null)
                "modelId": model_id,  # drop if None
                "probePackIds": probe_pack_ids,
                "priority": priority,
                "detectorConfig": det_payload,
            }
        )
        return self._request("POST", "/api/v2/assessments", json=body)

    def create_assessment_by_id(
        self,
        *,
        model_id: str,
        probe_pack_ids: List[str],
        priority: Literal["low", "normal", "high", "critical"] = "normal",
        detector_provider: Literal["openai", "anthropic"],
        detector_api_key: str,
        detector_model: str,
        detector_base_url: Optional[str] = None,
        detector_organization: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper for create_assessment with model_id."""
        return self.create_assessment(
            model_id=model_id,
            probe_pack_ids=probe_pack_ids,
            priority=priority,
            detector_provider=detector_provider,
            detector_api_key=detector_api_key,
            detector_model=detector_model,
            detector_base_url=detector_base_url,
            detector_organization=detector_organization,
        )

    def list_assessments(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: StatusFilter = "all",
        provider: ProviderFilter = "all",
        sort_by: str = "createdAt",
        sort_dir: SortDir = "desc",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "status": status,
            "provider": provider,
            "sortBy": sort_by,
            "sortDir": sort_dir,
        }
        if search:
            params["search"] = search
        return self._request("GET", "/api/v2/assessments", params=params)

    def iter_assessments(
        self, *, page_size: int = 50, **filters: Any
    ) -> Iterator[Dict[str, Any]]:
        page = 1
        while True:
            resp = self.list_assessments(page=page, page_size=page_size, **filters)
            items = resp.get("data", []) or []
            for i in items:
                yield i
            total_pages = resp.get("totalPages") or resp.get("pagination", {}).get(
                "totalPages"
            )
            if not total_pages or page >= total_pages:
                break
            page += 1

    def get_assessment(self, assessment_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v2/assessments/{assessment_id}")

    def cancel_assessment(self, assessment_id: str) -> Dict[str, Any]:
        try:
            return self._request(
                "PATCH",
                f"/api/v2/assessments/{assessment_id}",
                json={"action": "cancel"},
            )
        except Forbidden as e:
            # Map to specific error for SDK users (API keys not allowed to modify)
            raise NotAllowedForApiKey(
                e.status,
                e.message or "Assessment modification requires web UI",
                e.code,
                e.details,
            )

    # --- Models (list only) ---
    def list_models(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        provider: Optional[ProviderFilter] = None,
        status: Literal["active", "inactive", "both"] = "both",
        sort_by: str = "createdAt",
        sort_dir: SortDir = "desc",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "status": status,
            "sortBy": sort_by,
            "sortDir": sort_dir,
        }
        if search:
            params["search"] = search
        if provider:
            params["provider"] = provider
        return self._request("GET", "/api/models", params=params)

    def iter_models(
        self, *, page_size: int = 50, **filters: Any
    ) -> Iterator[Dict[str, Any]]:
        page = 1
        while True:
            resp = self.list_models(page=page, page_size=page_size, **filters)
            items = resp.get("data", []) or []
            for i in items:
                yield i
            total_pages = resp.get("totalPages") or resp.get("pagination", {}).get(
                "totalPages"
            )
            if not total_pages or page >= total_pages:
                break
            page += 1

    # --- Probes ---
    def list_owned_probes(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_public: Optional[bool] = None,
        sort_by: str = "createdAt",
        sort_dir: SortDir = "desc",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by,
            "sortDir": sort_dir,
        }
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if is_public is not None:
            params["isPublic"] = "true" if is_public else "false"
        return self._request("GET", "/api/v2/probes", params=params)

    def iter_owned_probes(
        self, *, page_size: int = 50, **filters: Any
    ) -> Iterator[Dict[str, Any]]:
        page = 1
        while True:
            resp = self.list_owned_probes(page=page, page_size=page_size, **filters)
            items = resp.get("data", []) or []
            for i in items:
                yield i
            total_pages = resp.get("totalPages") or resp.get("pagination", {}).get(
                "totalPages"
            )
            if not total_pages or page >= total_pages:
                break
            page += 1

    def list_imported_probes(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Literal[
            "importedAt", "name", "category", "probeCount", "promptCount"
        ] = "importedAt",
        sort_dir: SortDir = "desc",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by,
            "sortDir": sort_dir,
        }
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        return self._request("GET", "/api/v2/probes/imported", params=params)

    def iter_imported_probes(
        self, *, page_size: int = 50, **filters: Any
    ) -> Iterator[Dict[str, Any]]:
        page = 1
        while True:
            resp = self.list_imported_probes(page=page, page_size=page_size, **filters)
            items = resp.get("data", []) or []
            for i in items:
                yield i
            total_pages = resp.get("totalPages") or resp.get("pagination", {}).get(
                "totalPages"
            )
            if not total_pages or page >= total_pages:
                break
            page += 1

    def get_probe_pack(self, pack_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v2/probes/{pack_id}")

    def get_probe_pack_data(self, pack_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v2/probes/{pack_id}/data")

    # --- cleanup ---
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ModelRed":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
