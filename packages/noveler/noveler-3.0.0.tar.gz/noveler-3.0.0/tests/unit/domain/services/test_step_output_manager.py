#!/usr/bin/env python3
"""StepOutputManagerのユニットテスト

A38ステップ出力保存機能のテストケース。
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from noveler.domain.services.step_output_manager import StepOutputManager
from noveler.domain.value_objects.structured_step_output import (
    QualityMetrics,
    StepCompletionStatus,
    StructuredStepOutput,
)


@pytest.fixture
def temp_project_root():
    """テンポラリプロジェクトルートを作成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_path_service(temp_project_root):
    """モックPathServiceを作成"""
    mock_service = Mock()
    mock_service.project_root.return_value = temp_project_root
    return mock_service


@pytest.fixture
def step_output_manager(mock_path_service):
    """StepOutputManagerインスタンスを作成"""
    return StepOutputManager(mock_path_service)


class TestStepOutputManager:
    """StepOutputManagerのテストクラス"""

    @pytest.mark.asyncio
    async def test_save_step_output_basic(self, step_output_manager, temp_project_root):
        """基本的なステップ出力保存テスト"""
        episode_number = 1
        step_number = 5
        step_name = "STEP05_SampleService"
        llm_response = "サンプルLLM応答内容"
        structured_data = {"key": "value", "number": 42}

        # ステップ出力を保存
        saved_path = await step_output_manager.save_step_output(
            episode_number=episode_number,
            step_number=step_number,
            step_name=step_name,
            llm_response_content=llm_response,
            structured_data=structured_data,
        )

        # ファイルが作成されているか確認
        assert saved_path.exists()
        assert saved_path.parent == temp_project_root / ".noveler"
        assert saved_path.name.startswith("EP001_step05_")
        assert saved_path.suffix == ".json"

        # ファイル内容を確認
        with saved_path.open("r", encoding="utf-8") as f:
            content = json.load(f)

        assert content["episode_number"] == episode_number
        assert content["step_number"] == step_number
        assert content["step_name"] == step_name
        assert content["llm_response"]["raw_content"] == llm_response
        assert content["structured_data"] == structured_data

    @pytest.mark.asyncio
    async def test_save_structured_step_output(self, step_output_manager, temp_project_root):
        """StructuredStepOutput形式での保存テスト"""
        episode_number = 2
        step_number = 10
        llm_response = "構造化ステップ応答"

        # StructuredStepOutputを作成
        structured_output = StructuredStepOutput(
            step_id="STEP_10",
            step_name="テストステップ",
            completion_status=StepCompletionStatus.COMPLETED,
            structured_data={"test": True, "value": 100},
            quality_metrics=QualityMetrics(overall_score=0.8),
        )

        # 保存実行
        saved_path = await step_output_manager.save_structured_step_output(
            episode_number=episode_number,
            step_number=step_number,
            structured_output=structured_output,
            llm_response_content=llm_response,
        )

        # 結果確認
        assert saved_path.exists()
        assert saved_path.name.startswith("EP002_step10_")

        # 内容確認
        with saved_path.open("r", encoding="utf-8") as f:
            content = json.load(f)

        assert content["episode_number"] == episode_number
        assert content["step_number"] == step_number
        assert content["step_name"] == "テストステップ"
        assert content["structured_data"]["test"] is True
        assert content["quality_metrics"]["overall_score"] == 0.8

    @pytest.mark.asyncio
    async def test_list_step_outputs(self, step_output_manager):
        """ステップ出力ファイル一覧取得テスト"""
        # 複数のファイルを保存
        for step in [1, 3, 5]:
            await step_output_manager.save_step_output(
                episode_number=1,
                step_number=step,
                step_name=f"STEP{step:02d}",
                llm_response_content=f"Response {step}",
                structured_data={"step": step},
            )

        # 全体一覧を取得
        all_files = await step_output_manager.list_step_outputs()
        assert len(all_files) == 3

        # エピソードでフィルタ
        ep1_files = await step_output_manager.list_step_outputs(episode_number=1)
        assert len(ep1_files) == 3

        # ステップでフィルタ
        step3_files = await step_output_manager.list_step_outputs(step_number=3)
        assert len(step3_files) == 1

    @pytest.mark.asyncio
    async def test_load_step_output(self, step_output_manager):
        """ステップ出力ファイル読み込みテスト"""
        # ファイル保存
        saved_path = await step_output_manager.save_step_output(
            episode_number=1,
            step_number=7,
            step_name="LoadTest",
            llm_response_content="Load test content",
            structured_data={"load": "test"},
        )

        # ファイル読み込み
        loaded_data = await step_output_manager.load_step_output(saved_path)

        assert loaded_data["episode_number"] == 1
        assert loaded_data["step_number"] == 7
        assert loaded_data["step_name"] == "LoadTest"
        assert loaded_data["structured_data"]["load"] == "test"

    @pytest.mark.asyncio
    async def test_cleanup_old_outputs(self, step_output_manager):
        """古いファイルクリーンアップテスト"""
        # 異なるステップ番号で多数のファイルを作成（ファイル名重複を避ける）
        for i in range(10):
            await asyncio.sleep(0.05)  # ファイルタイムスタンプ重複を避けるため十分な待機
            await step_output_manager.save_step_output(
                episode_number=1,
                step_number=i + 1,  # 1から10まで異なるステップ番号
                step_name=f"Test{i}",
                llm_response_content=f"Content {i}",
                structured_data={"index": i},
            )

        # 実際に作成されたファイル数を確認
        files_before_cleanup = await step_output_manager.list_step_outputs(episode_number=1)
        assert len(files_before_cleanup) == 10  # 確実に10個作成されているはず

        # 最新5個を保持してクリーンアップ
        deleted_count = await step_output_manager.cleanup_old_outputs(
            episode_number=1,
            keep_latest=5
        )

        assert deleted_count == 5

        # 残りファイル数を確認
        remaining_files = await step_output_manager.list_step_outputs(episode_number=1)
        assert len(remaining_files) == 5

    @pytest.mark.asyncio
    async def test_get_statistics(self, step_output_manager):
        """統計情報取得テスト"""
        # 複数のステップファイルを作成
        for step in [1, 2, 3]:
            await step_output_manager.save_step_output(
                episode_number=1,
                step_number=step,
                step_name=f"STEP{step:02d}",
                llm_response_content=f"Content for step {step}",
                structured_data={"step": step},
            )

        # 統計情報取得
        stats = await step_output_manager.get_step_output_statistics(episode_number=1)

        assert stats["total_files"] == 3
        assert stats["steps_coverage"] == 3
        assert stats["episode_filter"] == 1
        assert 1 in stats["step_file_counts"]
        assert 2 in stats["step_file_counts"]
        assert 3 in stats["step_file_counts"]

    @pytest.mark.asyncio
    async def test_invalid_step_number(self, step_output_manager):
        """無効なステップ番号のテスト"""
        with pytest.raises(ValueError, match="ステップ番号は1-18の範囲"):
            await step_output_manager.save_step_output(
                episode_number=1,
                step_number=0,  # 無効
                step_name="Invalid",
                llm_response_content="Test",
                structured_data={},
            )

        with pytest.raises(ValueError, match="ステップ番号は1-18の範囲"):
            await step_output_manager.save_step_output(
                episode_number=1,
                step_number=19,  # 無効
                step_name="Invalid",
                llm_response_content="Test",
                structured_data={},
            )

    @pytest.mark.asyncio
    async def test_invalid_episode_number(self, step_output_manager):
        """無効なエピソード番号のテスト"""
        with pytest.raises(ValueError, match="エピソード番号は1以上"):
            await step_output_manager.save_step_output(
                episode_number=0,  # 無効
                step_number=1,
                step_name="Invalid",
                llm_response_content="Test",
                structured_data={},
            )

    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, step_output_manager):
        """存在しないファイル読み込みテスト"""
        nonexistent_path = Path("/tmp/nonexistent_file.json")

        with pytest.raises(FileNotFoundError, match="ステップ出力ファイルが見つかりません"):
            await step_output_manager.load_step_output(nonexistent_path)
