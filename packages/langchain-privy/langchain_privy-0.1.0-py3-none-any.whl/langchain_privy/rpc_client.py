"""RPC client for Privy Wallet API."""

import logging
from enum import Enum
from typing import Any, Optional

import requests

from langchain_privy.auth import PrivyAuth, PrivyConfig
from langchain_privy.chains import Chain, get_chain_config
from langchain_privy.utils import make_api_request

logger = logging.getLogger(__name__)


class RPCMethod(str, Enum):
    """Supported RPC methods for Privy Wallet API."""

    # Ethereum/EVM methods
    ETH_SEND_TRANSACTION = "eth_sendTransaction"
    ETH_SIGN_TRANSACTION = "eth_signTransaction"
    ETH_SIGN = "eth_sign"
    ETH_SIGN_TYPED_DATA = "eth_signTypedData"
    ETH_SIGN_TYPED_DATA_V4 = "eth_signTypedData_v4"
    PERSONAL_SIGN = "personal_sign"

    # Solana methods
    SOLANA_SIGN_MESSAGE = "signMessage"
    SOLANA_SIGN_TRANSACTION = "signTransaction"
    SOLANA_SIGN_ALL_TRANSACTIONS = "signAllTransactions"
    SOLANA_SIGN_AND_SEND_TRANSACTION = "signAndSendTransaction"

    # Bitcoin methods
    BTC_SIGN_MESSAGE = "btc_signMessage"

    # Utility methods
    GET_ADDRESSES = "get_addresses"


class PrivyRPCClient:
    """Client for interacting with Privy Wallet API RPC endpoints.

    This client handles signing transactions, messages, and other wallet
    operations through Privy's secure wallet infrastructure.
    """

    def __init__(self, config: PrivyConfig, wallet_id: str, wallet_address: Optional[str] = None):
        """Initialize Privy RPC client.

        Args:
            config: Privy configuration object
            wallet_id: Wallet identifier (from create_wallet or list_wallets)
            wallet_address: Optional wallet address (for compatibility)
        """
        self.config = config
        self.wallet_id = wallet_id
        self.wallet_address = wallet_address
        self.auth = PrivyAuth(config)
        self._session = requests.Session()

    def execute_rpc(
        self,
        wallet_id: str,
        method: RPCMethod | str,
        params: dict[str, Any],
        chain: Chain | str = Chain.ETHEREUM,
        include_caip2: bool = False,
    ) -> dict[str, Any]:
        """Execute an RPC method on a wallet.

        Args:
            wallet_id: Wallet ID to execute RPC on
            method: RPC method to execute
            params: Method parameters
            chain: Target blockchain
            include_caip2: Whether to include CAIP-2 chain ID in request body
                          (only needed for transaction methods like eth_sendTransaction)

        Returns:
            RPC response data

        Raises:
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs
            ValueError: If RPC returns an error response
        """
        chain_config = get_chain_config(chain)

        url = f"{self.config.api_url}/api/v1/wallets/{wallet_id}/rpc"

        method_str = method if isinstance(method, str) else method.value
        request_body: dict[str, Any] = {
            "method": method_str,
            "params": params,
        }

        # Only include caip2 for methods that need it (e.g., send transactions)
        if include_caip2:
            request_body["caip2"] = chain_config.caip2

        logger.info(
            "Executing RPC method",
            extra={
                "wallet_id": wallet_id,
                "method": method_str,
                "chain": chain_config.caip2,
            },
        )

        result = make_api_request(
            method="POST",
            url=url,
            session=self._session,
            headers=self.auth.get_auth_headers(),
            timeout=self.config.timeout,
            json=request_body,
        )

        # Check for RPC errors
        if "error" in result:
            error_msg = result["error"].get("message", "Unknown RPC error")
            logger.error(
                f"RPC error: {error_msg}",
                extra={"wallet_id": wallet_id, "method": method_str},
            )
            raise ValueError(f"RPC error: {error_msg}")

        return result

    def send_transaction(
        self,
        to: str,
        value: str,
        chain: Chain | str = Chain.ETHEREUM,
        data: Optional[str] = None,
        gas_limit: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send a transaction from the wallet.

        Args:
            to: Recipient address
            value: Transaction value in wei (as decimal string or hex string starting with 0x)
            chain: Target blockchain
            data: Transaction data (optional)
            gas_limit: Gas limit (optional)

        Returns:
            Transaction response with hash and transaction_id

        Raises:
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs
            ValueError: If RPC returns an error response
        """
        # Convert value to hex if it's not already
        if not value.startswith("0x"):
            # Assume it's a decimal string in wei
            value_int = int(value)
            value = hex(value_int)

        transaction_params: dict[str, Any] = {
            "to": to,
            "value": value,
        }

        if data:
            transaction_params["data"] = data
        if gas_limit:
            transaction_params["gas"] = gas_limit

        params = {"transaction": transaction_params}

        return self.execute_rpc(
            wallet_id=self.wallet_id,
            method=RPCMethod.ETH_SEND_TRANSACTION,
            params=params,
            chain=chain,
            include_caip2=True,  # Transactions need CAIP-2 chain ID
        )

    def sign_message(
        self,
        message: str,
        chain: Chain | str = Chain.ETHEREUM,
    ) -> dict[str, Any]:
        """Sign a message with the wallet.

        Args:
            message: Message to sign (hex string or plain text)
            chain: Target blockchain

        Returns:
            Signature response

        Raises:
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs
            ValueError: If chain type is unsupported or RPC returns an error
        """
        chain_config = get_chain_config(chain)

        # Use appropriate signing method based on chain type
        if chain_config.chain_type == "ethereum":
            method = RPCMethod.PERSONAL_SIGN
            params = {"message": message, "encoding": "utf-8"}
        elif chain_config.chain_type == "solana":
            method = RPCMethod.SOLANA_SIGN_MESSAGE
            # Solana requires base64 encoding
            import base64

            message_bytes = message.encode("utf-8")
            message_b64 = base64.b64encode(message_bytes).decode("utf-8")
            params = {"message": message_b64, "encoding": "base64"}
        elif chain_config.chain_type == "bitcoin":
            method = RPCMethod.BTC_SIGN_MESSAGE
            params = {"message": message}
        else:
            raise ValueError(f"Signing not supported for chain type: {chain_config.chain_type}")

        return self.execute_rpc(
            wallet_id=self.wallet_id,
            method=method,
            params=params,
            chain=chain,
        )

    def get_wallet_address(self) -> str:
        """Get the wallet's address.

        Returns:
            Wallet address

        Raises:
            ValueError: If wallet address is not available
        """
        if self.wallet_address:
            return self.wallet_address

        # Fetch wallet details from API if address not cached
        wallet = self.auth.get_wallet(self.wallet_id)
        self.wallet_address = wallet.get("address")

        if not self.wallet_address:
            raise ValueError(f"Could not retrieve address for wallet {self.wallet_id}")

        return self.wallet_address

    def get_balance(
        self, chain: Chain | str = Chain.ETHEREUM, asset: str = "eth"
    ) -> dict[str, Any]:
        """Get wallet balance.

        Args:
            chain: Target blockchain (e.g., "ethereum", "base", "solana")
            asset: Asset to check balance for (e.g., "eth", "sol", "usdc")

        Returns:
            Balance information

        Raises:
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs
            ValueError: If chain doesn't support balance API
        """
        # Validate chain exists
        get_chain_config(chain)

        # Map chain enum values to balance API chain names
        # Balance API uses underscores and different naming conventions
        BALANCE_API_CHAIN_MAP = {
            "ethereum": "ethereum",
            "ethereum-sepolia": "sepolia",
            "arbitrum": "arbitrum",
            "arbitrum-sepolia": "arbitrum_sepolia",
            "base": "base",
            "base-sepolia": "base_sepolia",
            "linea": "linea",
            "linea-sepolia": "linea_testnet",
            "optimism": "optimism",
            "optimism-sepolia": "optimism_sepolia",
            "polygon": "polygon",
            "polygon-amoy": "polygon_amoy",
            "solana": "solana",
            # Note: solana-devnet, bitcoin, and many other chains are NOT supported by balance API
        }

        chain_str = chain if isinstance(chain, str) else chain.value
        balance_api_chain = BALANCE_API_CHAIN_MAP.get(chain_str)

        if not balance_api_chain:
            raise ValueError(
                f"Balance API does not support chain '{chain_str}'. "
                f"Supported chains: {', '.join(BALANCE_API_CHAIN_MAP.keys())}"
            )

        url = f"{self.config.api_url}/api/v1/wallets/{self.wallet_id}/balance"

        logger.info(
            "Getting wallet balance",
            extra={"wallet_id": self.wallet_id, "chain": balance_api_chain, "asset": asset},
        )

        return make_api_request(
            method="GET",
            url=url,
            session=self._session,
            headers=self.auth.get_auth_headers(),
            timeout=self.config.timeout,
            params={"chain": balance_api_chain, "asset": asset},
        )

    def sign_typed_data(
        self,
        domain: dict[str, Any],
        types: dict[str, Any],
        value: dict[str, Any],
        chain: Chain | str = Chain.ETHEREUM,
    ) -> dict[str, Any]:
        """Sign typed data (EIP-712) with the wallet.

        Args:
            domain: EIP-712 domain parameters
            types: Type definitions
            value: Message value
            chain: Target blockchain (must be EVM)

        Returns:
            Signature response

        Raises:
            ValueError: If chain is not EVM or RPC returns an error
            PrivyAPIError: If API request fails
            PrivyNetworkError: If network error occurs
        """
        chain_config = get_chain_config(chain)
        if chain_config.chain_type != "ethereum":
            raise ValueError("signTypedData is only supported on EVM chains")

        params = {
            "typed_data": {
                "domain": domain,
                "types": types,
                "message": value,
                "primary_type": list(types.keys())[0] if types else "EIP712Domain",
            }
        }

        return self.execute_rpc(
            wallet_id=self.wallet_id,
            method=RPCMethod.ETH_SIGN_TYPED_DATA_V4,
            params=params,
            chain=chain,
        )
