#!/usr/bin/env bash
# A trusted source profile and protected directory must be configured first.
set -euo pipefail
umask 077
export PGSERVICEFILE
: "${PGSERVICEFILE:?Set the reviewed PostgreSQL service file}"
: "${BACKUP_DIR:?Set an existing private backup directory}"
: "${BACKUP_ID:?Set a non-secret backup identifier}"
[[ "$BACKUP_ID" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "Invalid backup identifier" >&2; exit 1; }
[ -d "$BACKUP_DIR" ] || { echo "Backup directory is missing" >&2; exit 1; }
backup=$(mktemp -d "$BACKUP_DIR/product-${BACKUP_ID}.XXXXXX")
pg_dump --no-password --dbname='service=source-backup' --format=custom --no-owner --no-privileges --file="$backup/product.dump"
pg_restore --list "$backup/product.dump" > "$backup/product.list"
(cd "$backup" && sha256sum product.dump > product.dump.sha256)
printf 'Archive created at %s; isolated restore and offsite copy are still required
' "$backup"
