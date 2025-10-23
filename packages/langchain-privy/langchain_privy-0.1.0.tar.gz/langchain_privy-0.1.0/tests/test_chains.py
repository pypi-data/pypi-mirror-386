"""Tests for chain configuration module."""

import pytest

from langchain_privy.chains import (
    Chain,
    get_chain_by_caip2,
    get_chain_by_chain_id,
    get_chain_config,
    is_evm_chain,
    is_testnet,
)


class TestChainConfig:
    """Test chain configuration utilities."""

    def test_get_chain_config_with_enum(self):
        """Test getting chain config with Chain enum."""
        config = get_chain_config(Chain.ETHEREUM)
        assert config.chain == Chain.ETHEREUM
        assert config.chain_id == 1
        assert config.chain_type == "ethereum"
        assert config.caip2 == "eip155:1"
        assert config.is_testnet is False
        assert config.native_currency == "ETH"

    def test_get_chain_config_with_string(self):
        """Test getting chain config with string."""
        config = get_chain_config("base")
        assert config.chain == Chain.BASE
        assert config.chain_id == 8453
        assert config.chain_type == "ethereum"

    def test_get_chain_config_invalid(self):
        """Test getting chain config with invalid chain."""
        with pytest.raises(ValueError, match="Unsupported chain"):
            get_chain_config("invalid-chain")

    def test_get_chain_by_caip2_ethereum(self):
        """Test getting chain by CAIP-2 identifier for Ethereum."""
        config = get_chain_by_caip2("eip155:1")
        assert config.chain == Chain.ETHEREUM
        assert config.chain_id == 1

    def test_get_chain_by_caip2_base(self):
        """Test getting chain by CAIP-2 identifier for Base."""
        config = get_chain_by_caip2("eip155:8453")
        assert config.chain == Chain.BASE
        assert config.chain_id == 8453

    def test_get_chain_by_caip2_solana(self):
        """Test getting chain by CAIP-2 identifier for Solana."""
        config = get_chain_by_caip2("solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp")
        assert config.chain == Chain.SOLANA
        assert config.chain_id is None
        assert config.chain_type == "solana"

    def test_get_chain_by_caip2_invalid(self):
        """Test getting chain by invalid CAIP-2 identifier."""
        with pytest.raises(ValueError, match="Unknown CAIP-2 identifier"):
            get_chain_by_caip2("invalid:123")

    def test_get_chain_by_chain_id_ethereum(self):
        """Test getting chain by chain ID for Ethereum."""
        config = get_chain_by_chain_id(1)
        assert config.chain == Chain.ETHEREUM

    def test_get_chain_by_chain_id_base(self):
        """Test getting chain by chain ID for Base."""
        config = get_chain_by_chain_id(8453)
        assert config.chain == Chain.BASE

    def test_get_chain_by_chain_id_invalid(self):
        """Test getting chain by invalid chain ID."""
        with pytest.raises(ValueError, match="Unknown chain ID"):
            get_chain_by_chain_id(999999)

    def test_is_evm_chain_ethereum(self):
        """Test checking if Ethereum is EVM chain."""
        assert is_evm_chain(Chain.ETHEREUM) is True
        assert is_evm_chain("ethereum") is True

    def test_is_evm_chain_base(self):
        """Test checking if Base is EVM chain."""
        assert is_evm_chain(Chain.BASE) is True

    def test_is_evm_chain_solana(self):
        """Test checking if Solana is EVM chain."""
        assert is_evm_chain(Chain.SOLANA) is False
        assert is_evm_chain("solana") is False

    def test_is_evm_chain_bitcoin(self):
        """Test checking if Bitcoin is EVM chain."""
        assert is_evm_chain(Chain.BITCOIN) is False

    def test_is_testnet_mainnet(self):
        """Test checking if mainnet chains are not testnets."""
        assert is_testnet(Chain.ETHEREUM) is False
        assert is_testnet(Chain.BASE) is False
        assert is_testnet(Chain.SOLANA) is False

    def test_is_testnet_testnet(self):
        """Test checking if testnet chains are testnets."""
        assert is_testnet(Chain.ETHEREUM_SEPOLIA) is True
        assert is_testnet(Chain.BASE_SEPOLIA) is True
        assert is_testnet(Chain.SOLANA_DEVNET) is True

    def test_all_evm_chains_have_chain_id(self):
        """Test that all EVM chains have a chain ID."""
        for chain in Chain:
            config = get_chain_config(chain)
            if config.chain_type == "ethereum":
                assert config.chain_id is not None, f"{chain} is missing chain_id"

    def test_all_chains_have_caip2(self):
        """Test that all chains have a CAIP-2 identifier."""
        for chain in Chain:
            config = get_chain_config(chain)
            assert config.caip2, f"{chain} is missing caip2"
            assert ":" in config.caip2, f"{chain} has invalid caip2 format"
