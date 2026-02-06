# Documentacao da API Samba AD

Esta API oferece gerenciamento de Samba Active Directory (Samba 4.x) usando
exclusivamente scripts Bash com `ldapadd`, `ldapmodify` e `ldapsearch`. Ela e stateless, o AD e a fonte
de verdade e o banco de dados local armazena apenas metadados, auditoria,
cache e informacoes de sincronizacao.

## Stack

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- JWT (token por aplicacao)
- Scripts Bash (`ldapadd`, `ldapmodify`, `ldapsearch`) via `subprocess` (sem `shell=True`)

## Regras tecnicas obrigatorias

- Nunca usar LDAP direto no Python
- Nunca usar `shell=True`
- Nunca executar comandos arbitrarios
- Toda chamada ao AD passa por scripts em `scripts_ad/`
- API stateless
- AD e a fonte da verdade
- Banco local apenas para auditoria, cache, metadados e sincronizacao

## Estrutura do projeto

```
.
├── app/                       # shim para uvicorn app.main:app
│   └── main.py
├── main.py                    # entrypoint principal
├── core/
│   ├── config.py
│   ├── security.py
│   ├── rate_limit.py
├── services/
│   ├── script_runner.py
│   ├── users.py
│   ├── groups.py
│   ├── app_tokens.py
├── api/
│   ├── v1/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── groups.py
├── models/
│   ├── user.py
│   ├── group.py
│   ├── auth.py
├── db/
│   ├── session.py
│   ├── models.py
├── audit/
│   └── logger.py
├── scripts/
│   ├── create_app_token.sh
├── scripts_ad/
│   ├── users/
│   └── groups/
└── docs/
    └── README.md
```

## Configuracao (variaveis de ambiente)

Crie um `.env` na raiz do projeto com os valores abaixo (exemplos):

```
APP_ENV=dev
CORS_ALLOW_ORIGINS=["*"]

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=30
JWT_NEVER_EXPIRES=true

DATABASE_URL=sqlite:///./app.db

RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

AD_SCRIPTS_DIR=scripts_ad
AD_SCRIPT_TIMEOUT_SECONDS=20
```

```
LDAP_URI="ldap://SRV-ADMASTER.nabarrete.local"
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local"
BIND_PW="<nao registrar aqui>"
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local"
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local"
DOMAIN="nabarrete.local"
```

Observacao: nunca coloque senhas reais na documentacao ou no repositorio.

Notas:
- `JWT_NEVER_EXPIRES=true` gera JWT sem o campo `exp` (nao expira). Se voce definir `JWT_NEVER_EXPIRES=false`, ai sim `JWT_ACCESS_TOKEN_MINUTES` passa a ser aplicado.

## Testar scripts `.sh` sem `export` manual (dev)

Objetivo: executar scripts em `scripts_ad/` definindo as variaveis **apenas para aquele comando**, sem persistir no ambiente do usuario.

Regras:
- Nao usar `shell=True` (inclusive em Python).
- Nao colocar senhas reais em arquivos versionados/documentacao.

### Opcao A (Bash): variaveis inline (nao persistem)

Modelo (copie/cole e ajuste):

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/list_users.sh
```

Exemplos por script:

Usuarios:

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/list_users.sh
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/get_user.sh jose.silva
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/create_user.sh jose.silva "SenhaForte#123" Jose Silva "Jose Silva" jose.silva@exemplo.com true
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/update_user.sh jose.silva Jose Silva "Jose Silva" jose.silva@exemplo.com "jose.silva@nabarrete.local"
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/disable_user.sh jose.silva
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/enable_user.sh jose.silva
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/reset_password.sh jose.silva "NovaSenha#123" true
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/delete_user.sh jose.silva
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/users/sync_users.sh
```

Grupos:

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/list_groups.sh
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/get_group.sh TI-HELPDESK
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/create_group.sh TI-HELPDESK "Grupo do helpdesk"
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/update_group.sh TI-HELPDESK "Descricao atualizada"
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/add_user_to_group.sh jose.silva TI-HELPDESK
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/remove_user_from_group.sh jose.silva TI-HELPDESK
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/disable_group.sh TI-HELPDESK "OU=Grupos Desativados,OU=Nabarrete,DC=nabarrete,DC=local"
```

```
LDAP_URI="ldap://srv-admaster.nabarrete.local" \
BIND_DN="CN=Suporte TI NEF,OU=ADM Users,OU=Nabarrete,DC=nabarrete,DC=local" \
BIND_PW="senha_aqui" \
BASE_DN="OU=Nabarrete,DC=nabarrete,DC=local" \
USERS_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local" \
DOMAIN="nabarrete.local" \
./scripts_ad/groups/sync_groups.sh
```

### Opcao B (recomendado): wrapper `scripts_ad/test_env.sh`

1) Crie seu arquivo local (nao versionado):

```
cp scripts_ad/test_env.local.example scripts_ad/test_env.local
```

2) Rode qualquer script passando o caminho relativo a `scripts_ad/`:

```
./scripts_ad/test_env.sh users/list_users.sh
./scripts_ad/test_env.sh users/get_user.sh jose.silva
./scripts_ad/test_env.sh groups/list_groups.sh
./scripts_ad/test_env.sh groups/add_user_to_group.sh jose.silva TI-HELPDESK
```

Observacao: se `BIND_PW` nao estiver definido em `scripts_ad/test_env.local`, o wrapper pede no prompt (sem eco).

### Opcao C (Python): `subprocess.run(..., env=...)` (sem depender do ambiente)

Use o runner de desenvolvimento:

```
python scripts_ad/devtools/run_script.py users/list_users.sh
python scripts_ad/devtools/run_script.py groups/list_groups.sh
python scripts_ad/devtools/run_script.py users/get_user.sh jose.silva
```

Ele carrega `scripts_ad/test_env.local` e sempre executa o `.sh` com `env={...}` (sem `shell=True`).

## Como rodar

1. Instale dependencias:
   - `fastapi`
   - `uvicorn`
   - `sqlalchemy`
   - `pydantic-settings`
   - `python-jose`

2. Suba o servidor:

```
uvicorn app.main:app --reload
```

3. Acesse a documentacao:
- Swagger: `http://localhost:8025/docs`
- OpenAPI: `http://localhost:8025/openapi.json`

## Autenticacao (JWT)

### Fluxo: aplicacao

Esse fluxo cria um `app_name`, gera um `app_secret` e retorna um JWT.
Guarde o `app_secret` com seguranca.

```
POST /api/v1/auth/app-token
```

Linux/macOS (bash):

```
chmod +x scripts/create_app_token.sh
./scripts/create_app_token.sh http://localhost:8025 NOME_DA_APLICACAO
```

Para renovar o JWT usando o `app_secret`:

```
POST /api/v1/auth/app-login
```

Exemplo curl:

```
curl -X POST http://localhost:8025/api/v1/auth/app-login \
  -H "Content-Type: application/json" \
  -d '{"app_name":"NOME_DA_APLICACAO","app_secret":"SEU_SECRET"}'
```

Retorno:
```
{
  "app_name": "NOME_DA_APLICACAO",
  "app_secret": "<secret-apenas-na-criacao>",
  "access_token": "<token>",
  "token_type": "bearer"
}
```

Use o token no header:
```
Authorization: Bearer <token>
```

### Testar no navegador (Swagger)

1. Abra `http://localhost:8025/docs`
2. Clique em **Authorize**
3. Cole `Bearer <token>`
4. Execute as rotas (ex.: `GET /api/v1/users`)

## RBAC

Roles disponiveis:
- `admin`
- `helpdesk`
- `auditor`

Controle aplicado via dependencias em cada endpoint.

## Rate limit

Aplicado nos endpoints sensiveis via dependencia `rate_limit_dependency`.
O limitador e em memoria (por processo).

## Auditoria

Todas as acoes criticas geram logs na tabela `audit_logs`:
- create user
- update user
- disable/enable user
- reset password
- alteracoes de grupos
- sincronizacoes

Campos principais:
- `actor`, `action`, `object_type`, `object_id`, `result`, `details_json`, `created_at`

O campo `details_json` inclui:
- `script`
- `arguments`
- `stdout`/`stderr` quando aplicavel

## Wrapper de scripts

Arquivo: `services/script_runner.py`

Regras:
- Usa `subprocess.run`
- Sem `shell=True`
- Captura stdout/stderr
- Lanca excecao se `returncode != 0`
- Sanitiza argumentos
- Timeout configuravel
- Injeta variaveis LDAP via ambiente

## Saida padronizada dos scripts

Todos os scripts retornam via stdout:
- `STATUS=OK`
- `ACTION=<acao>`
- `IDENTIFIER=<username ou group>`

Quando houver dados:
- `DATA_BEGIN`
- `<dados>`
- `DATA_END`

## Endpoints v1

### Usuarios

- `GET /api/v1/users`
- `GET /api/v1/users/{username}`
- `POST /api/v1/users`
- `PATCH /api/v1/users/{username}`
- `DELETE /api/v1/users/{username}`
- `POST /api/v1/users/{username}/reset-password`
- `POST /api/v1/users/{username}/enable`
- `POST /api/v1/users/{username}/disable`
- `POST /api/v1/users/{username}/groups`
- `DELETE /api/v1/users/{username}/groups`
- `POST /api/v1/sync/users`

### Grupos

- `GET /api/v1/groups`
- `GET /api/v1/groups/{groupname}`
- `POST /api/v1/groups`
- `PATCH /api/v1/groups/{groupname}`
- `POST /api/v1/groups/{groupname}/members`
- `DELETE /api/v1/groups/{groupname}/members`
- `POST /api/v1/groups/{groupname}/disable`
- `POST /api/v1/sync/groups`

## Exemplos rapidos (curl)

Gerar token por aplicacao (recomendado):
```
curl -X POST http://localhost:8025/api/v1/auth/app-token \
  -H "Content-Type: application/json" \
  -d '{"app_name":"gestao-nef"}'
```

Listar usuarios (com token):
```
curl http://localhost:8025/api/v1/users \
  -H "Authorization: Bearer <token>"
```

Resposta (texto):
```
STATUS=OK
ACTION=list_users
IDENTIFIER=list
DATA_BEGIN
usuario1
usuario2
DATA_END
```

Criar usuario:
```
curl -X POST "http://localhost:8025/api/v1/users" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jose.silva",
    "password": "SenhaForte#123",
    "given_name": "Jose",
    "surname": "Silva",
    "display_name": "Jose Silva",
    "mail": "jose.silva@exemplo.com",
    "must_change_password": true
  }'
```

## Sincronizacao

Os endpoints `/sync/users` e `/sync/groups`:
- listam objetos no AD
- normalizam saida dos scripts
- calculam hash por objeto
- persistem apenas metadados e auditoria

O AD nunca e sobrescrito a partir do banco.

## Observacoes

- Os comandos LDAP dependem de permissoes do host e do dominio.
- Para ambientes distribuidos, substitua o rate limit em memoria por Redis.
