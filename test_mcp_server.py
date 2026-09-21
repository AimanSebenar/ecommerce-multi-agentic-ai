"""
Quick manual test of the MCP server's tools - no agent framework needed.

This connects to your server as an MCP client would, over stdio, and calls
each tool. Run it after `docker compose up -d` and `python data/load_data.py`.

    python test_mcp_server.py
"""

import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            print("\n--- list_tables ---")
            result = await session.call_tool("list_tables", {})
            print(result.content[0].text)

            print("\n--- get_schema('orders') ---")
            result = await session.call_tool("get_schema", {"table_name": "orders"})
            print(result.content[0].text)

            print("\n--- run_query: order counts by status ---")
            result = await session.call_tool(
                "run_query",
                {
                    "sql": "SELECT order_status, COUNT(*) AS n FROM orders GROUP BY order_status ORDER BY n DESC",
                    "limit": 20,
                },
            )
            print(result.content[0].text)

            print("\n--- run_query: safety check, should be rejected ---")
            result = await session.call_tool(
                "run_query",
                {"sql": "DELETE FROM orders WHERE 1=1", "limit": 20},
            )
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
