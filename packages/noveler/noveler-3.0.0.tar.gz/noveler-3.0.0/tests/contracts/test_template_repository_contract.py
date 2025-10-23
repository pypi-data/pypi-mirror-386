"""
# File: tests/contracts/test_template_repository_contract.py
# Purpose: Contract test (baseline) for FileTemplateRepository search order and UTF-8 loading.
# Context: Phase C minimal — keeps behavior stable across refactors.

This test verifies the observable contract of noveler.infrastructure.repositories.file_template_repository:
- find_template(step_id:int, step_slug:str) searches in the documented order and returns the first match.
- load_template_content reads UTF-8 text and raises on missing files.

The test builds a temporary directory structure; it does not depend on project templates.
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import pytest

from noveler.infrastructure.repositories.file_template_repository import FileTemplateRepository


def _scaffold(base: Path) -> None:
    (base / "quality" / "checks").mkdir(parents=True, exist_ok=True)
    (base / "quality" / "checks" / "backup").mkdir(parents=True, exist_ok=True)
    (base / "writing").mkdir(parents=True, exist_ok=True)


def test_find_template_search_order_first_match_wins(tmp_path: Path) -> None:
    base = tmp_path / "templates"
    _scaffold(base)

    # Prepare filenames
    step_id = 1
    slug = "typo_check"
    filename = f"check_step{step_id:02d}_{slug}.yaml"

    # Case 1: only in writing -> returns writing
    writing = base / "writing" / filename
    writing.write_text("version: 1\n", encoding="utf-8")

    repo = FileTemplateRepository(base)
    found = repo.find_template(step_id, slug)
    assert found == writing

    # Case 2: adding backup should take precedence over writing
    backup = base / "quality" / "checks" / "backup" / filename
    backup.write_text("version: 1\n", encoding="utf-8")
    found2 = repo.find_template(step_id, slug)
    assert found2 == backup

    # Case 3: adding checks should take highest precedence
    checks = base / "quality" / "checks" / filename
    checks.write_text("version: 1\n", encoding="utf-8")
    found3 = repo.find_template(step_id, slug)
    assert found3 == checks


def test_load_template_content_utf8_and_missing(tmp_path: Path) -> None:
    base = tmp_path / "templates"
    _scaffold(base)
    p = base / "writing" / "check_step01_sample.yaml"
    text = "日本語UTF-8テンプレート\nkey: 値\n"
    p.write_text(text, encoding="utf-8")

    repo = FileTemplateRepository(base)
    content = repo.load_template_content(p)
    assert "key: 値" in content

    with pytest.raises(FileNotFoundError):
        repo.load_template_content(p.with_name("missing.yaml"))

