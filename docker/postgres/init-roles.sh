#!/bin/sh
set -eu

# Values arrive through environment injection and are never written to source.
# The optional host path lets the same idempotent script provision existing volumes.
if [ -n "${POSTGRES_HOST:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
  set -- --host "$POSTGRES_HOST"
else
  set --
fi

psql "$@" --set=ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" <<-'SQL'
\getenv migration_user POSTGRES_MIGRATION_USER
\getenv migration_password POSTGRES_MIGRATION_PASSWORD
\getenv application_user DATABASE_USER
\getenv application_password DATABASE_PASSWORD
\getenv backup_user POSTGRES_BACKUP_USER
\getenv backup_password POSTGRES_BACKUP_PASSWORD

SELECT format(
  'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION PASSWORD %L',
  :'migration_user', :'migration_password'
) WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'migration_user') \gexec

SELECT format(
  'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION PASSWORD %L',
  :'application_user', :'application_password'
) WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'application_user') \gexec

SELECT format(
  'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION PASSWORD %L',
  :'backup_user', :'backup_password'
) WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'backup_user') \gexec

SELECT format('ALTER ROLE %I PASSWORD %L', :'migration_user', :'migration_password') \gexec
SELECT format('ALTER ROLE %I PASSWORD %L', :'application_user', :'application_password') \gexec
SELECT format('ALTER ROLE %I INHERIT PASSWORD %L', :'backup_user', :'backup_password') \gexec

CREATE EXTENSION IF NOT EXISTS timescaledb;

ALTER SCHEMA public OWNER TO :"migration_user";
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CONNECT, TEMPORARY ON DATABASE :"DBNAME" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"DBNAME" TO :"migration_user", :"application_user";
GRANT CONNECT ON DATABASE :"DBNAME" TO :"backup_user";
GRANT pg_read_all_data TO :"backup_user" WITH INHERIT TRUE;
GRANT USAGE ON SCHEMA public TO :"application_user";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"application_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"application_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migration_user" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"application_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migration_user" IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO :"application_user";
SQL
