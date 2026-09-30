#!/usr/bin/env bash
# Target-specific operational template, not an automatic release approval.
set -euo pipefail
fail() { printf 'RELEASE REFUSED: %s\n' "$*" >&2; exit 2; }
: "${DOCKER_CONTEXT:?Choose and review the Docker context for this release}"
: "${PROJECT_NAME:?Choose the owned Compose project name}"
: "${DOMAIN:?Set the approved public domain}"
: "${APP_IMAGE:?Set the reviewed app image digest}"
: "${CADDY_IMAGE:?Set the reviewed Caddy image digest}"
: "${RELEASE_RECORD:=docs/integration-record.json}"
: "${RELEASE_APPROVAL_REFERENCE:?Reference the human release approval record}"
: "${BACKUP_POLICY_REFERENCE:?Reference the approved backup/restore policy}"
: "${ROLLBACK_OWNER:?Name the rollback owner}"
[[ -f "$RELEASE_RECORD" ]] || fail "missing integration record: $RELEASE_RECORD"
[[ -f check_integration_record.py ]] || fail "run from the product root with check_integration_record.py present"
[[ "$APP_IMAGE" == *@sha256:* ]] || fail "APP_IMAGE must include an immutable @sha256 digest"
[[ "$CADDY_IMAGE" == *@sha256:* ]] || fail "CADDY_IMAGE must include an immutable @sha256 digest"
case "$(printf '%s' "$DOMAIN" | tr '[:upper:]' '[:lower:]')" in
  localhost|127.0.0.1|*.invalid|*.test|*.example) fail "DOMAIN is not an approved public name" ;;
esac
python3 check_integration_record.py "$RELEASE_RECORD" >/dev/null
python3 - "$RELEASE_RECORD" <<'PY'
import json, sys
data=json.load(open(sys.argv[1],encoding='utf-8'))
stages={s['id']:s for s in data['stages']}
required=('V0','V1','V2','V3')
refused=[sid for sid in required if stages[sid]['status']!='pass']
if refused:
    raise SystemExit('V0-V3 must be pass before release; not pass: '+','.join(refused))
v35=stages['V3.5']
if v35['status']=='pass' and any(e['status']!='pass' for e in v35['evidence']):
    raise SystemExit('V3.5 pass record has incomplete evidence')
predeploy=('build_identity','controlled_migration','backup_and_isolated_restore','compatible_rollback')
not_passed=[e['kind'] for e in stages['V4']['evidence'] if e['kind'] in predeploy and e['status']!='pass']
if not_passed:
    raise SystemExit('release requires V4 build, migration, backup/restore and rollback evidence to pass; not pass: '+','.join(not_passed))
PY
read -r -p "Type APPROVED to release ${APP_IMAGE} to ${DOMAIN}: " approval
[[ "$approval" == "APPROVED" ]] || fail "interactive approval was not given"
compose=(docker --context "$DOCKER_CONTEXT" compose --project-name "$PROJECT_NAME" -f ops/compose.production.yaml)
# External database, roles, firewall, TLS connection and backups must be prepared.
"${compose[@]}" --profile tools pull app migrate edge
"${compose[@]}" --profile tools run --rm --no-deps migrate python -m alembic upgrade head
"${compose[@]}" up -d --wait app edge
curl --fail-with-body --silent --show-error --max-time 10 --noproxy '*' "https://${DOMAIN}/health/ready"
printf 'Health gate passed. Approval=%s; backup policy=%s; rollback owner=%s\n' \
  "$RELEASE_APPROVAL_REFERENCE" "$BACKUP_POLICY_REFERENCE" "$ROLLBACK_OWNER"
printf 'Now run authenticated, ordinary-member, removed-member and duplicate-request smoke checks. Health alone is insufficient.\n'
