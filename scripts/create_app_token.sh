#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./scripts/create_app_token.sh http://host:porta nome_app
#
# Exemplo:
#   ./scripts/create_app_token.sh http://localhost:8025 nefdesk

BASE_URL="${1:-http://localhost:8000}"
APP_NAME="${2:-}"

if [[ -z "$APP_NAME" ]]; then
  echo "Uso: $0 <base_url> <app_name>" >&2
  exit 2
fi

RESP_AND_CODE="$(
  curl -sS -X POST "${BASE_URL}/api/v1/auth/app-token" \
    -H "Content-Type: application/json" \
    -d "{\"app_name\":\"${APP_NAME}\"}" \
    -w $'\n%{http_code}'
)"

BODY="$(printf '%s' "$RESP_AND_CODE" | head -n -1)"
CODE="$(printf '%s' "$RESP_AND_CODE" | tail -n 1)"

if [[ "$CODE" != "200" ]]; then
  echo "Erro HTTP ${CODE} ao solicitar token." >&2
  echo "$BODY" >&2
  exit 1
fi

printf '%s\n' "$BODY"
