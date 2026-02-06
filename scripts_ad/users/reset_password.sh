#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"
DOMAIN="${DOMAIN:-}"

ACTION="reset_password"

# FUNCOES
error_exit() {
  echo "STATUS=ERROR" >&2
  echo "ACTION=${ACTION}" >&2
  echo "MESSAGE=$1" >&2
  exit 1
}

require_env() {
  if [[ -z "$2" ]]; then
    error_exit "Variavel obrigatoria ausente: $1"
  fi
}

encode_password() {
  local raw="$1"
  printf '"%s"' "$raw" | iconv -f UTF-8 -t UTF-16LE | base64 -w 0
}

ldap_search() {
  ldapsearch -LLL -o ldif-wrap=no -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW"
}

ldap_modify() {
  ldapmodify -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW"
}

get_user_dn() {
  ldap_search -b "$USERS_OU" "(sAMAccountName=${1})" dn \
    | awk '/^dn: / {sub(/^dn: /, "", $0); print; exit}'
}

# PROCESSAMENTO
USERNAME="${1:-}"
NEW_PASSWORD="${2:-}"
MUST_CHANGE="${3:-false}"

if [[ -z "$USERNAME" || -z "$NEW_PASSWORD" ]]; then
  error_exit "Uso: $0 <username> <new_password> [must_change]"
fi

require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "BASE_DN" "$BASE_DN"
require_env "USERS_OU" "$USERS_OU"
require_env "DOMAIN" "$DOMAIN"

DN="$(get_user_dn "$USERNAME")"
if [[ -z "$DN" ]]; then
  error_exit "Usuario nao encontrado"
fi

ENCODED_PW="$(encode_password "$NEW_PASSWORD")"
PWD_LAST_SET="-1"
if [[ "$MUST_CHANGE" == "true" || "$MUST_CHANGE" == "1" ]]; then
  PWD_LAST_SET="0"
fi

# ACAO PRINCIPAL
LDIF=$(cat <<EOF
dn: ${DN}
changetype: modify
replace: unicodePwd
unicodePwd:: ${ENCODED_PW}
-
replace: pwdLastSet
pwdLastSet: ${PWD_LAST_SET}
EOF
)

printf '%s\n' "$LDIF" | ldap_modify >/dev/null

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=${USERNAME}"
