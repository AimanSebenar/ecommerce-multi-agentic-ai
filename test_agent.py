import asyncio
import json

from agents.mcp_bridge import mcp_session, tools_as_openai_schema
from agents.orchestrator import handle_question


async def main():
    print("Commerce Copilot - Step 4 (SQL analyst only)")
    print("Type a question about the e-commerce data, or 'quit' to exit.\n")
    print("Example: 'Which product category has the most orders?'\n")

    async with mcp_session() as session:
        tools_schema = await tools_as_openai_schema(session)
        print(f"Connected to MCP server. Tools available: {[t['function']['name'] for t in tools_schema]}\n")

        while True:
            question = input("You: ").strip()
            if question.lower() in {"quit", "exit"}:
                break
            if not question:
                continue

            result = await handle_question(question, session, tools_schema)

            print("\n--- Trace ---")
            print(json.dumps(result["trace"], indent=2, default=str))

            print("\n--- Answer ---")
            print(result["answer"])
            print()


if __name__ == "__main__":
    asyncio.run(main())