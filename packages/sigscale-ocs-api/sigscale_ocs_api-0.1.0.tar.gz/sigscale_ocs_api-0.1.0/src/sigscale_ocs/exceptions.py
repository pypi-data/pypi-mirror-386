"""
Custom exceptions for the Sigscale OCS API wrapper.
"""

from typing import Any, Dict, Optional


class OCSAPIError(Exception):
    """Base exception for OCS API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(OCSAPIError):
    """401 Authentication Error."""

    pass


class BadRequestError(OCSAPIError):
    """400 Bad Request Error."""

    pass


class NotFoundError(OCSAPIError):
    """404 Not Found Error."""

    pass


class ServerError(OCSAPIError):
    """500 Internal Server Error."""

    pass
