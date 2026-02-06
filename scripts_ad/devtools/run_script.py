import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path


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

