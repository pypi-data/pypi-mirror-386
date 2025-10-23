#!/usr/bin/env python3
"""システム診断ドメインサービステスト

Command Pattern適用版のテスト


仕様書: SPEC-DOMAIN-SERVICES
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.domain.services.system_diagnostics import (
    DependencyDiagnosticCommand,
    DiagnosticResult,
    EnvironmentDiagnosticCommand,
    ProjectStructureDiagnosticCommand,
    SystemDiagnosticsService,
)


class TestDiagnosticResult:
    """診断結果のテスト"""

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-RESULT")
    def test_result(self) -> None:
        """診断結果が正常に作成されることを確認"""
        # When: 診断結果を作成
        result = DiagnosticResult(status="OK", details={"test": "value"}, messages=["テストメッセージ"])

        # Then: 期待される値が設定されている
        assert result.status == "OK"
        assert result.details == {"test": "value"}
        assert result.messages == ["テストメッセージ"]


class TestEnvironmentDiagnosticCommand:
    """環境診断コマンドのテスト"""

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-PYTHON_VERSION")
    def test_python_version(self) -> None:
        """Python バージョンが正常に検出されることを確認"""
        # Given: 環境診断コマンド
        command = EnvironmentDiagnosticCommand(quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: Python バージョンが検出される
        assert "python_version" in result.details
        assert (
            result.details["python_version"]
            == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-ENV_VARS")
    def test_environment_variables_detection(self) -> None:
        """環境変数の検出が正しく動作することを確認"""
        # Given: 環境診断コマンド
        command = EnvironmentDiagnosticCommand(quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: 環境変数がチェックされる
        assert "environment_variables" in result.details
        env_vars = result.details["environment_variables"]
        assert "PROJECT_ROOT" in env_vars
        assert "GUIDE_ROOT" in env_vars

    @patch.dict(os.environ, {}, clear=True)
    def test_is_doing(self) -> None:
        """環境変数が不足している場合に警告が発生することを確認"""
        # Given: 環境診断コマンド(環境変数なし)
        command = EnvironmentDiagnosticCommand(quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: 警告ステータスになる
        assert result.status == "WARNING"
        assert len(result.messages) >= 2  # PROJECT_ROOT、GUIDE_ROOTの警告

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-GET_NAME")
    def test_get_name(self) -> None:
        """コマンド名が正しく返されることを確認"""
        # Given: 環境診断コマンド
        command = EnvironmentDiagnosticCommand()

        # When: 名前を取得
        name = command.get_name()

        # Then: 期待される名前が返される
        assert name == "environment"


class TestDependencyDiagnosticCommand:
    """依存関係診断コマンドのテスト"""

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-REQUIRED_PACKAGES")
    def test_required_packages_detection(self) -> None:
        """必須パッケージの検出が正しく動作することを確認"""
        # Given: 依存関係診断コマンド
        command = DependencyDiagnosticCommand(quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: 必須パッケージがチェックされる
        assert "required_packages" in result.details
        assert "optional_packages" in result.details

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-OPTIONAL_PACKAGES")
    def test_optional_packages_detection(self) -> None:
        """オプションパッケージの検出が正しく動作することを確認"""
        # Given: 依存関係診断コマンド
        command = DependencyDiagnosticCommand(quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: オプションパッケージがチェックされる
        optional_packages = result.details["optional_packages"]
        assert "beautifulsoup4" in optional_packages
        assert "lxml" in optional_packages

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-GET_NAME")
    def test_get_name(self) -> None:
        """コマンド名が正しく返されることを確認"""
        # Given: 依存関係診断コマンド
        command = DependencyDiagnosticCommand()

        # When: 名前を取得
        name = command.get_name()

        # Then: 期待される名前が返される
        assert name == "dependencies"


class TestProjectStructureDiagnosticCommand:
    """プロジェクト構造診断コマンドのテスト"""

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-NON_EXISTENT_PROJECT")
    def test_non_existent_project(self) -> None:
        """プロジェクトが存在しない場合の処理を確認"""
        # Given: 存在しないプロジェクトルート
        non_existent_path = Path("/non/existent/path")
        command = ProjectStructureDiagnosticCommand(non_existent_path, quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: 警告ステータスになる
        assert result.status == "WARNING"
        assert "プロジェクトが見つかりません" in result.messages

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-VALID_PROJECT")
    def test_valid_project_root(self) -> None:
        """プロジェクトルートが正常な場合の処理を確認"""
        # Given: 現在のディレクトリをプロジェクトルートとする
        current_path = Path.cwd()
        command = ProjectStructureDiagnosticCommand(current_path, quiet=True)

        # When: 診断を実行
        result = command.execute()

        # Then: プロジェクトルートが設定される
        assert "project_root" in result.details
        assert result.details["project_root"] == str(current_path)

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-GET_NAME")
    def test_get_name(self) -> None:
        """コマンド名が正しく返されることを確認"""
        # Given: プロジェクト構造診断コマンド
        command = ProjectStructureDiagnosticCommand(Path.cwd())

        # When: 名前を取得
        name = command.get_name()

        # Then: 期待される名前が返される
        assert name == "project_structure"


class TestSystemDiagnosticsService:
    """システム診断サービスのテスト"""

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-SERVICE_EXECUTION")
    def test_service_command_execution(self) -> None:
        """コマンドの追加と実行が正しく動作することを確認"""
        # Given: システム診断サービス
        service = SystemDiagnosticsService()
        mock_command = Mock()
        mock_command.get_name.return_value = "test_command"
        mock_command.execute.return_value = DiagnosticResult(status="OK", details={"test": "result"}, messages=[])

        # When: コマンドを追加して実行
        service.add_command(mock_command)
        results = service.execute_all()

        # Then: コマンドが実行される
        assert "test_command" in results
        assert results["test_command"].status == "OK"
        mock_command.execute.assert_called_once()

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-UNNAMED")
    def test_unnamed(self) -> None:
        """複数のコマンドが正しく実行されることを確認"""
        # Given: システム診断サービスと複数のコマンド
        service = SystemDiagnosticsService()

        # 実際のコマンドを使用
        env_command = EnvironmentDiagnosticCommand(quiet=True)
        dep_command = DependencyDiagnosticCommand(quiet=True)

        service.add_command(env_command)
        service.add_command(dep_command)

        # When: すべてのコマンドを実行
        results = service.execute_all()

        # Then: すべてのコマンドの結果が返される
        assert "environment" in results
        assert "dependencies" in results
        assert len(results) == 2

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-UNNAMED")
    def test_basic_functionality(self) -> None:
        """全体ステータスの決定が正しく動作することを確認"""
        # Given: システム診断サービス
        service = SystemDiagnosticsService()

        # 異なるステータスの結果
        results = {
            "test1": DiagnosticResult(status="OK", details={}, messages=[]),
            "test2": DiagnosticResult(status="WARNING", details={}, messages=[]),
            "test3": DiagnosticResult(status="ERROR", details={}, messages=[]),
        }

        # When: 全体ステータスを決定
        overall_status = service.determine_overall_status(results)

        # Then: 最も深刻なステータスが返される
        assert overall_status == "ERROR"

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-UNNAMED")
    def test_edge_cases(self) -> None:
        """警告のみの場合のステータス決定を確認"""
        # Given: システム診断サービス
        service = SystemDiagnosticsService()

        results = {
            "test1": DiagnosticResult(status="OK", details={}, messages=[]),
            "test2": DiagnosticResult(status="WARNING", details={}, messages=[]),
        }

        # When: 全体ステータスを決定
        overall_status = service.determine_overall_status(results)

        # Then: WARNING が返される
        assert overall_status == "WARNING"

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-UNNAMED")
    def test_error_handling(self) -> None:
        """すべて正常な場合のステータス決定を確認"""
        # Given: システム診断サービス
        service = SystemDiagnosticsService()

        results = {
            "test1": DiagnosticResult(status="OK", details={}, messages=[]),
            "test2": DiagnosticResult(status="OK", details={}, messages=[]),
        }

        # When: 全体ステータスを決定
        overall_status = service.determine_overall_status(results)

        # Then: OK が返される
        assert overall_status == "OK"

    @pytest.mark.spec("SPEC-SYSTEM_DIAGNOSTICS-UNNAMED")
    def test_validation(self) -> None:
        """コマンド実行時のエラーが適切に処理されることを確認"""
        # Given: エラーを発生させるモックコマンド
        service = SystemDiagnosticsService()
        mock_command = Mock()
        mock_command.get_name.return_value = "error_command"
        mock_command.execute.side_effect = Exception("テストエラー")

        # When: コマンドを追加して実行
        service.add_command(mock_command)
        results = service.execute_all()

        # Then: エラーが適切に処理される
        assert "error_command" in results
        assert results["error_command"].status == "ERROR"
        assert "テストエラー" in results["error_command"].messages[0]
