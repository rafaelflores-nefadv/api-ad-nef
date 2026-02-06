#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"
DOMAIN="${DOMAIN:-}"

ACTION="create_group"

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

ldap_add() {
  ldapadd -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW"
}

# PROCESSAMENTO
GROUPNAME="${1:-}"
DESCRIPTION="${2:-}"

if [[ -z "$GROUPNAME" ]]; then
  error_exit "Uso: $0 <groupname> [description]"
fi

require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "BASE_DN" "$BASE_DN"
require_env "USERS_OU" "$USERS_OU"
require_env "DOMAIN" "$DOMAIN"

# ACAO PRINCIPAL
DESC_LINE=""
if [[ -n "$DESCRIPTION" ]]; then
  DESC_LINE="\ndescription: ${DESCRIPTION}"
fi

LDIF=$(cat <<EOF
dn: CN=${GROUPNAME},${BASE_DN}
objectClass: top
objectClass: group
cn: ${GROUPNAME}
sAMAccountName: ${GROUPNAME}
groupType: -2147483646${DESC_LINE}
EOF
)

printf '%s\n' "$LDIF" | ldap_add >/dev/null

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=${GROUPNAME}"
