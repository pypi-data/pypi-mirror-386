"""
Base OCS client for API interactions.
"""

import os
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from dotenv import load_dotenv

from .exceptions import (
    OCSAPIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    ServerError,
)

# Load environment variables
load_dotenv()


class OCSClient:
    """Base client for Sigscale OCS API interactions."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        """
        Initialize the OCS client.

        Args:
            base_url: OCS API base URL
            username: API username
            password: API password
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url or os.getenv("SIGSCALE_OCS_URL")
        self.username = username or os.getenv("SIGSCALE_OCS_USERNAME")
        self.password = password or os.getenv("SIGSCALE_OCS_PASSWORD")
        self.verify_ssl = (
            verify_ssl
            if verify_ssl is not None
            else os.getenv("SIGSCALE_OCS_VERIFY_SSL", "true").lower() == "true"
        )

        if not self.base_url:
            raise ValueError(
                "Base URL is required. Set SIGSCALE_OCS_URL environment "
                "variable or pass base_url parameter."
            )
        if not self.username or not self.password:
            raise ValueError(
                "Username and password are required. Set "
                "SIGSCALE_OCS_USERNAME and SIGSCALE_OCS_PASSWORD environment "
                "variables or pass them as parameters."
            )

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = self.verify_ssl
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if self.base_url is None:
            raise ValueError("Base URL is not set")
        return urljoin(self.base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
            # Handle empty responses
            if not response.content:
                return {}
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code
            error_data: Optional[Dict[str, Any]] = None
            try:
                error_data = response.json()
                error_message = error_data.get("message", str(e))
            except ValueError:
                error_message = str(e)

            if status_code == 401:
                raise AuthenticationError(error_message, status_code, error_data or {})
            elif status_code == 400:
                raise BadRequestError(error_message, status_code, error_data or {})
            elif status_code == 404:
                raise NotFoundError(error_message, status_code, error_data or {})
            elif status_code >= 500:
                raise ServerError(error_message, status_code, error_data or {})
            else:
                raise OCSAPIError(error_message, status_code, error_data or {})

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request to API endpoint."""
        url = self._build_url(endpoint)
        response = self.session.get(url, params=params)
        return self._handle_response(response)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make POST request to API endpoint."""
        url = self._build_url(endpoint)
        response = self.session.post(url, json=data)
        return self._handle_response(response)

    def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make PATCH request to API endpoint."""
        url = self._build_url(endpoint)
        response = self.session.patch(url, json=data)
        return self._handle_response(response)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request to API endpoint."""
        url = self._build_url(endpoint)
        response = self.session.delete(url)
        return self._handle_response(response)

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self) -> "OCSClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
