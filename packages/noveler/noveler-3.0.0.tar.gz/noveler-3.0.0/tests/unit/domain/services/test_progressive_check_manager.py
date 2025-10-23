#!/usr/bin/env python3
"""段階的品質チェック管理サービスのテスト

ProgressiveCheckManagerの段階的実行機能をテスト。
B20準拠: 既存実装パターンを活用したテスト設計。

仕様書: SPEC-QUALITY-110_progressive_check_flow
"""

import json
import pytest
from datetime import datetime
from typing import Any
from pathlib import Path
from unittest.mock import Mock, patch, create_autospec
from tempfile import TemporaryDirectory

from noveler.domain.services.progressive_check_manager import (
    ProgressiveCheckManager,
    CheckTaskDefinition,
    CheckExecutionResult,
    ProjectConfigError
)
from noveler.domain.services.workflow_state_store import SessionContext
from noveler.domain.value_objects.universal_prompt_execution import (
    PromptType,
    UniversalPromptRequest,
    UniversalPromptResponse,
)


class TestProgressiveCheckManager:
    """段階的品質チェック管理サービスのテスト"""

    def test_initialization_without_project_config_raises(self, temp_project_root):
        """プロジェクト設定ファイルが無い場合はQC-009で中断する"""
        config_path = temp_project_root / "プロジェクト設定.yaml"
        config_path.unlink()

        with pytest.raises(ProjectConfigError) as exc_info:
            ProgressiveCheckManager(temp_project_root, episode_number=1)

        err = exc_info.value
        assert getattr(err, "code", None) == "QC-009"

    def test_initialization_with_invalid_project_config_raises(self, temp_project_root):
        """target_lengthが不正な場合はQC-010で中断する"""
        config_path = temp_project_root / "プロジェクト設定.yaml"
        invalid_yaml = '\n'.join([
            "writing:",
            "  episode:",
            "    target_length:",
            "      min: 5000",
        ]) + '\n'
        config_path.write_text(invalid_yaml, encoding="utf-8")

        with pytest.raises(ProjectConfigError) as exc_info:
            ProgressiveCheckManager(temp_project_root, episode_number=1)

        err = exc_info.value
        assert getattr(err, "code", None) == "QC-010"

    def test_execute_step_with_target_length_override(self, temp_project_root):
        """config_overrides.target_lengthで上書きできる"""
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        overrides = {
            "config_overrides": {"target_length": {"min": 5000, "max": 8000}},
            "manuscript_content": "テスト原稿",
        }
        result = manager.execute_check_step(1, overrides, dry_run=True)

        metadata = result["execution_result"].get("metadata", {})
        snapshot = metadata.get("config_snapshot", {})
        target = snapshot.get("target_length", {})
        assert target.get("min") == 5000
        assert target.get("max") == 8000
        assert target.get("source") == "override"

    def test_execute_step_records_workflow_state(self, temp_project_root):
        """ステートストアへの記録が常時有効であることを検証する"""

        captured: dict[str, Any] = {}

        class DummyStore:
            def __init__(self) -> None:
                self.sessions: list[tuple[int, Any]] = []
                self.step_records: list[Any] = []
                self.committed = False
                self.rolled_back = False

            def begin_session(self, episode_number: int, iteration_policy: Any) -> SessionContext:  # type: ignore[override]
                self.sessions.append((episode_number, iteration_policy))
                session_dir = temp_project_root / ".noveler" / "checks" / "dummy" / "workflow"
                session_dir.mkdir(parents=True, exist_ok=True)
                lock_path = session_dir / "session.lock"
                lock_path.write_text("held", encoding="utf-8")
                session_path = session_dir / "session.json"
                session_path.write_text("{}", encoding="utf-8")
                return SessionContext(
                    session_id="dummy",
                    episode_number=episode_number,
                    state_version=1,
                    session_path=session_path,
                    lock_path=lock_path,
                )

            def record_step_execution(self, payload):  # type: ignore[override]
                self.step_records.append(payload)

            def record_issue(self, issue):  # type: ignore[override]
                captured.setdefault("issues", []).append(issue)

            def record_issue_resolution(self, resolution):  # type: ignore[override]
                captured.setdefault("resolutions", []).append(resolution)

            def append_fetch_log(self, log):  # type: ignore[override]
                captured.setdefault("fetch", []).append(log)

            def commit(self) -> None:
                self.committed = True

            def rollback(self) -> None:
                self.rolled_back = True

        def fake_factory(project_root: Path, episode_number: int, session_id: str | None) -> DummyStore:
            store = DummyStore()
            captured["store"] = store
            return store

        from noveler.domain.services import progressive_check_manager as pcm_module

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(pcm_module, "create_workflow_state_store", fake_factory)
        try:
            manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

            result = manager.execute_check_step(1, {"manuscript_content": "dummy"}, dry_run=True)

            assert result["success"] is True
            store: DummyStore = captured["store"]
            assert store.step_records, "ステップ実行がstate storeへ記録されていません"
            payload = store.step_records[-1]
            assert payload.step_id == 1
            assert store.committed is True
        finally:
            monkeypatch.undo()

    @pytest.fixture
    def temp_project_root(self):
        """テスト用一時プロジェクトディレクトリ"""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # manuscriptsディレクトリ作成
            manuscripts_dir = project_root / "manuscripts"
            manuscripts_dir.mkdir(parents=True, exist_ok=True)

            # テスト用原稿ファイル作成
            test_manuscript = manuscripts_dir / "episode_001.md"
            test_manuscript.write_text("テスト原稿内容です。これは品質チェック用のサンプルテキストです。", encoding="utf-8")

            # check_tasks.yamlをテスト環境にコピー
            config_dir = project_root / "src" / "noveler" / "infrastructure" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            # 実際の設定ファイルからコピー
            import shutil
            actual_config = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/src/noveler/infrastructure/config/check_tasks.yaml")
            if actual_config.exists():
                shutil.copy2(actual_config, config_dir / "check_tasks.yaml")

            project_config = project_root / "プロジェクト設定.yaml"
            default_config = '\n'.join([
                'writing:',
                '  episode:',
                '    target_length:',
                '      min: 6000',
                '      max: 10000',
            ]) + '\n'
            project_config.write_text(default_config, encoding='utf-8')

            yield project_root

    # Mocking fixtures removed as they reference non-existent imports

    def test_manager_initialization(self, temp_project_root):
        """ProgressiveCheckManagerの初期化テスト"""
        # Act
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Assert
        assert manager.project_root == temp_project_root
        assert manager.episode_number == 1
        assert manager.state_file.name.endswith("_session_state.json")
        assert manager.state_file.name.startswith("EP001_")
        assert manager.current_state["episode_number"] == 1
        assert manager.current_state["overall_status"] == "not_started"

        # 状態管理ファイルディレクトリの確認
        assert manager.state_file.parent.name == manager.session_id
        assert manager.state_file.parent.parent == temp_project_root / ".noveler" / "checks"
        assert manager.state_file.parent.parent.parent == temp_project_root / ".noveler"
        assert manager.state_file.exists()

    def test_start_session_creates_manifest(self, temp_project_root):
        """start_sessionでセッションIDとマニフェストが初期化されることを検証"""
        session_info = ProgressiveCheckManager.start_session(temp_project_root, episode_number=1)

        assert session_info["success"] is True
        session_id = session_info["session_id"]
        manifest_path = Path(temp_project_root) / ".noveler" / "checks" / session_id / "manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["session_id"] == session_id
        assert manifest["episode_number"] == 1
        assert manifest["current_step"] == 1
        template_meta = manifest["template_version_set"].get("1")
        assert template_meta is not None
        assert template_meta["path"].endswith("check_step01_typo_check.yaml")

        resumed = ProgressiveCheckManager(
            temp_project_root,
            episode_number=1,
            session_id=session_id,
            resume=True,
        )
        assert resumed.session_id == session_id
        assert resumed.current_state["current_step"] == 1


    def test_state_file_creation(self, temp_project_root):
        """状態ファイルの作成テスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=2)

        # Act
        # 初期化時に状態ファイルが作成される

        # Assert
        assert manager.state_file.exists()
        assert manager.state_file.is_file()

        # 正しい階層構造の確認
        expected_dir = temp_project_root / ".noveler" / "checks" / manager.session_id
        assert manager.state_file.parent == expected_dir
        assert manager.state_file.name == f"{manager.session_id}_session_state.json"

    def test_load_check_tasks(self, temp_project_root):
        """チェックタスク定義の読み込みテスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act
        tasks = manager.tasks_config["tasks"]

        # Assert
        assert isinstance(tasks, list)
        assert len(tasks) == 12  # check_tasks.yamlで定義された12ステップ

        # 最初のタスクの検証
        first_task = tasks[0]
        assert first_task["id"] == 1
        assert first_task["name"] == "誤字脱字チェック"
        assert first_task["phase"] == "basic_quality"
        assert "llm_instruction" in first_task

    def test_get_task_by_id(self, temp_project_root):
        """ID指定によるタスク取得テスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act
        task = manager._get_task_by_id(manager.tasks_config["tasks"], 1)

        # Assert
        assert task is not None
        assert task["id"] == 1
        assert task["name"] == "誤字脱字チェック"

        # 存在しないIDの場合
        non_existent_task = manager._get_task_by_id(manager.tasks_config["tasks"], 999)
        assert non_existent_task is None

    def test_step_by_step_execution(self, temp_project_root):
        """ステップバイステップ実行のテスト（メイン機能）"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # テスト用の段階的実行
        step_results = []

        # Act: ステップ1-3を順次実行
        for step_id in range(1, 4):  # 基本品質フェーズ（ステップ1-3）
            result = manager.execute_check_step(step_id, {
                "manuscript_content": "テスト原稿",
                "check_focus": "basic_quality"
            }, dry_run=True)

            step_results.append(result)

        # Assert
        assert len(step_results) == 3

        # 各ステップの結果検証
        for i, result in enumerate(step_results, 1):
            assert isinstance(result, dict)
            assert result["step_id"] == i
            assert result["success"] is True
            assert "execution_result" in result
            assert "next_task" in result

        # 進捗状況確認
        status = manager.get_check_status()
        assert len(manager.tasks_config["tasks"]) == 12
        assert len(manager.current_state["completed_steps"]) == 3
        assert manager.current_state["overall_status"] == "in_progress"

    def test_execute_check_step_with_iteration_policy(self, temp_project_root):
        """IterationPolicyを指定したチェックステップ実行を検証"""
        session_info = ProgressiveCheckManager.start_session(temp_project_root, episode_number=1)
        manager = ProgressiveCheckManager(
            temp_project_root,
            episode_number=1,
            session_id=session_info["session_id"],
            resume=True,
        )

        policy = {"count": 2, "until_pass": False, "dry_run": True}
        result = manager.execute_check_step(
            1,
            {"iteration_test": True},
            dry_run=False,
            iteration_policy=policy,
        )

        iteration_meta = result.get("iteration")
        assert iteration_meta is not None
        assert iteration_meta["attempts"] == 2
        assert iteration_meta["stopped_reason"] == "count_limit"
        execution_metadata = result["execution_result"]["metadata"]["iteration"]
        assert execution_metadata["policy"]["count"] == 2
        assert execution_metadata["attempts"] == 2

    def test_repeat_step_updates_manifest(self, temp_project_root):
        """repeat_stepがマニフェストの履歴を更新することを検証"""
        session_info = ProgressiveCheckManager.start_session(temp_project_root, episode_number=1)
        session_id = session_info["session_id"]
        manager = ProgressiveCheckManager(
            temp_project_root,
            episode_number=1,
            session_id=session_id,
            resume=True,
        )

        manager.execute_check_step(
            1,
            {"initial_run": True},
            dry_run=False,
            iteration_policy={"count": 1, "dry_run": True},
        )

        repeat_result = manager.repeat_step(
            1,
            iteration_policy={"count": 2, "dry_run": True},
            input_data={"repeat": True},
        )

        assert repeat_result["success"] is True
        assert repeat_result["attempts"] == 2
        assert repeat_result["stopped_reason"] == "count_limit"

        manifest_path = Path(temp_project_root) / ".noveler" / "checks" / session_id / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        completed = manifest.get("completed_steps", [])
        assert any(item.get("step_id") == 1 and item.get("attempts", 0) >= 3 for item in completed)


    def test_basic_execution(self, temp_project_root):
        """基本的な実行テスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act
        result = manager.execute_check_step(1, {
            "manuscript_path": "manuscripts/episode_001.md",
            "check_parameters": {"focus": "basic_typo"}
        }, dry_run=True)

        # Assert
        assert result["success"] is True
        assert result["step_id"] == 1
        assert "execution_result" in result
        assert "next_task" in result

        # 状態ファイルが更新されていることを確認
        assert 1 in manager.current_state["completed_steps"]
        assert manager.current_state["overall_status"] == "in_progress"

    def test_state_management(self, temp_project_root):
        """状態管理のテスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act: 複数ステップを実行して状態を更新
        manager.execute_check_step(1, {"test": "data1"}, dry_run=True)
        manager.execute_check_step(2, {"test": "data2"}, dry_run=True)

        # Assert
        status = manager.get_check_status()

        assert status["episode_number"] == 1
        assert len(manager.current_state["completed_steps"]) == 2
        assert manager.current_state["current_step"] == 3  # 次のステップに進んでいる

        # 状態ファイルが保存されていることを確認
        assert manager.state_file.exists()

    def test_execute_check_step_invokes_llm(self, temp_project_root):
        '''LLM統合経路が呼び出され、レスポンスが結果に反映されることを検証。'''

        class DummyUseCase:
            def __init__(self) -> None:
                self.requests: list[UniversalPromptRequest] = []

            async def execute_with_fallback(
                self, request: UniversalPromptRequest, fallback_enabled: bool = True
            ) -> UniversalPromptResponse:
                self.requests.append(request)
                payload = {
                    'summary': {
                        'overview': '主要な誤字脱字は見当たりませんでした。',
                        'score': 88,
                        'evidence': ['チェック実行']
                    },
                    'issues': {'typos': []},
                    'recommendations': ['最終確認を実施してください'],
                    'metrics': {'score': 88, 'issue_count': 0},
                }
                return UniversalPromptResponse(
                    success=True,
                    response_content=json.dumps(payload, ensure_ascii=False),
                    extracted_data=payload,
                    prompt_type=PromptType.QUALITY_CHECK,
                    execution_time_ms=123.0,
                )

        dummy_factory = DummyUseCase()
        manager = ProgressiveCheckManager(
            temp_project_root,
            episode_number=1,
            llm_use_case_factory=lambda: dummy_factory,
        )

        result = manager.execute_check_step(
            1, {'manuscript_content': 'これはテスト原稿です。'}, dry_run=False
        )

        assert result['success'] is True
        execution = result['execution_result']
        assert execution['metadata']['llm_used'] is True
        assert 'fallback_reason' not in execution['metadata']
        assert execution['overall_score'] == 88
        assert dummy_factory.requests, 'LLMユースケースが呼び出されていません'
        request = dummy_factory.requests[0]
        assert request.prompt_type == PromptType.QUALITY_CHECK

    def test_execute_check_step_fallback_on_error(self, temp_project_root):
        '''LLM実行が失敗した場合、フォールバック結果が返ることを検証。'''

        class FailingUseCase:
            async def execute_with_fallback(
                self, request: UniversalPromptRequest, fallback_enabled: bool = True
            ) -> UniversalPromptResponse:
                raise RuntimeError('forced failure')

        manager = ProgressiveCheckManager(
            temp_project_root,
            episode_number=1,
            llm_use_case_factory=lambda: FailingUseCase(),
        )

        result = manager.execute_check_step(
            1, {'manuscript_content': 'これはテスト原稿です。'}, dry_run=False
        )
        assert result['success'] is True
        execution = result['execution_result']
        metadata = execution['metadata']
        assert metadata['llm_used'] is False
        assert metadata.get('fallback_reason') == 'forced failure'
        assert execution['step_name'] == '誤字脱字チェック'
        assert execution['overall_score'] is not None

    def test_phase_based_execution(self, temp_project_root):
        """フェーズ別実行のテスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act: 基本品質フェーズ（ステップ1-3）を完了
        for step_id in range(1, 4):
            manager.execute_check_step(step_id, {"phase_test": True}, dry_run=True)

        status = manager.get_check_status()

        # Assert - ステップ1-3完了後、次のステップ4に進む
        current_task = status["current_task"]
        if current_task:
            assert current_task["id"] == 4  # 次のステップは4
        assert len(manager.current_state["completed_steps"]) == 3

        # 次のステップを実行
        manager.execute_check_step(4, {"phase_test": True}, dry_run=True)
        updated_status = manager.get_check_status()

        assert len(manager.current_state["completed_steps"]) == 4

    def test_error_handling_during_execution(self, temp_project_root):
        """実行中のエラー処理テスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act: 無効なステップIDでの実行
        result = manager.execute_check_step(999, {"invalid": True})

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "999" in result["error"]  # ステップIDが含まれることを確認

    def test_dry_run_execution(self, temp_project_root):
        """ドライラン実行のテスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act
        result = manager.execute_check_step(1, {"test": "dry_run"}, dry_run=True)

        # Assert
        assert result["success"] is True
        assert "execution_result" in result
        assert result["execution_result"]["dry_run"] is True

        # ドライランでは実際のファイル変更は発生しない
        manuscript_path = manager.project_root / "manuscripts" / "episode_001.md"
        original_content = manuscript_path.read_text(encoding="utf-8")

        # 原稿内容が変更されていないことを確認
        assert "テスト原稿内容です" in original_content

    def test_execution_history_tracking(self, temp_project_root):
        """実行履歴追跡のテスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act: 複数ステップを実行
        execution_results = []
        for step_id in range(1, 4):
            result = manager.execute_check_step(step_id, {"history_test": step_id}, dry_run=True)
            execution_results.append(result)

        # 履歴取得
        history = manager.get_check_history()

        # Assert
        assert len(history) == 3

        for i, record in enumerate(history):
            expected_step_id = i + 1
            assert record["step_id"] == expected_step_id
            assert record["status"] == "completed"
            assert "timestamp" in record

    def test_recovery_from_interruption(self, temp_project_root):
        """中断からの復旧テスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # 最初のセッションで一部ステップを実行
        manager.execute_check_step(1, {"recovery_test": True}, dry_run=True)
        manager.execute_check_step(2, {"recovery_test": True}, dry_run=True)

        # 新しいマネージャーインスタンス（中断後の復旧シミュレーション）
        recovery_manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act: 既存状態から継続（状態ファイルが自動で読み込まれる）
        # 継続実行
        result = recovery_manager.execute_check_step(3, {"recovery_test": True}, dry_run=True)

        # Assert
        assert result["success"] is True
        status = recovery_manager.get_check_status()
        assert len(recovery_manager.current_state["completed_steps"]) == 3


class TestCheckTaskDefinition:
    """チェックタスク定義のテスト"""

    def test_task_definition_parsing(self):
        """タスク定義の解析テスト"""
        # Arrange
        task_data = {
            "id": 1,
            "name": "誤字脱字チェック",
            "phase": "basic_quality",
            "description": "基本的な誤字脱字の検出",
            "prerequisites": [],
            "llm_instruction": "誤字脱字をチェックしてください",
            "success_criteria": ["誤字が0個", "脱字が0個"]
        }

        # Act
        task_def = CheckTaskDefinition.from_dict(task_data)

        # Assert
        assert task_def.id == 1
        assert task_def.name == "誤字脱字チェック"
        assert task_def.phase == "basic_quality"
        assert len(task_def.success_criteria) == 2


class TestCheckExecutionResult:
    """チェック実行結果のテスト"""

    def test_execution_result_creation(self):
        """実行結果作成のテスト"""
        # Act
        result = CheckExecutionResult(
            step_id=1,
            success=True,
            execution_time=2.5,
            issues_found=3,
            quality_score=85.0,
            next_step=2
        )

        # Assert
        assert result.step_id == 1
        assert result.success is True
        assert result.execution_time == 2.5
        assert result.issues_found == 3
        assert result.quality_score == 85.0
        assert result.next_step == 2

    def test_execution_result_serialization(self):
        """実行結果のシリアライゼーションテスト"""
        # Arrange
        result = CheckExecutionResult(
            step_id=1,
            success=True,
            execution_time=2.5,
            issues_found=3,
            quality_score=85.0,
            corrections=["修正1", "修正2"],
            next_step=2
        )

        # Act
        serialized = result.to_dict()

        # Assert
        assert serialized["step_id"] == 1
        assert serialized["success"] is True
        assert serialized["execution_time"] == 2.5
        assert len(serialized["corrections"]) == 2


@pytest.mark.integration
class TestProgressiveCheckIntegration:
    """段階的品質チェックの統合テスト"""

    @pytest.fixture
    def temp_project_root(self):
        """テスト用一時プロジェクトディレクトリ（統合テスト用）"""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # manuscriptsディレクトリ作成
            manuscripts_dir = project_root / "manuscripts"
            manuscripts_dir.mkdir(parents=True, exist_ok=True)

            # テスト用原稿ファイル作成
            test_manuscript = manuscripts_dir / "episode_001.md"
            test_manuscript.write_text("テスト原稿内容です。これは品質チェック用のサンプルテキストです。", encoding="utf-8")

            # check_tasks.yamlをテスト環境にコピー
            config_dir = project_root / "src" / "noveler" / "infrastructure" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            # 実際の設定ファイルからコピー
            import shutil
            actual_config = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/src/noveler/infrastructure/config/check_tasks.yaml")
            if actual_config.exists():
                shutil.copy2(actual_config, config_dir / "check_tasks.yaml")

            project_config = project_root / "プロジェクト設定.yaml"
            default_config = '\n'.join([
                'writing:',
                '  episode:',
                '    target_length:',
                '      min: 6000',
                '      max: 10000',
            ]) + '\n'
            project_config.write_text(default_config, encoding='utf-8')

            yield project_root

    def test_full_progressive_check_workflow(self, temp_project_root):
        """完全な段階的品質チェックワークフローのテスト"""
        # Arrange
        manager = ProgressiveCheckManager(temp_project_root, episode_number=1)

        # Act: 全12ステップを段階的に実行（簡略版）
        total_steps = 12
        completed_steps = 0

        for step_id in range(1, 6):  # 最初の5ステップをテスト
            result = manager.execute_check_step(step_id, {
                "workflow_test": True,
                "step_focus": f"step_{step_id}"
            }, dry_run=True)

            if result["success"]:
                completed_steps += 1

        # Assert
        final_status = manager.get_check_status()

        assert len(manager.current_state["completed_steps"]) == 5
        assert final_status["progress"]["percentage"] == round(5 / 12 * 100, 1)  # 約41.7%
        assert final_status["progress"]["total"] == 12

        # 実行履歴の確認
        history = manager.get_check_history()
        assert len(history) == 5

        # 状態ファイルの確認
        assert manager.state_file.exists()
        assert manager.state_file.is_file()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
