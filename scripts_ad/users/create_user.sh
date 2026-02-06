#!/bin/bash
set -e

# CONFIGURACOES
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"
DOMAIN="${DOMAIN:-}"

ACTION="create_user"

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

ldap_add() {
  ldapadd -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW"
}

ldap_modify() {
  ldapmodify -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW"
}

# PROCESSAMENTO
USERNAME="${1:-}"
PASSWORD="${2:-}"
GIVEN_NAME="${3:-}"
SURNAME="${4:-}"
DISPLAY_NAME="${5:-}"
MAIL="${6:-}"
MUST_CHANGE="${7:-true}"

if [[ -z "$USERNAME" || -z "$PASSWORD" || -z "$DISPLAY_NAME" ]]; then
  error_exit "Uso: $0 <username> <password> [given_name] [surname] <display_name> [mail] [must_change]"
fi

require_env "LDAP_URI" "$LDAP_URI"
require_env "BIND_DN" "$BIND_DN"
require_env "BIND_PW" "$BIND_PW"
require_env "BASE_DN" "$BASE_DN"
require_env "USERS_OU" "$USERS_OU"
require_env "DOMAIN" "$DOMAIN"

# ACAO PRINCIPAL
ATTRS=""
if [[ -n "$GIVEN_NAME" ]]; then
  ATTRS="${ATTRS}\ngivenName: ${GIVEN_NAME}"
fi
if [[ -n "$SURNAME" ]]; then
  ATTRS="${ATTRS}\nsn: ${SURNAME}"
fi
if [[ -n "$DISPLAY_NAME" ]]; then
  ATTRS="${ATTRS}\ndisplayName: ${DISPLAY_NAME}"
fi
if [[ -n "$MAIL" ]]; then
  ATTRS="${ATTRS}\nmail: ${MAIL}"
fi

PWD_LAST_SET="0"
if [[ "$MUST_CHANGE" == "false" || "$MUST_CHANGE" == "0" ]]; then
  PWD_LAST_SET="-1"
fi

# Fase 1 - cria usuario desativado
LDIF_CREATE=$(cat <<EOF
dn: CN=${DISPLAY_NAME},${USERS_OU}
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: ${DISPLAY_NAME}
sAMAccountName: ${USERNAME}
userPrincipalName: ${USERNAME}@${DOMAIN}
userAccountControl: 544${ATTRS}
EOF
)

printf '%s\n' "$LDIF_CREATE" | ldap_add >/dev/null

# Fase 2 - define senha e ativa conta
ENCODED_PW="$(encode_password "$PASSWORD")"
LDIF_MODIFY=$(cat <<EOF
dn: CN=${DISPLAY_NAME},${USERS_OU}
changetype: modify
replace: unicodePwd
unicodePwd:: ${ENCODED_PW}
-
replace: userAccountControl
userAccountControl: 512
-
replace: pwdLastSet
pwdLastSet: ${PWD_LAST_SET}
EOF
)

printf '%s\n' "$LDIF_MODIFY" | ldap_modify >/dev/null

# SAIDA PADRONIZADA
echo "STATUS=OK"
echo "ACTION=${ACTION}"
echo "IDENTIFIER=${USERNAME}"
