#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./scripts/get_token.sh http://host:porta usuario
#
# Exemplo:
#   ./scripts/get_token.sh http://localhost:8025 administrator

BASE_URL="${1:-http://localhost:8000}"
USERNAME="${2:-}"

if [[ -z "$USERNAME" ]]; then
  echo "Uso: $0 <base_url> <username>" >&2
  exit 2
fi

read -r -s -p "Senha para ${USERNAME}: " PASSWORD
echo

RESP_AND_CODE="$(
  curl -sS -X POST "${BASE_URL}/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=${USERNAME}" \
    --data-urlencode "password=${PASSWORD}" \
    -w $'\n%{http_code}'
)"

BODY="$(printf '%s' "$RESP_AND_CODE" | head -n -1)"
CODE="$(printf '%s' "$RESP_AND_CODE" | tail -n 1)"

if [[ "$CODE" != "200" ]]; then
  echo "Erro HTTP ${CODE} ao solicitar token." >&2
  echo "$BODY" >&2
  exit 1
fi

printf '%s' "$BODY" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])'
