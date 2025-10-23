#!/usr/bin/env python3
# File: tests/e2e/test_check_command_e2e.py
# Purpose: Validate the check command end-to-end by executing it through the MCP
#          server and asserting responses across diverse project scenarios.
# Context: Depends on mcp_servers.noveler.main.execute_novel_command and pytest
#          async fixtures. Exercises temporary project structures for E2E flows.
"""checkコマンドE2Eテスト

実際のMCPツール経由でのcheckコマンド実行をテストする包括的E2Eテストスイート
"""

import asyncio
import json
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from mcp_servers.noveler.main import execute_novel_command



@pytest.fixture
def e2e_project_dir():
    """E2Eテスト用プロジェクトディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="e2e_check_test_")
    temp_path = Path(temp_dir)

    # 完全なプロジェクト構造作成
    (temp_path / "temp/test_data/40_原稿").mkdir(parents=True, exist_ok=True)
    (temp_path / "50_管理資料").mkdir(exist_ok=True)
    (temp_path / "50_管理資料" / "plots").mkdir(exist_ok=True)
    (temp_path / "config").mkdir(exist_ok=True)
    (temp_path / "specs").mkdir(exist_ok=True)
    (temp_path / "tests").mkdir(exist_ok=True)
    (temp_path / "src").mkdir(exist_ok=True)
    (temp_path / "src" / "noveler").mkdir(exist_ok=True)

    # プロジェクト設定ファイル
    project_config = """
project:
  title: "E2Eテストプロジェクト"
  author: "E2Eテストユーザー"
  genre: "テストファンタジー"
  ncode: "N0000E2E"
  start_date: "2025-01-15"
  status: "執筆中"

quality:
  min_score: 70
  target_score: 85
  max_warnings: 5

paths:
  manuscripts: "temp/test_data/40_原稿"
  plots: "50_管理資料/plots"
  quality: "quality"
  specs: "specs"
"""
    (temp_path / "プロジェクト設定.yaml").write_text(project_config, encoding="utf-8")

    # サンプル原稿ファイル
    manuscript_content = """# 第001話 E2Eテスト物語

これはE2Eテスト用の原稿です。
品質チェック機能をテストするための内容を含んでいます。

## シーン1
主人公が冒険を始めます。
長い文章でもテストできるように、複数の文を含む段落を用意しています。

## シーン2
展開部分での出来事。

「こんにちは」と彼は言った。
「はい、こんにちは」と彼女は答えた。
"""
    (temp_path / "temp/test_data/40_原稿" / "第001話_E2Eテスト物語.md").write_text(
        manuscript_content, encoding="utf-8"
    )

    yield temp_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def e2e_project_with_specs(e2e_project_dir):
    """仕様書付きE2Eプロジェクト"""
    # テスト仕様書作成
    spec_content = """# TEST-FEATURE-001 テスト機能仕様書

## 概要
E2Eテスト用の機能仕様書

## 要件
- 基本要件をテストする
- 機能要件を明確にする
- 非機能要件を含める

## 設計方針
- DDD準拠設計
- Clean Architecture準拠
- テスタブルな実装

## 実装計画
1. Domain Entity作成
2. Use Case実装
3. Infrastructure実装
4. Presentation実装

## テスト計画
- 単体テスト
- 統合テスト
- E2Eテスト

## 受け入れ基準
- 全テスト成功
- コードレビュー完了
- 品質基準クリア
"""
    (e2e_project_dir / "specs" / "SPEC-TEST-FEATURE-001.md").write_text(
        spec_content, encoding="utf-8"
    )

    # テストファイル作成
    test_content = """#!/usr/bin/env python3
# Test file for E2E testing

def test_example():
    assert True

def test_feature_implementation():
    # Test implementation
    pass
"""
    (e2e_project_dir / "tests" / "test_e2e_feature.py").write_text(
        test_content, encoding="utf-8"
    )

    return e2e_project_dir


class TestCheckCommandE2E:
    """checkコマンドE2Eテストクラス"""

    @pytest.mark.e2e
    async def test_check_command_full_workflow_success(self, e2e_project_with_specs):
        """checkコマンド完全ワークフロー成功E2Eテスト"""
        # Act - 実際のMCP経由でcheckコマンド実行
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "test_feature",
                "target_layer": "domain",
                "auto_fix_issues": False,
                "create_missing_spec": False
            },
            project_root=str(e2e_project_with_specs)
        )

        # Assert
        assert result["success"] is True
        assert result["command"] == "check"
        assert "implementation_allowed" in result["result"]
        assert "current_stage" in result["result"]
        assert "completion_percentage" in result["result"]
        assert result["result"]["completion_percentage"] >= 50.0  # 仕様書とテストがあるため

    @pytest.mark.e2e
    async def test_check_command_with_missing_specs(self, e2e_project_dir):
        """checkコマンド仕様書なしE2Eテスト"""
        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "missing_spec_feature",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_dir)
        )

        # Assert
        assert result["success"] is True  # チェック自体は成功
        assert result["result"]["implementation_allowed"] is False
        assert "specification_required" in result["result"]["current_stage"]
        assert len(result["result"]["errors"]) > 0
        assert any("仕様書が見つかりません" in error for error in result["result"]["errors"])

    @pytest.mark.e2e
    async def test_check_command_with_auto_fix_enabled(self, e2e_project_dir):
        """checkコマンド自動修正有効E2Eテスト"""
        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "auto_fix_test",
                "target_layer": "domain",
                "auto_fix_issues": True,
                "create_missing_spec": True
            },
            project_root=str(e2e_project_dir)
        )

        # Assert
        assert result["success"] is True
        if "auto_fix_results" in result["result"]:
            auto_fix = result["result"]["auto_fix_results"]
            assert "attempted_fixes" in auto_fix
            if auto_fix["attempted_fixes"] > 0:
                assert "successful_fixes" in auto_fix

    @pytest.mark.e2e
    async def test_check_command_invalid_layer_e2e(self, e2e_project_with_specs):
        """checkコマンド無効レイヤーE2Eテスト"""
        # Arrange

        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "invalid_layer_test",
                "target_layer": "invalid_layer"
            },
            project_root=str(e2e_project_with_specs)
        )

        # Assert
        assert result["success"] is True  # チェック自体は成功
        assert len(result["result"]["errors"]) > 0
        assert any("無効なレイヤー" in error for error in result["result"]["errors"])

    @pytest.mark.e2e
    async def test_check_command_performance_e2e(self, e2e_project_with_specs):
        """checkコマンドパフォーマンスE2Eテスト"""
        # Arrange

        # Act
        start_time = time.perf_counter()
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "performance_test",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_with_specs)
        )
        end_time = time.perf_counter()

        # Assert
        execution_time = (end_time - start_time) * 1000  # ms
        assert result["success"] is True
        assert execution_time < 2000  # 2秒以内に完了
        assert result["result"]["execution_time_ms"] is not None
        assert result["result"]["execution_time_ms"] > 0

    @pytest.mark.e2e
    async def test_check_command_concurrent_execution_e2e(self, e2e_project_with_specs):
        """checkコマンド並行実行E2Eテスト"""
        # Arrange

        async def run_check(feature_name):
            return await execute_novel_command(
                command="check",
                options={
                    "feature_name": feature_name,
                    "target_layer": "domain"
                },
                project_root=str(e2e_project_with_specs)
            )

        # Act - 複数のcheckコマンドを並行実行
        results = await asyncio.gather(
            run_check("concurrent_test_1"),
            run_check("concurrent_test_2"),
            run_check("concurrent_test_3"),
            return_exceptions=True
        )

        # Assert
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent execution failed: {result}")
            assert result["success"] is True
            assert result["command"] == "check"

    @pytest.mark.e2e
    async def test_check_command_large_project_e2e(self, e2e_project_with_specs):
        """checkコマンド大規模プロジェクトE2Eテスト"""
        # Arrange - 大量のファイルを作成
        project_dir = e2e_project_with_specs

        # 多数の原稿ファイルを作成
        manuscripts_dir = project_dir / "temp/test_data/40_原稿"
        for i in range(10):
            content = f"""# 第{i+1:03d}話 大規模テスト物語

これは大規模テスト用の原稿{i+1}です。
多数のファイルが存在する環境でのパフォーマンステストを行います。

## シーン1
内容{i+1}の展開。

## シーン2
内容{i+1}の結末。
"""
            (manuscripts_dir / f"第{i+1:03d}話_大規模テスト物語.md").write_text(
                content, encoding="utf-8"
            )

        # 多数の仕様書を作成
        specs_dir = project_dir / "specs"
        for i in range(5):
            content = f"""# SPEC-LARGE-{i+1:03d} 大規模機能{i+1}仕様書

## 概要
大規模テスト用の機能{i+1}仕様書

## 要件
- 大規模要件{i+1}
"""
            (specs_dir / f"SPEC-LARGE-{i+1:03d}.md").write_text(content, encoding="utf-8")


        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "large_project_test",
                "target_layer": "domain"
            },
            project_root=str(project_dir)
        )

        # Assert
        assert result["success"] is True
        assert result["result"]["execution_time_ms"] < 5000  # 5秒以内

    @pytest.mark.e2e
    async def test_check_command_error_recovery_e2e(self, e2e_project_dir):
        """checkコマンドエラー回復E2Eテスト"""
        # Arrange - 問題のあるプロジェクト状態を作成
        project_dir = e2e_project_dir

        # 破損した設定ファイルを作成
        (project_dir / "プロジェクト設定.yaml").write_text("invalid: yaml: content: [", encoding="utf-8")


        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "error_recovery_test",
                "target_layer": "domain"
            },
            project_root=str(project_dir)
        )

        # Assert - エラーが発生してもクラッシュしない
        assert "success" in result
        if not result["success"]:
            assert "error" in result or len(result.get("result", {}).get("errors", [])) > 0

    @pytest.mark.e2e
    async def test_check_command_guidance_integration_e2e(self, e2e_project_with_specs):
        """checkコマンドガイダンス統合E2Eテスト"""
        # Arrange

        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "guidance_test",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_with_specs)
        )

        # Assert - ガイダンス情報が含まれている
        assert result["success"] is True
        assert "current_stage" in result["result"]
        assert "next_required_actions" in result["result"]
        assert len(result["result"]["next_required_actions"]) > 0

        # 具体的なガイダンス内容確認
        if result["result"]["implementation_allowed"]:
            assert "実装" in " ".join(result["result"]["next_required_actions"])


class TestCheckCommandE2EScenarios:
    """checkコマンドE2Eシナリオテスト"""

    @pytest.mark.e2e
    @pytest.mark.scenario
    async def test_new_project_setup_scenario(self, e2e_project_dir):
        """新規プロジェクト立ち上げシナリオE2Eテスト"""
        # Scenario: 新しいプロジェクトで初回checkを実行


        # Step 1: 初回チェック実行
        result1 = await execute_novel_command(
            command="check",
            options={
                "feature_name": "new_project_feature",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_dir)
        )

        # Assert Step 1: 仕様書なしで実装不許可
        assert result1["success"] is True
        assert result1["result"]["implementation_allowed"] is False
        assert "specification_required" in result1["result"]["current_stage"]

        # Step 2: 仕様書を作成
        specs_dir = e2e_project_dir / "specs"
        spec_content = """# SPEC-NEW-PROJECT-001 新規プロジェクト機能

## 概要
新規プロジェクト機能の仕様書
"""
        (specs_dir / "SPEC-NEW-PROJECT-001.md").write_text(spec_content, encoding="utf-8")

        # Step 3: 再チェック実行
        result2 = await execute_novel_command(
            command="check",
            options={
                "feature_name": "new_project_feature",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_dir)
        )

        # Assert Step 3: 仕様書作成後に状況改善
        assert result2["success"] is True
        assert result2["result"]["completion_percentage"] > result1["result"]["completion_percentage"]

    @pytest.mark.e2e
    @pytest.mark.scenario
    async def test_development_lifecycle_scenario(self, e2e_project_with_specs):
        """開発ライフサイクルシナリオE2Eテスト"""
        # Scenario: 開発の各段階でcheckコマンドを実行


        # Phase 1: 設計段階
        result_design = await execute_novel_command(
            command="check",
            options={
                "feature_name": "lifecycle_feature",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_with_specs)
        )

        assert result_design["success"] is True
        design_completion = result_design["result"]["completion_percentage"]

        # Phase 2: より多くのテストファイル追加
        tests_dir = e2e_project_with_specs / "tests"
        (tests_dir / "test_unit.py").write_text("# Unit tests", encoding="utf-8")
        (tests_dir / "test_integration.py").write_text("# Integration tests", encoding="utf-8")

        result_testing = await execute_novel_command(
            command="check",
            options={
                "feature_name": "lifecycle_feature",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_with_specs)
        )

        assert result_testing["success"] is True
        testing_completion = result_testing["result"]["completion_percentage"]

        # Assert: 開発進行とともに完了率が向上
        assert testing_completion >= design_completion

    @pytest.mark.e2e
    @pytest.mark.scenario
    async def test_team_collaboration_scenario(self, e2e_project_with_specs):
        """チーム協業シナリオE2Eテスト"""
        # Scenario: 複数の開発者が異なる機能をチェック


        # Developer 1: Domain layer feature
        result_dev1 = await execute_novel_command(
            command="check",
            options={
                "feature_name": "domain_feature",
                "target_layer": "domain"
            },
            project_root=str(e2e_project_with_specs)
        )

        # Developer 2: Application layer feature
        result_dev2 = await execute_novel_command(
            command="check",
            options={
                "feature_name": "application_feature",
                "target_layer": "application"
            },
            project_root=str(e2e_project_with_specs)
        )

        # Developer 3: Infrastructure layer feature
        result_dev3 = await execute_novel_command(
            command="check",
            options={
                "feature_name": "infrastructure_feature",
                "target_layer": "infrastructure"
            },
            project_root=str(e2e_project_with_specs)
        )

        # Assert: 全ての開発者のチェックが成功
        for result in [result_dev1, result_dev2, result_dev3]:
            assert result["success"] is True
            assert "current_stage" in result["result"]


@pytest.mark.spec("SPEC-CHECK-E2E-001")
class TestCheckCommandE2ESpecification:
    """checkコマンドE2E仕様準拠テスト"""

    @pytest.mark.e2e
    async def test_check_command_e2e_specification_compliance(
        self, e2e_project_with_specs
    ):
        """checkコマンドE2E仕様準拠テスト"""
        # Arrange

        # Act
        result = await execute_novel_command(
            command="check",
            options={
                "feature_name": "spec_compliance",
                "target_layer": "domain",
                "auto_fix_issues": True,
                "create_missing_spec": False,
                "force_codemap_update": False
            },
            project_root=str(e2e_project_with_specs)
        )

        # Assert - SPEC-CHECK-E2E-001準拠
        assert result["success"] is True
        assert result["command"] == "check"

        # 必須レスポンスフィールドの確認
        required_fields = [
            "implementation_allowed",
            "current_stage",
            "completion_percentage",
            "next_required_actions",
            "warnings",
            "errors",
            "execution_time_ms"
        ]

        for field in required_fields:
            assert field in result["result"], f"Required field '{field}' missing from result"

        # データ型の確認
        assert isinstance(result["result"]["implementation_allowed"], bool)
        assert isinstance(result["result"]["current_stage"], str)
        assert isinstance(result["result"]["completion_percentage"], (int, float))
        assert isinstance(result["result"]["next_required_actions"], list)
        assert isinstance(result["result"]["warnings"], list)
        assert isinstance(result["result"]["errors"], list)
        assert isinstance(result["result"]["execution_time_ms"], (int, float))

        # 値の妥当性確認
        assert 0 <= result["result"]["completion_percentage"] <= 100
        assert result["result"]["execution_time_ms"] > 0
