#!/usr/bin/env bash
set -euo pipefail

if [ "${#BACKUP_ENCRYPTION_KEY}" -lt 24 ]; then
  echo "BACKUP_ENCRYPTION_KEY must contain at least 24 characters" >&2
  exit 1
fi

backup_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="/backups/nethealth-config-${backup_timestamp}.tar.enc"
tar --create --directory=/config-source . \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
      -pass env:BACKUP_ENCRYPTION_KEY -out "$backup_path"
ln -sfn "$(basename "$backup_path")" /backups/latest-config.tar.enc
echo "Encrypted configuration backup created at $backup_path"
