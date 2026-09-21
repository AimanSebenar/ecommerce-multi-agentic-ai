"""
Database access layer for the MCP server.

Two layers of defense against writes / abuse, on top of connecting
as the `commerce_ro` role (which physically cannot write, see
db/init/01_readonly_role.sql):

  1. Statement-level check: the query must parse as a single SELECT
     (via sqlparse), no stacked statements, no forbidden keywords.
  2. Wrap-in-subquery: the query is always executed as
     `SELECT * FROM (<query>) AS sub LIMIT n`, which (a) enforces a
     row cap regardless of what the query itself asked for, and
     (b) makes multi-statement injection syntactically impossible,
     since a subquery can only ever contain one SELECT expression.
  3. A Postgres `statement_timeout` bounds runaway queries.
"""

import os 
import re
import sqlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

FORBIDDEN_KEYWORDS={
    'insert', 'update', 'delete', 'drop', 'alter', 'truncate',
    'grant', 'revoke', 'create', 'copy', 'call', 'do', 'vacuum',
    'reindex', 'execute', 'into',
}

DEFAULT_ROW_LIMIT = 200
MAX_ROW_LIMIT = 1000
STATEMENT_TIMEOUT_MS = 5000

class UnsafeQueryError(ValueError):
    pass

_engine: Engine | None=None

def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    db = os.environ["POSTGRES_DB"]
    user = os.environ["PG_READONLY_USER"]
    pw = os.environ["PG_READONLY_PASSWORD"]
    url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"

    _engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={'options': f'-c statement_timeout={STATEMENT_TIMEOUT_MS}'},
    )
    return _engine

def assert_query_is_safe(sql: str) -> None:
    """Raise UnsafeQueryError if the query isn't a single, plain SELECT."""

    if not sql or not sql.strip():
        raise UnsafeQueryError("Empty query.")

    statements = sqlparse.parse(sql)
    if len(statements) != 1:
        raise UnsafeQueryError("only a single SQL statement is allowed.")

    stmt = statements[0]
    stmt_type = stmt.get_type()
    if stmt_type != "SELECT":
        raise UnsafeQueryError(f"Only SELECT statements are allowed (got {stmt_type}).")

    lowered = sql.lower()
    for word in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{word}\b", lowered):
            raise UnsafeQueryError(f"Forbidden keyword detected: '{word}'")

    if ";" in sql.strip().rstrip(";"):
        raise UnsafeQueryError("Multiple statements are not allowed.")

def run_select(sql: str, limit: int = DEFAULT_ROW_LIMIT) -> dict:
    """Safely run a read only query and return {columns, rows, row_count}"""

    assert_query_is_safe(sql)
    limit = max(1, min(limit, MAX_ROW_LIMIT))

    wrapped =  f"SELECT * FROM ({sql.rstrip(':')}) AS sub LIMIT :limit"

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(wrapped), {"limit": limit})
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]

    return {'columns': columns, 'rows': rows, 'row_count': len(rows)}

def list_tables() -> list[str]:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        return [row[0] for row in result.fetchall()]

def get_table_schema(table_name: str) -> dict:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :t "
                "ORDER BY ordinal_position"
            ), {'t': table_name},
        )
        columns = [
            {'name': r[0], 'type': r[1], 'nullable': r[2] == 'YES'}
            for r in result.fetchall()
        ]
    if not columns:
        raise ValueError(f"Table '{table_name}' not found")
    return {'table': table_name, 'columns': columns}