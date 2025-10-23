"""Utility functions for Privy API interactions."""

import logging
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from langchain_privy.exceptions import (
    PrivyNetworkError,
    PrivyServerError,
    create_api_error,
)

# Configure logger
logger = logging.getLogger(__name__)


def sanitize_error_message(error: Exception, include_details: bool = False) -> str:
    """Sanitize error messages to remove sensitive information.

    Args:
        error: The exception to sanitize
        include_details: Whether to include non-sensitive details

    Returns:
        Sanitized error message safe for logging/display
    """
    error_str = str(error)

    # Remove any potential credentials or tokens
    sensitive_patterns = [
        "Bearer ",
        "Basic ",
        "Authorization:",
        "privy-app-secret",
        "app_secret",
        "PRIVY_APP_SECRET",
    ]

    for pattern in sensitive_patterns:
        if pattern in error_str:
            # Truncate message before sensitive data
            error_str = error_str.split(pattern)[0] + "[REDACTED]"
            break

    return error_str


def _is_retryable_error(exception: Exception) -> bool:
    """Determine if an error is retryable.

    Args:
        exception: The exception to check

    Returns:
        True if the error should be retried
    """
    # Retry network errors
    if isinstance(exception, (requests.Timeout, requests.ConnectionError)):
        return True

    # Retry server errors (5xx)
    if isinstance(exception, PrivyServerError):
        return True

    # Don't retry client errors (4xx) except rate limits
    return False


# Retry configuration for API calls
retry_api_call = retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError, PrivyServerError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying API call (attempt {retry_state.attempt_number}/3)",
        extra={
            "attempt": retry_state.attempt_number,
            "error": sanitize_error_message(retry_state.outcome.exception()),
        },
    ),
)


def handle_response(response: requests.Response) -> dict[str, Any]:
    """Handle API response and raise appropriate exceptions.

    Args:
        response: The HTTP response object

    Returns:
        Parsed JSON response

    Raises:
        PrivyAPIError: For various API error conditions
        PrivyNetworkError: For network-related errors
    """
    request_id = response.headers.get("x-request-id")

    try:
        response_body = response.json() if response.content else {}
    except ValueError:
        response_body = {"error": "Invalid JSON response"}

    if response.ok:
        logger.debug(
            "API call successful",
            extra={
                "status_code": response.status_code,
                "request_id": request_id,
                "url": response.url,
            },
        )
        return response_body

    # Extract error message
    error_message = response_body.get("error", response_body.get("message", "Unknown error"))

    # Log error (sanitized)
    logger.error(
        f"API error: {error_message}",
        extra={
            "status_code": response.status_code,
            "request_id": request_id,
            "url": response.url,
        },
    )

    # Create and raise appropriate exception
    error = create_api_error(
        status_code=response.status_code,
        message=error_message,
        response_body=response_body,
        request_id=request_id,
    )
    raise error


def make_api_request(
    method: str,
    url: str,
    session: requests.Session,
    headers: dict[str, str],
    timeout: int,
    **kwargs,
) -> dict[str, Any]:
    """Make an API request with retry logic and error handling.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to request
        session: Requests session to use
        headers: Request headers
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests

    Returns:
        Parsed JSON response

    Raises:
        PrivyAPIError: For various API error conditions
        PrivyNetworkError: For network-related errors
    """
    # Log request (without sensitive headers)
    safe_headers = {k: v for k, v in headers.items() if k.lower() not in ["authorization"]}
    logger.debug(
        f"Making {method} request",
        extra={
            "method": method,
            "url": url,
            "headers": safe_headers,
        },
    )

    @retry_api_call
    def _make_request() -> requests.Response:
        """Inner function with retry decorator."""
        try:
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
            return response
        except requests.Timeout as e:
            logger.warning(f"Request timeout after {timeout}s", extra={"url": url})
            raise PrivyNetworkError(f"Request timeout after {timeout} seconds", original_error=e)
        except requests.ConnectionError as e:
            logger.warning("Connection error", extra={"url": url})
            raise PrivyNetworkError("Failed to connect to Privy API", original_error=e)
        except Exception as e:
            logger.error(
                f"Unexpected error during request: {sanitize_error_message(e)}",
                extra={"url": url},
            )
            raise

    try:
        response = _make_request()
        return handle_response(response)
    except Exception as e:
        # Re-raise all Privy exceptions as-is (they're already properly typed)
        from langchain_privy.exceptions import PrivyError

        if isinstance(e, PrivyError):
            raise
        # Wrap unexpected exceptions
        raise PrivyNetworkError("Unexpected error during API request", original_error=e)
