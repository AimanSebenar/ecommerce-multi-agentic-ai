import sys
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "mcp_server.server"],
)

@asynccontextmanager
async def mcp_session():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            yield session

async def tools_as_openai_schema(session: ClientSession) -> list[dict]:
    result = await session.list_tools()
    schema = []
    for tool in result.tools:
        schema.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema
                    or {"type": "object", "properties": {}}
                }
            }
        )
    return schema

async def call_tool(session: ClientSession, name: str, args: dict) -> str:
    result = await session.call_tool(name, args)
    if not result.content:
        return ""

    texts = []
    for item in result.content:
        text = getattr(item, "text", None)
        if text is not None:
            texts.append(text)
        else:
            texts.append(str(item))

    return "\n".join(texts)