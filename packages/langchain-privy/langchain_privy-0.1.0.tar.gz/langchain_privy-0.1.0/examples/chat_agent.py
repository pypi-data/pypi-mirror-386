#!/usr/bin/env python
"""Working agent example using LangChain with Privy wallets."""

import os

from dotenv import load_dotenv

load_dotenv()

# ruff: noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from langchain_privy import PrivyWalletTool


def main():
    """Run a simple conversational agent with wallet capabilities."""
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required")
        return

    if not os.getenv("PRIVY_APP_ID") or not os.getenv("PRIVY_APP_SECRET"):
        print("❌ Error: PRIVY_APP_ID and PRIVY_APP_SECRET required")
        return

    print("=" * 80)
    print("Privy Wallet Agent - Simple Chat Interface")
    print("=" * 80)

    # Create wallet
    print("\n📱 Creating wallet...")
    tool = PrivyWalletTool()
    print(f"   ✓ Wallet: {tool.wallet_address}")

    # Initialize LLM with tool binding
    print("\n🤖 Initializing AI...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Bind the tool to the LLM
    llm_with_tools = llm.bind_tools([tool])
    print("   ✓ Ready!")

    # System message
    system_msg = SystemMessage(
        content=f"""You are a helpful multi-chain wallet assistant.
You started with an Ethereum wallet at address: {tool.wallet_address}

You can help users:
- Create new wallets for different chains (Ethereum, Solana, Base, Polygon, etc.)
- Get wallet addresses for different chains
- Check balances on BOTH mainnet and testnet (e.g., "solana" vs "solana-devnet")
- Sign messages for authentication/verification
- Send cryptocurrency transactions (if wallets are funded)
- Answer questions about wallets and blockchains

CRITICAL - Understanding Operations:
1. "sign_message" operation: For signing arbitrary text (authentication, proofs, verification)
   - Example: User asks "sign this message: Hello World"
   - Use: operation="sign_message", message="Hello World", chain="ethereum"

2. "send_transaction" operation: For creating and broadcasting actual blockchain transactions
   - Example: User asks "send 1 ETH to 0x123..." or "sign a transaction for 0.5 ETH to 0xabc..."
   - Use: operation="send_transaction", to="0x123...", value="1000000000000000000", chain="ethereum"
   - ALWAYS provide value as a decimal string in wei (1 ETH = 1000000000000000000 wei = 10^18 wei)
   - For Solana, use lamports (1 SOL = 1000000000 lamports = 10^9 lamports)
   - Do NOT convert to hex - provide the decimal number as a string
     (e.g., "1000000000000000000" not "0xde0b6b3a7640000")

When users say "sign a transaction" or "send a transaction", they mean send_transaction
operation with to/value parameters.
When users say "sign this message" or "sign for authentication", they mean sign_message operation.

Important notes:
- The SAME Solana wallet address works on mainnet ("solana"), devnet ("solana-devnet"), and testnet
- Balance checking only works on: ethereum, base, polygon, solana, arbitrum, optimism, linea
  (and their testnets)
- solana-devnet and bitcoin do NOT support balance checking
- Available testnets: ethereum-sepolia, base-sepolia, polygon-amoy, arbitrum-sepolia, etc.

When a user asks about a chain you don't have a wallet for, offer to create one.
Be concise and friendly."""
    )

    print("\n" + "=" * 80)
    print("💬 Chat with your multi-chain wallet! (type 'exit' to quit)")
    print("=" * 80)
    print("\nTry asking:")
    print("  - What's my wallet address?")
    print("  - Do I have a Solana wallet?")
    print("  - Create a Solana wallet for me")
    print("  - Check my balance on ethereum")
    print("  - Check my balance on base-sepolia")
    print("  - Sign this message: Hello World (for authentication)")
    print("  - Send 0.001 ETH to 0x123... (requires funded wallet)\n")

    conversation = [system_msg]

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!")
                break

            # Add user message to conversation
            conversation.append(HumanMessage(content=user_input))

            # Loop until we get a response without tool calls
            while True:
                # Get response from LLM
                print("\n🤔 Thinking...", end="", flush=True)
                response = llm_with_tools.invoke(conversation)
                print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."

                # Check if the model wants to use a tool
                if response.tool_calls:
                    print("🔧 Using wallet tool...\n")

                    # Add the AI response with tool calls to conversation
                    conversation.append(response)

                    for tool_call in response.tool_calls:
                        # Execute the tool
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]

                        if tool_name == "privy_wallet":
                            result = tool._run(**tool_args)
                            print(f"Tool result: {result}\n")

                            # Add tool response to conversation using ToolMessage
                            tool_message = ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call["id"],
                            )
                            conversation.append(tool_message)

                    # Continue loop to get final response
                    continue
                else:
                    # Direct response without tools - we're done
                    print(f"Agent: {response.content}\n")
                    conversation.append(response)
                    break

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

    # Summary
    print("\n" + "=" * 80)
    print("Session Info")
    print("=" * 80)
    print(f"Wallet ID: {tool.wallet_id}")
    print(f"Address: {tool.wallet_address}")


if __name__ == "__main__":
    main()
