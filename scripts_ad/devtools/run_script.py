import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path
import shutil
import tempfile


REQUIRED_KEYS = ("LDAP_URI", "BIND_DN", "BIND_PW", "BASE_DN", "USERS_OU", "DOMAIN")


def resolve_target(scripts_ad_dir: Path, target_input: str) -> Path:
    p = Path(target_input)
    if p.is_absolute():
        return p
    # aceita "./scripts_ad/users/list_users.sh" ou "users/list_users.sh"
    if target_input.startswith("./"):
        p = Path(target_input[2:])
    if str(p).startswith("scripts_ad" + os.sep) or str(p).startswith("scripts_ad/"):
        return (scripts_ad_dir.parent / p).resolve()
    return (scripts_ad_dir / p).resolve()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "Uso:\n"
            "  python scripts_ad/devtools/run_script.py <script_relativo_ao_scripts_ad> [args...]\n\n"
            "Exemplos:\n"
            "  python scripts_ad/devtools/run_script.py users/list_users.sh\n"
            "  python scripts_ad/devtools/run_script.py groups/list_groups.sh\n"
            "  python scripts_ad/devtools/run_script.py users/get_user.sh jose.silva\n",
            file=sys.stderr,
        )
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    scripts_ad_dir = repo_root / "scripts_ad"
    sys.path.insert(0, str(repo_root))
    from core.config import settings  # noqa: E402

    target_input = argv[1]
    script_args = argv[2:]
    target_path = resolve_target(scripts_ad_dir, target_input)

    if not target_path.exists():
        print(f"Script não encontrado: {target_path}", file=sys.stderr)
        print('Dica: use "users/list_users.sh" (relativo a scripts_ad/).', file=sys.stderr)
        return 2

    # Usa a config existente (core/config.py). Para senha, preferimos prompt/env
    # para não depender de valores hardcoded.
    loaded: dict[str, str] = {
        "LDAP_URI": str(settings.ldap_uri or "").strip(),
        "BIND_DN": str(settings.bind_dn or "").strip(),
        "BASE_DN": str(settings.base_dn or "").strip(),
        "USERS_OU": str(settings.users_ou or "").strip(),
        "DOMAIN": str(settings.domain or "").strip(),
    }

    for k in list(loaded.keys()):
        if os.environ.get(k):
            loaded[k] = os.environ[k].strip()

    bind_pw = os.environ.get("BIND_PW")
    if not bind_pw:
        bind_pw = getpass("BIND_PW (não será exibido): ")
    loaded["BIND_PW"] = bind_pw

    missing = [k for k in REQUIRED_KEYS if not loaded.get(k)]
    if missing:
        print(
            "Variáveis obrigatórias ausentes (via Settings/env/prompt): " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    env = {**os.environ, **loaded}

    real_ldapsearch = shutil.which("ldapsearch")
    if not real_ldapsearch:
        print(
            "ldapsearch não encontrado no PATH (instale ldap-utils/openldap-clients).",
            file=sys.stderr,
        )
        return 2

    script_name = target_path.name

    def write_block(fp, *args: str) -> None:
        for a in args:
            fp.write(a + "\n")
        fp.write("\n")

    with tempfile.TemporaryDirectory() as shim_dir:
        plan_path = Path(shim_dir) / "ldapsearch.plan"
        shim_path = Path(shim_dir) / "ldapsearch"

        shim_path.write_text(
            """#!/usr/bin/env bash
set -euo pipefail

REAL="${TEST_REAL_LDAPSEARCH:-}"
PLAN="${TEST_LDAPSEARCH_PLAN:-}"

if [[ -z "${REAL:-}" || ! -x "$REAL" ]]; then
  echo "[ldapsearch-shim] TEST_REAL_LDAPSEARCH inválido" >&2
  exit 127
fi

if [[ -z "${PLAN:-}" || ! -f "$PLAN" ]]; then
  exec "$REAL" "$@"
fi

LOCK="${PLAN}.lockdir"
for _i in {1..200}; do
  if mkdir "$LOCK" 2>/dev/null; then
    break
  fi
  sleep 0.01
done
if [[ ! -d "$LOCK" ]]; then
  exec "$REAL" "$@"
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

mapfile -t BLOCK < <(awk 'NF==0{exit} {print}' "$PLAN")
if [[ ${#BLOCK[@]} -eq 0 ]]; then
  exec "$REAL" "$@"
fi

awk 'BEGIN{skip=1} { if(skip){ if(NF==0){skip=0; next} else next } } {print}' "$PLAN" > "${PLAN}.tmp" && mv "${PLAN}.tmp" "$PLAN"
exec "$REAL" "$@" "${BLOCK[@]}"
""",
            encoding="utf-8",
        )
        os.chmod(shim_path, 0o755)

        with plan_path.open("w", encoding="utf-8") as fp:
            users_base = loaded["USERS_OU"]
            groups_base = loaded["BASE_DN"]

            if script_name == "list_users.sh":
                write_block(
                    fp,
                    "-b",
                    users_base,
                    "(&(objectClass=user)(!(objectClass=computer))(!(userAccountControl:1.2.840.113556.1.4.803:=2)))",
                    "sAMAccountName",
                )
            elif script_name == "list_groups.sh":
                write_block(
                    fp,
                    "-b",
                    groups_base,
                    "(&(objectClass=group)(groupType:1.2.840.113556.1.4.803:=2147483648))",
                    "sAMAccountName",
                )
            elif script_name == "get_user.sh":
                if len(script_args) < 1:
                    print("Uso: ... get_user.sh <username>", file=sys.stderr)
                    return 2
                username = script_args[0]
                write_block(fp, "-b", users_base, f"(sAMAccountName={username})")
            elif script_name == "get_group.sh":
                if len(script_args) < 1:
                    print("Uso: ... get_group.sh <groupname>", file=sys.stderr)
                    return 2
                groupname = script_args[0]
                write_block(fp, "-b", groups_base, f"(sAMAccountName={groupname})")
            elif script_name in ("disable_user.sh", "enable_user.sh"):
                if len(script_args) < 1:
                    print("Uso: ... <username>", file=sys.stderr)
                    return 2
                username = script_args[0]
                write_block(fp, "-b", users_base, f"(sAMAccountName={username})", "dn")
                write_block(fp, "-b", users_base, f"(sAMAccountName={username})", "userAccountControl")
            elif script_name in ("update_user.sh", "delete_user.sh", "reset_password.sh"):
                if len(script_args) < 1:
                    print("Uso: ... <username> ...", file=sys.stderr)
                    return 2
                username = script_args[0]
                write_block(fp, "-b", users_base, f"(sAMAccountName={username})", "dn")
            elif script_name in ("add_user_to_group.sh", "remove_user_from_group.sh"):
                if len(script_args) < 2:
                    print("Uso: ... <username> <groupname>", file=sys.stderr)
                    return 2
                username, groupname = script_args[0], script_args[1]
                write_block(fp, "-b", users_base, f"(sAMAccountName={username})", "dn")
                write_block(fp, "-b", groups_base, f"(sAMAccountName={groupname})", "dn")
            elif script_name in ("disable_group.sh", "update_group.sh"):
                if len(script_args) < 1:
                    print("Uso: ... <groupname> ...", file=sys.stderr)
                    return 2
                groupname = script_args[0]
                write_block(fp, "-b", groups_base, f"(sAMAccountName={groupname})", "dn")
            elif script_name == "sync_users.sh":
                write_block(fp, "-b", users_base, "(&(objectClass=user)(sAMAccountName=*))")
            elif script_name == "sync_groups.sh":
                write_block(fp, "-b", groups_base, "(objectClass=group)")
            else:
                # Sem plano: shim vira pass-through
                pass

        env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH','')}"
        env["TEST_REAL_LDAPSEARCH"] = real_ldapsearch
        env["TEST_LDAPSEARCH_PLAN"] = str(plan_path)

        result = subprocess.run(
            [str(target_path), *script_args],
            env=env,
            capture_output=True,
            text=True,
        )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

