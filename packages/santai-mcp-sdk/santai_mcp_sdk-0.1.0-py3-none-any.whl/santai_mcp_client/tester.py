# To run this file:
# export PYTHONPATH=$PWD/src
# python3 -m santai_mcp_client.tester

# test_selector.py
import os
import asyncio
from typing import Any, Dict, Tuple

# Adjust these imports to match your filenames/modules if needed
from santai_mcp_client.client import MCPClient
from santai_mcp_client.selector import Selector

# ---- Optional: supply config via env or hardcode here ----
MCP_SERVER_URL = "https://api.githubcopilot.com/mcp/"
LLM_BASE_ENDPOINT = os.getenv("OPENAI_API_BASE_URL", "http://35.170.110.189:9231/v1")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "sk-J6W3Xvc3H_F_Gqn39qfXAQ")

GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN", "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")

async def main() -> None:

    print("Creating MCP client...")
    client = MCPClient(
        # url=MCP_SERVER_URL,
        # token=GITHUB_TOKEN,
        transport = "stdio",
        commands = "npx",
        args = ["@playwright/mcp@latest"]
    )

    print("Listing tools from MCP server...")
    tools = await client.list_tools()
    if not tools:
        print("No tools found from MCP server.")
        return

    print(f"Discovered {len(tools)} tools:")
    for i, t in enumerate(tools, 1):
        print(
            f"  {i}. {t.name} — {t.description[:80]}{'...' if len(t.description) > 80 else ''}"
        )

    # Prepare a sample context/query for routing
    context = "Session context: user wants to find out more about their github details."
    query = "what are my account details"

    print("\nInitializing Selector and routing...")
    selector = Selector(
        base_endpoint=LLM_BASE_ENDPOINT,
        api_key=LLM_API_KEY,
    )

    # Choose a tool via LLM
    try:
        decision: Tuple[Dict[str, Any], Dict[str, Any]] = selector.choose_tool(
            context, query, tools
        )
    except Exception as e:
        print(f"Selector.choose_tool raised an error: {e}")
        return

    t_obj = decision.tool
    args = decision.args
    if not t_obj:
        print("Selector returned no matching tool.")
        return

    print("\n--- Routing Decision ---")
    print(f"Selected tool: {t_obj.get('name')}")
    print(f"Arguments: {args}")

    print("Executing tool...")
    result = await client.execute_tool(t_obj.get('name'), args)

    print(f"Tool Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
