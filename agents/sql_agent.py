import json
from agents.llm_client import get_client, get_model
from agents.mcp_bridge import call_tool

MAX_STEPS = 6

SYSTEM_PROMPT ="""You are a careful SQL data analyst for company's e-commerce database.

Rules:
- Always call `list_tables` and `get_schema` before writing a query if you are not
  already certain of the exact table and column names.
- Only ever write SELECT queries. You cannot write and should not attempt to.
- Prefer simple and readable SQL. Use GROUP BY / aggreates for summary questions
  rather than puling raw rows and summarising yourself.
- If a query tool returns an error, read it, fix the query and try again. 
  Do not give up after a failed attempt.
- When you have enough information, answer in plain English. Mention the actual
  numbers you found. Do not show raw SQL to the user unless asked to.
"""

async def run_sql_agent(question: str, session, tools_schema: list[dict], trace: list[dict]) -> str:
    client = get_client()
    model = get_model()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(MAX_STEPS):
        response = client.chat.completions.create(
            model= model,
            messages= messages,
            tools=tools_schema,
            tool_choice = "auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            trace.append({"agent": "sql_analyst", "type": "final_answer", "content": msg.content})
            return msg.content

        #happens if need to call tools again

        trace.append(
            {
                "agent": "sql_analyst",
                "type": "assistant_tool_request",
                "content": msg.content,
                "tool_calls": [
                    {"name": tc.function.name, "arguments": tc.function.arguments}
                    for tc in msg.tool_calls
                ],
            }
        )
        messages.append(msg)

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result_text = await call_tool(session, tc.function.name, args)

            trace.append(
                {
                    "agent": "sql_analyst",
                    "type": "tool_result",
                    "tool": tc.function.name,
                    "args": args,
                    "result": result_text,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                }
            )
    fallback = "I was not able to reach a final answer within the step limit."
    trace.append({"agent": "sql_analyst", "type": "final_answer", "content": fallback})
    return fallback