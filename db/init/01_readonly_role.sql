-- Runs automatically once, the first time the Postgres container starts.
-- Creates a dedicated read-only role that the MCP server will connect as.
-- This is defense-in-depth: even if the SQL-safety check in the MCP server
-- had a bug, this role physically cannot INSERT/UPDATE/DELETE/DROP anything.

CREATE ROLE commerce_ro WITH LOGIN PASSWORD 'commerce_ro_dev_pw';

GRANT CONNECT ON DATABASE commerce TO commerce_ro;
GRANT USAGE ON SCHEMA public TO commerce_ro;

-- Grant SELECT on tables that exist now...
GRANT SELECT ON ALL TABLES IN SCHEMA public TO commerce_ro;

-- ...and on any tables created later (e.g. when load_data.py runs after this).
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO commerce_ro;

-- Belt and suspenders: explicitly revoke write grants in case a future
-- migration accidentally grants them to PUBLIC.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM commerce_ro;
