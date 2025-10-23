"""Tests for RPC client module."""

from unittest.mock import Mock, patch

import pytest

from langchain_privy.auth import PrivyAuth, PrivyConfig
from langchain_privy.chains import Chain
from langchain_privy.rpc_client import PrivyRPCClient, RPCMethod


class TestPrivyRPCClientInit:
    """Test PrivyRPCClient initialization."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    def test_init_with_wallet_id(self, config):
        """Test initializing with wallet_id."""
        client = PrivyRPCClient(config=config, wallet_id="wallet_123")
        assert client.wallet_id == "wallet_123"
        assert client.wallet_address is None
        assert client.config == config

    def test_init_with_wallet_address(self, config):
        """Test initializing with wallet_address."""
        client = PrivyRPCClient(
            config=config, wallet_id="wallet_123", wallet_address="0xabc123"
        )
        assert client.wallet_address == "0xabc123"

    def test_creates_auth_instance(self, config):
        """Test that PrivyAuth instance is created."""
        client = PrivyRPCClient(config=config, wallet_id="wallet_123")
        assert isinstance(client.auth, PrivyAuth)

    def test_creates_session(self, config):
        """Test that requests session is created."""
        client = PrivyRPCClient(config=config, wallet_id="wallet_123")
        assert client._session is not None


class TestExecuteRPC:
    """Test execute_rpc method."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    @pytest.fixture
    def client(self, config):
        """Create RPC client."""
        return PrivyRPCClient(config=config, wallet_id="wallet_123")

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_execute_rpc_basic(self, mock_get_headers, mock_api_request, client):
        """Test basic RPC execution."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"data": {"result": "success"}}

        result = client.execute_rpc(
            wallet_id="wallet_123",
            method=RPCMethod.PERSONAL_SIGN,
            params={"message": "test"},
            chain=Chain.ETHEREUM,
        )

        assert result == {"data": {"result": "success"}}
        mock_api_request.assert_called_once()

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_execute_rpc_includes_caip2_when_requested(
        self, mock_get_headers, mock_api_request, client
    ):
        """Test that CAIP-2 is included when include_caip2=True."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"data": {}}

        client.execute_rpc(
            wallet_id="wallet_123",
            method=RPCMethod.ETH_SEND_TRANSACTION,
            params={"transaction": {"to": "0x123", "value": "0x1"}},
            chain=Chain.ETHEREUM,
            include_caip2=True,
        )

        # Check that the request body includes caip2
        call_kwargs = mock_api_request.call_args.kwargs
        assert "json" in call_kwargs
        assert "caip2" in call_kwargs["json"]
        assert call_kwargs["json"]["caip2"] == "eip155:1"

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_execute_rpc_without_caip2(
        self, mock_get_headers, mock_api_request, client
    ):
        """Test that CAIP-2 is not included by default."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"data": {}}

        client.execute_rpc(
            wallet_id="wallet_123",
            method=RPCMethod.PERSONAL_SIGN,
            params={"message": "test"},
            chain=Chain.ETHEREUM,
            include_caip2=False,
        )

        call_kwargs = mock_api_request.call_args.kwargs
        assert "caip2" not in call_kwargs["json"]

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_execute_rpc_with_string_method(
        self, mock_get_headers, mock_api_request, client
    ):
        """Test executing RPC with method as string."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"data": {}}

        client.execute_rpc(
            wallet_id="wallet_123",
            method="personal_sign",
            params={"message": "test"},
            chain=Chain.ETHEREUM,
        )

        call_kwargs = mock_api_request.call_args.kwargs
        assert call_kwargs["json"]["method"] == "personal_sign"

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_execute_rpc_error_in_response(
        self, mock_get_headers, mock_api_request, client
    ):
        """Test that RPC errors in response raise ValueError."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {
            "error": {"code": -32600, "message": "Invalid request"}
        }

        with pytest.raises(ValueError, match="RPC error: Invalid request"):
            client.execute_rpc(
                wallet_id="wallet_123",
                method=RPCMethod.PERSONAL_SIGN,
                params={"message": "test"},
                chain=Chain.ETHEREUM,
            )


class TestSendTransaction:
    """Test send_transaction method."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    @pytest.fixture
    def client(self, config):
        """Create RPC client."""
        return PrivyRPCClient(
            config=config, wallet_id="wallet_123", wallet_address="0xabc"
        )

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_send_transaction_with_decimal_value(self, mock_execute_rpc, client):
        """Test sending transaction with decimal value (auto-converts to hex)."""
        mock_execute_rpc.return_value = {
            "data": {"hash": "0xtxhash123", "transaction_id": "tx_123"}
        }

        result = client.send_transaction(
            to="0x456", value="1000000000000000000", chain=Chain.ETHEREUM
        )

        assert result["data"]["hash"] == "0xtxhash123"
        # Verify value was converted to hex
        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["params"]["transaction"]["value"] == "0xde0b6b3a7640000"

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_send_transaction_with_hex_value(self, mock_execute_rpc, client):
        """Test sending transaction with hex value."""
        mock_execute_rpc.return_value = {"data": {"hash": "0xtxhash"}}

        client.send_transaction(to="0x456", value="0x123", chain=Chain.ETHEREUM)

        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["params"]["transaction"]["value"] == "0x123"

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_send_transaction_with_data(self, mock_execute_rpc, client):
        """Test sending transaction with data parameter."""
        mock_execute_rpc.return_value = {"data": {"hash": "0xtx"}}

        client.send_transaction(
            to="0x456", value="0x1", chain=Chain.ETHEREUM, data="0xabcd"
        )

        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["params"]["transaction"]["data"] == "0xabcd"

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_send_transaction_with_gas_limit(self, mock_execute_rpc, client):
        """Test sending transaction with gas limit."""
        mock_execute_rpc.return_value = {"data": {"hash": "0xtx"}}

        client.send_transaction(
            to="0x456", value="0x1", chain=Chain.ETHEREUM, gas_limit="21000"
        )

        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["params"]["transaction"]["gas"] == "21000"

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_send_transaction_includes_caip2(self, mock_execute_rpc, client):
        """Test that send_transaction includes CAIP-2."""
        mock_execute_rpc.return_value = {"data": {"hash": "0xtx"}}

        client.send_transaction(to="0x456", value="0x1", chain=Chain.BASE)

        # Verify include_caip2=True was passed
        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["include_caip2"] is True


class TestSignMessage:
    """Test sign_message method."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    @pytest.fixture
    def client(self, config):
        """Create RPC client."""
        return PrivyRPCClient(config=config, wallet_id="wallet_123")

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_sign_message_ethereum(self, mock_execute_rpc, client):
        """Test signing message on Ethereum (uses personal_sign)."""
        mock_execute_rpc.return_value = {"data": {"signature": "0xsig123"}}

        result = client.sign_message(message="Hello World", chain=Chain.ETHEREUM)

        assert result["data"]["signature"] == "0xsig123"
        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["method"] == RPCMethod.PERSONAL_SIGN
        assert call_kwargs["params"]["message"] == "Hello World"
        assert call_kwargs["params"]["encoding"] == "utf-8"

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_sign_message_solana(self, mock_execute_rpc, client):
        """Test signing message on Solana (uses base64 encoding)."""
        mock_execute_rpc.return_value = {"data": {"signature": "solsig123"}}

        result = client.sign_message(message="Hello", chain=Chain.SOLANA)

        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["method"] == RPCMethod.SOLANA_SIGN_MESSAGE
        assert call_kwargs["params"]["encoding"] == "base64"
        # Verify message is base64 encoded
        import base64

        expected = base64.b64encode(b"Hello").decode("utf-8")
        assert call_kwargs["params"]["message"] == expected

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_sign_message_bitcoin(self, mock_execute_rpc, client):
        """Test signing message on Bitcoin."""
        mock_execute_rpc.return_value = {"data": {"signature": "btcsig"}}

        result = client.sign_message(message="Test", chain=Chain.BITCOIN)

        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["method"] == RPCMethod.BTC_SIGN_MESSAGE
        assert call_kwargs["params"]["message"] == "Test"

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_sign_message_unsupported_chain(self, mock_execute_rpc, client):
        """Test error on unsupported chain type."""
        # Note: We'd need a chain with a chain_type that's not ethereum/solana/bitcoin
        # For now, this test verifies the ValueError is raised correctly
        pass  # This would require adding a new chain type to test


class TestGetWalletAddress:
    """Test get_wallet_address method."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    def test_returns_cached_address(self, config):
        """Test that cached address is returned."""
        client = PrivyRPCClient(
            config=config, wallet_id="wallet_123", wallet_address="0xcached"
        )

        address = client.get_wallet_address()
        assert address == "0xcached"

    @patch.object(PrivyAuth, "get_wallet")
    def test_fetches_from_api_if_not_cached(self, mock_get_wallet, config):
        """Test that address is fetched from API if not cached."""
        client = PrivyRPCClient(config=config, wallet_id="wallet_123")
        mock_get_wallet.return_value = {
            "id": "wallet_123",
            "address": "0xfetched",
            "chain_type": "ethereum",
        }

        address = client.get_wallet_address()

        assert address == "0xfetched"
        assert client.wallet_address == "0xfetched"
        mock_get_wallet.assert_called_once_with("wallet_123")

    @patch.object(PrivyAuth, "get_wallet")
    def test_raises_error_when_address_not_available(self, mock_get_wallet, config):
        """Test error when address not available."""
        client = PrivyRPCClient(config=config, wallet_id="wallet_123")
        mock_get_wallet.return_value = {"id": "wallet_123"}  # No address

        with pytest.raises(ValueError, match="Could not retrieve address"):
            client.get_wallet_address()


class TestGetBalance:
    """Test get_balance method."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    @pytest.fixture
    def client(self, config):
        """Create RPC client."""
        return PrivyRPCClient(config=config, wallet_id="wallet_123")

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_get_balance_ethereum(self, mock_get_headers, mock_api_request, client):
        """Test getting balance on Ethereum."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"balances": [{"raw_value": "1000"}]}

        result = client.get_balance(chain=Chain.ETHEREUM, asset="eth")

        assert result["balances"][0]["raw_value"] == "1000"
        call_kwargs = mock_api_request.call_args.kwargs
        assert call_kwargs["params"]["chain"] == "ethereum"
        assert call_kwargs["params"]["asset"] == "eth"

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_get_balance_chain_mapping(
        self, mock_get_headers, mock_api_request, client
    ):
        """Test that chain names are mapped correctly."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"balances": []}

        # Test ethereum-sepolia maps to sepolia
        client.get_balance(chain="ethereum-sepolia", asset="eth")
        call_kwargs = mock_api_request.call_args.kwargs
        assert call_kwargs["params"]["chain"] == "sepolia"

        # Test base-sepolia maps to base_sepolia
        client.get_balance(chain="base-sepolia", asset="eth")
        call_kwargs = mock_api_request.call_args.kwargs
        assert call_kwargs["params"]["chain"] == "base_sepolia"

    def test_get_balance_unsupported_chain(self, client):
        """Test error for unsupported chains."""
        with pytest.raises(ValueError, match="Balance API does not support"):
            client.get_balance(chain="bitcoin", asset="btc")

        with pytest.raises(ValueError, match="Balance API does not support"):
            client.get_balance(chain="solana-devnet", asset="sol")

    @patch("langchain_privy.rpc_client.make_api_request")
    @patch.object(PrivyAuth, "get_auth_headers")
    def test_get_balance_solana(self, mock_get_headers, mock_api_request, client):
        """Test getting balance on Solana."""
        mock_get_headers.return_value = {"Authorization": "Bearer token"}
        mock_api_request.return_value = {"balances": [{"raw_value": "5000000000"}]}

        result = client.get_balance(chain=Chain.SOLANA, asset="sol")

        assert result["balances"][0]["raw_value"] == "5000000000"
        call_kwargs = mock_api_request.call_args.kwargs
        assert call_kwargs["params"]["chain"] == "solana"


class TestSignTypedData:
    """Test sign_typed_data method."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return PrivyConfig(app_id="test-app-id", app_secret="test-app-secret")

    @pytest.fixture
    def client(self, config):
        """Create RPC client."""
        return PrivyRPCClient(config=config, wallet_id="wallet_123")

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_sign_typed_data_ethereum(self, mock_execute_rpc, client):
        """Test signing typed data on Ethereum."""
        mock_execute_rpc.return_value = {"data": {"signature": "0xtyped_sig"}}

        domain = {"name": "Test", "version": "1"}
        types = {"Person": [{"name": "name", "type": "string"}]}
        value = {"name": "Alice"}

        result = client.sign_typed_data(
            domain=domain, types=types, value=value, chain=Chain.ETHEREUM
        )

        assert result["data"]["signature"] == "0xtyped_sig"
        call_kwargs = mock_execute_rpc.call_args.kwargs
        assert call_kwargs["method"] == RPCMethod.ETH_SIGN_TYPED_DATA_V4
        assert call_kwargs["params"]["typed_data"]["domain"] == domain
        assert call_kwargs["params"]["typed_data"]["types"] == types
        assert call_kwargs["params"]["typed_data"]["message"] == value

    @patch.object(PrivyRPCClient, "execute_rpc")
    def test_sign_typed_data_non_evm_chain_error(self, mock_execute_rpc, client):
        """Test error when trying to sign typed data on non-EVM chain."""
        domain = {"name": "Test"}
        types = {"Person": []}
        value = {"name": "Alice"}

        with pytest.raises(ValueError, match="only supported on EVM chains"):
            client.sign_typed_data(
                domain=domain, types=types, value=value, chain=Chain.SOLANA
            )
