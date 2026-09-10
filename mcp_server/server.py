from mcp.server.fastmcp import FastMCP
from mcp_server import db 

mcp = FastMCP('commerce-db')


@mcp.tool()
def list_tables() -> list[str]:
    """List every table available in the commerce database."""
    return db.list_tables()

@mcp.tool()
def get_schema(table_name: str) -> dict:
    """
    Get the column names, ta=ypes, and nullability for one table.
    Call list_tables first if you don't know the table name.
    """
    return db.get_table_schema(table_name)

@mcp.tool()
def run_query(sql: str, limit: int = 200) -> dict:
    """
    Run a read-only SQL SELECT query against the commerce database and
    return the results.

    Rules enforced server-side (not just suggested in this docstring):
        - Must be a single SELECT statement. No INSERT/UPDATE/DELETE/DROP/etc.
        - Results are capped at `limit` rows (max 1000), regardless of what the query itself requests.
        - Queries that run longer than 5 seconds are aborted.
    
    Args:
        sql: A single SELECT statement. e.g.
            "SELECT customer_state, COUNT(*) FROM customers GROUP BY 1"
        limit: Max rows to return (default 200, hard cao 1000).
    
    Returns:
        A dict with `columns` (list of column names), `rows` (list of row value lists), and `row_count`.
    """
    try:
        return db.run_select(sql, limit=limit)
    except db.UnsafeQueryError as e:
        #call agent as a tool error not crash
        #agent can read this and retry with a corrected query
        return {"error": str(e)}

if __name__=="__main__":
    mcp.run(transport="stdio")