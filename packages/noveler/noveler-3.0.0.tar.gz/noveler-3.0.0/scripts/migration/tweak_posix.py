from pathlib import Path

path = Path("src/noveler/infrastructure/repositories/configuration_repository.py")
lines = path.read_text(encoding="utf-8").splitlines()

for idx, line in enumerate(lines):
    if line.strip().startswith("def _as_posix"):
        lines[idx:idx+4] = [
            "    @staticmethod",
            "    def _as_posix(path_value: str | Path) -> str:",
            "        \"\"\"Normalize filesystem paths to POSIX-style strings.\"\"\"",
            "        return str(Path(path_value)).replace('\\\\', '/').replace('\\', '/')",
        ]
        break
else:
    raise SystemExit("_as_posix not found")

Path("src/noveler/infrastructure/repositories/configuration_repository.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
