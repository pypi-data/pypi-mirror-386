"""
Low-level HTTP client used internally by the SDK.

This module provides the APIClient class that handles all HTTP communication
with the Circuit backend, including authentication, request/response logging,
and error handling.
"""

import json
import os
from pathlib import Path
from typing import Any, TypeVar

import requests
from pydantic import BaseModel

from .types.config import API_BASE_URL_DEPLOYED, API_BASE_URL_LOCAL, SDKConfig

T = TypeVar("T", bound=BaseModel)


class APIError(Exception):
    """
    Custom exception for API errors that includes structured error details.

    Attributes:
        message: Detailed error message from API (or None if not provided)
        error: Short error category/title from API (or None if not provided)
        error_details: Full error response from API
        status_code: HTTP status code (if available)
    """

    def __init__(
        self,
        message: str | None = None,
        error: str | None = None,
        error_details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ):
        # Use message if available, otherwise error, otherwise generic message
        display_message = message or error or "API request failed"
        super().__init__(display_message)
        self.message = message
        self.error = error
        self.error_details = error_details or {}
        self.status_code = status_code

    def __str__(self) -> str:
        """Returns the most detailed error information available."""
        result = self.message or self.error or "API request failed"
        return str(result)

    @property
    def error_message(self) -> str:
        """
        Convenience property that returns the most useful error string.
        Prioritizes message (detailed) over error (category).
        Always returns a string, converting dicts/objects to JSON if needed.
        """
        # Prioritize message, then error, then default
        result = self.message or self.error or "API request failed"
        return str(result)


class APIClient:
    """
    Low-level HTTP client used internally by the SDK.

    - Automatically detects Lambda environment and uses VPC proxy
    - Falls back to HTTP requests for local development with session token auth
    - Adds session ID and agent slug headers automatically

    Authentication:
    - Lambda environments: No additional auth needed (VPC proxy handles it)
    - Local development: Session token from CLI auth config if available
    - Always includes session ID and agent slug headers for validation

    Although this class can be used directly, most users should interact with
    higher-level abstractions like AgentSdk and AgentUtils.

    Example:
        ```python
        from agent_sdk import SDKConfig
        from agent_sdk.client import APIClient

        config = SDKConfig(session_id=123)
        client = APIClient(config)

        # Make authenticated requests
        response = client.post("/v1/logs", [{"type": "observe", "shortMessage": "test"}])
        ```
    """

    def __init__(self, config: SDKConfig) -> None:
        """
        Create an API client.

        Args:
            config: SDK configuration containing session ID, base URL, and other settings
        """
        self.config = config
        self.base_url = config.base_url or self._get_default_base_url()

    def _is_lambda_environment(self) -> bool:
        """Check if running in AWS Lambda environment."""
        # Check for Lambda-specific environment variables
        return (
            os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
            or os.environ.get("LAMBDA_TASK_ROOT") is not None
            or os.environ.get("AWS_EXECUTION_ENV") is not None
        )

    def _get_default_base_url(self) -> str:
        """Get default base URL based on environment."""
        if self._is_lambda_environment():
            # Use internal VPC URL for Lambda agents
            return API_BASE_URL_DEPLOYED
        else:
            # Default to local development URL
            return API_BASE_URL_LOCAL

    def _get_auth_headers(self) -> dict[str, str]:
        """
        Generate authentication headers for requests.

        Authentication priority:
        1. Circuit environment: No Authorization header (VPC proxy handles auth)
        2. Authorization header from request: Use if provided
        3. Filesystem lookup: Fall back to local auth config

        Returns:
            Dictionary of headers to include in requests
        """
        headers: dict[str, str] = {}

        # Always include session ID header
        if self.config.session_id:
            headers["X-Session-Id"] = str(self.config.session_id)

        # Include agent slug if available (for deployed agents)
        agent_slug = self._get_agent_slug()
        if agent_slug:
            headers["X-Agent-Slug"] = agent_slug

        # For Lambda environments, we don't need additional auth
        # as the proxy handles Cloudflare Access authentication
        if self._is_lambda_environment():
            return headers

        # Use Authorization header from incoming request if provided
        if self.config.authorization_header:
            headers["Authorization"] = self.config.authorization_header
            return headers

        # Fall back to local development session token
        try:
            auth_config = self._load_auth_config()
            if auth_config and auth_config.get("sessionToken"):
                headers["Authorization"] = f"Bearer {auth_config['sessionToken']}"
        except Exception:
            # Auth config not available, continue without auth
            pass

        return headers

    def _get_agent_slug(self) -> str | None:
        """Get agent slug from environment variables."""
        # Check for agent slug in environment variables
        return os.environ.get("CIRCUIT_AGENT_SLUG")

    def _load_auth_config(self) -> dict[str, Any] | None:
        """
        Try to load auth config from the same location the CLI uses.

        Returns:
            Auth configuration dictionary or None if not available
        """
        # Try main config directory first
        try:
            home = Path.home()
            auth_path = home / ".config" / "circuit" / "auth.json"

            if auth_path.exists():
                with open(auth_path, encoding="utf-8") as f:
                    main_data: dict[str, Any] = json.load(f)
                    return main_data
        except Exception:
            # Auth config not available in main directory
            pass

        # Try fallback directory
        try:
            home = Path.home()
            auth_path = home / ".circuit" / "auth.json"

            if auth_path.exists():
                with open(auth_path, encoding="utf-8") as f:
                    fallback_data: dict[str, Any] = json.load(f)
                    return fallback_data
        except Exception:
            # Auth config not available in fallback directory
            pass

        return None

    def _mask_sensitive_data(self, data: Any) -> Any:
        """
        Mask sensitive information in data structures.

        Args:
            data: Data to mask

        Returns:
            Data with sensitive information masked
        """
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key.lower() in ["authorization", "x-api-key", "bearer", "token"]:
                    if isinstance(value, str) and len(value) > 8:
                        # Show first 8 characters and mask the rest
                        masked_data[key] = f"{value[:8]}...***MASKED***"
                    else:
                        masked_data[key] = "***MASKED***"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

    def _log(self, log: str, data: Any = None) -> None:
        """Internal logging - currently a no-op."""
        # Internal client logging removed for simplicity
        pass

    def _make_request(
        self, method: str, endpoint: str, data: Any = None
    ) -> dict[str, Any] | list[Any]:
        """
        Perform a JSON HTTP request.

        Automatically attaches auth headers.
        Raises helpful errors when the HTTP response is not ok.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API path beginning with /v1/...
            data: Optional JSON payload to serialize

        Returns:
            Parsed JSON response

        Raises:
            requests.RequestException: When response.ok is False or other HTTP errors
        """
        url = f"{self.base_url}{endpoint}"

        auth_headers = self._get_auth_headers()
        default_headers = {
            "Content-Type": "application/json",
            **auth_headers,
        }

        # Prepare request data
        json_data = None
        if data is not None:
            if isinstance(data, BaseModel):
                # Use mode='json' for proper JSON serialization with by_alias for field name mapping
                # Use exclude_unset=True to omit fields never set (for .optional() in schemas)
                # Keep fields explicitly set to None for .nullable() fields that require null
                json_data = data.model_dump(
                    mode="json", by_alias=True, exclude_unset=True
                )
            else:
                json_data = data

        # Log request summary
        request_summary = {
            "method": method,
            "url": url,
            "headers": default_headers,
            "body": json_data,
            "session_id": self.config.session_id,
            "environment": self._get_environment_info(),
        }
        self._log(f"HTTP {method} {endpoint}", request_summary)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=default_headers,
                json=json_data,
                timeout=900,
            )

            # Log response summary
            response_summary = {
                "status": response.status_code,
                "status_text": response.reason,
                "headers": dict(response.headers),
            }

            if not response.ok:
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {}

                response_summary["error_data"] = error_data
                self._log(f"HTTP {response.status_code} ERROR", response_summary)

                # Raise custom exception with full error details from API
                # Ensure message and error are always strings, not dicts
                raw_message = error_data.get("message")
                raw_error = error_data.get("error")

                # Convert to strings if they're dicts/objects
                message_str = (
                    json.dumps(raw_message)
                    if isinstance(raw_message, dict)
                    else str(raw_message)
                    if raw_message is not None
                    else None
                )
                error_str = (
                    json.dumps(raw_error)
                    if isinstance(raw_error, dict)
                    else str(raw_error)
                    if raw_error is not None
                    else None
                )

                raise APIError(
                    message=message_str,
                    error=error_str,
                    error_details=error_data if error_data else {},
                    status_code=response.status_code,
                )

            response_data: dict[str, Any] | list[Any] = response.json()
            response_summary["response_data"] = response_data
            self._log(f"HTTP {response.status_code} SUCCESS", response_summary)

            return response_data

        except APIError:
            # Re-raise our custom API errors as-is
            raise
        except requests.RequestException as e:
            # Wrap other request exceptions (network errors, timeouts, etc.)
            self._log("REQUEST EXCEPTION", {"error": str(e), "endpoint": endpoint})
            raise APIError(
                message=str(e),
                error="Request failed",
                error_details={"type": type(e).__name__},
            ) from e

    def _get_environment_info(self) -> str:
        """Get human-readable environment information."""
        if self._is_lambda_environment():
            return "Circuit (using VPC proxy)"
        else:
            return "Local Development"

    def get(self, endpoint: str) -> dict[str, Any] | list[Any]:
        """
        HTTP GET convenience method.

        Args:
            endpoint: API path beginning with /v1/...

        Returns:
            Parsed JSON response
        """
        return self._make_request("GET", endpoint)

    def post(self, endpoint: str, data: Any = None) -> dict[str, Any] | list[Any]:
        """
        HTTP POST convenience method sending a JSON body.

        Args:
            endpoint: API path beginning with /v1/...
            data: Optional JSON payload to serialize

        Returns:
            Parsed JSON response
        """
        return self._make_request("POST", endpoint, data)

    def delete(self, endpoint: str) -> dict[str, Any] | list[Any]:
        """
        HTTP DELETE convenience method.

        Args:
            endpoint: API path beginning with /v1/...

        Returns:
            Parsed JSON response
        """
        return self._make_request("DELETE", endpoint)
