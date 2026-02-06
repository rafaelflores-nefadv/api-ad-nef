import hashlib
import hmac
from datetime import datetime, timezone
from secrets import token_urlsafe
from typing import Tuple

from sqlalchemy.orm import Session

from core.config import settings
from core.security import Role, create_access_token
from db.models import AppClient


def _hash_secret(secret: str) -> str:
    key = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(key, secret.encode("utf-8"), hashlib.sha256).hexdigest()


def create_app_credentials(db: Session, app_name: str) -> Tuple[str, str]:
    secret = token_urlsafe(32)
    secret_hash = _hash_secret(secret)
    existing = db.query(AppClient).filter(AppClient.app_name == app_name).one_or_none()
    now = datetime.now(timezone.utc)
    if existing:
        existing.secret_hash = secret_hash
        existing.last_used = now
    else:
        db.add(AppClient(app_name=app_name, secret_hash=secret_hash, created_at=now, last_used=now))
    db.commit()
    return app_name, secret


def verify_app_secret(db: Session, app_name: str, secret: str) -> bool:
    client = db.query(AppClient).filter(AppClient.app_name == app_name).one_or_none()
    if not client:
        return False
    expected = _hash_secret(secret)
    if not hmac.compare_digest(expected, client.secret_hash):
        return False
    client.last_used = datetime.now(timezone.utc)
    db.commit()
    return True


def issue_app_token(app_name: str) -> str:
    return create_access_token(subject=f"app:{app_name}", role=Role.admin, extra={"app": app_name})
