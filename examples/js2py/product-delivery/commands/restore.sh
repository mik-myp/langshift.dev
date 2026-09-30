#!/usr/bin/env bash
# Restore ONLY a trusted archive into a separately approved isolated cluster.
set -euo pipefail
umask 077
export PGSERVICEFILE
: "${PGSERVICEFILE:?Set the reviewed PostgreSQL service file}"
: "${BACKUP_PATH:?Set the private directory containing product.dump and its checksum}"
: "${RESTORE_DATABASE:?Set a fresh restore_ database name}"
: "${RESTORE_TARGET_APPROVAL:?Reference the approved isolated target record}"
[[ "$RESTORE_DATABASE" =~ ^restore_[a-z0-9_]+$ && ${#RESTORE_DATABASE} -le 63 ]] || { echo "Invalid isolated database name" >&2; exit 1; }
(cd "$BACKUP_PATH" && sha256sum --check product.dump.sha256)
# Source and restore endpoint identities must already have been compared by the operator.
# No --clean, DROP, production connection, or overwrite fallback is provided.
createdb --no-password --maintenance-db='service=restore-admin' -- "$RESTORE_DATABASE"
psql --no-password --dbname='service=restore-admin' --set=ON_ERROR_STOP=1 --set=restore_name="$RESTORE_DATABASE" <<'SQL'
SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'restore_name') \gexec
SQL
pg_restore --no-password --dbname="service=restore-admin dbname=$RESTORE_DATABASE" \
  --no-owner --no-privileges --exit-on-error --single-transaction "$BACKUP_PATH/product.dump"
printf 'Restore imported into %s; keep it isolated until data, roles and sessions are reviewed
' "$RESTORE_DATABASE"
