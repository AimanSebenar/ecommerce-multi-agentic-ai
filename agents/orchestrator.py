from agents.sql_agent import run_sql_agent

async def handle_question(question: str, session, tools_schema: list[dict]) -> dict:
    #a record of the agent's workflow
    trace: list[dict] = [{"agent": "orchestrator", "type": "route", "content": "sql_analyst"}]

    answer = await run_sql_agent(question, session, tools_schema, trace)

    return {"answer": answer, "trace": trace}