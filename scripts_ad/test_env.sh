#!/usr/bin/env bash
set -euo pipefail

# Wrapper para testar scripts em scripts_ad/ sem "export" manual.
# - Carrega variáveis de um arquivo local (não versionado): scripts_ad/test_env.local
# - Se BIND_PW não estiver definido, solicita via prompt (sem eco)
# - Executa o script alvo com env inline (não persiste no ambiente do usuário)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/test_env.local"

usage() {
  cat <<'EOF' >&2
Uso:
  ./scripts_ad/test_env.sh <script_relativo_ao_scripts_ad> [args...]

Exemplos:
  ./scripts_ad/test_env.sh users/list_users.sh
  ./scripts_ad/test_env.sh users/get_user.sh jose.silva
  ./scripts_ad/test_env.sh groups/add_user_to_group.sh jose.silva TI-HELPDESK

Config:
  - Copie scripts_ad/test_env.local.example para scripts_ad/test_env.local
  - Preencha LDAP_URI, BIND_DN, BASE_DN, USERS_OU, DOMAIN
  - BIND_PW é opcional no arquivo (se ausente/vazio, será solicitado no prompt)
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

TARGET_INPUT="$1"
shift

# Resolve path do script alvo
if [[ "$TARGET_INPUT" == /* || "$TARGET_INPUT" == ./* ]]; then
  TARGET_PATH="$TARGET_INPUT"
else
  TARGET_PATH="${SCRIPT_DIR}/${TARGET_INPUT}"
fi

if [[ ! -f "$TARGET_PATH" ]]; then
  echo "Arquivo não encontrado: ${TARGET_PATH}" >&2
  echo "Dica: use caminho relativo a scripts_ad/, ex.: users/list_users.sh" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Config local não encontrada: ${CONFIG_FILE}" >&2
  echo "Crie a partir do exemplo: cp \"${CONFIG_FILE}.example\" \"${CONFIG_FILE}\"" >&2
  exit 1
fi

# Carrega variáveis do arquivo local (formato KEY=VALUE)
set -a
# shellcheck disable=SC1090
source "$CONFIG_FILE"
set +a

if [[ -z "${BIND_PW:-}" ]]; then
  read -r -s -p "BIND_PW: " BIND_PW
  echo
fi

required_vars=(LDAP_URI BIND_DN BIND_PW BASE_DN USERS_OU DOMAIN)
for k in "${required_vars[@]}"; do
  if [[ -z "${!k:-}" ]]; then
    echo "Variável obrigatória ausente: ${k}" >&2
    exit 1
  fi
done

exec env \
  LDAP_URI="$LDAP_URI" \
  BIND_DN="$BIND_DN" \
  BIND_PW="$BIND_PW" \
  BASE_DN="$BASE_DN" \
  USERS_OU="$USERS_OU" \
  DOMAIN="$DOMAIN" \
  "$TARGET_PATH" "$@"

