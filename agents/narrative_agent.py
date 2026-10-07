from agents.llm_client import get_client, get_model

SYSTEM_PROMPT = """You are a data-reporting writer for a business audience.

You'll be given a user's question, a SQL analyst's findings, and an
insight analyst's notable observations. Combine them into ONE clear,
concise answer:
- A few sentences, plain English, use layman terms but technical terms if really needed.
- Include the concrete numbers that matter, don't make the reader dig
  for them.
- Add a single short caveat sentence ONLY if one is genuinely warranted
  (small sample size, limited time range, possible data quality issue).
  Do not invent a caveat just to seem careful.
- Do not mention "the SQL analyst" or "the insight agent" - just answer
  the question directly, as if you did the analysis yourself.
"""

def run_narrative_agent(question: str, sql_answer: str, insight_text: str, trace: list[dict]) ->str:
    client = get_client()
    model = get_model()

    user_message = (
        f"User's question: {question}\n\n"
        f"SQL analyst's findings: {sql_answer}\n\n"
        f"Insight analyst's observations: {insight_text}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    content = response.choices[0].message.content

    trace.append({
        "agent": "narrative",
        "type": "final_answer",
        "content": content
    })
    return content