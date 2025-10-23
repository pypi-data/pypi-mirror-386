# File: tests/unit/scripts/test_slash_commands_hydration.py
# Purpose: Minimal test for hydrate_slash_commands.py merge logic
# Context: Ensures template commands overwrite/extend config while preserving metadata

from __future__ import annotations

from pathlib import Path
import json

import yaml

from scripts.setup.hydrate_slash_commands import hydrate_from_templates, write_yaml


def _dump_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_hydrate_merges_and_overrides(tmp_path: Path) -> None:
    config = tmp_path / "config" / "slash_commands.yaml"
    tdir = tmp_path / "templates" / "slash_commands"

    # Base config: one command with old description
    _dump_yaml(
        config,
        {
            "version": "1.0.0",
            "last_updated": "2025-01-01",
            "commands": [
                {
                    "name": "/test",
                    "script": "bin/test",
                    "description": "OLD",
                }
            ],
        },
    )

    # Template: updates /test description and adds /test-changed
    _dump_yaml(
        tdir / "root_commands.yaml",
        {
            "commands": [
                {
                    "name": "/test",
                    "script": "bin/test",
                    "description": "NEW",
                },
                {
                    "name": "/test-changed",
                    "script": "bin/test-changed",
                    "description": "added",
                },
            ]
        },
    )

    merged = hydrate_from_templates(config, tdir)
    # version kept, last_updated refreshed (non-empty)
    assert merged.get("version") == "1.0.0"
    assert merged.get("last_updated")

    # commands: /test overwritten to NEW, /test-changed appended
    by_name = {c["name"]: c for c in merged.get("commands", [])}
    assert by_name["/test"]["description"] == "NEW"
    assert by_name["/test-changed"]["script"] == "bin/test-changed"

