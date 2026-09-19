#!/bin/sh
set -eu

# This initialization runs only when Docker creates a fresh database volume.
# Values arrive through environment injection and are never written to source.
psql --set=ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" <<-'SQL'
\getenv migration_user POSTGRES_MIGRATION_USER
\getenv migration_password POSTGRES_MIGRATION_PASSWORD
\getenv application_user DATABASE_USER
\getenv application_password DATABASE_PASSWORD

SELECT format(
  'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION PASSWORD %L',
  :'migration_user', :'migration_password'
) WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'migration_user') \gexec

SELECT format(
  'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION PASSWORD %L',
  :'application_user', :'application_password'
) WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'application_user') \gexec

CREATE EXTENSION IF NOT EXISTS timescaledb;

ALTER SCHEMA public OWNER TO :"migration_user";
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CONNECT, TEMPORARY ON DATABASE :"DBNAME" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"DBNAME" TO :"migration_user", :"application_user";
GRANT USAGE ON SCHEMA public TO :"application_user";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"application_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"application_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migration_user" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"application_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migration_user" IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO :"application_user";
SQL
