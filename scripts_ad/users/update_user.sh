#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"
DOMAIN="${DOMAIN:-}"

ACTION="update_user"

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

# PROCESSAMENTO
USERNAME="${1:-}"
GIVEN_NAME="${2:-}"
SURNAME="${3:-}"
DISPLAY_NAME="${4:-}"
MAIL="${5:-}"
UPN="${6:-}"

if [[ -z "$USERNAME" ]]; then
  error_exit "Uso: $0 <username> [given_name] [surname] [display_name] [mail] [upn]"
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

LDIF="dn: ${DN}
changetype: modify"

HAS_CHANGE="false"

if [[ -n "$GIVEN_NAME" ]]; then
  LDIF="${LDIF}
replace: givenName
givenName: ${GIVEN_NAME}
-"
  HAS_CHANGE="true"
fi
if [[ -n "$SURNAME" ]]; then
  LDIF="${LDIF}
replace: sn
sn: ${SURNAME}
-"
  HAS_CHANGE="true"
fi
if [[ -n "$DISPLAY_NAME" ]]; then
  LDIF="${LDIF}
replace: displayName
displayName: ${DISPLAY_NAME}
-"
  HAS_CHANGE="true"
fi
if [[ -n "$MAIL" ]]; then
  LDIF="${LDIF}
replace: mail
mail: ${MAIL}
-"
  HAS_CHANGE="true"
fi
if [[ -n "$UPN" ]]; then
  LDIF="${LDIF}
replace: userPrincipalName
userPrincipalName: ${UPN}
-"
  HAS_CHANGE="true"
fi

if [[ "$HAS_CHANGE" != "true" ]]; then
  error_exit "Nenhum atributo para atualizar"
fi

# ACAO PRINCIPAL
printf '%s\n' "$LDIF" | ldap_modify >/dev/null

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=${USERNAME}"
