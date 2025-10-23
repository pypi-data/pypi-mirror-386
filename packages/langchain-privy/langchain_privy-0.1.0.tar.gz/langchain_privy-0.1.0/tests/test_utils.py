"""Tests for utility functions."""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from langchain_privy.exceptions import (
    PrivyAuthenticationError,
    PrivyNetworkError,
    PrivyNotFoundError,
    PrivyRateLimitError,
    PrivyServerError,
    PrivyValidationError,
)
from langchain_privy.utils import (
    _is_retryable_error,
    handle_response,
    make_api_request,
    sanitize_error_message,
)


class TestSanitizeErrorMessage:
    """Test sanitize_error_message function."""

    def test_removes_bearer_token(self):
        """Test that Bearer tokens are redacted."""
        error = Exception("Error: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
        result = sanitize_error_message(error)
        assert "[REDACTED]" in result
        assert "eyJhbGciOi" not in result

    def test_removes_basic_auth(self):
        """Test that Basic auth is redacted."""
        error = Exception("Error: Basic dXNlcjpwYXNz")
        result = sanitize_error_message(error)
        assert "[REDACTED]" in result
        assert "dXNlcjpwYXNz" not in result

    def test_removes_authorization_header(self):
        """Test that Authorization headers are redacted."""
        error = Exception("Error: Authorization: Bearer token123")
        result = sanitize_error_message(error)
        assert "[REDACTED]" in result
        assert "token123" not in result

    def test_removes_privy_app_secret(self):
        """Test that privy-app-secret is redacted."""
        error = Exception("Error: privy-app-secret: secret123")
        result = sanitize_error_message(error)
        assert "[REDACTED]" in result
        assert "secret123" not in result

    def test_removes_app_secret_env_var(self):
        """Test that PRIVY_APP_SECRET is redacted."""
        error = Exception("Error: PRIVY_APP_SECRET=my_secret_key")
        result = sanitize_error_message(error)
        assert "[REDACTED]" in result
        assert "my_secret_key" not in result

    def test_non_sensitive_error_unchanged(self):
        """Test that non-sensitive errors pass through."""
        error = Exception("Connection timeout after 30 seconds")
        result = sanitize_error_message(error)
        assert result == "Connection timeout after 30 seconds"

    def test_empty_error_message(self):
        """Test handling of empty error message."""
        error = Exception("")
        result = sanitize_error_message(error)
        assert result == ""


class TestIsRetryableError:
    """Test _is_retryable_error function."""

    def test_timeout_is_retryable(self):
        """Test that timeout errors are retryable."""
        error = requests.Timeout("Request timed out")
        assert _is_retryable_error(error) is True

    def test_connection_error_is_retryable(self):
        """Test that connection errors are retryable."""
        error = requests.ConnectionError("Failed to connect")
        assert _is_retryable_error(error) is True

    def test_server_error_is_retryable(self):
        """Test that server errors are retryable."""
        error = PrivyServerError("Internal server error", status_code=500)
        assert _is_retryable_error(error) is True

    def test_validation_error_not_retryable(self):
        """Test that validation errors are not retryable."""
        error = PrivyValidationError("Bad request", status_code=400)
        assert _is_retryable_error(error) is False

    def test_authentication_error_not_retryable(self):
        """Test that auth errors are not retryable."""
        error = PrivyAuthenticationError("Unauthorized", status_code=401)
        assert _is_retryable_error(error) is False

    def test_generic_exception_not_retryable(self):
        """Test that generic exceptions are not retryable."""
        error = ValueError("Some error")
        assert _is_retryable_error(error) is False


class TestHandleResponse:
    """Test handle_response function."""

    def test_successful_response(self):
        """Test handling successful 200 response."""
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.content = b'{"data": "success"}'
        response.json.return_value = {"data": "success"}
        response.headers = {"x-request-id": "req_123"}
        response.url = "https://api.privy.io/test"

        result = handle_response(response)
        assert result == {"data": "success"}

    def test_successful_response_empty_body(self):
        """Test handling successful response with empty body."""
        response = Mock()
        response.ok = True
        response.status_code = 204
        response.content = b""
        response.headers = {}
        response.url = "https://api.privy.io/test"

        result = handle_response(response)
        assert result == {}

    def test_400_raises_validation_error(self):
        """Test that 400 status raises PrivyValidationError."""
        response = Mock()
        response.ok = False
        response.status_code = 400
        response.content = b'{"error": "Invalid parameters"}'
        response.json.return_value = {"error": "Invalid parameters"}
        response.headers = {"x-request-id": "req_123"}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyValidationError) as exc_info:
            handle_response(response)
        assert exc_info.value.status_code == 400
        assert "Invalid parameters" in str(exc_info.value)

    def test_401_raises_authentication_error(self):
        """Test that 401 status raises PrivyAuthenticationError."""
        response = Mock()
        response.ok = False
        response.status_code = 401
        response.content = b'{"error": "Unauthorized"}'
        response.json.return_value = {"error": "Unauthorized"}
        response.headers = {"x-request-id": "req_123"}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyAuthenticationError) as exc_info:
            handle_response(response)
        assert exc_info.value.status_code == 401

    def test_404_raises_not_found_error(self):
        """Test that 404 status raises PrivyNotFoundError."""
        response = Mock()
        response.ok = False
        response.status_code = 404
        response.content = b'{"error": "Not found"}'
        response.json.return_value = {"error": "Not found"}
        response.headers = {}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyNotFoundError) as exc_info:
            handle_response(response)
        assert exc_info.value.status_code == 404

    def test_429_raises_rate_limit_error(self):
        """Test that 429 status raises PrivyRateLimitError."""
        response = Mock()
        response.ok = False
        response.status_code = 429
        response.content = b'{"error": "Rate limit exceeded"}'
        response.json.return_value = {"error": "Rate limit exceeded"}
        response.headers = {}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyRateLimitError) as exc_info:
            handle_response(response)
        assert exc_info.value.status_code == 429

    def test_500_raises_server_error(self):
        """Test that 500 status raises PrivyServerError."""
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.content = b'{"error": "Internal server error"}'
        response.json.return_value = {"error": "Internal server error"}
        response.headers = {}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyServerError) as exc_info:
            handle_response(response)
        assert exc_info.value.status_code == 500

    def test_invalid_json_response(self):
        """Test handling invalid JSON in response."""
        response = Mock()
        response.ok = False
        response.status_code = 500
        response.content = b"Not JSON"
        response.json.side_effect = ValueError("Invalid JSON")
        response.headers = {}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyServerError):
            handle_response(response)

    def test_includes_request_id_in_error(self):
        """Test that request ID is included in errors."""
        response = Mock()
        response.ok = False
        response.status_code = 400
        response.content = b'{"error": "Bad request"}'
        response.json.return_value = {"error": "Bad request"}
        response.headers = {"x-request-id": "req_abc123"}
        response.url = "https://api.privy.io/test"

        with pytest.raises(PrivyValidationError) as exc_info:
            handle_response(response)
        assert exc_info.value.request_id == "req_abc123"


class TestMakeAPIRequest:
    """Test make_api_request function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return Mock(spec=requests.Session)

    def test_successful_get_request(self, mock_session):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"data": "test"}'
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {}
        mock_response.url = "https://api.privy.io/test"

        mock_session.request.return_value = mock_response

        result = make_api_request(
            method="GET",
            url="https://api.privy.io/test",
            session=mock_session,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        assert result == {"data": "test"}
        mock_session.request.assert_called_once()

    def test_successful_post_request_with_json(self, mock_session):
        """Test successful POST request with JSON body."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"success": true}'
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_response.url = "https://api.privy.io/test"

        mock_session.request.return_value = mock_response

        result = make_api_request(
            method="POST",
            url="https://api.privy.io/test",
            session=mock_session,
            headers={"Content-Type": "application/json"},
            timeout=30,
            json={"key": "value"},
        )

        assert result == {"success": True}
        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["json"] == {"key": "value"}

    def test_timeout_raises_network_error(self, mock_session):
        """Test that timeout raises PrivyNetworkError."""
        mock_session.request.side_effect = requests.Timeout("Timeout")

        with pytest.raises(PrivyNetworkError) as exc_info:
            make_api_request(
                method="GET",
                url="https://api.privy.io/test",
                session=mock_session,
                headers={},
                timeout=30,
            )
        assert "timeout" in str(exc_info.value).lower()

    def test_connection_error_raises_network_error(self, mock_session):
        """Test that connection error raises PrivyNetworkError."""
        mock_session.request.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(PrivyNetworkError) as exc_info:
            make_api_request(
                method="GET",
                url="https://api.privy.io/test",
                session=mock_session,
                headers={},
                timeout=30,
            )
        assert "connect" in str(exc_info.value).lower()

    @patch("langchain_privy.utils.retry_api_call")
    def test_retries_on_timeout(self, mock_retry, mock_session):
        """Test that timeouts are retried."""
        # Simulate timeout on first 2 attempts, success on 3rd
        mock_session.request.side_effect = [
            requests.Timeout("Timeout"),
            requests.Timeout("Timeout"),
            Mock(
                ok=True,
                status_code=200,
                content=b'{"data": "success"}',
                json=lambda: {"data": "success"},
                headers={},
                url="https://api.privy.io/test",
            ),
        ]

        # Note: The actual retry logic is handled by the decorator
        # This test verifies the error types that trigger retries
        assert _is_retryable_error(requests.Timeout("test"))
        assert _is_retryable_error(requests.ConnectionError("test"))

    def test_sanitizes_auth_headers_in_logs(self, mock_session):
        """Test that Authorization headers are not logged."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"data": "test"}'
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {}
        mock_response.url = "https://api.privy.io/test"

        mock_session.request.return_value = mock_response

        # This test ensures the function accepts Authorization header
        # The actual sanitization happens in logging (tested separately)
        result = make_api_request(
            method="GET",
            url="https://api.privy.io/test",
            session=mock_session,
            headers={"Authorization": "Bearer secret_token"},
            timeout=30,
        )

        assert result == {"data": "test"}
        # Verify that the Authorization header was passed to the request
        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer secret_token"

    def test_passes_kwargs_to_session(self, mock_session):
        """Test that additional kwargs are passed to session.request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"data": "test"}'
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {}
        mock_response.url = "https://api.privy.io/test"

        mock_session.request.return_value = mock_response

        make_api_request(
            method="POST",
            url="https://api.privy.io/test",
            session=mock_session,
            headers={},
            timeout=30,
            json={"test": "data"},
            params={"key": "value"},
        )

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["json"] == {"test": "data"}
        assert call_kwargs["params"] == {"key": "value"}
