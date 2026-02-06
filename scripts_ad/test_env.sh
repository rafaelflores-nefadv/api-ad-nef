#!/usr/bin/env bash
set -euo pipefail

# Wrapper para testar scripts em scripts_ad/ sem "export" manual.
# - Lê variáveis de configuração do projeto (core/config.py) via Python
# - Se BIND_PW não estiver definido no ambiente, solicita via prompt (sem eco)
# - Executa o script alvo com env inline (não persiste no ambiente do usuário)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-}"

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

exec env \
  "${ENV_KV[@]}" \
  BIND_PW="$BIND_PW" \
  "$TARGET_PATH" "$@"

