import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.config import settings


CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


class ScriptExecutionError(RuntimeError):
    def __init__(self, message: str, *, stdout: str = "", stderr: str = "", returncode: int = 1):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _sanitize_arg(value: str) -> str:
    if CONTROL_CHARS_RE.search(value):
        raise ScriptExecutionError("Parametro contem caracteres invalidos")
    return value


def _script_base_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    base = Path(settings.ad_scripts_dir)
    if base.is_absolute():
        return base
    return (root / base).resolve()


def _script_env() -> Dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "LDAP_URI": settings.ldap_uri,
            "BIND_DN": settings.bind_dn,
            "BIND_PW": settings.bind_pw,
            "BASE_DN": settings.base_dn,
            "USERS_OU": settings.users_ou,
            "DOMAIN": settings.domain,
        }
    )
    return env


def run_script(
    script_relative: str,
    args: Iterable[str],
    *,
    timeout_seconds: Optional[int] = None,
) -> str:
    base_dir = _script_base_dir()
    script_path = (base_dir / script_relative).resolve()
    if not script_path.exists():
        raise ScriptExecutionError(f"Script nao encontrado: {script_path}")
    if not script_path.is_file():
        raise ScriptExecutionError(f"Caminho do script invalido: {script_path}")

    timeout = timeout_seconds or settings.ad_script_timeout_seconds
    cmd = [str(script_path)] + [_sanitize_arg(str(arg)) for arg in args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_script_env(),
            check=False,
        )
    except FileNotFoundError as exc:
        raise ScriptExecutionError(
            f"Executavel nao encontrado: {script_path}",
            stdout="",
            stderr=str(exc),
            returncode=127,
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ScriptExecutionError(
            "Timeout ao executar script",
            stdout=(exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            returncode=124,
        ) from exc

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        raise ScriptExecutionError("Falha ao executar script", stdout=stdout, stderr=stderr, returncode=result.returncode)
    return stdout


def extract_data_block(output: str) -> str:
    lines = output.splitlines()
    try:
        start = lines.index("DATA_BEGIN")
        end = lines.index("DATA_END")
    except ValueError as exc:
        raise ScriptExecutionError("Saida do script sem bloco DATA") from exc
    if end <= start:
        raise ScriptExecutionError("Saida do script com bloco DATA invalido")
    return "\n".join(lines[start + 1 : end]).strip()


def parse_ldif_entries(ldif_text: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}

    def _commit() -> None:
        nonlocal current
        if current:
            entries.append(current)
            current = {}

    for raw_line in ldif_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            _commit()
            continue
        if "::" in line:
            key, value = line.split("::", 1)
            decoded = base64.b64decode(value.strip()).decode("utf-8", errors="replace")
            value = decoded
        elif ":" in line:
            key, value = line.split(":", 1)
            value = value.strip()
        else:
            continue
        key = key.strip()
        if key in current:
            existing = current[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                current[key] = [existing, value]
        else:
            current[key] = value
    _commit()
    return entries


def normalize_for_hash(payload: Dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
