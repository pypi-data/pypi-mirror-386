"""Tests for custom exception classes."""

import pytest

from langchain_privy.exceptions import (
    PrivyAPIError,
    PrivyAuthenticationError,
    PrivyConfigurationError,
    PrivyError,
    PrivyNetworkError,
    PrivyNotFoundError,
    PrivyRateLimitError,
    PrivyServerError,
    PrivyValidationError,
    create_api_error,
)


class TestPrivyError:
    """Test base PrivyError class."""

    def test_init_with_message(self):
        """Test initializing with just a message."""
        error = PrivyError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_init_with_details(self):
        """Test initializing with message and details."""
        details = {"key": "value", "code": 123}
        error = PrivyError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details


class TestPrivyAPIError:
    """Test PrivyAPIError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = PrivyAPIError("API error", status_code=400)
        assert error.message == "API error"
        assert error.status_code == 400
        assert error.response_body == {}
        assert error.request_id is None

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        response_body = {"error": "details"}
        error = PrivyAPIError(
            "API error",
            status_code=400,
            response_body=response_body,
            request_id="req_123",
        )
        assert error.response_body == response_body
        assert error.request_id == "req_123"

    def test_str_without_request_id(self):
        """Test string representation without request ID."""
        error = PrivyAPIError("API error", status_code=400)
        assert str(error) == "HTTP 400: API error"

    def test_str_with_request_id(self):
        """Test string representation with request ID."""
        error = PrivyAPIError("API error", status_code=400, request_id="req_123")
        assert str(error) == "HTTP 400: API error | Request ID: req_123"

    def test_details_includes_status_code(self):
        """Test that details includes status code."""
        error = PrivyAPIError("API error", status_code=404)
        assert error.details["status_code"] == 404


class TestPrivyAuthenticationError:
    """Test PrivyAuthenticationError class."""

    def test_inherits_from_api_error(self):
        """Test that it inherits from PrivyAPIError."""
        error = PrivyAuthenticationError("Auth failed", status_code=401)
        assert isinstance(error, PrivyAPIError)
        assert error.status_code == 401

    def test_401_error(self):
        """Test 401 unauthorized error."""
        error = PrivyAuthenticationError("Unauthorized", status_code=401)
        assert str(error) == "HTTP 401: Unauthorized"

    def test_403_error(self):
        """Test 403 forbidden error."""
        error = PrivyAuthenticationError("Forbidden", status_code=403)
        assert str(error) == "HTTP 403: Forbidden"


class TestPrivyValidationError:
    """Test PrivyValidationError class."""

    def test_inherits_from_api_error(self):
        """Test that it inherits from PrivyAPIError."""
        error = PrivyValidationError("Invalid params", status_code=400)
        assert isinstance(error, PrivyAPIError)
        assert error.status_code == 400

    def test_400_error(self):
        """Test 400 bad request error."""
        error = PrivyValidationError("Invalid parameters", status_code=400)
        assert "400" in str(error)
        assert "Invalid parameters" in str(error)


class TestPrivyNotFoundError:
    """Test PrivyNotFoundError class."""

    def test_inherits_from_api_error(self):
        """Test that it inherits from PrivyAPIError."""
        error = PrivyNotFoundError("Not found", status_code=404)
        assert isinstance(error, PrivyAPIError)

    def test_404_error(self):
        """Test 404 not found error."""
        error = PrivyNotFoundError("Wallet not found", status_code=404)
        assert "404" in str(error)
        assert "Wallet not found" in str(error)


class TestPrivyRateLimitError:
    """Test PrivyRateLimitError class."""

    def test_inherits_from_api_error(self):
        """Test that it inherits from PrivyAPIError."""
        error = PrivyRateLimitError("Rate limit exceeded", status_code=429)
        assert isinstance(error, PrivyAPIError)

    def test_init_without_retry_after(self):
        """Test initialization without retry_after."""
        error = PrivyRateLimitError("Rate limit", status_code=429)
        assert error.retry_after is None

    def test_init_with_retry_after(self):
        """Test initialization with retry_after."""
        error = PrivyRateLimitError("Rate limit", status_code=429, retry_after=60)
        assert error.retry_after == 60

    def test_str_without_retry_after(self):
        """Test string representation without retry_after."""
        error = PrivyRateLimitError("Rate limit", status_code=429)
        assert str(error) == "HTTP 429: Rate limit"

    def test_str_with_retry_after(self):
        """Test string representation with retry_after."""
        error = PrivyRateLimitError("Rate limit", status_code=429, retry_after=60)
        expected = "HTTP 429: Rate limit | Retry after 60 seconds"
        assert str(error) == expected


class TestPrivyServerError:
    """Test PrivyServerError class."""

    def test_inherits_from_api_error(self):
        """Test that it inherits from PrivyAPIError."""
        error = PrivyServerError("Server error", status_code=500)
        assert isinstance(error, PrivyAPIError)

    def test_500_error(self):
        """Test 500 internal server error."""
        error = PrivyServerError("Internal error", status_code=500)
        assert "500" in str(error)

    def test_502_error(self):
        """Test 502 bad gateway error."""
        error = PrivyServerError("Bad gateway", status_code=502)
        assert "502" in str(error)

    def test_503_error(self):
        """Test 503 service unavailable error."""
        error = PrivyServerError("Service unavailable", status_code=503)
        assert "503" in str(error)


class TestPrivyNetworkError:
    """Test PrivyNetworkError class."""

    def test_inherits_from_base_error(self):
        """Test that it inherits from PrivyError."""
        error = PrivyNetworkError("Network error")
        assert isinstance(error, PrivyError)

    def test_init_without_original_error(self):
        """Test initialization without original error."""
        error = PrivyNetworkError("Connection failed")
        assert error.message == "Connection failed"
        assert error.original_error is None

    def test_init_with_original_error(self):
        """Test initialization with original error."""
        original = ConnectionError("TCP connection failed")
        error = PrivyNetworkError("Network error", original_error=original)
        assert error.original_error == original
        assert "TCP connection failed" in error.details["original_error"]

    def test_str_representation(self):
        """Test string representation."""
        error = PrivyNetworkError("Timeout occurred")
        assert str(error) == "Timeout occurred"


class TestPrivyConfigurationError:
    """Test PrivyConfigurationError class."""

    def test_inherits_from_base_error(self):
        """Test that it inherits from PrivyError."""
        error = PrivyConfigurationError("Config error")
        assert isinstance(error, PrivyError)

    def test_configuration_error(self):
        """Test configuration error message."""
        error = PrivyConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"


class TestCreateAPIError:
    """Test create_api_error factory function."""

    def test_create_400_error(self):
        """Test creating 400 validation error."""
        error = create_api_error(400, "Bad request")
        assert isinstance(error, PrivyValidationError)
        assert error.status_code == 400

    def test_create_401_error(self):
        """Test creating 401 authentication error."""
        error = create_api_error(401, "Unauthorized")
        assert isinstance(error, PrivyAuthenticationError)
        assert error.status_code == 401

    def test_create_403_error(self):
        """Test creating 403 authentication error."""
        error = create_api_error(403, "Forbidden")
        assert isinstance(error, PrivyAuthenticationError)
        assert error.status_code == 403

    def test_create_404_error(self):
        """Test creating 404 not found error."""
        error = create_api_error(404, "Not found")
        assert isinstance(error, PrivyNotFoundError)
        assert error.status_code == 404

    def test_create_429_error_without_retry_after(self):
        """Test creating 429 rate limit error without retry_after."""
        error = create_api_error(429, "Rate limited")
        assert isinstance(error, PrivyRateLimitError)
        assert error.retry_after is None

    def test_create_429_error_with_retry_after(self):
        """Test creating 429 rate limit error with retry_after."""
        response_body = {"retry_after": 120}
        error = create_api_error(429, "Rate limited", response_body=response_body)
        assert isinstance(error, PrivyRateLimitError)
        assert error.retry_after == 120

    def test_create_500_error(self):
        """Test creating 500 server error."""
        error = create_api_error(500, "Server error")
        assert isinstance(error, PrivyServerError)
        assert error.status_code == 500

    def test_create_502_error(self):
        """Test creating 502 server error."""
        error = create_api_error(502, "Bad gateway")
        assert isinstance(error, PrivyServerError)

    def test_create_503_error(self):
        """Test creating 503 server error."""
        error = create_api_error(503, "Service unavailable")
        assert isinstance(error, PrivyServerError)

    def test_create_generic_error(self):
        """Test creating generic API error for unknown status codes."""
        error = create_api_error(418, "I'm a teapot")
        assert isinstance(error, PrivyAPIError)
        assert not isinstance(error, PrivyValidationError)
        assert error.status_code == 418

    def test_with_request_id(self):
        """Test creating error with request ID."""
        error = create_api_error(500, "Error", request_id="req_123")
        assert error.request_id == "req_123"
        assert "req_123" in str(error)

    def test_with_response_body(self):
        """Test creating error with response body."""
        response_body = {"error": "details", "code": "ERR_001"}
        error = create_api_error(400, "Error", response_body=response_body)
        assert error.response_body == response_body
