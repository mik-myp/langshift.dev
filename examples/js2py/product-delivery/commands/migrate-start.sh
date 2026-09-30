#!/usr/bin/env bash
# Copy/adapt to the target's owned Compose project and reviewed images.
set -euo pipefail
: "${DOMAIN:?Set the approved public domain}"
compose=(docker compose -f ops/compose.production.yaml)
"${compose[@]}" --profile tools run --rm --no-deps migrate python -m alembic upgrade head
"${compose[@]}" up -d --wait app edge
curl --fail-with-body --silent --show-error --max-time 10 --noproxy '*' "https://${DOMAIN}/health/ready"
