"""Authentication module for Privy API access."""

import base64
import logging
import os
from dataclasses import dataclass
from typing import Optional

import requests

from langchain_privy.utils import make_api_request

logger = logging.getLogger(__name__)


@dataclass
class PrivyConfig:
    """Configuration for Privy API access.

    Attributes:
        app_id: Your Privy application ID
        app_secret: Your Privy application secret (keep this secure!)
        api_url: Base URL for Privy API (defaults to production)
        timeout: Request timeout in seconds
    """

    app_id: str
    app_secret: str
    api_url: str = "https://auth.privy.io"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "PrivyConfig":
        """Create configuration from environment variables.

        Expected environment variables:
        - PRIVY_APP_ID: Your Privy application ID
        - PRIVY_APP_SECRET: Your Privy application secret
        - PRIVY_API_URL: (Optional) Custom API URL

        Returns:
            PrivyConfig instance

        Raises:
            ValueError: If required environment variables are not set
        """
        app_id = os.getenv("PRIVY_APP_ID")
        app_secret = os.getenv("PRIVY_APP_SECRET")

        if not app_id:
            raise ValueError("PRIVY_APP_ID environment variable is required")
        if not app_secret:
            raise ValueError("PRIVY_APP_SECRET environment variable is required")

        api_url = os.getenv("PRIVY_API_URL", "https://auth.privy.io")

        return cls(
            app_id=app_id,
            app_secret=app_secret,
            api_url=api_url,
        )


class PrivyAuth:
    """Handles authentication and wallet management with Privy API.

    This class manages server-side authentication using Privy App Secrets
    and provides methods for creating and managing server wallets.
    """

    def __init__(self, config: PrivyConfig):
        """Initialize Privy authentication handler.

        Args:
            config: Privy configuration object
        """
        self.config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "privy-app-id": config.app_id,
            }
        )

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for Privy API requests.

        Uses HTTP Basic Authentication with app_id:app_secret encoded in base64.

        Returns:
            Dictionary of headers including app credentials
        """
        # Encode app_id:app_secret as Basic Auth
        credentials = f"{self.config.app_id}:{self.config.app_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Content-Type": "application/json",
            "privy-app-id": self.config.app_id,
            "Authorization": f"Basic {encoded_credentials}",
        }

    def create_wallet(self, chain_type: str = "ethereum") -> dict:
        """Create a new server wallet.

        Creates a wallet that is managed by the application (not tied to a Privy user).
        The wallet is created in Privy's secure enclave and can be used for
        blockchain operations.

        Args:
            chain_type: The blockchain type for the wallet. Supported values include:
                       "ethereum", "solana", "base", "polygon", "arbitrum", etc.
                       Defaults to "ethereum".

        Returns:
            Dictionary containing wallet information:
            - id: Unique wallet identifier
            - address: Blockchain address
            - chain_type: The blockchain type
            - created_at: Timestamp of creation

        Raises:
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs

        Example:
            >>> auth = PrivyAuth(config)
            >>> wallet = auth.create_wallet("ethereum")
            >>> print(wallet['address'])
            '0x1234...'
        """
        url = f"{self.config.api_url}/api/v1/wallets"

        logger.info("Creating wallet", extra={"chain_type": chain_type})

        return make_api_request(
            method="POST",
            url=url,
            session=self._session,
            headers=self.get_auth_headers(),
            timeout=self.config.timeout,
            json={"chain_type": chain_type},
        )

    def list_wallets(
        self, chain_type: Optional[str] = None, limit: int = 50, cursor: Optional[str] = None
    ) -> dict:
        """List all wallets for this application.

        Retrieves wallets created by this application. Results are paginated.

        Args:
            chain_type: Optional filter by chain type (e.g., "ethereum", "solana")
            limit: Maximum number of wallets to return (default 50, max 100)
            cursor: Pagination cursor from previous response

        Returns:
            Dictionary containing:
            - data: List of wallet objects
            - next_cursor: Cursor for next page (None if no more results)

        Raises:
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs

        Example:
            >>> auth = PrivyAuth(config)
            >>> result = auth.list_wallets(chain_type="ethereum", limit=10)
            >>> for wallet in result['data']:
            ...     print(wallet['address'])
        """
        url = f"{self.config.api_url}/api/v1/wallets"

        params = {"limit": min(limit, 100)}
        if chain_type:
            params["chain_type"] = chain_type
        if cursor:
            params["cursor"] = cursor

        return make_api_request(
            method="GET",
            url=url,
            session=self._session,
            headers=self.get_auth_headers(),
            timeout=self.config.timeout,
            params=params,
        )

    def get_wallet(self, wallet_id: str) -> dict:
        """Get details for a specific wallet.

        Args:
            wallet_id: The wallet identifier

        Returns:
            Dictionary containing wallet information

        Raises:
            PrivyAPIError: If API request fails
            PrivyNotFoundError: If wallet not found
            PrivyNetworkError: If network error occurs

        Example:
            >>> auth = PrivyAuth(config)
            >>> wallet = auth.get_wallet("wal_xxx")
            >>> print(wallet['address'])
        """
        url = f"{self.config.api_url}/api/v1/wallets/{wallet_id}"

        return make_api_request(
            method="GET",
            url=url,
            session=self._session,
            headers=self.get_auth_headers(),
            timeout=self.config.timeout,
        )
