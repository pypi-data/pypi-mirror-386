"""Chain configuration utilities for multi-chain support."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Chain(str, Enum):
    """Supported blockchain networks."""

    # Ethereum and EVM chains
    ETHEREUM = "ethereum"
    ETHEREUM_SEPOLIA = "ethereum-sepolia"
    ETHEREUM_HOLESKY = "ethereum-holesky"

    # Layer 2 chains
    BASE = "base"
    BASE_SEPOLIA = "base-sepolia"
    OPTIMISM = "optimism"
    OPTIMISM_SEPOLIA = "optimism-sepolia"
    ARBITRUM = "arbitrum"
    ARBITRUM_SEPOLIA = "arbitrum-sepolia"
    POLYGON = "polygon"
    POLYGON_AMOY = "polygon-amoy"
    ZORA = "zora"
    ZORA_SEPOLIA = "zora-sepolia"

    # Other EVM chains
    AVALANCHE = "avalanche"
    AVALANCHE_FUJI = "avalanche-fuji"
    BSC = "bsc"
    BSC_TESTNET = "bsc-testnet"
    CELO = "celo"
    CELO_ALFAJORES = "celo-alfajores"
    LINEA = "linea"
    LINEA_SEPOLIA = "linea-sepolia"

    # Non-EVM chains
    SOLANA = "solana"
    SOLANA_DEVNET = "solana-devnet"
    BITCOIN = "bitcoin"
    BITCOIN_TESTNET = "bitcoin-testnet"


@dataclass
class ChainConfig:
    """Configuration for a blockchain network.

    Attributes:
        chain: The chain identifier
        chain_id: Numeric chain ID (for EVM chains)
        chain_type: The type of chain (ethereum, solana, bitcoin)
        caip2: CAIP-2 format identifier
        is_testnet: Whether this is a testnet
        native_currency: Native currency symbol
    """

    chain: Chain
    chain_id: Optional[int]
    chain_type: str
    caip2: str
    is_testnet: bool
    native_currency: str


# Chain configuration mapping
CHAIN_CONFIGS: dict[Chain, ChainConfig] = {
    # Ethereum Mainnet
    Chain.ETHEREUM: ChainConfig(
        chain=Chain.ETHEREUM,
        chain_id=1,
        chain_type="ethereum",
        caip2="eip155:1",
        is_testnet=False,
        native_currency="ETH",
    ),
    Chain.ETHEREUM_SEPOLIA: ChainConfig(
        chain=Chain.ETHEREUM_SEPOLIA,
        chain_id=11155111,
        chain_type="ethereum",
        caip2="eip155:11155111",
        is_testnet=True,
        native_currency="ETH",
    ),
    Chain.ETHEREUM_HOLESKY: ChainConfig(
        chain=Chain.ETHEREUM_HOLESKY,
        chain_id=17000,
        chain_type="ethereum",
        caip2="eip155:17000",
        is_testnet=True,
        native_currency="ETH",
    ),
    # Base
    Chain.BASE: ChainConfig(
        chain=Chain.BASE,
        chain_id=8453,
        chain_type="ethereum",
        caip2="eip155:8453",
        is_testnet=False,
        native_currency="ETH",
    ),
    Chain.BASE_SEPOLIA: ChainConfig(
        chain=Chain.BASE_SEPOLIA,
        chain_id=84532,
        chain_type="ethereum",
        caip2="eip155:84532",
        is_testnet=True,
        native_currency="ETH",
    ),
    # Optimism
    Chain.OPTIMISM: ChainConfig(
        chain=Chain.OPTIMISM,
        chain_id=10,
        chain_type="ethereum",
        caip2="eip155:10",
        is_testnet=False,
        native_currency="ETH",
    ),
    Chain.OPTIMISM_SEPOLIA: ChainConfig(
        chain=Chain.OPTIMISM_SEPOLIA,
        chain_id=11155420,
        chain_type="ethereum",
        caip2="eip155:11155420",
        is_testnet=True,
        native_currency="ETH",
    ),
    # Arbitrum
    Chain.ARBITRUM: ChainConfig(
        chain=Chain.ARBITRUM,
        chain_id=42161,
        chain_type="ethereum",
        caip2="eip155:42161",
        is_testnet=False,
        native_currency="ETH",
    ),
    Chain.ARBITRUM_SEPOLIA: ChainConfig(
        chain=Chain.ARBITRUM_SEPOLIA,
        chain_id=421614,
        chain_type="ethereum",
        caip2="eip155:421614",
        is_testnet=True,
        native_currency="ETH",
    ),
    # Polygon
    Chain.POLYGON: ChainConfig(
        chain=Chain.POLYGON,
        chain_id=137,
        chain_type="ethereum",
        caip2="eip155:137",
        is_testnet=False,
        native_currency="MATIC",
    ),
    Chain.POLYGON_AMOY: ChainConfig(
        chain=Chain.POLYGON_AMOY,
        chain_id=80002,
        chain_type="ethereum",
        caip2="eip155:80002",
        is_testnet=True,
        native_currency="MATIC",
    ),
    # Zora
    Chain.ZORA: ChainConfig(
        chain=Chain.ZORA,
        chain_id=7777777,
        chain_type="ethereum",
        caip2="eip155:7777777",
        is_testnet=False,
        native_currency="ETH",
    ),
    Chain.ZORA_SEPOLIA: ChainConfig(
        chain=Chain.ZORA_SEPOLIA,
        chain_id=999999999,
        chain_type="ethereum",
        caip2="eip155:999999999",
        is_testnet=True,
        native_currency="ETH",
    ),
    # Avalanche
    Chain.AVALANCHE: ChainConfig(
        chain=Chain.AVALANCHE,
        chain_id=43114,
        chain_type="ethereum",
        caip2="eip155:43114",
        is_testnet=False,
        native_currency="AVAX",
    ),
    Chain.AVALANCHE_FUJI: ChainConfig(
        chain=Chain.AVALANCHE_FUJI,
        chain_id=43113,
        chain_type="ethereum",
        caip2="eip155:43113",
        is_testnet=True,
        native_currency="AVAX",
    ),
    # BSC
    Chain.BSC: ChainConfig(
        chain=Chain.BSC,
        chain_id=56,
        chain_type="ethereum",
        caip2="eip155:56",
        is_testnet=False,
        native_currency="BNB",
    ),
    Chain.BSC_TESTNET: ChainConfig(
        chain=Chain.BSC_TESTNET,
        chain_id=97,
        chain_type="ethereum",
        caip2="eip155:97",
        is_testnet=True,
        native_currency="BNB",
    ),
    # Celo
    Chain.CELO: ChainConfig(
        chain=Chain.CELO,
        chain_id=42220,
        chain_type="ethereum",
        caip2="eip155:42220",
        is_testnet=False,
        native_currency="CELO",
    ),
    Chain.CELO_ALFAJORES: ChainConfig(
        chain=Chain.CELO_ALFAJORES,
        chain_id=44787,
        chain_type="ethereum",
        caip2="eip155:44787",
        is_testnet=True,
        native_currency="CELO",
    ),
    # Linea
    Chain.LINEA: ChainConfig(
        chain=Chain.LINEA,
        chain_id=59144,
        chain_type="ethereum",
        caip2="eip155:59144",
        is_testnet=False,
        native_currency="ETH",
    ),
    Chain.LINEA_SEPOLIA: ChainConfig(
        chain=Chain.LINEA_SEPOLIA,
        chain_id=59141,
        chain_type="ethereum",
        caip2="eip155:59141",
        is_testnet=True,
        native_currency="ETH",
    ),
    # Solana
    Chain.SOLANA: ChainConfig(
        chain=Chain.SOLANA,
        chain_id=None,
        chain_type="solana",
        caip2="solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
        is_testnet=False,
        native_currency="SOL",
    ),
    Chain.SOLANA_DEVNET: ChainConfig(
        chain=Chain.SOLANA_DEVNET,
        chain_id=None,
        chain_type="solana",
        caip2="solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1",
        is_testnet=True,
        native_currency="SOL",
    ),
    # Bitcoin
    Chain.BITCOIN: ChainConfig(
        chain=Chain.BITCOIN,
        chain_id=None,
        chain_type="bitcoin",
        caip2="bip122:000000000019d6689c085ae165831e93",
        is_testnet=False,
        native_currency="BTC",
    ),
    Chain.BITCOIN_TESTNET: ChainConfig(
        chain=Chain.BITCOIN_TESTNET,
        chain_id=None,
        chain_type="bitcoin",
        caip2="bip122:000000000933ea01ad0ee984209779ba",
        is_testnet=True,
        native_currency="BTC",
    ),
}


def get_chain_config(chain: Chain | str) -> ChainConfig:
    """Get configuration for a specific chain.

    Args:
        chain: Chain identifier (as Chain enum or string)

    Returns:
        ChainConfig object for the specified chain

    Raises:
        ValueError: If chain is not supported
    """
    if isinstance(chain, str):
        try:
            chain = Chain(chain)
        except ValueError:
            raise ValueError(f"Unsupported chain: {chain}")

    config = CHAIN_CONFIGS.get(chain)
    if not config:
        raise ValueError(f"No configuration found for chain: {chain}")

    return config


def get_chain_by_caip2(caip2: str) -> ChainConfig:
    """Get chain configuration by CAIP-2 identifier.

    Args:
        caip2: CAIP-2 format chain identifier (e.g., "eip155:1")

    Returns:
        ChainConfig object for the specified chain

    Raises:
        ValueError: If CAIP-2 identifier is not recognized
    """
    for config in CHAIN_CONFIGS.values():
        if config.caip2 == caip2:
            return config

    raise ValueError(f"Unknown CAIP-2 identifier: {caip2}")


def get_chain_by_chain_id(chain_id: int) -> ChainConfig:
    """Get chain configuration by numeric chain ID (EVM chains only).

    Args:
        chain_id: Numeric chain ID

    Returns:
        ChainConfig object for the specified chain

    Raises:
        ValueError: If chain ID is not recognized
    """
    for config in CHAIN_CONFIGS.values():
        if config.chain_id == chain_id:
            return config

    raise ValueError(f"Unknown chain ID: {chain_id}")


def is_evm_chain(chain: Chain | str) -> bool:
    """Check if a chain is an EVM-compatible chain.

    Args:
        chain: Chain identifier

    Returns:
        True if chain is EVM-compatible, False otherwise
    """
    config = get_chain_config(chain)
    return config.chain_type == "ethereum"


def is_testnet(chain: Chain | str) -> bool:
    """Check if a chain is a testnet.

    Args:
        chain: Chain identifier

    Returns:
        True if chain is a testnet, False otherwise
    """
    config = get_chain_config(chain)
    return config.is_testnet
