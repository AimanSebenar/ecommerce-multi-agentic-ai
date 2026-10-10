
import asyncio

import pandas as pd
import streamlit as st

from agents.mcp_bridge import mcp_session, tools_as_openai_schema
from agents.orchestrator import handle_question
from tracing.logger import log_run

st.set_page_config(page_title="Commerce Copilot", page_icon="🛒", layout="centered")

st.title("Multi-agentic AI E-Commerce Data Workflow")
st.caption(
    "Multi-agent analytics over the Olist e-commerce dataset "
    "SQL analyst → insight agent → narrative agent, via a custom MCP server + GPT-OSS-120B (opensource)."
)


async def ask(question: str) -> dict:
    async with mcp_session() as session:
        tools_schema = await tools_as_openai_schema(session)
        return await handle_question(question, session, tools_schema)


question = st.text_input(
    "Ask a question about the data",
    placeholder="Which product category has the most orders?",
)
run_clicked = st.button("Ask", type="primary")

if run_clicked and not question.strip():
    st.warning("Type a question first.")

elif run_clicked:
    with st.spinner("Agents are working…"):
        result = asyncio.run(ask(question))
        log_run(question, result)

    st.markdown("### Answer")
    st.write(result["answer"])

    data = result.get("data")
    if data and data.get("rows"):
        st.markdown("### Data")
        df = pd.DataFrame(data["rows"], columns=data["columns"])
        st.dataframe(df, use_container_width=True)

    with st.expander("Show agent trace (what each agent actually did)"):
        st.json(result["trace"])
