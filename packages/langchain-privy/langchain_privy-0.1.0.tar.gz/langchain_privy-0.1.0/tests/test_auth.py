"""Tests for authentication module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from langchain_privy.auth import PrivyAuth, PrivyConfig


class TestPrivyConfig:
    """Test PrivyConfig class."""

    def test_create_config(self):
        """Test creating a PrivyConfig instance."""
        config = PrivyConfig(
            app_id="test-app-id",
            app_secret="test-app-secret",
        )
        assert config.app_id == "test-app-id"
        assert config.app_secret == "test-app-secret"
        assert config.api_url == "https://auth.privy.io"
        assert config.timeout == 30

    def test_create_config_custom_url(self):
        """Test creating config with custom API URL."""
        config = PrivyConfig(
            app_id="test-app-id",
            app_secret="test-app-secret",
            api_url="https://custom.privy.io",
        )
        assert config.api_url == "https://custom.privy.io"

    @patch.dict(
        os.environ,
        {
            "PRIVY_APP_ID": "env-app-id",
            "PRIVY_APP_SECRET": "env-app-secret",
        },
    )
    def test_from_env(self):
        """Test creating config from environment variables."""
        config = PrivyConfig.from_env()
        assert config.app_id == "env-app-id"
        assert config.app_secret == "env-app-secret"

    @patch.dict(
        os.environ,
        {
            "PRIVY_APP_ID": "env-app-id",
            "PRIVY_APP_SECRET": "env-app-secret",
            "PRIVY_API_URL": "https://custom.privy.io",
        },
    )
    def test_from_env_custom_url(self):
        """Test creating config from env with custom URL."""
        config = PrivyConfig.from_env()
        assert config.api_url == "https://custom.privy.io"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_missing_app_id(self):
        """Test error when PRIVY_APP_ID is missing."""
        with pytest.raises(ValueError, match="PRIVY_APP_ID environment variable is required"):
            PrivyConfig.from_env()

    @patch.dict(os.environ, {"PRIVY_APP_ID": "test"}, clear=True)
    def test_from_env_missing_app_secret(self):
        """Test error when PRIVY_APP_SECRET is missing."""
        with pytest.raises(ValueError, match="PRIVY_APP_SECRET environment variable is required"):
            PrivyConfig.from_env()


class TestPrivyAuth:
    """Test PrivyAuth class."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        return PrivyConfig(
            app_id="test-app-id",
            app_secret="test-app-secret",
        )

    @pytest.fixture
    def auth(self, config):
        """Create a PrivyAuth instance."""
        return PrivyAuth(config)

    def test_create_auth(self, config):
        """Test creating a PrivyAuth instance."""
        auth = PrivyAuth(config)
        assert auth.config == config

    def test_get_auth_headers(self, auth):
        """Test getting authentication headers."""
        import base64

        headers = auth.get_auth_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["privy-app-id"] == "test-app-id"

        # Verify Basic Auth format
        assert headers["Authorization"].startswith("Basic ")
        encoded = headers["Authorization"][6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "test-app-id:test-app-secret"

    @patch("langchain_privy.auth.requests.Session.request")
    def test_create_wallet(self, mock_request, auth):
        """Test creating a wallet."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "wal_abc123",
            "address": "0x1234567890123456789012345678901234567890",
            "chain_type": "ethereum",
            "created_at": 1234567890,
        }
        mock_request.return_value = mock_response

        wallet = auth.create_wallet("ethereum")

        assert wallet["id"] == "wal_abc123"
        assert wallet["address"] == "0x1234567890123456789012345678901234567890"
        assert wallet["chain_type"] == "ethereum"
        mock_request.assert_called_once()

    @patch("langchain_privy.auth.requests.Session.request")
    def test_list_wallets(self, mock_request, auth):
        """Test listing wallets."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "wal_abc123",
                    "address": "0x1234567890123456789012345678901234567890",
                    "chain_type": "ethereum",
                },
                {
                    "id": "wal_def456",
                    "address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                    "chain_type": "ethereum",
                },
            ],
            "next_cursor": None,
        }
        mock_request.return_value = mock_response

        result = auth.list_wallets(chain_type="ethereum")

        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "wal_abc123"
        assert result["data"][1]["id"] == "wal_def456"
        assert result["next_cursor"] is None

    @patch("langchain_privy.auth.requests.Session.request")
    def test_get_wallet(self, mock_request, auth):
        """Test getting a specific wallet."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "wal_abc123",
            "address": "0x1234567890123456789012345678901234567890",
            "chain_type": "ethereum",
            "created_at": 1234567890,
        }
        mock_request.return_value = mock_response

        wallet = auth.get_wallet("wal_abc123")

        assert wallet["id"] == "wal_abc123"
        assert wallet["address"] == "0x1234567890123456789012345678901234567890"
        mock_request.assert_called_once()
