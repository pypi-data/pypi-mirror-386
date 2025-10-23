"""LangChain integration for Privy embedded wallets."""

from langchain_privy.auth import PrivyAuth, PrivyConfig
from langchain_privy.chains import Chain, get_chain_config
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
)
from langchain_privy.rpc_client import PrivyRPCClient, RPCMethod
from langchain_privy.wallet_tool import PrivyWalletTool

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "PrivyWalletTool",
    "PrivyRPCClient",
    "PrivyAuth",
    "PrivyConfig",
    "Chain",
    "get_chain_config",
    "RPCMethod",
    # Exceptions
    "PrivyError",
    "PrivyAPIError",
    "PrivyAuthenticationError",
    "PrivyValidationError",
    "PrivyNotFoundError",
    "PrivyRateLimitError",
    "PrivyServerError",
    "PrivyNetworkError",
    "PrivyConfigurationError",
]
