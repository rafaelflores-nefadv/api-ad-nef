from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.config import settings


CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


class SambaToolError(RuntimeError):
    def __init__(self, message: str, *, stdout: str = "", stderr: str = "", returncode: int = 1):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _sanitize_arg(value: str) -> str:
    if CONTROL_CHARS_RE.search(value):
        raise SambaToolError("Parametro contem caracteres invalidos")
    return value


def _build_base_args() -> List[str]:
    args = [settings.samba_tool_path]
    if settings.samba_realm:
        args += ["--realm", settings.samba_realm]
    if settings.samba_workgroup:
        args += ["--workgroup", settings.samba_workgroup]
    return args


def run_samba_tool(
    args: Iterable[str],
    *,
    timeout_seconds: Optional[int] = None,
    dry_run: Optional[bool] = None,
    env_extra: Optional[Dict[str, str]] = None,
) -> str:
    timeout = timeout_seconds or settings.samba_timeout_seconds
    dry = settings.samba_dry_run if dry_run is None else dry_run

    full_args = _build_base_args() + [_sanitize_arg(str(arg)) for arg in args]
    if dry:
        return f"DRY_RUN: {' '.join(full_args)}"

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    try:
        result = subprocess.run(
            full_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SambaToolError(
            f"Executavel nao encontrado: {settings.samba_tool_path}",
            stdout="",
            stderr=str(exc),
            returncode=127,
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SambaToolError(
            "Timeout ao executar samba-tool",
            stdout=(exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            returncode=124,
        ) from exc
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        raise SambaToolError("Falha ao executar samba-tool", stdout=stdout, stderr=stderr, returncode=result.returncode)
    return stdout


def parse_list_output(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_key_value_output(text: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    current_key: Optional[str] = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current_key = key.strip()
            data[current_key] = value.strip()
            continue
        if current_key:
            data[current_key] = f"{data[current_key]}\n{line.strip()}"
    return data


def normalize_for_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


def samba_user_list() -> List[str]:
    output = run_samba_tool(["user", "list"])
    return parse_list_output(output)


def samba_user_show(username: str) -> Dict[str, str]:
    output = run_samba_tool(["user", "show", username])
    return parse_key_value_output(output)


def samba_user_create(username: str, password: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["user", "create", username, password], dry_run=dry_run)


def samba_user_update_basic(username: str, attrs: Dict[str, str], *, dry_run: Optional[bool] = None) -> None:
    args = ["user", "rename", username]
    if "given_name" in attrs:
        args += ["--given-name", attrs["given_name"]]
    if "surname" in attrs:
        args += ["--surname", attrs["surname"]]
    if "display_name" in attrs:
        args += ["--display-name", attrs["display_name"]]
    if "mail" in attrs:
        args += ["--mail-address", attrs["mail"]]
    if "upn" in attrs:
        args += ["--upn", attrs["upn"]]
    run_samba_tool(args, dry_run=dry_run)


def samba_user_set_password(
    username: str, new_password: str, must_change: bool, *, dry_run: Optional[bool] = None
) -> None:
    args = ["user", "setpassword", username, "--newpassword", new_password]
    if must_change:
        args.append("--must-change-at-next-login")
    run_samba_tool(args, dry_run=dry_run)


def samba_user_enable(username: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["user", "enable", username], dry_run=dry_run)


def samba_user_disable(username: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["user", "disable", username], dry_run=dry_run)


def samba_user_add_to_group(username: str, group: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["group", "addmembers", group, username], dry_run=dry_run)


def samba_user_remove_from_group(username: str, group: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["group", "removemembers", group, username], dry_run=dry_run)


def samba_group_list() -> List[str]:
    output = run_samba_tool(["group", "list"])
    return parse_list_output(output)


def samba_group_show(groupname: str) -> Dict[str, str]:
    output = run_samba_tool(["group", "show", groupname])
    return parse_key_value_output(output)


def samba_group_create(groupname: str, description: Optional[str], *, dry_run: Optional[bool] = None) -> None:
    args = ["group", "add", groupname]
    if description:
        args += ["--description", description]
    run_samba_tool(args, dry_run=dry_run)


def samba_group_update_description(groupname: str, description: str, *, dry_run: Optional[bool] = None) -> None:
    editor_path = str(Path(__file__).with_name("samba_group_editor.py"))
    env_extra = {"SAMBA_EDIT_DESCRIPTION": description, "SAMBA_EDIT_TARGET": groupname}
    run_samba_tool(["group", "edit", groupname, "--editor", editor_path], env_extra=env_extra, dry_run=dry_run)


def samba_group_add_member(groupname: str, member: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["group", "addmembers", groupname, member], dry_run=dry_run)


def samba_group_remove_member(groupname: str, member: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["group", "removemembers", groupname, member], dry_run=dry_run)


def samba_group_disable_move(groupname: str, target_ou_dn: str, *, dry_run: Optional[bool] = None) -> None:
    run_samba_tool(["group", "move", groupname, target_ou_dn], dry_run=dry_run)


def samba_verify_user_password(username: str, password: str) -> None:
    env_extra = {"PASSWD": password}
    run_samba_tool(["user", "get-kerberos-ticket", username], env_extra=env_extra)
