import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path


REQUIRED_KEYS = ("LDAP_URI", "BIND_DN", "BIND_PW", "BASE_DN", "USERS_OU", "DOMAIN")


def _strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        return v[1:-1]
    return v


def load_test_env(env_file: Path) -> dict[str, str]:
    """
    Carrega um arquivo estilo .env simples (KEY=VALUE).
    Aceita valores com aspas simples/duplas e ignora comentários/linhas vazias.
    """
    data: dict[str, str] = {}
    if not env_file.exists():
        return data

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = _strip_quotes(v.strip())
        if k:
            data[k] = v
    return data


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
    env_file = scripts_ad_dir / "test_env.local"

    target_input = argv[1]
    script_args = argv[2:]
    target_path = resolve_target(scripts_ad_dir, target_input)

    if not target_path.exists():
        print(f"Script não encontrado: {target_path}", file=sys.stderr)
        print('Dica: use "users/list_users.sh" (relativo a scripts_ad/).', file=sys.stderr)
        return 2

    loaded = load_test_env(env_file)

    # Senha nunca deve ficar hardcoded: se não vier do arquivo, pede no prompt.
    if not loaded.get("BIND_PW"):
        loaded["BIND_PW"] = getpass("BIND_PW (não será exibido): ")

    missing = [k for k in REQUIRED_KEYS if not loaded.get(k)]
    if missing:
        print(
            "Variáveis obrigatórias ausentes em scripts_ad/test_env.local: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        print(
            "Crie o arquivo a partir de scripts_ad/test_env.local.example.",
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

