# Langchain Privy Examples

This directory contains a working example that demonstrates how to use `langchain-privy` to build AI agents with wallet capabilities.

## Setup

1. Install the package and dependencies:

```bash
pip install -e ..
pip install -r requirements.txt
```

2. Set up your environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export PRIVY_APP_ID="your-privy-app-id"
export PRIVY_APP_SECRET="your-privy-app-secret"
```

## Chat Agent (`chat_agent.py`)

An interactive chat agent that can perform wallet operations through natural language conversation.

**Features:**
- Automatic wallet creation (no user management needed)
- Interactive chat interface
- Get wallet addresses on different chains
- Check wallet balances
- Sign messages
- Multi-chain support (Ethereum, Base, Polygon, Solana, etc.)

**Run it:**
```bash
python chat_agent.py
```

**Example interactions:**
- "What's my wallet address?"
- "What can you do?"
- "Tell me about my wallet"
- "Get my address on Base"
- "Check my balance on Ethereum"

## How It Works

The chat agent demonstrates key features of the `langchain-privy` integration:

1. **Automatic Wallet Creation**: No user management required - wallets are created automatically
2. **Tool Binding**: Uses LangChain's `bind_tools()` to enable the LLM to call wallet operations
3. **Multi-chain Support**: Works across 30+ blockchains (Ethereum, Base, Polygon, Solana, etc.)
4. **Security**: Private keys never leave Privy's secure infrastructure
5. **Natural Language**: Users interact with wallets using plain English

## Creating Your Own Agent

Here's a minimal example:

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_privy import PrivyWalletTool

# Initialize tool (auto-creates wallet)
tool = PrivyWalletTool()

# Create agent
agent = create_agent(
    model=ChatOpenAI(temperature=0, model="gpt-4"),
    tools=[tool],
    system_prompt="You are a helpful wallet assistant."
)

# Use the agent
result = agent.invoke({"messages": [("user", "What is my wallet address?")]})
print(result["messages"][-1].content)
```

## Tips

- Start with small operations (checking addresses/balances)
- Always test on testnets first
- Set up transaction policies in your Privy dashboard
- Monitor gas prices for mainnet operations
- Use verbose=True to see agent reasoning

## Troubleshooting

**Authentication errors**: Verify your `PRIVY_APP_ID` and `PRIVY_APP_SECRET` are correct

**Chain not supported**: Check that the chain name matches those in `langchain_privy.chains.Chain`

**Transaction failures**: Ensure the wallet has sufficient balance for gas fees

**OpenAI errors**: Make sure your `OPENAI_API_KEY` is valid and has credits

## Next Steps

- Integrate with your application's backend
- Add transaction approval workflows
- Add monitoring and logging for production use
- Implement custom business logic

## Resources

- [Privy Documentation](https://docs.privy.io)
- [LangChain Documentation](https://python.langchain.com)
- [Package Source Code](..)
