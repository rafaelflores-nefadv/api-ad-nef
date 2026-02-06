from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from core.config import settings

class Role(str, Enum):
    admin = "admin"
    helpdesk = "helpdesk"
    auditor = "auditor"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/app-login")


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


def actor_from_payload(payload: Dict[str, Any]) -> str:
    if payload.get("app"):
        return str(payload["app"])
    subject = str(payload.get("sub", ""))
    if subject.startswith("app:"):
        return subject.split("app:", 1)[1]
    return subject or "unknown"
