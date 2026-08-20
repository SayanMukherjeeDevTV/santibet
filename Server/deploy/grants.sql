-- Least-privilege grants for the application's runtime Postgres role.
--
-- Run this once against your database AFTER the Alembic migrations have
-- created the tables (order matters: the tables must exist for GRANT to
-- reference them). Re-run any time you add a new append-only table.
--
--   psql "$DATABASE_URL" -f deploy/grants.sql
--
-- Rationale: ledger_entries and audit_log are append-only by design (see
-- their model docstrings). Revoking UPDATE/DELETE at the database level
-- means a bug or a compromised application process literally cannot alter
-- financial or compliance history - not just "shouldn't", "can't". This is
-- defense in depth on top of (not a replacement for) never writing
-- UPDATE/DELETE against these tables in application code.
--
-- Replace `santibet_app` below if you used a different role name when you
-- created the database (see README "Database setup").
--
-- IMPORTANT CAVEAT: if `santibet_app` is also the OWNER of these tables (the
-- default if you ran the Alembic migrations as that same role), it can
-- still ALTER TABLE to re-grant itself UPDATE/DELETE, or DROP the table
-- outright - ownership includes DDL rights regardless of DML REVOKEs. This
-- script still meaningfully raises the bar against an ordinary application
-- bug (an accidental UPDATE statement will fail immediately), but it is not
-- a substitute for a compromised-credentials threat model. For that, run
-- migrations as a separate, more-privileged `santibet_migrator` role that
-- OWNS the tables, and have the running application connect only as
-- `santibet_app`, which never has ownership or DDL rights at all - only the
-- DML grants below.

-- Ledger: INSERT + SELECT only. No UPDATE, no DELETE, ever.
REVOKE UPDATE, DELETE ON ledger_entries FROM santibet_app;
GRANT SELECT, INSERT ON ledger_entries TO santibet_app;
GRANT USAGE, SELECT ON SEQUENCE ledger_entries_id_seq TO santibet_app;

-- Audit log: same story - INSERT + SELECT only.
REVOKE UPDATE, DELETE ON audit_log FROM santibet_app;
GRANT SELECT, INSERT ON audit_log TO santibet_app;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO santibet_app;

-- Everything else keeps normal read/write access (the default from table
-- ownership), since those tables legitimately need UPDATE (order status,
-- position shares, user profile fields, etc).
