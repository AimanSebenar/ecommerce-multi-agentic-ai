from agents.sql_agent import run_sql_agent
from agents.insight_agent import run_insight_agent
from agents.narrative_agent import run_narrative_agent

async def handle_question(question: str, session, tools_schema: list[dict]) -> dict:
    #a record of the agent's workflow
    trace: list[dict] = [{
        "agent": "orchestrator",
        "type": "route",
        "content": "sql_analyst -> insight -> narrative"}]

    sql_answer = await run_sql_agent(question, session, tools_schema, trace)
    insight_text = run_insight_agent(question, sql_answer["data"], trace)
    narrative_text = run_narrative_agent(question,sql_answer["answer"], insight_text, trace)


    return {"answer": narrative_text, "data": sql_answer["data"], "trace": trace}