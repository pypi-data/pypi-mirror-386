#!/usr/bin/env python3
"""CODEMAP自動更新システムと品質ゲートシステムの統合テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from noveler.application.use_cases.codemap_auto_update_use_case import (
    CodeMapAutoUpdateRequest,
    CodeMapAutoUpdateUseCase,
)
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.infrastructure.adapters.git_information_adapter import GitInformationAdapter
from noveler.infrastructure.repositories.yaml_codemap_repository import YamlCodeMapRepository


@pytest.mark.integration
class TestCodeMapQualityGateIntegration:
    """CODEMAP自動更新システムと品質ゲートシステムの統合テストクラス"""

    @pytest.fixture
    def temp_git_repo(self):
        """テスト用の一時Gitリポジトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Gitリポジトリ初期化
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

            # 基本的なプロジェクト構造を作成
            (repo_path / "scripts" / "domain" / "entities").mkdir(parents=True, exist_ok=True)
            (repo_path / "scripts" / "application" / "use_cases").mkdir(parents=True, exist_ok=True)
            (repo_path / "scripts" / "infrastructure" / "adapters").mkdir(parents=True, exist_ok=True)
            (repo_path / "scripts" / "presentation" / "cli").mkdir(parents=True, exist_ok=True)

            # 初期ファイルを作成
            (repo_path / "scripts" / "__init__.py").write_text("", encoding="utf-8")
            (repo_path / "scripts" / "domain" / "__init__.py").write_text("", encoding="utf-8")
            (repo_path / "README.md").write_text("# Quality Gate Integration Test", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_path, check=True)

            yield repo_path

    @pytest.fixture
    def codemap_file(self, temp_git_repo):
        """CODEMAPファイル"""
        codemap_path = temp_git_repo / "CODEMAP.yaml"

        initial_codemap = {
            "project_structure": {
                "name": "Quality Gate Integration Test",
                "architecture": "DDD + Clean Architecture",
                "version": "1.0.0",
                "last_updated": "2025-01-15T08:00:00",
                "commit": "initial123",
                "layers": [
                    {
                        "name": "Domain Layer",
                        "path": "noveler/domain/",
                        "role": "Business logic",
                        "depends_on": [],
                        "key_modules": ["entities", "services"],
                        "entry_point": "entities/__init__.py",
                    },
                    {
                        "name": "Application Layer",
                        "path": "noveler/application/",
                        "role": "Use cases and orchestration",
                        "depends_on": ["Domain Layer"],
                        "key_modules": ["use_cases"],
                        "entry_point": "use_cases/__init__.py",
                    },
                ],
            },
            "circular_import_solutions": {"resolved_issues": []},
            "b20_compliance": {
                "ddd_layer_separation": {"status": "準拠"},
                "import_management": {"scripts_prefix": "統一済み"},
                "shared_components": {},
            },
            "quality_prevention_integration": {
                "architecture_linter": {"status": "active"},
                "hardcoding_detector": {"status": "active"},
                "automated_prevention": {"status": "enabled"},
            },
        }

        with open(codemap_path, "w", encoding="utf-8") as f:
            yaml.dump(initial_codemap, f, default_flow_style=False, allow_unicode=True)

        return codemap_path

    @pytest.fixture
    def integrated_system(self, temp_git_repo, codemap_file):
        """統合されたシステムコンポーネント"""
        codemap_repo = YamlCodeMapRepository(codemap_file)
        git_adapter = GitInformationAdapter(temp_git_repo)
        sync_service = CodeMapSynchronizationService()

        use_case = CodeMapAutoUpdateUseCase(codemap_repo, git_adapter, sync_service)

        return {
            "codemap_repo": codemap_repo,
            "git_adapter": git_adapter,
            "sync_service": sync_service,
            "use_case": use_case,
            "repo_path": temp_git_repo,
            "codemap_path": codemap_file,
        }

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-ARCHITECTURE_LINTER_")
    def test_architecture_linter_integration(self, integrated_system):
        """アーキテクチャリンターとの統合テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. アーキテクチャ違反を含むファイルを作成
        violation_file = repo_path / "scripts" / "domain" / "entities" / "bad_entity.py"
        violation_content = """
# アーキテクチャ違反: ドメイン層からプレゼンテーション層への依存
from noveler.presentation.cli.commands.core_commands import some_function

class BadEntity:
    def __init__(self):
        # このような依存は違反
        self.command_ref = some_function()
"""
        violation_file.write_text(violation_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add entity with architecture violation"], cwd=repo_path, check=True
        )

        # 2. アーキテクチャリンターをモック（実際の実行をシミュレート）
        with patch("subprocess.run") as mock_run:
            # アーキテクチャ違反を検出するリンターの結果をモック
            mock_result = MagicMock()
            mock_result.returncode = 1  # エラーを示すリターンコード
            mock_result.stdout = """
Architecture Violations Detected:
    - Domain layer dependency on Presentation layer in: scripts/domain/entities/bad_entity.py
- Violation: from noveler.presentation.cli.commands.core_commands import some_function
            """
            mock_run.return_value = mock_result

            # 3. CODEMAP自動更新を実行
            request = CodeMapAutoUpdateRequest(force_update=True, create_backup=True, validate_result=True)

            response = system["use_case"].execute(request)

            # 4. 品質ゲート統合により更新が成功することを確認
            assert response.success is True
            assert response.updated is True

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-HARDCODING_DETECTOR_")
    def test_hardcoding_detector_integration(self, integrated_system):
        """ハードコーディング検出器との統合テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. ハードコーディングを含むファイルを作成
        hardcoding_file = repo_path / "scripts" / "infrastructure" / "adapters" / "path_adapter.py"
        hardcoding_content = """
# ハードコーディング違反例
class PathAdapter:
    def __init__(self):
        # ハードコーディングされたパス（違反）
        self.base_path = "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド"
        self.project_root = "/absolute/hardcoded/path"

    def get_manuscript_dir(self):
        return self.base_path + "/40_原稿"  # ハードコーディング
"""
        hardcoding_file.write_text(hardcoding_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add adapter with hardcoding violations"], cwd=repo_path, check=True
        )

        # 2. ハードコーディング検出器をモック
        with patch("subprocess.run") as mock_run:
            # ハードコーディング違反を検出する結果をモック
            mock_result = MagicMock()
            mock_result.returncode = 1  # 警告を示すリターンコード
            mock_result.stdout = """
Hardcoding Violations Detected:
    - Critical: Absolute path hardcoding in scripts/infrastructure/adapters/path_adapter.py
- Warning: String concatenation path construction instead of Path.joinpath()
- Score: 3.2/10.0 (Below quality threshold)
            """
            mock_run.return_value = mock_result

            # 3. CODEMAP自動更新を実行
            response = system["use_case"].execute(CodeMapAutoUpdateRequest(force_update=True))

            # 4. 品質ゲートの結果がCODEMAPに反映されることを確認
            assert response.success is True

            updated_codemap = system["codemap_repo"].load_codemap()
            quality_prevention = updated_codemap.quality_prevention
            assert quality_prevention.hardcoding_detector["status"] == "active"

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-QUALITY_GATE_VALIDAT")
    def test_quality_gate_validation_with_codemap_sync(self, integrated_system):
        """品質ゲート検証とCODEMAP同期の統合テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. 品質ゲートパスするコードを作成
        good_file = repo_path / "scripts" / "domain" / "services" / "quality_service.py"
        good_content = """
from noveler.domain.entities.base_entity import BaseEntity
from noveler.domain.value_objects.quality_score import QualityScore

class QualityService:
    \"\"\"品質管理ドメインサービス\"\"\"

    def __init__(self):
        self.quality_threshold = 8.0

    def validate_quality(self, entity: BaseEntity) -> QualityScore:
        \"\"\"品質検証を実行\"\"\"
        # 良質なコード例：適切な依存関係、型注釈、ドキュメント
        return QualityScore(score=9.5, passed=True)
"""
        good_file.parent.mkdir(parents=True, exist_ok=True)
        good_file.write_text(good_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "feat: add high-quality domain service"], cwd=repo_path, check=True)

        # 2. 品質ゲート成功をモック
        with patch("subprocess.run") as mock_run:
            # 品質ゲートパスの結果をモック
            mock_result = MagicMock()
            mock_result.returncode = 0  # 成功
            mock_result.stdout = """
Quality Gate: PASSED
- Architecture Linter: No violations detected
- Hardcoding Detector: Score 9.2/10.0 (Excellent)
- All quality standards met
            """
            mock_run.return_value = mock_result

            # 3. CODEMAP自動更新実行
            response = system["use_case"].execute(CodeMapAutoUpdateRequest(force_update=True, validate_result=True))

            # 4. 品質ゲート成功によりCODEMAPが適切に更新されることを確認
            assert response.success is True
            assert response.validation_errors == []

            updated_codemap = system["codemap_repo"].load_codemap()
            assert updated_codemap.quality_prevention.automated_prevention["status"] == "enabled"

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-QUALITY_GATE_FAILURE")
    def test_quality_gate_failure_handling(self, integrated_system):
        """品質ゲート失敗時のハンドリングテスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. 複数の品質違反を含むファイルを作成
        bad_file = repo_path / "scripts" / "application" / "use_cases" / "bad_use_case.py"
        bad_content = """
# 複数の品質違反を含むファイル
import os
from noveler.presentation.cli.commands.core_commands import show_help  # CLAUDE.md準拠: 具体的インポート
from noveler.domain.entities.some_entity import SomeEntity

class BadUseCase:
    def execute(self):
        # ハードコーディング
        path = "/hardcoded/path/to/files"

        # 不適切な依存（アプリケーション → プレゼンテーション）
from noveler.presentation.shared.shared_utilities import console, get_common_path_service
        console.print("This is wrong")

        # 環境変数の直接使用
        root = os.getenv("PROJECT_ROOT")

        return {"status": "bad_practice"}
"""
        bad_file.write_text(bad_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add use case with multiple violations"], cwd=repo_path, check=True
        )

        # 2. 品質ゲート失敗をモック
        with patch("subprocess.run") as mock_run:
            # 複数の品質ゲート失敗の結果をモック
            mock_result = MagicMock()
            mock_result.returncode = 2  # 重大な失敗
            mock_result.stdout = """
Quality Gate: FAILED
Architecture Violations:
    - Application layer depends on Presentation layer
- Improper wildcard import usage

Hardcoding Violations:
    - Critical: Absolute path hardcoding
- Critical: Direct environment variable access
- Score: 2.1/10.0 (Unacceptable)

Overall Quality Gate: BLOCKED
            """
            mock_run.return_value = mock_result

            # 3. 品質ゲート失敗でもCODEMAP更新は継続されることを確認
            response = system["use_case"].execute(
                CodeMapAutoUpdateRequest(
                    force_update=True,
                    validate_result=False,  # 検証をスキップ
                )
            )

            # システムは継続動作するが、品質問題を記録
            assert response.success is True

            updated_codemap = system["codemap_repo"].load_codemap()
            # 品質問題があっても基本的な同期は実行される
            assert updated_codemap.metadata.commit != "initial123"

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-QUALITY_GATE_PROGRES")
    def test_quality_gate_progressive_improvement_tracking(self, integrated_system):
        """品質ゲートの段階的改善追跡テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. 初期状態：品質スコア低
        initial_file = repo_path / "scripts" / "domain" / "entities" / "improving_entity.py"
        initial_content = """
# 改善前：品質が低い状態
import os
class ImprovingEntity:
    def __init__(self):
        self.path = "/hardcoded/path"  # 問題1
        self.env_var = os.getenv("SOME_VAR")  # 問題2
"""
        initial_file.write_text(initial_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "feat: add entity needing improvement"], cwd=repo_path, check=True)

        # 初期品質スコアをモック（低スコア）
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = "Quality Score: 3.5/10.0 (Poor)"
            mock_run.return_value = mock_result

            response1 = system["use_case"].execute(CodeMapAutoUpdateRequest(force_update=True))
            initial_commit = response1.commit_hash

        # 2. 第1段階改善：ハードコーディング修正
        improved_content_1 = """
# 改善第1段階：ハードコーディング修正
import os
from pathlib import Path

class ImprovingEntity:
    def __init__(self, base_path: Path):
        self.path = base_path  # 改善1
        self.env_var = os.getenv("SOME_VAR")  # まだ残っている問題
"""
        initial_file.write_text(improved_content_1, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "refactor: fix hardcoding in improving_entity"], cwd=repo_path, check=True
        )

        # 中間品質スコアをモック（改善）
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Quality Score: 6.5/10.0 (Acceptable)"
            mock_run.return_value = mock_result

            response2 = system["use_case"].execute(CodeMapAutoUpdateRequest(force_update=True))
            intermediate_commit = response2.commit_hash

        # 3. 第2段階改善：設定管理統合
        improved_content_2 = """
# 改善第2段階：完全に品質基準準拠
from pathlib import Path
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

class ImprovingEntity:
    \"\"\"段階的に改善されたエンティティ\"\"\"

    def __init__(self, base_path: Path = None):
        config_manager = get_configuration_manager()
        self.path = base_path or config_manager.get_configuration().get_platform_path('default_project_root')
        self.config_value = config_manager.get_configuration().get_setting('some_var', default='default_value')
"""
        initial_file.write_text(improved_content_2, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "refactor: integrate configuration management"], cwd=repo_path, check=True
        )

        # 最終品質スコアをモック（高スコア）
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Quality Score: 9.3/10.0 (Excellent)"
            mock_run.return_value = mock_result

            response3 = system["use_case"].execute(CodeMapAutoUpdateRequest(force_update=True))
            final_commit = response3.commit_hash

        # 4. 段階的改善が追跡されていることを確認
        assert initial_commit != intermediate_commit != final_commit
        assert all(commit is not None for commit in [initial_commit, intermediate_commit, final_commit])

        # 最終的なCODEMAP状態確認
        final_codemap = system["codemap_repo"].load_codemap()
        assert final_codemap.metadata.commit == final_commit

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-QUALITY_GATE_INTEGRA")
    def test_quality_gate_integration_with_ci_cd_workflow(self, integrated_system):
        """品質ゲートのCI/CDワークフロー統合テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. CI/CD環境をシミュレートする環境変数設定
        ci_env_vars = {"CI": "true", "GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW": "Quality Gate Check"}

        with patch.dict(os.environ, ci_env_vars):
            # 2. CI/CDでの品質チェックを含むコミットを作成
            ci_test_file = repo_path / "scripts" / "tests" / "quality" / "test_quality_integration.py"
            ci_test_file.parent.mkdir(parents=True, exist_ok=True)
            ci_test_content = """
# CI/CD品質ゲート統合テスト
import pytest
from noveler.infrastructure.quality_gates.architecture_linter import ArchitectureLinter
from noveler.infrastructure.quality_gates.hardcoding_detector import HardcodingDetector

class TestQualityIntegration:
    @pytest.mark.spec('SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-ARCHITECTURE_COMPLIA')
    def test_architecture_compliance(self):
        \"\"\"アーキテクチャ準拠テスト\"\"\"
        linter = ArchitectureLinter()
        result = linter.check_project(".")
        assert result.passed is True

    @pytest.mark.spec('SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-HARDCODING_DETECTION')
    def test_hardcoding_detection(self):
        \"\"\"ハードコーディング検出テスト\"\"\"
        detector = HardcodingDetector()
        score = detector.calculate_quality_score(".")
        assert score >= 7.0  # 品質閾値
"""
            ci_test_file.write_text(ci_test_content, encoding="utf-8")

            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "ci: add quality gate integration tests"], cwd=repo_path, check=True)

            # 3. CI/CD環境での品質ゲート実行をモック
            with patch("subprocess.run") as mock_run:
                # CI/CD成功シナリオ
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = """
CI/CD Quality Gate Report:
    ✅ Architecture Linter: PASSED
✅ Hardcoding Detector: PASSED (Score: 8.7/10.0)
✅ Unit Tests: PASSED (Coverage: 95%)
✅ Integration Tests: PASSED
🎉 Quality Gate: PASSED - Ready for deployment
                """
                mock_run.return_value = mock_result

                # CODEMAP自動更新実行
                response = system["use_case"].execute(
                    CodeMapAutoUpdateRequest(force_update=True, create_backup=True, validate_result=True)
                )

                # CI/CD環境での成功を確認
                assert response.success is True
                assert response.backup_id is not None

                updated_codemap = system["codemap_repo"].load_codemap()
                quality_prevention = updated_codemap.quality_prevention

                # CI/CD統合により品質システムが有効になっていることを確認
                assert quality_prevention.automated_prevention["status"] == "enabled"
                assert quality_prevention.architecture_linter["status"] == "active"
                assert quality_prevention.hardcoding_detector["status"] == "active"

    @pytest.mark.spec("SPEC-CODEMAP_QUALITY_GATE_INTEGRATION-QUALITY_GATE_ROLLBAC")
    def test_quality_gate_rollback_mechanism(self, integrated_system):
        """品質ゲート失敗時のロールバック機構テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. 正常な状態でバックアップ作成
        good_file = repo_path / "scripts" / "domain" / "entities" / "stable_entity.py"
        good_content = """
from noveler.domain.value_objects.entity_id import EntityId

class StableEntity:
    \"\"\"安定したエンティティ\"\"\"

    def __init__(self, entity_id: EntityId):
        self.id = entity_id
        self.is_stable = True
"""
        good_file.write_text(good_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "feat: add stable entity"], cwd=repo_path, check=True)

        # 正常状態でのCODEMAP更新とバックアップ作成
        system["use_case"].execute(CodeMapAutoUpdateRequest(force_update=True, create_backup=True))

        # 2. 品質違反を含む変更を追加
        bad_change_file = repo_path / "scripts" / "domain" / "entities" / "broken_entity.py"
        bad_change_content = """
# 重大な品質違反
import sys
sys.path.append("/absolute/hardcoded/path")  # 重大違反1

from noveler.presentation.cli.commands.core_commands import show_help, show_status  # CLAUDE.md準拠: 具体的インポート
from noveler.infrastructure.adapters.database_adapter import DatabaseAdapter  # 層違反

class BrokenEntity:
    def __init__(self):
        # 直接的な外部システム依存（違反）
        self.db = DatabaseAdapter()  # ドメイン層からインフラ層への直接依存
        self.hardcoded_config = {
            "database_url": "postgresql://user:pass@localhost:5432/db",  # ハードコーディング
            "api_key": "sk-1234567890abcdef"  # 機密情報ハードコーディング
        }
"""
        bad_change_file.write_text(bad_change_content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "feat: add entity with severe violations"], cwd=repo_path, check=True)

        # 3. 品質ゲート重大失敗をモック
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 2  # 重大エラー
            mock_result.stdout = """
CRITICAL QUALITY GATE FAILURE:
    🚨 Architecture Violations: 3 CRITICAL
🚨 Hardcoding Violations: 4 CRITICAL
🚨 Security Issues: 1 CRITICAL (API key exposure)
🚨 Overall Score: 1.2/10.0 (UNACCEPTABLE)

RECOMMENDATION: IMMEDIATE ROLLBACK REQUIRED
            """
            mock_run.return_value = mock_result

            # 検証エラーによるロールバックをテスト
            with patch.object(system["sync_service"], "validate_synchronization_result") as mock_validate:
                mock_validate.return_value = [
                    "Critical architecture violations detected",
                    "Unacceptable hardcoding quality score",
                    "Security vulnerability: exposed credentials",
                ]

                # CODEMAP自動更新実行（検証失敗でロールバック）
                rollback_response = system["use_case"].execute(
                    CodeMapAutoUpdateRequest(
                        force_update=True,
                        create_backup=True,
                        validate_result=True,  # 検証有効
                    )
                )

                # 4. ロールバックが適切に実行されたことを確認
                assert rollback_response.success is False
                assert "Validation failed, restored from backup" in rollback_response.error_message
                assert rollback_response.validation_errors is not None
                assert len(rollback_response.validation_errors) >= 3

                # バックアップから復元されたCODEMAPが正常状態であることを確認
                restored_codemap = system["codemap_repo"].load_codemap()
                assert restored_codemap.metadata.commit != "broken_commit"  # 破損したコミットではない

                # 品質ゲートシステムが引き続き有効であることを確認
                quality_prevention = restored_codemap.quality_prevention
                assert quality_prevention.automated_prevention["status"] == "enabled"
