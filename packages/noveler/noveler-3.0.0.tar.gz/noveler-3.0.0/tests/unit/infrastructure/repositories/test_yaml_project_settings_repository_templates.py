# File: tests/unit/infrastructure/repositories/test_yaml_project_settings_repository_templates.py
# Purpose: Validate that YamlProjectSettingsRepository honours file template overrides when DI is unavailable.
# Context: Uses direct repository calls with dynamically generated project roots.

"""Tests for template-aware behaviour of YamlProjectSettingsRepository."""

from pathlib import Path

import pytest

import noveler.infrastructure.yaml_project_settings_repository as repo_module
from noveler.infrastructure.yaml_project_settings_repository import YamlProjectSettingsRepository


@pytest.mark.unit
@pytest.mark.parametrize("template_name", ["custom_project.yaml", "custom_project.yml"])
def test_repository_uses_template_without_di(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, template_name: str) -> None:
    """Ensure fallback path resolution consults file_templates even without DI container."""
    # Arrange: ensure resolve_service raises so the fallback branch executes.
    def _raise_value_error(_: str):
        raise ValueError("service not available")

    monkeypatch.setattr(repo_module, "resolve_service", _raise_value_error)

    rc_path = tmp_path / ".novelerrc.yaml"
    rc_path.write_text(
        "file_templates:\n  project_config: {name}\n".format(name=template_name),
        encoding="utf-8",
    )
    project_config_path = tmp_path / template_name
    project_config_path.write_text(
        "タイトル: テンプレート対応\n",
        encoding="utf-8",
    )

    repository = YamlProjectSettingsRepository()

    # Act
    title = repository.get_title(tmp_path)

    # Assert
    assert title == "テンプレート対応"
