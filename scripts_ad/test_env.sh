#!/usr/bin/env bash
set -euo pipefail

# Wrapper para testar scripts em scripts_ad/ sem "export" manual.
# - Lê variáveis de configuração do projeto (core/config.py) via Python
# - Se BIND_PW não estiver definido no ambiente, solicita via prompt (sem eco)
# - Executa o script alvo com env inline (não persiste no ambiente do usuário)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-}"
TEST_ENV_DEBUG="${TEST_ENV_DEBUG:-0}"

usage() {
  cat <<'EOF' >&2
Uso:
  ./scripts_ad/test_env.sh <script_relativo_ao_scripts_ad> [args...]

Exemplos:
  ./scripts_ad/test_env.sh users/list_users.sh
  ./scripts_ad/test_env.sh users/get_user.sh jose.silva
  ./scripts_ad/test_env.sh groups/add_user_to_group.sh jose.silva TI-HELPDESK

Config:
  - As variáveis LDAP são obtidas do `core/config.py` (Settings).
  - Se você já usa `.env` para a API, o Settings também respeita esse arquivo.
  - Por segurança, a senha (BIND_PW) é solicitada no prompt, a menos que BIND_PW
    já esteja definido no ambiente do processo.
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

if [[ -z "${BIND_PW:-}" ]]; then
  read -r -s -p "BIND_PW: " BIND_PW
  echo
fi

pick_python() {
  # 1) override explícito
  if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN:-}" ]]; then
    echo "$PYTHON_BIN"
    return 0
  fi
  # 2) venv ativo
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    echo "${VIRTUAL_ENV}/bin/python"
    return 0
  fi
  # 3) venv no repo
  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    echo "${REPO_ROOT}/.venv/bin/python"
    return 0
  fi
  if [[ -x "${REPO_ROOT}/venv/bin/python" ]]; then
    echo "${REPO_ROOT}/venv/bin/python"
    return 0
  fi
  # 4) python do sistema
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  return 1
}

PYTHON="$(pick_python || true)"
if [[ -z "${PYTHON:-}" ]]; then
  echo "Python não encontrado. Instale Python 3.11+ ou ative a venv da API." >&2
  echo "Dica: VIRTUAL_ENV=/caminho/venv ou PYTHON_BIN=/caminho/python" >&2
  exit 1
fi

# Coleta config do Settings (core/config.py) sem precisar de arquivos extras.
# Usa separador NUL para preservar valores com espaços.
mapfile -d '' -t ENV_KV < <(
  REPO_ROOT="$REPO_ROOT" "$PYTHON" - <<'PY'
import os
import sys
from pathlib import Path

repo_root_env = os.environ.get("REPO_ROOT")
if not repo_root_env:
    raise SystemExit("REPO_ROOT não definido (erro interno do wrapper).")
repo_root = Path(repo_root_env).resolve()

sys.path.insert(0, str(repo_root))
from core.config import settings  # noqa: E402

pairs = {
    "LDAP_URI": settings.ldap_uri,
    "BIND_DN": settings.bind_dn,
    "BASE_DN": settings.base_dn,
    "USERS_OU": settings.users_ou,
    "DOMAIN": settings.domain,
}

# Se o usuário já passou algo no ambiente, respeita.
for k in list(pairs.keys()):
    if os.environ.get(k):
        pairs[k] = os.environ[k]

for k, v in pairs.items():
    v = "" if v is None else str(v)
    # normaliza: remove espaços/CRLF que podem quebrar DN/base
    v = v.strip()
    sys.stdout.write(f"{k}={v}\0")
PY
)

# Validação mínima (BIND_PW vem do prompt/ambiente)
required_vars=(LDAP_URI BIND_DN BASE_DN USERS_OU DOMAIN)
for k in "${required_vars[@]}"; do
  FOUND="false"
  for kv in "${ENV_KV[@]}"; do
    if [[ "$kv" == "${k}="* && -n "${kv#*=}" ]]; then
      FOUND="true"
      break
    fi
  done
  if [[ "$FOUND" != "true" ]]; then
    echo "Variável obrigatória ausente ou vazia (via Settings/env): ${k}" >&2
    exit 1
  fi
done

if [[ -z "${BIND_PW:-}" ]]; then
  echo "Variável obrigatória ausente: BIND_PW" >&2
  exit 1
fi

if [[ "$TEST_ENV_DEBUG" == "1" || "$TEST_ENV_DEBUG" == "true" ]]; then
  echo "[test_env] repo_root=${REPO_ROOT}" >&2
  echo "[test_env] python=${PYTHON}" >&2
  echo "[test_env] target=${TARGET_PATH}" >&2
  echo "[test_env] env:" >&2
  for kv in "${ENV_KV[@]}"; do
    echo "  - ${kv}" >&2
  done
  echo "  - BIND_PW=<redacted,len=${#BIND_PW}>" >&2
fi

# -----------------------------------------------------------------------------
# Compatibilidade (TESTE): shim temporário para `ldapsearch`
#
# Alguns scripts chamam `ldapsearch` via função, mas os argumentos (ex.: `-b`,
# filtro, atributos) não chegam ao binário. Em ambientes onde não existe BASE
# padrão no ldap.conf, isso resulta em "empty base DN" / No such object (32).
#
# Para NÃO alterar os scripts `.sh`, este wrapper injeta um `ldapsearch` shim no
# PATH que adiciona os argumentos esperados, de forma temporária e só no teste.
# -----------------------------------------------------------------------------

REAL_LDAPSEARCH="$(command -v ldapsearch || true)"
if [[ -z "${REAL_LDAPSEARCH:-}" ]]; then
  echo "ldapsearch não encontrado no PATH (instale ldap-utils/openldap-clients)." >&2
  exit 1
fi

SHIM_DIR="$(mktemp -d)"
PLAN_FILE="$(mktemp)"

cleanup() {
  rm -f "$PLAN_FILE" 2>/dev/null || true
  rm -rf "$SHIM_DIR" 2>/dev/null || true
}
trap cleanup EXIT

cat > "${SHIM_DIR}/ldapsearch" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

REAL="${TEST_REAL_LDAPSEARCH:-}"
PLAN="${TEST_LDAPSEARCH_PLAN:-}"

if [[ -z "${REAL:-}" || ! -x "$REAL" ]]; then
  echo "[ldapsearch-shim] TEST_REAL_LDAPSEARCH inválido" >&2
  exit 127
fi

if [[ -z "${PLAN:-}" || ! -f "$PLAN" ]]; then
  exec "$REAL" "$@"
fi

# Lock simples para consumo do plano (evita corrida entre múltiplos ldapsearch)
LOCK="${PLAN}.lockdir"
for _i in {1..200}; do
  if mkdir "$LOCK" 2>/dev/null; then
    break
  fi
  sleep 0.01
done
if [[ ! -d "$LOCK" ]]; then
  exec "$REAL" "$@"
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

# Lê o primeiro bloco (uma chamada) do plano: args em 1 por linha, bloco termina em linha vazia
mapfile -t BLOCK < <(awk 'NF==0{exit} {print}' "$PLAN")
if [[ ${#BLOCK[@]} -eq 0 ]]; then
  exec "$REAL" "$@"
fi

# Remove o primeiro bloco do arquivo de plano
awk 'BEGIN{skip=1} { if(skip){ if(NF==0){skip=0; next} else next } } {print}' "$PLAN" > "${PLAN}.tmp" && mv "${PLAN}.tmp" "$PLAN"

# Executa ldapsearch real com args originais + args planejados
exec "$REAL" "$@" "${BLOCK[@]}"
SH
chmod +x "${SHIM_DIR}/ldapsearch"

SCRIPT_NAME="$(basename "$TARGET_PATH")"

write_block() {
  # Cada linha = 1 argumento. Termina bloco com linha vazia.
  for arg in "$@"; do
    printf '%s\n' "$arg" >> "$PLAN_FILE"
  done
  printf '\n' >> "$PLAN_FILE"
}

case "$SCRIPT_NAME" in
  list_users.sh)
    write_block \
      -b "$(
        for kv in "${ENV_KV[@]}"; do [[ "$kv" == USERS_OU=* ]] && printf '%s' "${kv#*=}"; done
      )" \
      "(&(objectClass=user)(!(objectClass=computer))(!(userAccountControl:1.2.840.113556.1.4.803:=2)))" \
      sAMAccountName
    ;;
  list_groups.sh)
    write_block \
      -b "$(
        for kv in "${ENV_KV[@]}"; do [[ "$kv" == BASE_DN=* ]] && printf '%s' "${kv#*=}"; done
      )" \
      "(&(objectClass=group)(groupType:1.2.840.113556.1.4.803:=2147483648))" \
      sAMAccountName
    ;;
  get_user.sh)
    USERNAME="${1:-}"
    if [[ -z "${USERNAME:-}" ]]; then
      echo "Uso: ./scripts_ad/test_env.sh users/get_user.sh <username>" >&2
      exit 1
    fi
    write_block \
      -b "$(
        for kv in "${ENV_KV[@]}"; do [[ "$kv" == USERS_OU=* ]] && printf '%s' "${kv#*=}"; done
      )" \
      "(sAMAccountName=${USERNAME})"
    ;;
  get_group.sh)
    GROUPNAME="${1:-}"
    if [[ -z "${GROUPNAME:-}" ]]; then
      echo "Uso: ./scripts_ad/test_env.sh groups/get_group.sh <groupname>" >&2
      exit 1
    fi
    write_block \
      -b "$(
        for kv in "${ENV_KV[@]}"; do [[ "$kv" == BASE_DN=* ]] && printf '%s' "${kv#*=}"; done
      )" \
      "(sAMAccountName=${GROUPNAME})"
    ;;
  disable_user.sh|enable_user.sh)
    USERNAME="${1:-}"
    if [[ -z "${USERNAME:-}" ]]; then
      echo "Uso: $0 <username>" >&2
      exit 1
    fi
    USERS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == USERS_OU=* ]] && printf '%s' "${kv#*=}"; done
    )"
    write_block -b "$USERS_BASE" "(sAMAccountName=${USERNAME})" dn
    write_block -b "$USERS_BASE" "(sAMAccountName=${USERNAME})" userAccountControl
    ;;
  update_user.sh|delete_user.sh|reset_password.sh)
    USERNAME="${1:-}"
    if [[ -z "${USERNAME:-}" ]]; then
      echo "Uso: $0 <username> ..." >&2
      exit 1
    fi
    USERS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == USERS_OU=* ]] && printf '%s' "${kv#*=}"; done
    )"
    write_block -b "$USERS_BASE" "(sAMAccountName=${USERNAME})" dn
    ;;
  add_user_to_group.sh|remove_user_from_group.sh)
    USERNAME="${1:-}"
    GROUPNAME="${2:-}"
    if [[ -z "${USERNAME:-}" || -z "${GROUPNAME:-}" ]]; then
      echo "Uso: $0 <username> <groupname>" >&2
      exit 1
    fi
    USERS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == USERS_OU=* ]] && printf '%s' "${kv#*=}"; done
    )"
    GROUPS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == BASE_DN=* ]] && printf '%s' "${kv#*=}"; done
    )"
    write_block -b "$USERS_BASE" "(sAMAccountName=${USERNAME})" dn
    write_block -b "$GROUPS_BASE" "(sAMAccountName=${GROUPNAME})" dn
    ;;
  disable_group.sh|update_group.sh)
    GROUPNAME="${1:-}"
    if [[ -z "${GROUPNAME:-}" ]]; then
      echo "Uso: $0 <groupname> ..." >&2
      exit 1
    fi
    GROUPS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == BASE_DN=* ]] && printf '%s' "${kv#*=}"; done
    )"
    write_block -b "$GROUPS_BASE" "(sAMAccountName=${GROUPNAME})" dn
    ;;
  sync_users.sh)
    USERS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == USERS_OU=* ]] && printf '%s' "${kv#*=}"; done
    )"
    write_block -b "$USERS_BASE" "(&(objectClass=user)(sAMAccountName=*))"
    ;;
  sync_groups.sh)
    GROUPS_BASE="$(
      for kv in "${ENV_KV[@]}"; do [[ "$kv" == BASE_DN=* ]] && printf '%s' "${kv#*=}"; done
    )"
    write_block -b "$GROUPS_BASE" "(objectClass=group)"
    ;;
  *)
    # Sem plano: shim vira pass-through pro ldapsearch real
    ;;
esac

PATH="${SHIM_DIR}:$PATH" \
TEST_REAL_LDAPSEARCH="$REAL_LDAPSEARCH" \
TEST_LDAPSEARCH_PLAN="$PLAN_FILE" \
env \
  "${ENV_KV[@]}" \
  BIND_PW="$BIND_PW" \
  PATH="${SHIM_DIR}:$PATH" \
  TEST_REAL_LDAPSEARCH="$REAL_LDAPSEARCH" \
  TEST_LDAPSEARCH_PLAN="$PLAN_FILE" \
  "$TARGET_PATH" "$@"

exit_code=$?
exit "$exit_code"

