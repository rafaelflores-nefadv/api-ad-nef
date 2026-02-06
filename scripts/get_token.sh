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

curl -fsS -X POST "${BASE_URL}/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=${USERNAME}" \
  --data-urlencode "password=${PASSWORD}" \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])'
