import os
from pathlib import Path


def main() -> None:
    if len(os.sys.argv) < 2:
        raise SystemExit("Arquivo LDIF nao informado")
    target_file = Path(os.sys.argv[1])
    description = os.environ.get("SAMBA_EDIT_DESCRIPTION")
    if not description:
        raise SystemExit("Descricao nao informada")

    content = target_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("description:"):
            new_lines.append(f"description: {description}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"description: {description}")
    target_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
