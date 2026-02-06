#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"
DOMAIN="${DOMAIN:-}"

ACTION="remove_user_from_group"

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

get_group_dn() {
  ldap_search -b "$BASE_DN" "(sAMAccountName=${1})" dn \
    | awk '/^dn: / {sub(/^dn: /, "", $0); print; exit}'
}

# PROCESSAMENTO
USERNAME="${1:-}"
GROUPNAME="${2:-}"

if [[ -z "$USERNAME" || -z "$GROUPNAME" ]]; then
  error_exit "Uso: $0 <username> <groupname>"
fi

require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "BASE_DN" "$BASE_DN"
require_env "USERS_OU" "$USERS_OU"
require_env "DOMAIN" "$DOMAIN"

USER_DN="$(get_user_dn "$USERNAME")"
GROUP_DN="$(get_group_dn "$GROUPNAME")"
if [[ -z "$USER_DN" ]]; then
  error_exit "Usuario nao encontrado"
fi
if [[ -z "$GROUP_DN" ]]; then
  error_exit "Grupo nao encontrado"
fi

# ACAO PRINCIPAL
LDIF=$(cat <<EOF
dn: ${GROUP_DN}
changetype: modify
delete: member
member: ${USER_DN}
EOF
)

printf '%s\n' "$LDIF" | ldap_modify >/dev/null

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=${GROUPNAME}"
