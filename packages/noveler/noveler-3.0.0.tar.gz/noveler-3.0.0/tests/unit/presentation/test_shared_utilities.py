"""
shared_utilities.pyのテスト

特にCommonPathServiceとget_common_path_service関数の
TARGET_PROJECT_ROOT環境変数対応機能をテスト


仕様書: SPEC-PRESENTATION
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.presentation.shared.shared_utilities import CommonPathService, get_common_path_service


class TestCommonPathService:
    """CommonPathServiceのテストクラス"""

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_detect_project_root_with_target_project_root_env(self):
        """TARGET_PROJECT_ROOT環境変数による外部指定のテスト"""
        path_service = get_common_path_service()
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_path = Path(temp_dir) / "test_project"
            test_project_path.mkdir()

            # 必要なディレクトリを作成
            (test_project_path / str(path_service.get_manuscript_dir())).mkdir()
            (test_project_path / str(path_service.get_management_dir())).mkdir()

            with patch.dict(os.environ, {"TARGET_PROJECT_ROOT": str(test_project_path)}):
                service = CommonPathService()
                assert service.project_root == test_project_path

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_detect_project_root_with_project_root_env_fallback(self):
        """PROJECT_ROOT環境変数による従来の外部指定のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_path = Path(temp_dir) / "test_project"
            test_project_path.mkdir()

            # 必要なディレクトリを作成
            path_service = get_common_path_service()
            (test_project_path / str(path_service.get_manuscript_dir())).mkdir()
            (test_project_path / str(path_service.get_management_dir())).mkdir()

            with patch.dict(
                os.environ,
                {
                    "PROJECT_ROOT": str(test_project_path),
                    "TARGET_PROJECT_ROOT": "",  # TARGET_PROJECT_ROOTは空
                },
                clear=False,
            ):
                service = CommonPathService()
                assert service.project_root == test_project_path

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_detect_project_root_priority_order(self):
        """環境変数の優先順位テスト（TARGET_PROJECT_ROOT > PROJECT_ROOT）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_project_path = Path(temp_dir) / "target_project"
            regular_project_path = Path(temp_dir) / "regular_project"

            # 両方のプロジェクトディレクトリを作成
            for project_path in [target_project_path, regular_project_path]:
                project_path.mkdir()
                path_service = get_common_path_service()
                (project_path / str(path_service.get_manuscript_dir())).mkdir()
                (project_path / str(path_service.get_management_dir())).mkdir()

            with patch.dict(
                os.environ, {"TARGET_PROJECT_ROOT": str(target_project_path), "PROJECT_ROOT": str(regular_project_path)}
            ):
                service = CommonPathService()
                # TARGET_PROJECT_ROOTが優先される
                assert service.project_root == target_project_path

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_backward_compatibility_no_env_vars(self):
        """環境変数なしでの従来動作の確認"""
        with patch.dict(os.environ, {}, clear=True):
            # 環境変数なしで動作することを確認
            service = CommonPathService()
            # 現在のディレクトリがデフォルトになる
            assert service.project_root == Path.cwd()


class TestGetCommonPathService:
    """get_common_path_service関数のテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        # グローバルインスタンスをリセット
        from noveler.presentation.cli import shared_utilities

        shared_utilities._common_path_service = None

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_get_common_path_service_with_target_project_root(self):
        """target_project_rootパラメータによる外部指定のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_path = Path(temp_dir) / "target_project"
            test_project_path.mkdir()

            # 必要なディレクトリを作成
            path_service = get_common_path_service()
            (test_project_path / str(path_service.get_manuscript_dir())).mkdir()
            (test_project_path / str(path_service.get_management_dir())).mkdir()

            service = get_common_path_service(target_project_root=test_project_path)
            assert service.project_root == test_project_path

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_get_common_path_service_with_both_parameters(self):
        """project_rootとtarget_project_root両方指定時の動作テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project"
            target_path = Path(temp_dir) / "target"

            for path in [project_path, target_path]:
                path.mkdir()
                path_service = get_common_path_service()
                (path / str(path_service.get_manuscript_dir())).mkdir()
                (path / str(path_service.get_management_dir())).mkdir()

            # project_rootが優先される
            service = get_common_path_service(project_root=project_path, target_project_root=target_path)

            assert service.project_root == project_path

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_get_common_path_service_env_cleanup(self):
        """環境変数の適切なクリーンアップテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_path = Path(temp_dir) / "test_project"
            test_project_path.mkdir()

            # 元の環境変数値を保存
            original_value = os.environ.get("TARGET_PROJECT_ROOT")

            try:
                get_common_path_service(target_project_root=test_project_path)

                # 関数実行後、環境変数が元に戻されていることを確認
                assert os.environ.get("TARGET_PROJECT_ROOT") == original_value

            finally:
                # テスト環境のクリーンアップ
                if original_value is not None:
                    os.environ["TARGET_PROJECT_ROOT"] = original_value
                else:
                    os.environ.pop("TARGET_PROJECT_ROOT", None)

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_backward_compatibility_existing_usage(self):
        """既存コードとの後方互換性テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_path = Path(temp_dir) / "existing_project"
            test_project_path.mkdir()

            # 従来の使い方でも動作することを確認
            service = get_common_path_service(project_root=test_project_path)
            assert service.project_root == test_project_path

            # パラメータなしでも動作することを確認
            service_no_params = get_common_path_service()
            assert service_no_params is not None

    @pytest.mark.parametrize("env_var_name", ["TARGET_PROJECT_ROOT", "PROJECT_ROOT"])
    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_environment_variable_integration(self, env_var_name):
        """環境変数との統合テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_path = Path(temp_dir) / "env_test_project"
            test_project_path.mkdir()
            path_service = get_common_path_service()
            (test_project_path / str(path_service.get_manuscript_dir())).mkdir()
            (test_project_path / str(path_service.get_management_dir())).mkdir()

            with patch.dict(os.environ, {env_var_name: str(test_project_path)}):
                service = get_common_path_service()
                assert service.project_root == test_project_path

    @pytest.mark.spec("SPEC-PRESENTATION")
    def test_get_common_path_service_resets_mock_cache(self):
        """モック化されたグローバルキャッシュを再初期化することを確認"""
        from noveler.presentation.shared import shared_utilities as shared_utils

        original_service = getattr(shared_utils, "_common_path_service", None)
        try:
            shared_utils._common_path_service = Mock()

            service = get_common_path_service()

            assert isinstance(service, CommonPathService)
        finally:
            shared_utils._common_path_service = original_service


if __name__ == "__main__":
    pytest.main([__file__])
