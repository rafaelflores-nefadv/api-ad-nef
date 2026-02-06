import json
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def log_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    object_type: str,
    object_id: str,
    result: str,
    details: Dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=object_id,
        result=result,
        details_json=json.dumps(details, ensure_ascii=True) if details else None,
    )
    db.add(entry)
    db.commit()
