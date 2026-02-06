#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"

ACTION="list_groups"

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
require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "BASE_DN" "$BASE_DN"

# ACAO PRINCIPAL
if ! GROUPS="$(
  ldap_search -b "$BASE_DN" "(&(objectClass=group)(groupType:1.2.840.113556.1.4.803:=2147483648))" sAMAccountName \
    | awk -F': ' '/^sAMAccountName: / {print $2}'
)"; then
  error_exit "Falha ao listar grupos"
fi

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=list"
echo "DATA_BEGIN"
printf '%s\n' "$GROUPS"
echo "DATA_END"
