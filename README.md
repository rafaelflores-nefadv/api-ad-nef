# api-ad-nef

API REST para gerenciamento de Samba Active Directory (Samba 4.x) usando **exclusivamente** `samba-tool` via `subprocess`.

## Documentacao

A documentacao completa (configuracao, autenticacao por aplicacao, exemplos e endpoints) esta em:

- `docs/README.md`

## Quickstart

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Subir a API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8025
```

Abrir Swagger:

- `http://localhost:8025/docs`
