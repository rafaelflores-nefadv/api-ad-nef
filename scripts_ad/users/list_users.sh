#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
USERS_OU="${USERS_OU:-}"

ACTION="list_users"

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
  ldapsearch -x -LLL -o ldif-wrap=no -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW"
}

# PROCESSAMENTO
require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "USERS_OU" "$USERS_OU"

# ACAO PRINCIPAL
LDAP_ERR_FILE="$(mktemp)"
if ! RESULT="$(ldap_search -b "$USERS_OU" "(&(objectClass=user)(!(objectClass=computer))(!(userAccountControl:1.2.840.113556.1.4.803:=2)))" sAMAccountName 2>"$LDAP_ERR_FILE")"; then
  if [[ -s "$LDAP_ERR_FILE" ]]; then
    cat "$LDAP_ERR_FILE" >&2
  fi
  rm -f "$LDAP_ERR_FILE"
  error_exit "Falha ao listar usuarios"
fi
if [[ -s "$LDAP_ERR_FILE" ]]; then
  cat "$LDAP_ERR_FILE" >&2
  rm -f "$LDAP_ERR_FILE"
  error_exit "Falha ao listar usuarios"
fi
rm -f "$LDAP_ERR_FILE"
USERS="$(printf '%s\n' "$RESULT" | awk -F': ' '/^sAMAccountName: / {print $2}')"

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=list"
echo "DATA_BEGIN"
printf '%s\n' "$USERS"
echo "DATA_END"
