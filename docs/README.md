# Documentacao da API Samba AD

Esta API oferece gerenciamento de Samba Active Directory (Samba 4.x) usando
exclusivamente o `samba-tool` via `subprocess`. Ela e stateless, o AD e a fonte
de verdade e o banco de dados local armazena apenas metadados, auditoria,
cache e informacoes de sincronizacao.

## Stack

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- JWT (OAuth2 Password Flow)
- `samba-tool` via `subprocess` (sem `shell=True`)

## Regras tecnicas obrigatorias

- Nunca usar LDAP direto
- Nunca usar `shell=True`
- Nunca executar comandos arbitrarios
- Toda chamada ao AD passa por `app/services/samba.py`
- API stateless
- AD e a fonte da verdade
- Banco local apenas para auditoria, cache, metadados e sincronizacao

## Estrutura do projeto

```
app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   ├── rate_limit.py
├── services/
│   ├── samba.py
│   ├── samba_group_editor.py
│   ├── users.py
│   ├── groups.py
├── api/
│   ├── v1/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── groups.py
├── models/
│   ├── user.py
│   ├── group.py
├── db/
│   ├── session.py
│   ├── models.py
└── audit/
    └── logger.py
```

## Configuracao (variaveis de ambiente)

Crie um `.env` na raiz do projeto com os valores abaixo (exemplos):

```
APP_ENV=dev
CORS_ALLOW_ORIGINS=["*"]

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=30

DATABASE_URL=sqlite:///./app.db

SAMBA_TOOL_PATH=samba-tool
SAMBA_REALM=NABARRETE.LOCAL
SAMBA_WORKGROUP=NABARRETE
SAMBA_AUTH_USER=SuporteTI.NEF
SAMBA_AUTH_DOMAIN=NABARRETE
SAMBA_TIMEOUT_SECONDS=20
SAMBA_DRY_RUN=false

RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

As configuracoes abaixo foram fornecidas como padrao do ambiente, mas
nao sao usadas pela API porque o acesso ao AD e feito via `samba-tool`,
nao via LDAP direto:

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
- `SAMBA_AUTH_*` sao opcionais e nao sao usados no comando por padrao.
- `SAMBA_DRY_RUN=true` evita executar o `samba-tool` e retorna o comando.

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
- Swagger: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

## Autenticacao (JWT)

Endpoint de login:
```
POST /api/v1/auth/token
```

Body (form-data):
- `username`
- `password`

### Gerar token via terminal (sem expor senha na linha de comando)

Linux/macOS (bash):

```
chmod +x scripts/get_token.sh
./scripts/get_token.sh http://localhost:8025 SEU_USUARIO
```

Windows (PowerShell):

```
powershell -ExecutionPolicy Bypass -File .\scripts\get_token.ps1 -BaseUrl "http://localhost:8025" -Username "SEU_USUARIO"
```

Retorno:
```
{
  "access_token": "<token>",
  "token_type": "bearer"
}
```

Use o token no header:
```
Authorization: Bearer <token>
```

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

## Wrapper samba-tool

Arquivo: `app/services/samba.py`

Regras:
- Usa `subprocess.run`
- Sem `shell=True`
- Captura stdout/stderr
- Lanca excecao se `returncode != 0`
- Sanitiza argumentos
- Timeout configuravel
- Dry-run opcional

## Endpoints v1

### Usuarios

- `GET /api/v1/users`
- `GET /api/v1/users/{username}`
- `POST /api/v1/users`
- `PATCH /api/v1/users/{username}`
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

Login:
```
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=administrator&password=senha"
```

Listar usuarios:
```
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <token>"
```

Criar usuario (dry-run):
```
curl -X POST "http://localhost:8000/api/v1/users?dry_run=true" \
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

Os endpoints `/sync/users` e `/sync/groups` executam em background e:
- listam objetos no AD
- normalizam saida do `samba-tool`
- calculam hash por objeto
- persistem apenas metadados e auditoria

O AD nunca e sobrescrito a partir do banco.

## Observacoes

- Alguns comandos do `samba-tool` dependem de permissoes do host e do dominio.
- Para ambientes distribuidos, substitua o rate limit em memoria por Redis.
