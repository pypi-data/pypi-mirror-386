"""Tests for wallet tool module."""

from unittest.mock import Mock, patch

import pytest

from langchain_privy.auth import PrivyAuth, PrivyConfig
from langchain_privy.chains import Chain
from langchain_privy.rpc_client import PrivyRPCClient
from langchain_privy.wallet_tool import (
    PrivyGetWalletAddressTool,
    PrivySignMessageTool,
    PrivySendTransactionTool,
    PrivyWalletTool,
)


class TestPrivyWalletToolInit:
    """Test PrivyWalletTool initialization."""

    @patch.object(PrivyAuth, "create_wallet")
    def test_init_auto_creates_wallet(self, mock_create_wallet):
        """Test that wallet is auto-created on initialization."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xabc",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()

        assert tool.wallet_id == "wallet_123"
        assert tool.wallet_address == "0xabc"
        assert "ethereum" in tool.wallets
        mock_create_wallet.assert_called_once_with(chain_type="ethereum")

    @patch.object(PrivyAuth, "create_wallet")
    def test_init_with_custom_chain_type(self, mock_create_wallet):
        """Test initialization with custom chain type."""
        mock_create_wallet.return_value = {
            "id": "wallet_sol",
            "address": "sol_address",
            "chain_type": "solana",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool(chain_type="solana")

        assert "solana" in tool.wallets
        mock_create_wallet.assert_called_once_with(chain_type="solana")

    @patch.object(PrivyAuth, "get_wallet")
    def test_init_with_existing_wallet_id(self, mock_get_wallet):
        """Test initialization with existing wallet_id."""
        mock_get_wallet.return_value = {
            "id": "wallet_existing",
            "address": "0xexisting",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool(wallet_id="wallet_existing")

        assert tool.wallet_id == "wallet_existing"
        assert tool.wallet_address == "0xexisting"
        mock_get_wallet.assert_called_once_with("wallet_existing")

    def test_init_with_explicit_credentials(self):
        """Test initialization with explicit app_id and app_secret."""
        with patch.object(PrivyAuth, "create_wallet") as mock_create:
            mock_create.return_value = {
                "id": "wallet_1",
                "address": "0x1",
                "chain_type": "ethereum",
            }
            tool = PrivyWalletTool(app_id="app_id", app_secret="app_secret")

        assert tool.config.app_id == "app_id"
        assert tool.config.app_secret == "app_secret"

    def test_init_with_config_object(self):
        """Test initialization with PrivyConfig object."""
        config = PrivyConfig(app_id="config_app", app_secret="config_secret")

        with patch.object(PrivyAuth, "create_wallet") as mock_create:
            mock_create.return_value = {
                "id": "wallet_1",
                "address": "0x1",
                "chain_type": "ethereum",
            }
            tool = PrivyWalletTool(config=config)

        assert tool.config == config


class TestPrivyWalletToolProperties:
    """Test PrivyWalletTool properties."""

    @patch.object(PrivyAuth, "create_wallet")
    def test_wallet_id_property(self, mock_create_wallet):
        """Test wallet_id property returns first wallet ID."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xabc",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()

        assert tool.wallet_id == "wallet_123"

    @patch.object(PrivyAuth, "create_wallet")
    def test_wallet_address_property(self, mock_create_wallet):
        """Test wallet_address property returns first wallet address."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xaddress",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()

        assert tool.wallet_address == "0xaddress"

    @patch.object(PrivyAuth, "create_wallet")
    def test_get_wallet_for_chain(self, mock_create_wallet):
        """Test _get_wallet_for_chain method."""
        mock_create_wallet.return_value = {
            "id": "wallet_eth",
            "address": "0xeth",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()

        # Should find ethereum wallet for ethereum chain
        wallet = tool._get_wallet_for_chain("ethereum")
        assert wallet is not None
        assert wallet["id"] == "wallet_eth"

        # Should find ethereum wallet for base chain (same chain_type)
        wallet = tool._get_wallet_for_chain("base")
        assert wallet is not None

        # Should not find solana wallet
        wallet = tool._get_wallet_for_chain("solana")
        assert wallet is None


class TestPrivyWalletToolOperationRouting:
    """Test operation routing in _run method."""

    @patch.object(PrivyAuth, "create_wallet")
    def test_run_routes_to_create_wallet(self, mock_create_wallet):
        """Test that create_wallet operation is routed correctly."""
        mock_create_wallet.side_effect = [
            {"id": "wallet_eth", "address": "0xeth", "chain_type": "ethereum"},
            {"id": "wallet_sol", "address": "sol_addr", "chain_type": "solana"},
        ]

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._run(operation="create_wallet", chain="solana")

        assert "solana" in result.lower()
        assert "wallet_sol" in result

    @patch.object(PrivyAuth, "create_wallet")
    def test_run_routes_to_get_wallet_address(self, mock_create_wallet):
        """Test that get_wallet_address operation is routed correctly."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xabc",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._run(operation="get_wallet_address", chain="ethereum")

        assert "0xabc" in result

    @patch.object(PrivyAuth, "create_wallet")
    def test_run_invalid_operation(self, mock_create_wallet):
        """Test that invalid operation returns error."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xabc",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._run(operation="invalid_operation")

        assert "Error" in result or "Unsupported" in result

    @patch.object(PrivyAuth, "create_wallet")
    def test_run_normalizes_operation_name(self, mock_create_wallet):
        """Test that operation names are normalized (lowercase, stripped)."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xabc",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            # Test with uppercase and whitespace
            result = tool._run(operation="  GET_WALLET_ADDRESS  ", chain="ethereum")

        assert "0xabc" in result


class TestCreateWalletOperation:
    """Test _create_wallet operation."""

    @patch.object(PrivyAuth, "create_wallet")
    def test_create_wallet_success(self, mock_create_wallet):
        """Test successful wallet creation."""
        mock_create_wallet.side_effect = [
            {"id": "wallet_eth", "address": "0xeth", "chain_type": "ethereum"},
            {"id": "wallet_sol", "address": "sol_addr", "chain_type": "solana"},
        ]

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._create_wallet(chain="solana")

        assert "created successfully" in result.lower()
        assert "wallet_sol" in result
        assert "sol_addr" in result
        assert "solana" in tool.wallets

    @patch.object(PrivyAuth, "create_wallet")
    def test_create_wallet_already_exists(self, mock_create_wallet):
        """Test error when wallet already exists for chain type."""
        mock_create_wallet.return_value = {
            "id": "wallet_eth",
            "address": "0xeth",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            # Try to create another ethereum wallet (base uses ethereum chain_type)
            result = tool._create_wallet(chain="base")

        assert "already exists" in result.lower()

    @patch.object(PrivyAuth, "create_wallet")
    def test_create_wallet_error_handling(self, mock_create_wallet):
        """Test error handling in wallet creation."""
        mock_create_wallet.side_effect = [
            {"id": "wallet_eth", "address": "0xeth", "chain_type": "ethereum"},
            Exception("API error"),
        ]

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._create_wallet(chain="solana")

        assert "Error" in result
        assert "API error" in result


class TestGetWalletAddressOperation:
    """Test _get_wallet_address operation."""

    @patch.object(PrivyAuth, "create_wallet")
    def test_get_wallet_address_success(self, mock_create_wallet):
        """Test getting wallet address successfully."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xmyaddress",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._get_wallet_address(chain="ethereum")

        assert "0xmyaddress" in result

    @patch.object(PrivyAuth, "create_wallet")
    def test_get_wallet_address_no_wallet(self, mock_create_wallet):
        """Test error when no wallet exists for chain."""
        mock_create_wallet.return_value = {
            "id": "wallet_eth",
            "address": "0xeth",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._get_wallet_address(chain="solana")

        assert "No" in result and "wallet found" in result
        assert "create_wallet" in result.lower()


class TestSendTransactionOperation:
    """Test _send_transaction operation."""

    @patch.object(PrivyAuth, "create_wallet")
    @patch.object(PrivyRPCClient, "send_transaction")
    def test_send_transaction_success(self, mock_send_tx, mock_create_wallet):
        """Test successful transaction sending."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xsender",
            "chain_type": "ethereum",
        }
        mock_send_tx.return_value = {
            "data": {"hash": "0xtxhash", "transaction_id": "tx_123"}
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._send_transaction(
                to="0xrecipient", value="1000", chain="ethereum"
            )

        assert "0xtxhash" in result
        assert "tx_123" in result
        assert "successfully" in result.lower()

    @patch.object(PrivyAuth, "create_wallet")
    def test_send_transaction_no_wallet(self, mock_create_wallet):
        """Test error when no wallet for chain."""
        mock_create_wallet.return_value = {
            "id": "wallet_eth",
            "address": "0xeth",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._send_transaction(
                to="0xrecipient", value="1000", chain="solana"
            )

        assert "No" in result and "wallet found" in result

    @patch.object(PrivyAuth, "create_wallet")
    @patch.object(PrivyRPCClient, "send_transaction")
    def test_send_transaction_with_data(self, mock_send_tx, mock_create_wallet):
        """Test sending transaction with data parameter."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xsender",
            "chain_type": "ethereum",
        }
        mock_send_tx.return_value = {
            "data": {"hash": "0xtx", "transaction_id": "tx_1"}
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            tool._send_transaction(
                to="0xrecipient", value="1000", chain="ethereum", data="0xabcd"
            )

        # Verify data was passed
        call_kwargs = mock_send_tx.call_args.kwargs
        assert call_kwargs["data"] == "0xabcd"


class TestSignMessageOperation:
    """Test _sign_message operation."""

    @patch.object(PrivyAuth, "create_wallet")
    @patch.object(PrivyRPCClient, "sign_message")
    def test_sign_message_success(self, mock_sign, mock_create_wallet):
        """Test successful message signing."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xaddr",
            "chain_type": "ethereum",
        }
        mock_sign.return_value = {"data": {"signature": "0xsig123"}}

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._sign_message(message="Hello World", chain="ethereum")

        assert "0xsig123" in result
        assert "successfully" in result.lower()

    @patch.object(PrivyAuth, "create_wallet")
    def test_sign_message_no_wallet(self, mock_create_wallet):
        """Test error when no wallet for chain."""
        mock_create_wallet.return_value = {
            "id": "wallet_eth",
            "address": "0xeth",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._sign_message(message="Test", chain="solana")

        assert "No" in result and "wallet found" in result


class TestGetBalanceOperation:
    """Test _get_balance operation."""

    @patch.object(PrivyAuth, "create_wallet")
    @patch.object(PrivyRPCClient, "get_balance")
    def test_get_balance_ethereum(self, mock_get_balance, mock_create_wallet):
        """Test getting balance on Ethereum."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xaddr",
            "chain_type": "ethereum",
        }
        mock_get_balance.return_value = {
            "balances": [
                {
                    "raw_value": "1000000000000000000",
                    "raw_value_decimals": 18,
                    "display_values": {"eth": "1.0"},
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._get_balance(chain="ethereum")

        assert "1.0" in result
        assert "ETH" in result

    @patch.object(PrivyAuth, "create_wallet")
    @patch.object(PrivyRPCClient, "get_balance")
    def test_get_balance_solana(self, mock_get_balance, mock_create_wallet):
        """Test getting balance on Solana (uses SOL)."""
        mock_create_wallet.return_value = {
            "id": "wallet_sol",
            "address": "sol_addr",
            "chain_type": "solana",
        }
        mock_get_balance.return_value = {
            "balances": [
                {
                    "raw_value": "5000000000",
                    "raw_value_decimals": 9,
                    "display_values": {"sol": "5.0"},
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool(chain_type="solana")
            result = tool._get_balance(chain="solana")

        assert "5.0" in result
        assert "SOL" in result
        mock_get_balance.assert_called_with(chain="solana", asset="sol")

    @patch.object(PrivyAuth, "create_wallet")
    @patch.object(PrivyRPCClient, "get_balance")
    def test_get_balance_zero(self, mock_get_balance, mock_create_wallet):
        """Test balance when wallet has zero balance."""
        mock_create_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xaddr",
            "chain_type": "ethereum",
        }
        mock_get_balance.return_value = {"balances": []}

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._get_balance(chain="ethereum")

        assert "0" in result
        assert "ETH" in result

    @patch.object(PrivyAuth, "create_wallet")
    def test_get_balance_no_wallet(self, mock_create_wallet):
        """Test error when no wallet for chain."""
        mock_create_wallet.return_value = {
            "id": "wallet_eth",
            "address": "0xeth",
            "chain_type": "ethereum",
        }

        with patch.dict(
            "os.environ",
            {"PRIVY_APP_ID": "test_app", "PRIVY_APP_SECRET": "test_secret"},
        ):
            tool = PrivyWalletTool()
            result = tool._get_balance(chain="solana")

        assert "No" in result and "wallet found" in result


class TestSpecializedTools:
    """Test specialized tool classes."""

    def test_privy_get_wallet_address_tool(self):
        """Test PrivyGetWalletAddressTool initialization."""
        config = PrivyConfig(app_id="test", app_secret="secret")

        with patch.object(PrivyRPCClient, "__init__", return_value=None):
            tool = PrivyGetWalletAddressTool(
                config=config, wallet_id="wallet_123", wallet_address="0xaddr"
            )

        assert tool.name == "get_wallet_address"
        assert tool.wallet_id == "wallet_123"

    @patch.object(PrivyRPCClient, "get_wallet_address")
    def test_privy_get_wallet_address_tool_run(self, mock_get_address):
        """Test PrivyGetWalletAddressTool._run."""
        mock_get_address.return_value = "0xmyaddress"
        config = PrivyConfig(app_id="test", app_secret="secret")

        tool = PrivyGetWalletAddressTool(
            config=config, wallet_id="wallet_123", wallet_address="0xmyaddress"
        )
        result = tool._run(chain="ethereum")

        assert "0xmyaddress" in result

    def test_privy_send_transaction_tool(self):
        """Test PrivySendTransactionTool initialization."""
        config = PrivyConfig(app_id="test", app_secret="secret")

        with patch.object(PrivyRPCClient, "__init__", return_value=None):
            tool = PrivySendTransactionTool(config=config, wallet_id="wallet_123")

        assert tool.name == "send_transaction"

    @patch.object(PrivyRPCClient, "send_transaction")
    def test_privy_send_transaction_tool_run(self, mock_send_tx):
        """Test PrivySendTransactionTool._run."""
        mock_send_tx.return_value = {"data": {"hash": "0xtxhash"}}
        config = PrivyConfig(app_id="test", app_secret="secret")

        tool = PrivySendTransactionTool(config=config, wallet_id="wallet_123")
        result = tool._run(to="0xrecipient", value="1000", chain="ethereum")

        assert "0xtxhash" in result

    def test_privy_sign_message_tool(self):
        """Test PrivySignMessageTool initialization."""
        config = PrivyConfig(app_id="test", app_secret="secret")

        with patch.object(PrivyRPCClient, "__init__", return_value=None):
            tool = PrivySignMessageTool(config=config, wallet_id="wallet_123")

        assert tool.name == "sign_message"

    @patch.object(PrivyRPCClient, "sign_message")
    def test_privy_sign_message_tool_run(self, mock_sign):
        """Test PrivySignMessageTool._run."""
        mock_sign.return_value = {"data": {"signature": "0xsig"}}
        config = PrivyConfig(app_id="test", app_secret="secret")

        tool = PrivySignMessageTool(config=config, wallet_id="wallet_123")
        result = tool._run(message="Hello", chain="ethereum")

        assert "0xsig" in result
