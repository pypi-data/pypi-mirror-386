#!/usr/bin/env python3
"""CODEMAP自動更新システムの統合テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from noveler.application.use_cases.codemap_auto_update_use_case import (
    CodeMapAutoUpdateRequest,
    CodeMapAutoUpdateUseCase,
)
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.infrastructure.adapters.git_information_adapter import GitInformationAdapter
from noveler.infrastructure.git.hooks.codemap_post_commit_hook import CodeMapPostCommitHook
from noveler.infrastructure.repositories.yaml_codemap_repository import YamlCodeMapRepository


@pytest.mark.integration
class TestCodeMapAutoUpdateIntegration:
    """CODEMAP自動更新システムの統合テストクラス"""

    @pytest.fixture
    def temp_git_repo(self):
        """一時的なGitリポジトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Gitリポジトリ初期化
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

            # 初期コミット
            readme_file = repo_path / "README.md"
            readme_file.write_text("# Test Repository", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_path, check=True)

            yield repo_path

    @pytest.fixture
    def codemap_file(self, temp_git_repo):
        """CODEMAPファイル"""
        codemap_path = temp_git_repo / "CODEMAP.yaml"

        # 初期CODEMAP作成
        initial_codemap = {
            "project_structure": {
                "name": "Integration Test Project",
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
                    }
                ],
            },
            "circular_import_solutions": {
                "resolved_issues": [
                    {
                        "location": "noveler/domain/entities/test_entity.py",
                        "issue": "循環インポート問題",
                        "solution": "バレルモジュール適用",
                        "status": "未完了",
                        "commit": None,
                    }
                ]
            },
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
        """統合されたCODEMAP自動更新システム"""
        # 実際のコンポーネントを使用
        codemap_repository = YamlCodeMapRepository(codemap_file)
        git_adapter = GitInformationAdapter(temp_git_repo)
        sync_service = CodeMapSynchronizationService()

        use_case = CodeMapAutoUpdateUseCase(codemap_repository, git_adapter, sync_service)

        return {
            "use_case": use_case,
            "repository": codemap_repository,
            "git_adapter": git_adapter,
            "sync_service": sync_service,
            "repo_path": temp_git_repo,
            "codemap_path": codemap_file,
        }

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-FULL_INTEGRATION_WOR")
    def test_full_integration_workflow(self, integrated_system):
        """フル統合ワークフローのテスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. 新しいファイルを作成してコミット
        test_file = repo_path / "scripts" / "domain" / "entities" / "test_entity.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Test entity file\nclass TestEntity:\n    pass\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fix: resolve circular import in test_entity.py"], cwd=repo_path, check=True
        )

        # 2. CODEMAP自動更新を実行
        request = CodeMapAutoUpdateRequest(force_update=False, create_backup=True, validate_result=True)

        response = system["use_case"].execute(request)

        # 3. 結果検証
        assert response.success is True
        assert response.updated is True
        assert response.backup_id is not None
        assert response.commit_hash is not None
        assert response.execution_time_ms > 0

        # 4. CODEMAPファイルが更新されていることを確認
        updated_codemap = system["repository"].load_codemap()
        assert updated_codemap is not None
        assert updated_codemap.metadata.commit != "initial123"

        # 5. 問題が完了としてマークされていることを確認
        # CODEMAPの構造に応じて適切にアクセス
        resolved_issues = getattr(updated_codemap, 'circular_import_solutions', {}).get('resolved_issues', [])
        if not resolved_issues:
            # バックアップとしてcircular_import_issuesも確認
            resolved_issues = getattr(updated_codemap, 'circular_import_issues', [])

        test_issue = next(
            (issue for issue in resolved_issues if "test_entity.py" in str(issue.get('location', ''))), None
        )

        assert test_issue is not None
        # is_completed()メソッドではなく、statusフィールドを確認
        status = test_issue.get('status', '未完了') if isinstance(test_issue, dict) else getattr(test_issue, 'status', '未完了')
        assert status in ['完了', 'completed', '解決済み']

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-POST_COMMIT_HOOK_INT")
    def test_post_commit_hook_integration(self, integrated_system):
        """Post-commitフック統合テスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # Post-commitフッククラスをテスト
        hook = CodeMapPostCommitHook(repo_path)

        # 新しい変更を作成
        change_file = repo_path / "scripts" / "presentation" / "cli" / "commands" / "__init__.py"
        change_file.parent.mkdir(parents=True, exist_ok=True)
        change_file.write_text(
            "# Barrel module implementation\nfrom tests.integration.core_commands import show_help, show_status\n", encoding="utf-8"
        )

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "feat: implement barrel module for commands"], cwd=repo_path, check=True)

        # フック実行
        success = hook.execute(force_update=False, skip_validation=False)

        # 結果確認
        assert success is True

        # CODEMAPが更新されたことを確認
        updated_codemap = system["repository"].load_codemap()
        assert updated_codemap is not None

        # バレルモジュール関連の問題が処理されたことを確認
        barrel_issues = [
            issue for issue in updated_codemap.circular_import_issues if "バレルモジュール" in issue.solution
        ]
        if barrel_issues:
            assert any(issue.is_completed() for issue in barrel_issues)

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-BACKUP_AND_RESTORE_I")
    def test_backup_and_restore_integration(self, integrated_system):
        """バックアップ・復元統合テスト"""
        system = integrated_system
        repository = system["repository"]

        # 1. 初期状態のバックアップ作成
        initial_backup_id = repository.create_backup()
        assert initial_backup_id is not None

        # 2. CODEMAPを変更
        codemap = repository.load_codemap()
        original_commit = codemap.metadata.commit
        codemap.metadata.commit = "modified_commit"
        codemap.metadata.last_updated = datetime.now(timezone.utc)

        save_success = repository.save_codemap(codemap)
        assert save_success is True

        # 3. 変更が反映されていることを確認
        modified_codemap = repository.load_codemap()
        assert modified_codemap.metadata.commit == "modified_commit"

        # 4. バックアップから復元
        restore_success = repository.restore_from_backup(initial_backup_id)
        assert restore_success is True

        # 5. 元の状態に戻ったことを確認
        restored_codemap = repository.load_codemap()
        assert restored_codemap.metadata.commit == original_commit

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-VALIDATION_AND_ROLLB")
    def test_validation_and_rollback_integration(self, integrated_system):
        """検証とロールバック統合テスト"""
        system = integrated_system

        # 検証エラーを意図的に発生させるため、同期サービスをモック
        with patch.object(
            system["sync_service"], "validate_synchronization_result", return_value=["Test validation error"]
        ):
            request = CodeMapAutoUpdateRequest(force_update=True, create_backup=True, validate_result=True)

            # 実行
            response = system["use_case"].execute(request)

            # 検証エラーによる失敗とロールバックを確認
            assert response.success is False
            assert "Validation failed, restored from backup" in response.error_message
            assert response.validation_errors == ["Test validation error"]
            assert response.backup_id is not None

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-SYSTEM_STATUS_INTEGR")
    def test_system_status_integration(self, integrated_system):
        """システム状態確認統合テスト"""
        system = integrated_system

        # システム状態取得
        status = system["use_case"].get_update_status()

        # 基本状態確認
        assert status["codemap_available"] is True
        assert status["git_repository"] is True
        assert status["current_commit"] is not None
        assert status["latest_commit"] is not None
        assert "completion_rate" in status
        assert isinstance(status["completion_rate"], int | float)

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-CLI_INTEGRATION")
    def test_cli_integration(self, integrated_system, temp_git_repo):
        """CLI統合テスト"""
        system = integrated_system

        # CLIコマンドの基本的な機能テスト
        from click.testing import CliRunner

        from noveler.presentation.cli.commands.codemap_commands import codemap_group

        runner = CliRunner()

        # status コマンドテスト
        with runner.isolated_filesystem():
            result = runner.invoke(
                codemap_group,
                ["status", "--codemap-path", str(system["codemap_path"]), "--repository-path", str(temp_git_repo)],
            )

            assert result.exit_code == 0

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-CONCURRENT_ACCESS_SA")
    def test_concurrent_access_safety(self, integrated_system):
        """並行アクセス安全性テスト"""
        system = integrated_system

        # 複数のリクエストを並行実行（簡単なテスト）
        request1 = CodeMapAutoUpdateRequest(force_update=True, create_backup=True)
        request2 = CodeMapAutoUpdateRequest(force_update=True, create_backup=True)

        # 逐次実行（実際の並行性はテストが複雑になるため簡易版）
        response1 = system["use_case"].execute(request1)
        response2 = system["use_case"].execute(request2)

        # 両方が成功または適切に処理されることを確認
        assert response1.success is True
        assert response2.success is True
        assert response1.backup_id != response2.backup_id  # 異なるバックアップID

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-ERROR_RECOVERY_INTEG")
    def test_error_recovery_integration(self, integrated_system):
        """エラー回復統合テスト"""
        system = integrated_system

        # 一時的にGitアダプターを無効化してエラーを発生させる
        with patch.object(system["git_adapter"], "is_git_repository", return_value=False):
            request = CodeMapAutoUpdateRequest()
            response = system["use_case"].execute(request)

            # エラーハンドリングが適切に動作することを確認
            assert response.success is False
            assert response.error_message == "Not a Git repository"
            assert response.execution_time_ms > 0

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-LARGE_REPOSITORY_SIM")
    def test_large_repository_simulation(self, integrated_system):
        """大規模リポジトリシミュレーションテスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 複数のファイルとディレクトリを作成
        for i in range(5):
            for layer in ["domain", "application", "infrastructure", "presentation"]:
                layer_dir = repo_path / "scripts" / layer / f"module_{i}"
                layer_dir.mkdir(parents=True, exist_ok=True)

                test_file = layer_dir / f"test_file_{i}.py"
                test_file.write_text(f"# Module {i} in {layer} layer\n", encoding="utf-8")
        # 一括コミット
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add multiple modules across all layers"], cwd=repo_path, check=True
        )

        # 大規模変更の処理能力をテスト
        request = CodeMapAutoUpdateRequest(force_update=True)
        response = system["use_case"].execute(request)

        assert response.success is True
        assert response.updated is True
        # 実行時間が妥当な範囲内であることを確認（10秒以内）
        assert response.execution_time_ms < 10000

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-YAML_STRUCTURE_VALID")
    def test_yaml_structure_validation_integration(self, integrated_system):
        """YAML構造検証統合テスト"""
        system = integrated_system
        repository = system["repository"]

        # 構造検証テスト
        validation_errors = repository.validate_yaml_structure()

        # 初期状態では検証エラーがないはず
        assert validation_errors == []

        # 不正な構造のYAMLを作成
        invalid_yaml_content = "invalid_structure: true\nmissing_required_sections: yes"
        system["codemap_path"].write_text(invalid_yaml_content, encoding="utf-8")

        # 検証エラーが検出されることを確認
        validation_errors = repository.validate_yaml_structure()
        assert len(validation_errors) > 0
        assert any("Missing" in error for error in validation_errors)

    @pytest.mark.spec("SPEC-CODEMAP_AUTO_UPDATE_INTEGRATION-PERFORMANCE_BENCHMAR")
    def test_performance_benchmarking(self, integrated_system):
        """パフォーマンスベンチマークテスト"""
        system = integrated_system

        # 複数回実行して平均実行時間を測定
        execution_times = []

        for _i in range(5):
            request = CodeMapAutoUpdateRequest(force_update=True)
            response = system["use_case"].execute(request)

            assert response.success is True
            execution_times.append(response.execution_time_ms)

        # 平均実行時間が合理的な範囲内であることを確認
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 5000  # 5秒以内

        # 実行時間の一貫性を確認（標準偏差が平均の50%以内）
        import statistics

        std_dev = statistics.stdev(execution_times)
        assert std_dev < avg_time * 0.5
