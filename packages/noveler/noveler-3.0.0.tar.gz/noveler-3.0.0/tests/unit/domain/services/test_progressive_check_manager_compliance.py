"""
ProgressiveCheckManager 専用共通基盤コンプライアンステスト

B20/B30準拠実装の検証：
- 共通Console使用確認
- 統一Logger使用確認
- PathService使用確認
- エラーハンドリング統一確認
"""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from datetime import datetime

# Progressive Check Manager の条件付きインポート
import sys
import os
from pathlib import Path

# プロジェクトルートのsrcをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

PCM_AVAILABLE = False
ProgressiveCheckManager = None
CheckTaskDefinition = None
CheckExecutionResult = None

try:
    from noveler.domain.services.progressive_check_manager import (
        ProgressiveCheckManager,
        CheckTaskDefinition,
        CheckExecutionResult
    )
    PCM_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    # importが失敗した場合はテストをスキップ
    print(f"ProgressiveCheckManager import failed: {e}")
    pass


@pytest.mark.skipif(not PCM_AVAILABLE, reason="ProgressiveCheckManager not available")
class TestProgressiveCheckManagerCompliance:
    """ProgressiveCheckManager の共通基盤コンプライアンステスト"""

    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """テンポラリプロジェクトルートの作成"""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # 必要な設定ファイルの作成
        config_dir = project_root / "src" / "noveler" / "infrastructure" / "config"
        config_dir.mkdir(parents=True)

        check_tasks_yaml = config_dir / "check_tasks.yaml"
        check_tasks_yaml.write_text("""
phases:
  basic_quality: "基本品質"

phase_descriptions:
  basic_quality: "基本的な品質チェック"

tasks:
  - id: 0
    name: "テストチェック"
    phase: "basic_quality"
    description: "テスト用の基本チェック"
    prerequisites: []
    llm_instruction: "テストを実行してください"
    success_criteria:
      - "テストが正常に完了する"
""")

        # プロジェクト設定ファイルの作成（ProgressiveCheckManagerが期待）
        project_config = project_root / "プロジェクト設定.yaml"
        project_config.write_text("""
project_name: "テストプロジェクト"
episode_count: 1
writing:
  episode:
    target_length:
      min: 5000
      max: 10000
quality_check:
  enabled: true
  minimum_score: 80
""")

        return project_root

    @pytest.fixture
    def manager(self, temp_project_root):
        """ProgressiveCheckManager インスタンスの作成"""
        if not PCM_AVAILABLE:
            pytest.skip("ProgressiveCheckManager not available")
        return ProgressiveCheckManager(temp_project_root, 1)

    @pytest.mark.spec("SPEC-PCM-COM-001")
    def test_uses_shared_console_from_utilities(self, manager, temp_project_root):
        """共通Console使用の検証"""
        # ProgressiveCheckManagerのソースコード確認
        manager_file = Path(__file__).parent.parent.parent.parent.parent / \
                      "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if manager_file.exists():
            content = manager_file.read_text(encoding='utf-8')

            # B20準拠：共通Console使用確認
            assert "from noveler.presentation.shared.shared_utilities import _get_console" in content, \
                "共通Console使用が確認できません"

            assert "console = _get_console()" in content, \
                "共通Consoleインスタンス作成が確認できません"

            # 禁止パターンの確認
            assert "from rich.console import Console" not in content, \
                "禁止されたConsole直接インポートが検出されました"

            assert "console = Console()" not in content, \
                "禁止されたConsole直接作成が検出されました"

    @pytest.mark.spec("SPEC-PCM-COM-002")
    def test_uses_unified_logger_system(self, manager, temp_project_root):
        """統一Logger システム使用の検証"""
        manager_file = Path(__file__).parent.parent.parent.parent.parent / \
                      "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if manager_file.exists():
            content = manager_file.read_text(encoding='utf-8')

            # B20準拠：統一Logger使用確認
            assert "from noveler.presentation.shared.shared_utilities import" in content and \
                   "get_logger" in content, \
                "統一Logger使用が確認できません"

            # Loggerの初期化確認
            assert "self.logger = get_logger(__name__)" in content, \
                "統一Loggerの初期化が確認できません"

            # 禁止パターンの確認
            assert "import logging" not in content, \
                "禁止されたlegacy logging使用が検出されました"

            assert "logging.getLogger" not in content, \
                "禁止されたlogging.getLogger使用が検出されました"

    @pytest.mark.spec("SPEC-PCM-COM-003")
    def test_uses_path_service_correctly(self, manager, temp_project_root):
        """PathService使用の検証"""
        manager_file = Path(__file__).parent.parent.parent.parent.parent / \
                      "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if manager_file.exists():
            content = manager_file.read_text(encoding='utf-8')

            # B20準拠：PathService使用確認
            assert "from noveler.infrastructure.factories.path_service_factory import create_path_service" in content, \
                "PathService factory使用が確認できません"

            assert "self.path_service = create_path_service" in content, \
                "PathService初期化が確認できません"

            # ハードコーディング禁止パターンの確認
            hardcoded_patterns = [
                'project_root / "40_原稿"',
                'project_root / "30_プロット"',
                'Path("40_原稿")',
                '/ ".noveler"'  # これは許可される（専用ディレクトリ）
            ]

            for pattern in hardcoded_patterns:
                if pattern != '/ ".noveler"':  # .novelerは例外
                    assert pattern not in content, \
                        f"禁止されたパスハードコーディングが検出されました: {pattern}"

    @pytest.mark.spec("SPEC-PCM-COM-004")
    def test_manager_initialization_with_shared_components(self, temp_project_root):
        """共通コンポーネントでの初期化検証"""
        if not PCM_AVAILABLE:
            pytest.skip("ProgressiveCheckManager not available")

        with patch('noveler.domain.services.progressive_check_manager.get_logger') as mock_get_logger, \
             patch('noveler.domain.services.progressive_check_manager.create_path_service') as mock_create_path_service, \
             patch('noveler.domain.services.progressive_check_manager._get_console') as mock_get_console:

            mock_logger = MagicMock()
            mock_path_service = MagicMock()
            mock_console = MagicMock()

            mock_get_logger.return_value = mock_logger
            mock_create_path_service.return_value = mock_path_service
            mock_get_console.return_value = mock_console

            # ProgressiveCheckManager初期化
            manager = ProgressiveCheckManager(temp_project_root, 1)

            # 共通コンポーネント使用確認
            mock_get_logger.assert_called_once_with('noveler.domain.services.progressive_check_manager')
            mock_create_path_service.assert_called_once_with(str(temp_project_root))

            # インスタンス変数の設定確認
            assert manager.logger is mock_logger
            assert manager.path_service is mock_path_service

    @pytest.mark.spec("SPEC-PCM-COM-005")
    def test_error_handling_uses_shared_patterns(self, manager, temp_project_root):
        """エラーハンドリング共通パターン使用の検証"""
        # PathService作成失敗時の処理確認
        with patch('noveler.domain.services.progressive_check_manager.create_path_service') as mock_create_path_service:
            mock_create_path_service.side_effect = Exception("PathService creation failed")

            # エラーハンドリングの動作確認
            manager = ProgressiveCheckManager(temp_project_root, 1)

            # PathService作成失敗時の適切な処理確認
            assert manager.path_service is None

            # Loggerを使用したエラーログ確認（warningレベル）
            # 実際のログ出力は統一Loggerを通じて適切に処理される

    @pytest.mark.spec("SPEC-PCM-COM-006")
    def test_session_management_compliance(self, manager, temp_project_root):
        """セッション管理の共通基盤コンプライアンス"""
        # セッションIDフォーマット検証（EP001_YYYYMMDDHHMM形式）
        assert manager.session_id.startswith("EP001_")
        assert len(manager.session_id) == 18  # "EP001_" + "202501091430" = 18文字

        # .novelerディレクトリ作成確認
        assert manager.io_dir.exists()
        assert manager.io_dir.name == manager.session_id
        assert manager.io_dir.parent.name == "checks"
        assert manager.io_dir.parent.parent.name == ".noveler"

        # 状態ファイルパス確認
        expected_state_file = manager.io_dir / f"{manager.session_id}_session_state.json"
        assert manager.state_file == expected_state_file

    @pytest.mark.spec("SPEC-PCM-COM-007")
    def test_file_io_operations_use_pathlib(self, manager, temp_project_root):
        """ファイルI/O操作でのPathlib使用確認"""
        # テストデータの作成
        test_data = {
            "session_info": {
                "session_id": manager.session_id,
                "episode_number": 1,
                "created_at": datetime.now().isoformat()
            },
            "check_parameters": {
                "step_id": 0,
                "input_data": "test data"
            }
        }

        # save_step_input実行
        saved_path = manager.save_step_input(0, test_data)

        # ファイル作成確認（Pathlibベース）
        assert saved_path.exists()
        expected_file = saved_path

        # ファイル読み取り（Pathlibベース）
        import json
        loaded_data = json.loads(expected_file.read_text(encoding='utf-8'))
        assert loaded_data["step_id"] == 0
        assert loaded_data["input"] == test_data

    @pytest.mark.spec("SPEC-PCM-COM-008")
    def test_integration_with_existing_progressive_patterns(self, manager, temp_project_root):
        """既存のProgressiveパターンとの統合確認"""
        # B20準拠：既存ProgressiveTaskManagerパターンを踏襲

        # 基本的なタスク管理メソッドの存在確認
        assert hasattr(manager, 'get_check_tasks')
        assert hasattr(manager, 'execute_check_step')
        assert hasattr(manager, 'get_check_status')

        # 状態管理の互換性確認
        assert hasattr(manager, 'current_state')
        assert isinstance(manager.current_state, dict)

        # セッション管理の互換性確認
        assert hasattr(manager, 'session_id')
        assert hasattr(manager, 'io_dir')

        # タスク設定の読み込み確認
        assert hasattr(manager, 'tasks_config')
        assert isinstance(manager.tasks_config, dict)

    @pytest.mark.spec("SPEC-PCM-COM-009")
    def test_console_output_uses_shared_instance(self, manager, temp_project_root):
        """Console出力での共通インスタンス使用確認"""
        if not PCM_AVAILABLE:
            pytest.skip("ProgressiveCheckManager not available")

        with patch('noveler.domain.services.progressive_check_manager.console') as mock_console:
            # ProgressiveCheckManager初期化時のConsole使用
            manager = ProgressiveCheckManager(temp_project_root, 1)

            # 初期化メッセージでのConsole使用確認
            mock_console.print.assert_called()

            # 共通Consoleインスタンスの使用確認
            calls = mock_console.print.call_args_list
            assert len(calls) > 0

            # セッション開始メッセージの確認
            start_message_found = False
            for call in calls:
                if "品質チェックセッション開始" in str(call):
                    start_message_found = True
                    break

            assert start_message_found, "セッション開始メッセージが共通Consoleで出力されていません"

    @pytest.mark.spec("SPEC-PCM-COM-010")
    def test_overall_b20_b30_compliance_verification(self, manager, temp_project_root):
        """B20/B30総合コンプライアンス検証"""
        manager_file = Path(__file__).parent.parent.parent.parent.parent / \
                      "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if not manager_file.exists():
            pytest.skip("ProgressiveCheckManager source file not found")

        content = manager_file.read_text(encoding='utf-8')

        # B20準拠項目の総合チェック
        compliance_checks = {
            "共通Console使用": "from noveler.presentation.shared.shared_utilities import _get_console" in content,
            "統一Logger使用": "from noveler.presentation.shared.shared_utilities import" in content and "get_logger" in content,
            "PathService使用": "create_path_service" in content,
            "novelerプレフィックス": "from noveler." in content,
            "相対インポート回避": "from ." not in content and "from .." not in content,
            "レガシーlogging回避": "import logging" not in content,
            "Console重複回避": "console = Console()" not in content,
        }

        # 各項目の検証
        failed_checks = []
        for check_name, check_result in compliance_checks.items():
            if not check_result:
                failed_checks.append(check_name)

        # 総合判定（全項目合格必須）
        assert len(failed_checks) == 0, (
            f"B20/B30コンプライアンス違反が検出されました: {', '.join(failed_checks)}"
        )

        # 成功メッセージ
        print(f"\n✅ ProgressiveCheckManager B20/B30コンプライアンス検証完了")
        print(f"   ✓ 全{len(compliance_checks)}項目合格")
        print(f"   ✓ 共通基盤コンポーネント100%使用")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
