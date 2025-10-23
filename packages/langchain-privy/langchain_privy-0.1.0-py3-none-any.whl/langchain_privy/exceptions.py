"""Custom exceptions for Privy API interactions."""

from typing import Optional


class PrivyError(Exception):
    """Base exception for all Privy-related errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize Privy error.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PrivyAPIError(PrivyError):
    """Exception raised when Privy API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Optional[dict] = None,
        request_id: Optional[str] = None,
    ):
        """Initialize API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code from the API
            response_body: Optional response body (sanitized)
            request_id: Optional request ID for debugging
        """
        super().__init__(message, details={"status_code": status_code})
        self.status_code = status_code
        self.response_body = response_body or {}
        self.request_id = request_id

    def __str__(self) -> str:
        """Format error message."""
        parts = [f"HTTP {self.status_code}: {self.message}"]
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return " | ".join(parts)


class PrivyAuthenticationError(PrivyAPIError):
    """Exception raised for authentication failures (401, 403)."""

    pass


class PrivyValidationError(PrivyAPIError):
    """Exception raised for invalid request parameters (400)."""

    pass


class PrivyNotFoundError(PrivyAPIError):
    """Exception raised when a resource is not found (404)."""

    pass


class PrivyRateLimitError(PrivyAPIError):
    """Exception raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        status_code: int,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        """Initialize rate limit error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (429)
            retry_after: Number of seconds to wait before retrying
            **kwargs: Additional arguments passed to PrivyAPIError
        """
        super().__init__(message, status_code, **kwargs)
        self.retry_after = retry_after

    def __str__(self) -> str:
        """Format error message."""
        base = super().__str__()
        if self.retry_after:
            return f"{base} | Retry after {self.retry_after} seconds"
        return base


class PrivyServerError(PrivyAPIError):
    """Exception raised for server errors (500, 502, 503, 504)."""

    pass


class PrivyNetworkError(PrivyError):
    """Exception raised for network-related errors (timeouts, connection errors)."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """Initialize network error.

        Args:
            message: Human-readable error message
            original_error: The original exception that caused this error
        """
        super().__init__(message, details={"original_error": str(original_error)})
        self.original_error = original_error


class PrivyConfigurationError(PrivyError):
    """Exception raised for configuration errors."""

    pass


def create_api_error(
    status_code: int,
    message: str,
    response_body: Optional[dict] = None,
    request_id: Optional[str] = None,
) -> PrivyAPIError:
    """Create the appropriate API error based on status code.

    Args:
        status_code: HTTP status code
        message: Error message
        response_body: Optional response body
        request_id: Optional request ID

    Returns:
        Appropriate PrivyAPIError subclass
    """
    if status_code == 400:
        return PrivyValidationError(message, status_code, response_body, request_id)
    elif status_code in (401, 403):
        return PrivyAuthenticationError(message, status_code, response_body, request_id)
    elif status_code == 404:
        return PrivyNotFoundError(message, status_code, response_body, request_id)
    elif status_code == 429:
        retry_after = None
        if response_body:
            retry_after = response_body.get("retry_after")
        return PrivyRateLimitError(
            message, status_code, retry_after=retry_after, response_body=response_body, request_id=request_id
        )
    elif status_code >= 500:
        return PrivyServerError(message, status_code, response_body, request_id)
    else:
        return PrivyAPIError(message, status_code, response_body, request_id)
