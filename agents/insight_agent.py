from agents.llm_client import get_client, get_model

MAX_ROWS_SHOWN = 50

SYSTEM_PROMPT = """You are a data insight analyst. You're given a user's
question and a table of SQL query results.

Your job is NOT to restate every row. Find what is genuinely notable:
- The largest value and what share of the total it represents, if that's
  meaningful for this data.
- A sizeable gap between the top result and the runner-up, if there is one.
- Anything that looks like an outlier.
- A trend, if there's a date/time column.

Rules:
- Every claim must reference actual numbers from the table. No vague
  language like "significantly higher" without a number/statistic attached.
- If the data is small (e.g. fewer than ~20 total records) or genuinely
  flat/uninteresting, say that plainly instead of inventing a pattern.
- Output a few short bullet points, nothing else.
"""

def run_insight_agent(question: str, data: dict | None, trace: list[dict]) -> str:
    if not data or not data.get("rows"):
        content = "No query results are available to analyze."
        trace.append({"agent": "insight", "type": "final_answer", "content": content})
        return content

    client = get_client()
    model = get_model()

    user_message = (
        f"User's question: {question}\n\n"
        f"Query results:\n{_render_table(data)}"
    )

    response = client.chat.completions.create(
        model=model,
        messages= [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    content = response.choices[0].message.content

    trace.append({
        "agent": "insight",
        "type": "final_answer",
        "content": content
        })
    return content

def _render_table(data: dict) -> str:
    columns = data.get("columns", [])
    rows = data.get("rows", [])[:MAX_ROWS_SHOWN]
    lines = [" | ".join(str(c) for c in columns)]
    for row in rows:
        lines.append(" | ".join(str(v) for v in row))
    note = ""
    if data.get("row_count", 0) > MAX_ROWS_SHOWN:
        note = f"\n(showing first {MAX_ROWS_SHOWN} of {data['row_count']} rows)"
    return "\n".join(lines) + note