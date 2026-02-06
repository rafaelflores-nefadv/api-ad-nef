from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from core.config import settings
from services.samba import SambaToolError, samba_verify_user_password


class Role(str, Enum):
    admin = "admin"
    helpdesk = "helpdesk"
    auditor = "auditor"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(subject: str, role: Role, extra: Dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "role": role.value, "iat": int(now.timestamp())}
    if not settings.jwt_never_expires:
        expire = now + timedelta(minutes=settings.jwt_access_token_minutes)
        payload["exp"] = int(expire.timestamp())
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc
    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token incompleto")
    return payload


def get_current_payload(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return verify_token(token)


def require_roles(*roles: Role):
    def _checker(payload: Dict[str, Any] = Depends(get_current_payload)) -> Dict[str, Any]:
        if payload.get("role") not in {role.value for role in roles}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissao insuficiente")
        return payload

    return _checker


def authenticate_and_issue_token(form: OAuth2PasswordRequestForm) -> Dict[str, str]:
    try:
        samba_verify_user_password(form.username, form.password)
    except SambaToolError as exc:
        # Diferenciar falhas de autenticacao de falhas de infraestrutura
        if exc.returncode in {124, 127}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=exc.stderr or str(exc),
            ) from exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.stderr or str(exc)) from exc
    return {"access_token": create_access_token(form.username, Role.admin), "token_type": "bearer"}
