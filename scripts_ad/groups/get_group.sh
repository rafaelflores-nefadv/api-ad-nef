#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"
DOMAIN="${DOMAIN:-}"

ACTION="get_group"

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

# PROCESSAMENTO
GROUPNAME="${1:-}"
if [[ -z "$GROUPNAME" ]]; then
  error_exit "Uso: $0 <groupname>"
fi

require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "BASE_DN" "$BASE_DN"
require_env "USERS_OU" "$USERS_OU"
require_env "DOMAIN" "$DOMAIN"

# ACAO PRINCIPAL
RESULT="$(
  ldap_search -b "$BASE_DN" "(sAMAccountName=${GROUPNAME})"
)"

if ! printf '%s\n' "$RESULT" | grep -q '^dn: '; then
  error_exit "Grupo nao encontrado"
fi

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=${GROUPNAME}"
echo "DATA_BEGIN"
printf '%s\n' "$RESULT"
echo "DATA_END"
