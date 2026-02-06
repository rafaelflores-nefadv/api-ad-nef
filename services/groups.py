import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.audit.logger import log_audit
from app.db.models import GroupMeta
from app.db.session import SessionLocal
from app.services import samba


def list_groups() -> List[str]:
    return samba.samba_group_list()


def get_group(groupname: str) -> Dict[str, Any]:
    return samba.samba_group_show(groupname)


def create_group(
    db: Session, actor: str, groupname: str, description: str | None, *, dry_run: bool | None = None
) -> None:
    samba.samba_group_create(groupname, description, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="create_group",
        object_type="group",
        object_id=groupname,
        result="success",
    )


def update_group_description(
    db: Session, actor: str, groupname: str, description: str, *, dry_run: bool | None = None
) -> None:
    samba.samba_group_update_description(groupname, description, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="update_group_description",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"description": description},
    )


def add_member(db: Session, actor: str, groupname: str, member: str, *, dry_run: bool | None = None) -> None:
    samba.samba_group_add_member(groupname, member, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="add_group_member",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"member": member},
    )


def remove_member(
    db: Session, actor: str, groupname: str, member: str, *, dry_run: bool | None = None
) -> None:
    samba.samba_group_remove_member(groupname, member, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="remove_group_member",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"member": member},
    )


def disable_group(
    db: Session, actor: str, groupname: str, target_ou_dn: str, *, dry_run: bool | None = None
) -> None:
    samba.samba_group_disable_move(groupname, target_ou_dn, dry_run=dry_run)
    log_audit(
        db,
        actor=actor,
        action="disable_group",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"target_ou": target_ou_dn},
    )


def sync_groups(db: Session, actor: str) -> Dict[str, int]:
    groups = samba.samba_group_list()
    updated = 0
    for groupname in groups:
        attributes = samba.samba_group_show(groupname)
        payload = {"groupname": groupname, "attributes": attributes}
        ad_hash = samba.normalize_for_hash(payload)
        existing = db.query(GroupMeta).filter(GroupMeta.groupname == groupname).one_or_none()
        if existing and existing.ad_hash == ad_hash:
            continue
        if existing:
            existing.ad_hash = ad_hash
            existing.extra_json = json.dumps(payload, ensure_ascii=True)
            existing.last_sync = datetime.now(timezone.utc)
        else:
            db.add(
                GroupMeta(
                    groupname=groupname,
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
        action="sync_groups",
        object_type="sync",
        object_id="groups",
        result="success",
        details={"total": len(groups), "updated": updated},
    )
    return {"total": len(groups), "updated": updated}


def sync_groups_job(actor: str) -> Dict[str, int]:
    db = SessionLocal()
    try:
        return sync_groups(db, actor)
    finally:
        db.close()
