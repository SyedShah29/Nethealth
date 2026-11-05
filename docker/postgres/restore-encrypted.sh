#!/usr/bin/env bash
set -euo pipefail

if [ "${#BACKUP_ENCRYPTION_KEY}" -lt 24 ]; then
  echo "BACKUP_ENCRYPTION_KEY must contain at least 24 characters" >&2
  exit 1
fi
if [ ! -f "$BACKUP_FILE" ]; then
  echo "BACKUP_FILE does not exist" >&2
  exit 1
fi
if [ "$RESTORE_DATABASE" = "$POSTGRES_DB" ]; then
  echo "Refusing to restore over the source database" >&2
  exit 1
fi
case "$RESTORE_DATABASE" in
  *_restore_verify) ;;
  *)
    if [ "${ALLOW_PRODUCTION_RESTORE:-false}" != "true" ]; then
      echo "Non-verification restores require ALLOW_PRODUCTION_RESTORE=true" >&2
      exit 1
    fi
    ;;
esac

decrypted_dump="/tmp/nethealth-restore.dump"
cleanup() {
  rm -f "$decrypted_dump"
}
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass env:BACKUP_ENCRYPTION_KEY -in "$BACKUP_FILE" -out "$decrypted_dump"

export PGPASSWORD="$POSTGRES_RESTORE_PASSWORD"
if [ "${RESTORE_REPLACE:-false}" = "true" ]; then
  dropdb --host=postgres --username="$POSTGRES_RESTORE_USER" --if-exists "$RESTORE_DATABASE"
fi
createdb --host=postgres --username="$POSTGRES_RESTORE_USER" "$RESTORE_DATABASE"
pg_restore --host=postgres --username="$POSTGRES_RESTORE_USER" \
  --dbname="$RESTORE_DATABASE" --no-owner --no-privileges --exit-on-error "$decrypted_dump"
psql --host=postgres --username="$POSTGRES_RESTORE_USER" --dbname="$RESTORE_DATABASE" \
  --set=ON_ERROR_STOP=1 --command="SELECT count(*) AS migration_rows FROM alembic_version"
echo "Encrypted backup restored and verified in $RESTORE_DATABASE"
