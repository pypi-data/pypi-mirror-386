#!/usr/bin/env python3

"""Tests.tests.unit.infrastructure.test_yaml_quality_record_repository_minimal
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from noveler.infrastructure.repositories.yaml_quality_record_repository import (
    YamlQualityRecordRepository,
)


def test_save_check_result_with_minimal_flat_record(tmp_path: Path):
    # ベースパス直下にプロジェクトディレクトリを作成
    project_root = tmp_path / "p1"
    project_root.mkdir(parents=True, exist_ok=True)

    repo = YamlQualityRecordRepository(base_path=tmp_path)

    record = {
        "project_name": "p1",
        "episode_number": 1,
        # フラットな最小情報のみ（quality_result構造は省略）
        "score": 85.0,
        "issues": [
            "軽微なスタイル問題",
            {"type": "warning", "message": "句読点の間隔", "severity": "warning"},
        ],
        "metadata": {"source": "unit-test"},
    }

    # 例外が出ずに保存できること
    repo.save_check_result(record)

    # 実ファイルが存在することを確認
    # パスサービスのデフォルト設定では management/品質記録.yaml
    quality_record_file = project_root / "management" / "品質記録.yaml"
    assert quality_record_file.exists(), f"品質記録ファイルが存在しません: {quality_record_file}"

    # YAMLとして読み込めること、および内容にエントリが1件以上含まれること
    content = yaml.safe_load(quality_record_file.read_text(encoding="utf-8"))
    assert isinstance(content, dict)
    assert len(content) > 0
