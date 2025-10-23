"""LangChain Tool implementation for Privy wallets."""

from typing import Dict, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from langchain_privy.auth import PrivyAuth, PrivyConfig
from langchain_privy.chains import Chain, get_chain_config
from langchain_privy.rpc_client import PrivyRPCClient


class GetWalletAddressInput(BaseModel):
    """Input for get_wallet_address operation."""

    chain: str = Field(
        default="ethereum",
        description="Blockchain network to get address for (e.g., 'ethereum', 'base', 'solana')",
    )


class SendTransactionInput(BaseModel):
    """Input for send_transaction operation."""

    to: str = Field(description="Recipient wallet address")
    value: str = Field(description="Amount to send in wei (for EVM) or lamports (for Solana)")
    chain: str = Field(
        default="ethereum",
        description="Blockchain network to send transaction on",
    )
    data: Optional[str] = Field(
        default=None,
        description="Transaction data (hex string, optional)",
    )


class SignMessageInput(BaseModel):
    """Input for sign_message operation."""

    message: str = Field(description="Message to sign")
    chain: str = Field(
        default="ethereum",
        description="Blockchain network to sign message on",
    )


class GetBalanceInput(BaseModel):
    """Input for get_balance operation."""

    chain: str = Field(
        default="ethereum",
        description="Blockchain network to check balance on",
    )


class CreateWalletInput(BaseModel):
    """Input for create_wallet operation."""

    chain: str = Field(
        description=(
            "Blockchain chain type for the new wallet " "(e.g., 'ethereum', 'solana', 'bitcoin')"
        )
    )


class WalletToolInput(BaseModel):
    """Input schema for PrivyWalletTool."""

    operation: str = Field(
        description=(
            "Operation to perform: 'create_wallet', 'get_wallet_address', "
            "'send_transaction', 'sign_message', or 'get_balance'"
        )
    )
    chain: str = Field(
        default="ethereum", description="Blockchain network (e.g., 'ethereum', 'base', 'solana')"
    )
    to: Optional[str] = Field(
        default=None, description="Recipient address for send_transaction operation"
    )
    value: Optional[str] = Field(
        default=None, description="Amount to send in wei (for send_transaction)"
    )
    message: Optional[str] = Field(
        default=None, description="Message to sign (for sign_message operation)"
    )
    data: Optional[str] = Field(
        default=None, description="Transaction data (optional, for send_transaction)"
    )


class PrivyWalletTool(BaseTool):
    """LangChain tool for Privy wallet operations.

    This tool enables LangChain agents to perform wallet operations using Privy's
    wallet infrastructure, including:
    - Getting wallet addresses
    - Sending transactions
    - Signing messages
    - Checking balances

    The tool handles multi-chain operations and manages authentication with Privy API.
    Wallets are automatically created if not provided.
    """

    name: str = "privy_wallet"
    description: str = """
    Interact with blockchain wallets using Privy.
    This tool can:
    - Create new wallets for different chains (Ethereum, Solana, Bitcoin, etc.)
    - Get wallet addresses on different chains
    - Send cryptocurrency transactions
    - Sign messages for authentication
    - Check wallet balances

    Operations are performed securely through Privy's wallet infrastructure.
    Private keys never leave Privy's secure environment.
    """

    config: PrivyConfig = Field(exclude=True)
    auth: PrivyAuth = Field(exclude=True)
    # Dictionary mapping chain_type -> wallet info
    wallets: Dict[str, dict] = Field(default_factory=dict, exclude=True)

    args_schema: Type[BaseModel] = WalletToolInput

    def __init__(
        self,
        wallet_id: Optional[str] = None,
        chain_type: str = "ethereum",
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        config: Optional[PrivyConfig] = None,
        **kwargs,
    ):
        """Initialize Privy wallet tool.

        Args:
            wallet_id: Optional wallet ID. If not provided, a new wallet will be created.
            chain_type: Chain type for auto-created wallet (default: "ethereum")
            app_id: Privy application ID (can be set via PRIVY_APP_ID env var)
            app_secret: Privy application secret (can be set via PRIVY_APP_SECRET env var)
            config: PrivyConfig object (if provided, app_id and app_secret are ignored)
            **kwargs: Additional arguments passed to BaseTool
        """
        if config is None:
            if app_id and app_secret:
                config = PrivyConfig(app_id=app_id, app_secret=app_secret)
            else:
                config = PrivyConfig.from_env()

        auth = PrivyAuth(config)
        wallets = {}

        # Auto-create initial wallet if not provided
        if wallet_id is None:
            wallet = auth.create_wallet(chain_type=chain_type)
            wallets[chain_type] = {
                "id": wallet["id"],
                "address": wallet.get("address"),
                "chain_type": chain_type,
            }
        else:
            # Fetch wallet details if wallet_id provided
            wallet = auth.get_wallet(wallet_id)
            chain_type = wallet.get("chain_type", chain_type)
            wallets[chain_type] = {
                "id": wallet["id"],
                "address": wallet.get("address"),
                "chain_type": chain_type,
            }

        super().__init__(
            config=config,
            auth=auth,
            wallets=wallets,
            **kwargs,
        )

    @property
    def wallet_id(self) -> Optional[str]:
        """Get the default (first) wallet ID for backwards compatibility."""
        if self.wallets:
            return list(self.wallets.values())[0]["id"]
        return None

    @property
    def wallet_address(self) -> Optional[str]:
        """Get the default (first) wallet address for backwards compatibility."""
        if self.wallets:
            return list(self.wallets.values())[0]["address"]
        return None

    def _get_wallet_for_chain(self, chain: str) -> Optional[dict]:
        """Get wallet for a specific chain, looking up by chain_type."""
        chain_config = get_chain_config(chain)
        return self.wallets.get(chain_config.chain_type)

    def _run(
        self,
        operation: str,
        **kwargs,
    ) -> str:
        """Execute a wallet operation.

        Args:
            operation: Operation to perform (create_wallet, get_wallet_address,
                send_transaction, etc.)
            **kwargs: Operation-specific parameters

        Returns:
            Operation result as string

        Raises:
            ValueError: If operation is not supported or parameters are invalid
        """
        operation = operation.lower().strip()

        try:
            if operation == "create_wallet":
                return self._create_wallet(**kwargs)
            elif operation == "get_wallet_address":
                return self._get_wallet_address(**kwargs)
            elif operation == "send_transaction":
                return self._send_transaction(**kwargs)
            elif operation == "sign_message":
                return self._sign_message(**kwargs)
            elif operation == "get_balance":
                return self._get_balance(**kwargs)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        except Exception as e:
            return f"Error performing {operation}: {str(e)}"

    def _create_wallet(self, chain: str, **kwargs) -> str:
        """Create a new wallet for a specific chain."""
        try:
            chain_config = get_chain_config(chain)
            chain_type = chain_config.chain_type

            # Check if wallet already exists for this chain type
            if chain_type in self.wallets:
                wallet = self.wallets[chain_type]
                return (
                    f"Wallet already exists for {chain_type}!\n"
                    f"Wallet ID: {wallet['id']}\n"
                    f"Address: {wallet['address']}"
                )

            # Create new wallet
            wallet = self.auth.create_wallet(chain_type=chain_type)
            self.wallets[chain_type] = {
                "id": wallet["id"],
                "address": wallet.get("address"),
                "chain_type": chain_type,
            }

            return (
                f"New {chain_type} wallet created successfully!\n"
                f"Wallet ID: {wallet['id']}\n"
                f"Address: {wallet.get('address')}"
            )
        except Exception as e:
            return f"Error creating wallet: {str(e)}"

    def _get_wallet_address(self, chain: str = "ethereum", **kwargs) -> str:
        """Get wallet address for a specific chain."""
        try:
            wallet = self._get_wallet_for_chain(chain)
            if not wallet:
                chain_config = get_chain_config(chain)
                return (
                    f"No {chain_config.chain_type} wallet found. "
                    "Use create_wallet operation to create one."
                )

            return f"Wallet address: {wallet['address']}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _send_transaction(
        self,
        to: str,
        value: str,
        chain: str = "ethereum",
        data: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Send a transaction."""
        try:
            wallet = self._get_wallet_for_chain(chain)
            if not wallet:
                chain_config = get_chain_config(chain)
                return (
                    f"No {chain_config.chain_type} wallet found. "
                    "Use create_wallet operation to create one."
                )

            rpc_client = PrivyRPCClient(
                config=self.config, wallet_id=wallet["id"], wallet_address=wallet["address"]
            )

            chain_enum = Chain(chain)
            result = rpc_client.send_transaction(
                to=to,
                value=value,
                chain=chain_enum,
                data=data,
            )

            tx_hash = result.get("data", {}).get("hash")
            tx_id = result.get("data", {}).get("transaction_id")

            return (
                f"Transaction sent successfully!\n"
                f"Transaction hash: {tx_hash}\n"
                f"Transaction ID: {tx_id}\n"
                f"Chain: {chain}"
            )
        except Exception as e:
            return f"Error sending transaction: {str(e)}"

    def _sign_message(self, message: str, chain: str = "ethereum", **kwargs) -> str:
        """Sign a message."""
        try:
            wallet = self._get_wallet_for_chain(chain)
            if not wallet:
                chain_config = get_chain_config(chain)
                return (
                    f"No {chain_config.chain_type} wallet found. "
                    "Use create_wallet operation to create one."
                )

            rpc_client = PrivyRPCClient(
                config=self.config, wallet_id=wallet["id"], wallet_address=wallet["address"]
            )

            chain_enum = Chain(chain)
            result = rpc_client.sign_message(message=message, chain=chain_enum)

            signature = result.get("data", {}).get("signature")
            return f"Message signed successfully!\nSignature: {signature}"
        except Exception as e:
            return f"Error signing message: {str(e)}"

    def _get_balance(self, chain: str = "ethereum", **kwargs) -> str:
        """Get wallet balance."""
        try:
            wallet = self._get_wallet_for_chain(chain)
            if not wallet:
                chain_config = get_chain_config(chain)
                return (
                    f"No {chain_config.chain_type} wallet found. "
                    "Use create_wallet operation to create one."
                )

            rpc_client = PrivyRPCClient(
                config=self.config, wallet_id=wallet["id"], wallet_address=wallet["address"]
            )

            # Determine default asset based on chain
            chain_config = get_chain_config(chain)
            if chain_config.chain_type == "solana":
                asset = "sol"
            elif chain_config.chain_type == "bitcoin":
                asset = "btc"
            else:  # ethereum and EVM chains
                asset = "eth"

            chain_name = chain if isinstance(chain, str) else chain
            result = rpc_client.get_balance(chain=chain_name, asset=asset)

            # Extract balance information
            balances = result.get("balances", [])
            if not balances:
                return f"Wallet balance on {chain}: 0 {asset.upper()}"

            # Format balance output
            balance_data = balances[0]  # Get first balance
            raw_value = balance_data.get("raw_value", "0")
            decimals = balance_data.get("raw_value_decimals", 18)
            display_values = balance_data.get("display_values", {})

            # Get human-readable value
            display_value = display_values.get(asset, str(int(raw_value) / (10**decimals)))

            return f"Wallet balance on {chain}: {display_value} {asset.upper()}"
        except Exception as e:
            return f"Error getting balance: {str(e)}"

    async def _arun(
        self,
        operation: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Async version of _run (not implemented yet)."""
        # For now, just call the sync version
        # In the future, we could implement async HTTP requests
        return self._run(operation=operation, **kwargs)


# Convenience functions for creating specialized tools


class PrivyGetWalletAddressTool(BaseTool):
    """Specialized tool for getting wallet addresses."""

    name: str = "get_wallet_address"
    description: str = "Get the wallet address. " "Returns the blockchain address for this wallet."
    args_schema: Type[BaseModel] = GetWalletAddressInput

    config: PrivyConfig = Field(exclude=True)
    wallet_id: str = Field(exclude=True)
    rpc_client: PrivyRPCClient = Field(exclude=True)

    def __init__(
        self, config: PrivyConfig, wallet_id: str, wallet_address: Optional[str] = None, **kwargs
    ):
        """Initialize the tool."""
        rpc_client = PrivyRPCClient(
            config=config, wallet_id=wallet_id, wallet_address=wallet_address
        )
        super().__init__(config=config, wallet_id=wallet_id, rpc_client=rpc_client, **kwargs)

    def _run(self, chain: str = "ethereum", **kwargs) -> str:
        """Get wallet address."""
        try:
            address = self.rpc_client.get_wallet_address()
            return f"{address}"
        except Exception as e:
            return f"Error: {str(e)}"


class PrivySendTransactionTool(BaseTool):
    """Specialized tool for sending transactions."""

    name: str = "send_transaction"
    description: str = (
        "Send a cryptocurrency transaction on a blockchain. "
        "You must specify the recipient address, amount (in wei for EVM or lamports for Solana), "
        "and the blockchain network."
    )
    args_schema: Type[BaseModel] = SendTransactionInput

    config: PrivyConfig = Field(exclude=True)
    wallet_id: str = Field(exclude=True)
    rpc_client: PrivyRPCClient = Field(exclude=True)

    def __init__(
        self, config: PrivyConfig, wallet_id: str, wallet_address: Optional[str] = None, **kwargs
    ):
        """Initialize the tool."""
        rpc_client = PrivyRPCClient(
            config=config, wallet_id=wallet_id, wallet_address=wallet_address
        )
        super().__init__(config=config, wallet_id=wallet_id, rpc_client=rpc_client, **kwargs)

    def _run(
        self, to: str, value: str, chain: str = "ethereum", data: Optional[str] = None, **kwargs
    ) -> str:
        """Send transaction."""
        try:
            chain_enum = Chain(chain)
            result = self.rpc_client.send_transaction(
                to=to, value=value, chain=chain_enum, data=data
            )

            tx_hash = result.get("data", {}).get("hash")
            return f"Transaction sent! Hash: {tx_hash}"
        except Exception as e:
            return f"Error: {str(e)}"


class PrivySignMessageTool(BaseTool):
    """Specialized tool for signing messages."""

    name: str = "sign_message"
    description: str = "Sign a message with the wallet for authentication or verification purposes."
    args_schema: Type[BaseModel] = SignMessageInput

    config: PrivyConfig = Field(exclude=True)
    wallet_id: str = Field(exclude=True)
    rpc_client: PrivyRPCClient = Field(exclude=True)

    def __init__(
        self, config: PrivyConfig, wallet_id: str, wallet_address: Optional[str] = None, **kwargs
    ):
        """Initialize the tool."""
        rpc_client = PrivyRPCClient(
            config=config, wallet_id=wallet_id, wallet_address=wallet_address
        )
        super().__init__(config=config, wallet_id=wallet_id, rpc_client=rpc_client, **kwargs)

    def _run(self, message: str, chain: str = "ethereum", **kwargs) -> str:
        """Sign message."""
        try:
            chain_enum = Chain(chain)
            result = self.rpc_client.sign_message(message=message, chain=chain_enum)

            signature = result.get("data", {}).get("signature")
            return f"Signature: {signature}"
        except Exception as e:
            return f"Error: {str(e)}"
