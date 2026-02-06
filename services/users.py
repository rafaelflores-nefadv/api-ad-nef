import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from audit.logger import log_audit
from db.models import UserMeta
from db.session import SessionLocal
from services import samba


def list_users() -> List[str]:
    return samba.samba_user_list()


def get_user(username: str) -> Dict[str, Any]:
    return samba.samba_user_show(username)


def create_user(db: Session, actor: str, payload: Dict[str, Any], *, dry_run: bool | None = None) -> None:
    samba.samba_user_create(payload["username"], payload["password"], dry_run=dry_run)
    attrs = {
        key: value
        for key, value in payload.items()
        if key in {"given_name", "surname", "display_name", "mail"} and value
    }
    if attrs:
        samba.samba_user_update_basic(payload["username"], attrs, dry_run=dry_run)
    if payload.get("must_change_password"):
        samba.samba_user_set_password(payload["username"], payload["password"], must_change=True, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="create_user",
        object_type="user",
        object_id=payload["username"],
        result="success",
    )


def update_user(
    db: Session, actor: str, username: str, attrs: Dict[str, Any], *, dry_run: bool | None = None
) -> None:
    samba.samba_user_update_basic(username, {k: v for k, v in attrs.items() if v}, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="update_user",
        object_type="user",
        object_id=username,
        result="success",
        details=attrs,
    )


def reset_password(
    db: Session, actor: str, username: str, new_password: str, must_change: bool, *, dry_run: bool | None = None
) -> None:
    samba.samba_user_set_password(username, new_password, must_change=must_change, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="reset_password",
        object_type="user",
        object_id=username,
        result="success",
    )


def enable_user(db: Session, actor: str, username: str, *, dry_run: bool | None = None) -> None:
    samba.samba_user_enable(username, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="enable_user",
        object_type="user",
        object_id=username,
        result="success",
    )


def disable_user(db: Session, actor: str, username: str, *, dry_run: bool | None = None) -> None:
    samba.samba_user_disable(username, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="disable_user",
        object_type="user",
        object_id=username,
        result="success",
    )


def add_user_to_group(db: Session, actor: str, username: str, group: str, *, dry_run: bool | None = None) -> None:
    samba.samba_user_add_to_group(username, group, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="add_user_to_group",
        object_type="user",
        object_id=username,
        result="success",
        details={"group": group},
    )


def remove_user_from_group(
    db: Session, actor: str, username: str, group: str, *, dry_run: bool | None = None
) -> None:
    samba.samba_user_remove_from_group(username, group, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="remove_user_from_group",
        object_type="user",
        object_id=username,
        result="success",
        details={"group": group},
    )


def sync_users(db: Session, actor: str) -> Dict[str, int]:
    users = samba.samba_user_list()
    updated = 0
    for username in users:
        attributes = samba.samba_user_show(username)
        payload = {"username": username, "attributes": attributes}
        ad_hash = samba.normalize_for_hash(payload)
        existing = db.query(UserMeta).filter(UserMeta.username == username).one_or_none()
        if existing and existing.ad_hash == ad_hash:
            continue
        if existing:
            existing.ad_hash = ad_hash
            existing.extra_json = json.dumps(payload, ensure_ascii=True)
            existing.last_sync = datetime.now(timezone.utc)
        else:
            db.add(
                UserMeta(
                    username=username,
                    ad_hash=ad_hash,
                    extra_json=json.dumps(payload, ensure_ascii=True),
                    last_sync=datetime.now(timezone.utc),
                )
            )
        updated += 1
    db.commit()
    log_audit(
        db,
        actor=actor,
        action="sync_users",
        object_type="sync",
        object_id="users",
        result="success",
        details={"total": len(users), "updated": updated},
    )
    return {"total": len(users), "updated": updated}


def sync_users_job(actor: str) -> Dict[str, int]:
    db = SessionLocal()
    try:
        return sync_users(db, actor)
    finally:
        db.close()
