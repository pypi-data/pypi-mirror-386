# Contributing to langchain-privy

Thank you for your interest in contributing to langchain-privy! This guide will help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/privy-io/privy.git
cd public-packages/langchain-privy
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

4. Set up environment variables for testing:
```bash
export PRIVY_APP_ID="your-test-app-id"
export PRIVY_APP_SECRET="your-test-app-secret"
export PRIVY_USER_ID="did:privy:test-user-id"
```

## Code Quality

We use several tools to maintain code quality:

### Formatting
```bash
# Format code with black
black langchain_privy tests examples

# Check formatting
black --check langchain_privy tests examples
```

### Linting
```bash
# Lint with ruff
ruff check langchain_privy tests examples

# Auto-fix issues
ruff check --fix langchain_privy tests examples
```

### Type Checking
```bash
# Check types with mypy
mypy langchain_privy
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=langchain_privy --cov-report=html

# Run specific test file
pytest tests/test_chains.py

# Run specific test
pytest tests/test_chains.py::TestChainConfig::test_get_chain_config_with_enum
```

## Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for all functions and methods
- Write docstrings for all public APIs (Google style)
- Keep lines under 100 characters
- Use meaningful variable and function names

### Example Function:
```python
def send_transaction(
    self,
    to: str,
    value: str,
    chain: Chain | str = Chain.ETHEREUM,
) -> dict[str, Any]:
    """Send a transaction from the user's wallet.

    Args:
        to: Recipient address
        value: Transaction value in wei
        chain: Target blockchain

    Returns:
        Transaction response with hash and transaction_id

    Raises:
        ValueError: If user has no wallet for the chain
        requests.HTTPError: If API request fails
    """
    # Implementation
```

## Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external API calls
- Test both success and failure cases

### Example Test:
```python
def test_get_wallet_address(self, mock_rpc_client):
    """Test getting wallet address."""
    mock_rpc_client.get_wallet_address.return_value = "0x1234..."

    result = wallet_tool._get_wallet_address(chain="ethereum")

    assert "0x1234..." in result
    mock_rpc_client.get_wallet_address.assert_called_once()
```

## Pull Request Process

1. **Create a branch**: Use a descriptive name like `feature/add-nft-support` or `fix/auth-error`

2. **Make your changes**:
   - Write tests for new features
   - Update documentation
   - Follow code style guidelines
   - Ensure all tests pass

3. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference issues if applicable
   ```bash
   git commit -m "feat: add NFT transfer support

   Implements NFT transfer functionality using ERC-721 standard.
   Includes tests and documentation.

   Closes #123"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**:
   - Provide a clear description of the changes
   - Link related issues
   - Add screenshots for UI changes
   - Wait for review

## Commit Message Format

We follow conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Build/tooling changes

## Adding New Chains

To add support for a new blockchain:

1. Add the chain to `Chain` enum in `langchain_privy/chains.py`
2. Add configuration to `CHAIN_CONFIGS` dictionary
3. Add tests to `tests/test_chains.py`
4. Update documentation

Example:
```python
# In chains.py
class Chain(str, Enum):
    # ... existing chains
    NEW_CHAIN = "new-chain"

CHAIN_CONFIGS[Chain.NEW_CHAIN] = ChainConfig(
    chain=Chain.NEW_CHAIN,
    chain_id=12345,
    chain_type="ethereum",
    caip2="eip155:12345",
    is_testnet=False,
    native_currency="NEW",
)
```

## Adding New RPC Methods

To add support for a new RPC method:

1. Add method to `RPCMethod` enum in `langchain_privy/rpc_client.py`
2. Implement method in `PrivyRPCClient` class
3. Add tests
4. Update documentation

## Documentation

- Update README.md for new features
- Add docstrings to all public APIs
- Create examples for complex features
- Update CHANGELOG.md

## Questions?

- Open an issue for bugs or feature requests
- Join our Discord for discussions
- Email support@privy.io for sensitive issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
