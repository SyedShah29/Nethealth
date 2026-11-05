#!/usr/bin/env bash
set -euo pipefail

if [ "${#BACKUP_ENCRYPTION_KEY}" -lt 24 ]; then
  echo "BACKUP_ENCRYPTION_KEY must contain at least 24 characters" >&2
  exit 1
fi

backup_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="/backups/nethealth-${backup_timestamp}.dump.enc"

cleanup_partial_backup() {
  exit_code="$?"
  trap - EXIT
  if [ "$exit_code" -ne 0 ]; then
    rm -f "$backup_path"
  fi
  exit "$exit_code"
}
trap cleanup_partial_backup EXIT

PGPASSWORD="$POSTGRES_BACKUP_PASSWORD" pg_dump \
  --host=postgres \
  --username="$POSTGRES_BACKUP_USER" \
  --dbname="$POSTGRES_DB" \
  --no-owner \
  --no-privileges \
  --format=custom \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
      -pass env:BACKUP_ENCRYPTION_KEY \
      -out "$backup_path"

trap - EXIT
ln -sfn "$(basename "$backup_path")" /backups/latest.dump.enc
echo "Encrypted backup created at $backup_path"
