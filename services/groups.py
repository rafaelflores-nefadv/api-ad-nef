import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from audit.logger import log_audit
from db.models import GroupMeta
from db.session import SessionLocal
from services.script_runner import (
    ScriptExecutionError,
    extract_data_block,
    normalize_for_hash,
    parse_ldif_entries,
    run_script,
)


def _log_and_raise(
    db: Session,
    *,
    actor: str,
    action: str,
    object_type: str,
    object_id: str,
    script: str,
    arguments: List[str],
    exc: ScriptExecutionError,
) -> None:
    log_audit(
        db,
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=object_id,
        result="error",
        details={"script": script, "arguments": arguments, "stdout": exc.stdout, "stderr": exc.stderr},
    )
    raise exc


def list_groups(db: Session, actor: str) -> str:
    script = "groups/list_groups.sh"
    args: List[str] = []
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="list_groups",
            object_type="group",
            object_id="list",
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="list_groups",
        object_type="group",
        object_id="list",
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def get_group(db: Session, actor: str, groupname: str) -> str:
    script = "groups/get_group.sh"
    args = [groupname]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="get_group",
            object_type="group",
            object_id=groupname,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="get_group",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def create_group(db: Session, actor: str, groupname: str, description: str | None) -> str:
    script = "groups/create_group.sh"
    args = [groupname, description or ""]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="create_group",
            object_type="group",
            object_id=groupname,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="create_group",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def update_group_description(db: Session, actor: str, groupname: str, description: str) -> str:
    script = "groups/update_group.sh"
    args = [groupname, description]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="update_group_description",
            object_type="group",
            object_id=groupname,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="update_group_description",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def add_member(db: Session, actor: str, groupname: str, member: str) -> str:
    script = "groups/add_user_to_group.sh"
    args = [member, groupname]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="add_group_member",
            object_type="group",
            object_id=groupname,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="add_group_member",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"script": script, "arguments": args, "member": member},
    )
    return output


def remove_member(db: Session, actor: str, groupname: str, member: str) -> str:
    script = "groups/remove_user_from_group.sh"
    args = [member, groupname]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="remove_group_member",
            object_type="group",
            object_id=groupname,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="remove_group_member",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"script": script, "arguments": args, "member": member},
    )
    return output


def disable_group(db: Session, actor: str, groupname: str, target_ou_dn: str) -> str:
    script = "groups/disable_group.sh"
    args = [groupname, target_ou_dn]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="disable_group",
            object_type="group",
            object_id=groupname,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="disable_group",
        object_type="group",
        object_id=groupname,
        result="success",
        details={"script": script, "arguments": args, "target_ou": target_ou_dn},
    )
    return output


def sync_groups(db: Session, actor: str) -> str:
    script = "groups/sync_groups.sh"
    args: List[str] = []
    try:
        output = run_script(script, args)
        data_block = extract_data_block(output)
        entries = parse_ldif_entries(data_block)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="sync_groups",
            object_type="sync",
            object_id="groups",
            script=script,
            arguments=args,
            exc=exc,
        )
    except Exception as exc:
        error = ScriptExecutionError("Falha ao processar saida do script", stdout=output if "output" in locals() else "")
        _log_and_raise(
            db,
            actor=actor,
            action="sync_groups",
            object_type="sync",
            object_id="groups",
            script=script,
            arguments=args,
            exc=error,
        )
        raise exc

    updated = 0
    for entry in entries:
        groupname = entry.get("sAMAccountName") or entry.get("cn")
        if not groupname:
            continue
        payload = {"groupname": groupname, "attributes": entry}
        ad_hash = normalize_for_hash(payload)
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
        details={"script": script, "arguments": args, "total": len(entries), "updated": updated},
    )
    return output


def sync_groups_job(actor: str) -> Dict[str, int]:
    db = SessionLocal()
    try:
        sync_groups(db, actor)
        return {"status": "ok"}
    finally:
        db.close()
