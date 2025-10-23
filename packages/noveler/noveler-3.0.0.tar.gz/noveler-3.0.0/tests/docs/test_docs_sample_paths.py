#!/usr/bin/env python3

"""Tests.tests.docs.test_docs_sample_paths
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.integration
def test_docs_mentions_priority_and_default_sample_name():
    repo_root = Path(__file__).resolve().parents[2]
    docs = repo_root / "docs" / "references" / "quick_reference.md"
    assert docs.exists(), f"docs/references/quick_reference.md not found at {docs}"

    content = docs.read_text(encoding="utf-8")
    # 優先順位の3要素がドキュメントに記載されていること
    assert "PROJECT_ROOT" in content
    assert "paths.samples.root" in content
    assert "NOVELER_SAMPLES_ROOT" in content

    # 既定サンプル名の記載を確認
    default_name = "10_Fランク魔法使いはDEBUGログを読む"
    assert default_name in content


@pytest.mark.integration
def test_default_sample_directory_exists_or_skip(monkeypatch):
    # 実環境に既定サンプルがあれば、解決先として採用されることを確認
    # 無い場合はスキップ（環境依存）
    from noveler.infrastructure.factories import path_service_factory as psf

    # DOCSの既定サンプル名
    default_name = "10_Fランク魔法使いはDEBUGログを読む"

    # 実装準拠: 00_ガイドの1つ上に既定サンプルがあるかを確認
    guide_root = Path(__file__).resolve().parents[2]
    candidate = guide_root.parent / default_name

    if not candidate.exists():
        pytest.skip(f"既定サンプルディレクトリが存在しないためスキップ: {candidate}")

    # 環境変数や設定は未指定として検証（影響を排除）
    for k in ["PROJECT_ROOT", "NOVELER_TEST_PROJECT_ROOT", "NOVELER_SAMPLES_ROOT"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(
        psf,
        "ConfigurationManager",
        lambda: type("_M", (), {"get_configuration": lambda self, force_reload=False: None})(),
    )

    resolved = psf._resolve_project_root(None)
    assert resolved == candidate.resolve()
