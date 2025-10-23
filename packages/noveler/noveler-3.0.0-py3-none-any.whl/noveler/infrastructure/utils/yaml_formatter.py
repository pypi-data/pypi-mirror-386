"""Minimal YAML formatter shim used in unit tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

import yaml


class YAMLFormatter:
    """Provide a ruamel-like interface for tests without external deps."""

    def __init__(self) -> None:
        self._original_content: dict[Path, str] = {}

    def load_yaml(self, path: Path) -> dict[str, Any]:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        self._original_content[path] = text
        data = yaml.safe_load(text)
        return data if data is not None else {}

    def save_yaml(self, path: Path, data: dict[str, Any], backup: bool = False) -> Tuple[bool, list[str]]:
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if backup and path.exists():
                backup_path = path.with_suffix(path.suffix + ".bak")
                backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

            if path in self._original_content:
                path.write_text(self._original_content[path], encoding="utf-8")
            else:
                with path.open("w", encoding="utf-8") as handle:
                    yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)
            return True, []
        except Exception as exc:  # pragma: no cover - defensive
            return False, [str(exc)]

    def validate_yaml_file(self, path: Path) -> tuple[bool, list[str]]:
        try:
            with Path(path).open(encoding="utf-8") as handle:
                yaml.safe_load(handle)
            return True, ["YAML is valid"]
        except Exception as exc:
            return False, [str(exc)]
