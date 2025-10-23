#!/usr/bin/env python3
"""CODEMAP自動更新システムとGitHookRepositoryの統合テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

from noveler.application.use_cases.codemap_auto_update_use_case import (
    CodeMapAutoUpdateUseCase,
)
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.infrastructure.adapters.git_information_adapter import GitInformationAdapter
from noveler.infrastructure.git.hooks.codemap_post_commit_hook import (
    CodeMapPostCommitHook,
    install_codemap_post_commit_hook,
)
from noveler.infrastructure.repositories.git_hook_repository import GitHookRepository
from noveler.infrastructure.repositories.yaml_codemap_repository import YamlCodeMapRepository


@pytest.mark.integration
class TestCodeMapGitHookIntegration:
    """CODEMAP自動更新システムとGitHookRepositoryの統合テストクラス"""

    @pytest.fixture
    def temp_git_repo(self):
        """テスト用の一時Gitリポジトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Gitリポジトリ初期化
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

            # 初期コミット
            readme_file = repo_path / "README.md"
            readme_file.write_text("# Test Repository for GitHook Integration", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_path, check=True)

            yield repo_path

    @pytest.fixture
    def guide_root(self, temp_git_repo):
        """ガイドルートディレクトリ"""
        guide_dir = temp_git_repo / "guide"
        guide_dir.mkdir()
        return guide_dir

    @pytest.fixture
    def codemap_file(self, temp_git_repo):
        """CODEMAPファイル"""
        codemap_path = temp_git_repo / "CODEMAP.yaml"

        initial_codemap = {
            "project_structure": {
                "name": "GitHook Integration Test",
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
    def git_hook_repo(self, temp_git_repo, guide_root):
        """GitHookRepositoryインスタンス"""
        return GitHookRepository(temp_git_repo, guide_root)

    @pytest.fixture
    def codemap_repo(self, codemap_file):
        """CODEMAPリポジトリインスタンス"""
        return YamlCodeMapRepository(codemap_file)

    @pytest.fixture
    def integrated_system(self, temp_git_repo, git_hook_repo, codemap_repo):
        """統合されたシステムコンポーネント"""
        git_adapter = GitInformationAdapter(temp_git_repo)
        sync_service = CodeMapSynchronizationService()

        use_case = CodeMapAutoUpdateUseCase(codemap_repo, git_adapter, sync_service)

        return {
            "git_hook_repo": git_hook_repo,
            "codemap_repo": codemap_repo,
            "git_adapter": git_adapter,
            "use_case": use_case,
            "repo_path": temp_git_repo,
        }

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-GIT_HOOK_INSTALLATIO")
    def test_git_hook_installation_and_codemap_integration(self, integrated_system):
        """GitHookインストールとCODEMAP統合テスト"""
        system = integrated_system
        git_hook_repo = system["git_hook_repo"]
        repo_path = system["repo_path"]

        # 1. post-commitフックがまだ存在しないことを確認
        assert not git_hook_repo.hook_exists("post-commit")

        # 2. CODEMAPポストコミットフックをインストール
        install_success = install_codemap_post_commit_hook(repo_path)
        assert install_success is True

        # 3. フックが正しくインストールされたことを確認
        assert git_hook_repo.hook_exists("post-commit")
        assert git_hook_repo.is_hook_executable("post-commit")

        # 4. フック情報を取得して検証
        hook_info = git_hook_repo.get_hook_info("post-commit")
        assert hook_info is not None
        assert hook_info["name"] == "post-commit"
        assert hook_info["exists"] is True
        assert hook_info["executable"] is True

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-POST_COMMIT_HOOK_EXE")
    def test_post_commit_hook_execution_with_codemap_update(self, integrated_system):
        """post-commitフック実行とCODEMAP更新統合テスト"""
        system = integrated_system
        repo_path = system["repo_path"]
        codemap_repo = system["codemap_repo"]

        # 1. post-commitフックをインストール
        install_codemap_post_commit_hook(repo_path)

        # 2. 循環インポート修正をシミュレートするファイルを作成
        test_file = repo_path / "scripts" / "domain" / "entities" / "test_entity.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# Fixed circular import issue\nclass TestEntity:\n    pass\n", encoding="utf-8")

        # 3. ファイルをコミット（post-commitフックが自動実行される）
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fix: resolve circular import in test_entity.py"], cwd=repo_path, check=True
        )

        # 4. CODEMAPが自動更新されたことを確認
        updated_codemap = codemap_repo.load_codemap()
        assert updated_codemap is not None
        assert updated_codemap.metadata.commit != "initial123"

        # 5. 循環インポート問題が完了としてマークされたことを確認
        test_issue = next(
            (issue for issue in updated_codemap.circular_import_issues if "test_entity.py" in issue.location), None
        )

        assert test_issue is not None
        assert test_issue.is_completed()

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-GIT_HOOK_REPOSITORY_")
    def test_git_hook_repository_hook_management(self, git_hook_repo, temp_git_repo):
        """GitHookRepositoryによるフック管理テスト"""
        # 1. 初期状態：フックが存在しないことを確認
        assert not git_hook_repo.hook_exists("post-commit")

        # 2. フックをインストール
        hook_script = "#!/bin/sh\necho 'Test hook executed'\n"
        install_result = git_hook_repo.install_hook("post-commit", hook_script)
        assert install_result["success"] is True
        assert install_result["message"] is not None

        # 3. フックが存在することを確認
        assert git_hook_repo.hook_exists("post-commit")
        assert git_hook_repo.is_hook_executable("post-commit")

        # 4. フックをテスト実行
        test_result = git_hook_repo.test_hook("post-commit")
        assert test_result["success"] is True

        # 5. フックをアンインストール
        uninstall_result = git_hook_repo.uninstall_hook("post-commit")
        assert uninstall_result["success"] is True

        # 6. フックが削除されたことを確認
        assert not git_hook_repo.hook_exists("post-commit")

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-MULTIPLE_HOOKS_COEXI")
    def test_multiple_hooks_coexistence(self, git_hook_repo, temp_git_repo):
        """複数フックの共存テスト"""
        # 1. 複数のフックをインストール
        hooks = {
            "pre-commit": "#!/bin/sh\necho 'Pre-commit hook'\n",
            "post-commit": "#!/bin/sh\necho 'Post-commit hook'\n",
            "pre-push": "#!/bin/sh\necho 'Pre-push hook'\n",
        }

        for hook_name, hook_script in hooks.items():
            result = git_hook_repo.install_hook(hook_name, hook_script)
            assert result["success"] is True

        # 2. すべてのフックが存在することを確認
        all_hooks_info = git_hook_repo.get_all_hooks_info()
        installed_hooks = {hook["name"] for hook in all_hooks_info if hook["exists"]}

        for hook_name in hooks:
            assert hook_name in installed_hooks
            assert git_hook_repo.is_hook_executable(hook_name)

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-CODEMAP_HOOK_ERROR_H")
    def test_codemap_hook_error_handling(self, integrated_system):
        """CODEMAPフックエラーハンドリングテスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. post-commitフックをインストール
        install_codemap_post_commit_hook(repo_path)

        # 2. CODEMAPファイルを破損させる（YAMLエラーを発生させる）
        codemap_path = repo_path / "CODEMAP.yaml"
        codemap_path.write_text("invalid: yaml: content: [", encoding="utf-8")

        # 3. CODEMAPPostCommitHookを直接テスト（エラーハンドリング確認）
        hook = CodeMapPostCommitHook(repo_path)

        # エラーが発生しても処理が継続されることを確認
        result = hook.execute(force_update=False, skip_validation=True)

        # フック実行は失敗するが、例外は発生しない
        assert result is False

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-GIT_HOOK_REPOSITORY_")
    def test_git_hook_repository_integration_with_existing_hooks(self, git_hook_repo):
        """既存フックとの統合テスト"""
        # 1. 既存のpost-commitフックを作成
        existing_hook_content = "#!/bin/sh\n# Existing hook\necho 'Existing post-commit'\n"
        git_hook_repo.install_hook("post-commit", existing_hook_content)

        # 2. CODEMAPフックを追加インストール（既存フックを上書き）
        codemap_hook_content = git_hook_repo._generate_hook_script(
            "post-commit",
            {
                "codemap_integration": True,
                "repository_path": str(git_hook_repo.repository_path),
                "guide_root": str(git_hook_repo.guide_root),
            },
        )

        install_result = git_hook_repo.install_hook("post-commit", codemap_hook_content)
        assert install_result["success"] is True
        assert "已覆盖现有钩子" in install_result["message"] or "overwritten" in install_result["message"].lower()

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-HOOK_SCRIPT_GENERATI")
    def test_hook_script_generation(self, git_hook_repo):
        """フックスクリプト生成テスト"""
        # 1. post-commitフック用のスクリプト生成
        config = {
            "codemap_integration": True,
            "repository_path": str(git_hook_repo.repository_path),
            "guide_root": str(git_hook_repo.guide_root),
            "python_executable": "python3",
        }

        script_content = git_hook_repo._generate_hook_script("post-commit", config)

        # 2. 生成されたスクリプトの内容確認
        assert "#!/bin/sh" in script_content
        assert "post-commit" in script_content
        assert "codemap" in script_content.lower()
        assert str(git_hook_repo.repository_path) in script_content
        assert "python" in script_content

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-HOOK_EXECUTION_IN_DI")
    def test_hook_execution_in_different_git_states(self, integrated_system):
        """異なるGit状態でのフック実行テスト"""
        system = integrated_system
        repo_path = system["repo_path"]
        codemap_repo = system["codemap_repo"]

        # 1. post-commitフックをインストール
        install_codemap_post_commit_hook(repo_path)

        # テストケース1: 新規ファイル追加
        new_file = repo_path / "scripts" / "application" / "use_cases" / "new_use_case.py"
        new_file.parent.mkdir(parents=True, exist_ok=True)
        new_file.write_text("class NewUseCase:\n    pass\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "feat: add new use case"], cwd=repo_path, check=True)

        # CODEMAPが更新されたことを確認
        updated_codemap_1 = codemap_repo.load_codemap()
        first_update_commit = updated_codemap_1.metadata.commit

        # テストケース2: 既存ファイル修正
        new_file.write_text("class NewUseCase:\n    def execute(self):\n        pass\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "refactor: improve new use case"], cwd=repo_path, check=True)

        # CODEMAPが再度更新されたことを確認
        updated_codemap_2 = codemap_repo.load_codemap()
        second_update_commit = updated_codemap_2.metadata.commit

        # 各コミットで異なるハッシュが記録されることを確認
        assert first_update_commit != "initial123"
        assert second_update_commit != first_update_commit
        assert second_update_commit != "initial123"

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-HOOK_REPOSITORY_ERRO")
    def test_hook_repository_error_recovery(self, git_hook_repo):
        """GitHookRepositoryエラー回復テスト"""
        # 1. 無効なフックスクリプトのインストールを試行
        invalid_script = "invalid shell script content without shebang"

        result = git_hook_repo.install_hook("post-commit", invalid_script)

        # インストールは成功するが、実行時にエラーになる可能性がある
        assert result["success"] is True

        # 2. フックの存在とテスト実行
        assert git_hook_repo.hook_exists("post-commit")

        # テスト実行（エラーが発生する可能性があるが、例外は発生しない）
        test_result = git_hook_repo.test_hook("post-commit")
        # テスト結果は失敗する可能性があるが、システムは継続する
        assert isinstance(test_result, dict)
        assert "success" in test_result

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-CODEMAP_HOOK_PERFORM")
    def test_codemap_hook_performance(self, integrated_system):
        """CODEMAPフックパフォーマンステスト"""
        system = integrated_system
        repo_path = system["repo_path"]

        # 1. post-commitフックをインストール
        install_codemap_post_commit_hook(repo_path)

        # 2. 複数ファイルの一括コミット（大規模変更のシミュレーション）
        for i in range(10):
            for layer in ["domain", "application", "infrastructure"]:
                layer_dir = repo_path / "scripts" / layer / f"module_{i}"
                layer_dir.mkdir(parents=True, exist_ok=True)

                test_file = layer_dir / f"test_file_{i}.py"
                test_file.write_text(
                    f"# Module {i} in {layer} layer\nclass TestClass{i}:\n    pass\n", encoding="utf-8"
                )
        # 3. パフォーマンス測定用のコミット実行
        import time

        start_time = time.time()

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add multiple modules for performance test"], cwd=repo_path, check=True
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # 4. パフォーマンス検証（10秒以内で完了することを確認）
        assert execution_time < 10.0

        # 5. CODEMAPが正しく更新されたことを確認
        updated_codemap = system["codemap_repo"].load_codemap()
        assert updated_codemap is not None
        assert updated_codemap.metadata.commit != "initial123"

    @pytest.mark.spec("SPEC-CODEMAP_GIT_HOOK_INTEGRATION-HOOK_UNINSTALLATION_")
    def test_hook_uninstallation_cleanup(self, git_hook_repo):
        """フックアンインストール時のクリーンアップテスト"""
        # 1. 複数のフックをインストール
        hooks_to_install = ["pre-commit", "post-commit", "pre-push"]

        for hook_name in hooks_to_install:
            script = f"#!/bin/sh\necho '{hook_name} executed'\n"
            result = git_hook_repo.install_hook(hook_name, script)
            assert result["success"] is True

        # 2. すべてのフックが存在することを確認
        for hook_name in hooks_to_install:
            assert git_hook_repo.hook_exists(hook_name)

        # 3. 個別にアンインストール
        for hook_name in hooks_to_install:
            uninstall_result = git_hook_repo.uninstall_hook(hook_name)
            assert uninstall_result["success"] is True
            assert not git_hook_repo.hook_exists(hook_name)

        # 4. 完全にクリーンアップされたことを確認
        all_hooks_info = git_hook_repo.get_all_hooks_info()
        existing_hooks = [hook for hook in all_hooks_info if hook["exists"]]

        # インストールしたフックが完全に削除されていることを確認
        installed_hook_names = {hook["name"] for hook in existing_hooks}
        for hook_name in hooks_to_install:
            assert hook_name not in installed_hook_names
