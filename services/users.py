import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from audit.logger import log_audit
from db.models import UserMeta
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


def list_users(db: Session, actor: str) -> str:
    script = "users/list_users.sh"
    args: List[str] = []
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="list_users",
            object_type="user",
            object_id="list",
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="list_users",
        object_type="user",
        object_id="list",
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def get_user(db: Session, actor: str, username: str) -> str:
    script = "users/get_user.sh"
    args = [username]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="get_user",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="get_user",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def create_user(db: Session, actor: str, payload: Dict[str, Any]) -> str:
    script = "users/create_user.sh"
    args = [
        payload["username"],
        payload["password"],
        payload.get("given_name") or "",
        payload.get("surname") or "",
        payload.get("display_name") or "",
        payload.get("mail") or "",
        "true" if payload.get("must_change_password") else "false",
    ]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="create_user",
            object_type="user",
            object_id=payload["username"],
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="create_user",
        object_type="user",
        object_id=payload["username"],
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def update_user(db: Session, actor: str, username: str, attrs: Dict[str, Any]) -> str:
    script = "users/update_user.sh"
    args = [
        username,
        attrs.get("given_name") or "",
        attrs.get("surname") or "",
        attrs.get("display_name") or "",
        attrs.get("mail") or "",
        attrs.get("upn") or "",
    ]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="update_user",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="update_user",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def reset_password(db: Session, actor: str, username: str, new_password: str, must_change: bool) -> str:
    script = "users/reset_password.sh"
    args = [username, new_password, "true" if must_change else "false"]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="reset_password",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="reset_password",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def enable_user(db: Session, actor: str, username: str) -> str:
    script = "users/enable_user.sh"
    args = [username]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="enable_user",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="enable_user",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def disable_user(db: Session, actor: str, username: str) -> str:
    script = "users/disable_user.sh"
    args = [username]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="disable_user",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="disable_user",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def delete_user(db: Session, actor: str, username: str) -> str:
    script = "users/delete_user.sh"
    args = [username]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="delete_user",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="delete_user",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args},
    )
    return output


def add_user_to_group(db: Session, actor: str, username: str, group: str) -> str:
    script = "groups/add_user_to_group.sh"
    args = [username, group]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="add_user_to_group",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="add_user_to_group",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args, "group": group},
    )
    return output


def remove_user_from_group(db: Session, actor: str, username: str, group: str) -> str:
    script = "groups/remove_user_from_group.sh"
    args = [username, group]
    try:
        output = run_script(script, args)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="remove_user_from_group",
            object_type="user",
            object_id=username,
            script=script,
            arguments=args,
            exc=exc,
        )
    log_audit(
        db,
        actor=actor,
        action="remove_user_from_group",
        object_type="user",
        object_id=username,
        result="success",
        details={"script": script, "arguments": args, "group": group},
    )
    return output


def sync_users(db: Session, actor: str) -> str:
    script = "users/sync_users.sh"
    args: List[str] = []
    try:
        output = run_script(script, args)
        data_block = extract_data_block(output)
        entries = parse_ldif_entries(data_block)
    except ScriptExecutionError as exc:
        _log_and_raise(
            db,
            actor=actor,
            action="sync_users",
            object_type="sync",
            object_id="users",
            script=script,
            arguments=args,
            exc=exc,
        )
    except Exception as exc:
        error = ScriptExecutionError("Falha ao processar saida do script", stdout=output if "output" in locals() else "")
        _log_and_raise(
            db,
            actor=actor,
            action="sync_users",
            object_type="sync",
            object_id="users",
            script=script,
            arguments=args,
            exc=error,
        )
        raise exc

    updated = 0
    for entry in entries:
        username = entry.get("sAMAccountName")
        if not username:
            continue
        payload = {"username": username, "attributes": entry}
        ad_hash = normalize_for_hash(payload)
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
        details={"script": script, "arguments": args, "total": len(entries), "updated": updated},
    )
    return output


def sync_users_job(actor: str) -> Dict[str, int]:
    db = SessionLocal()
    try:
        sync_users(db, actor)
        return {"status": "ok"}
    finally:
        db.close()
