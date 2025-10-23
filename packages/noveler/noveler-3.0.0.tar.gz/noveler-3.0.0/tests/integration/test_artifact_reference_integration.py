"""アーティファクト参照システムの統合テスト

SPEC-ARTIFACT-001: アーティファクト参照システム
- 大容量コンテンツの効率的な参照渡し
- SHA256ベースのコンテンツアドレッシング
- MCPツール統合による透過的アクセス
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from noveler.domain.services.artifact_store_service import ArtifactStoreService, create_artifact_store
from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager
from noveler.domain.services.progressive_write_runtime_deps import (
    ProgressiveWriteRuntimeDeps,
)


class TestArtifactReferenceIntegration:
    """アーティファクト参照システムの統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.temp_dir) / ".noveler" / "artifacts"
        self.storage_dir.mkdir(parents=True)
        self.artifact_store = create_artifact_store(storage_dir=self.storage_dir)

    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_store_and_fetch_artifact(self):
        """アーティファクトの保存と取得"""
        # テストコンテンツ
        content = "# 第001話プロット\n\nこれはテスト用のプロット内容です。"

        # アーティファクトとして保存
        artifact_id = self.artifact_store.store(
            content=content,
            content_type="text",
            source_file="test_plot.md",
            description="テストプロット",
            tags={"episode": "001", "type": "plot"}
        )

        # IDが正しい形式であることを確認
        assert artifact_id.startswith("artifact:")
        assert len(artifact_id) == 21  # "artifact:" + 12文字のハッシュ

        # アーティファクトを取得
        fetched_content = self.artifact_store.fetch(artifact_id)
        assert fetched_content == content

    def test_list_artifacts_with_tags(self):
        """タグによるアーティファクトのリスト取得"""
        # 複数のアーティファクトを作成
        artifact1_id = self.artifact_store.store(
            content="プロット1",
            tags={"episode": "001", "type": "plot"}
        )
        artifact2_id = self.artifact_store.store(
            content="プロット2",
            tags={"episode": "002", "type": "plot"}
        )
        artifact3_id = self.artifact_store.store(
            content="原稿1",
            tags={"episode": "001", "type": "manuscript"}
        )

        # エピソード001のアーティファクトを取得
        episode1_artifacts = self.artifact_store.list_artifacts(tags={"episode": "001"})
        assert len(episode1_artifacts) == 2
        artifact_ids = [a["artifact_id"] for a in episode1_artifacts]
        assert artifact1_id in artifact_ids
        assert artifact3_id in artifact_ids

        # プロット型のアーティファクトを取得
        plot_artifacts = self.artifact_store.list_artifacts(tags={"type": "plot"})
        assert len(plot_artifacts) == 2
        artifact_ids = [a["artifact_id"] for a in plot_artifacts]
        assert artifact1_id in artifact_ids
        assert artifact2_id in artifact_ids

    def test_progressive_write_manager_integration(self):
        """ProgressiveWriteManagerとの統合テスト"""
        # モックの設定
        mock_path_service = MagicMock()
        mock_path_service.project_root = Path(self.temp_dir)
        mock_path_service.get_plots_dir.return_value = Path(self.temp_dir) / "plots"

        deps = ProgressiveWriteRuntimeDeps(
            path_service_factory=lambda _project_root: mock_path_service,
            artifact_store_factory=lambda *, storage_dir, **options: self.artifact_store,
            progress_display_factory=lambda episode, total_steps: MagicMock(),
            feedback_system_factory=lambda episode: MagicMock(),
            io_logger_factory=lambda project_root: None,
        )

        # プロットファイルを作成
        plots_dir = Path(self.temp_dir) / "plots"
        plots_dir.mkdir(parents=True)
        plot_file = plots_dir / "第001話_プロット.md"
        plot_content = "# 第001話プロット\n\nテストプロット内容"
        plot_file.write_text(plot_content, encoding="utf-8")

        # ProgressiveWriteManagerを初期化
        manager = ProgressiveWriteManager(project_root=Path(self.temp_dir), episode_number=1, deps=deps)

        # ステップ7（会話設計）を実行
        task = {
            "id": 7,
            "name": "会話設計",
            "phase": "dialogue",
            "prerequisites": []
        }

        result = manager._execute_step_logic(task)

        # 結果を確認
        assert result["step_id"] == 7
        assert result["step_name"] == "会話設計"
        assert result["metadata"]["success_criteria_met"] is True
        assert "plot_artifact_id" in result["metadata"]
        assert len(result["artifacts"]) == 1

        # アーティファクトIDを使って内容を取得できることを確認
        artifact_id = result["artifacts"][0]
        fetched_content = self.artifact_store.fetch(artifact_id)
        assert fetched_content == plot_content

    def test_mcp_tool_integration(self):
        """MCPツールとの統合テスト（シミュレーション）"""
        # プロットコンテンツを準備
        plot_content = """# 第001話プロット

## あらすじ
主人公が冒険の旅に出る決意をする。

## シーン構成
1. 朝の目覚め
2. 村での別れ
3. 旅立ち
"""

        # アーティファクトとして保存
        artifact_id = self.artifact_store.store(
            content=plot_content,
            content_type="text",
            source_file="episode_001_plot.md",
            description="第001話プロット",
            tags={"episode": "001", "type": "plot"}
        )

        # MCPツールのfetch_artifactをシミュレート
        def simulate_fetch_artifact(artifact_id: str, section: str = None) -> dict:
            """fetch_artifact MCPツールのシミュレーション"""
            content = self.artifact_store.fetch(artifact_id, section)
            if content:
                return {
                    "success": True,
                    "artifact_id": artifact_id,
                    "content": content,
                    "section": section
                }
            else:
                return {
                    "success": False,
                    "error": f"Artifact not found: {artifact_id}"
                }

        # fetch_artifactを実行
        result = simulate_fetch_artifact(artifact_id)
        assert result["success"] is True
        assert result["content"] == plot_content

        # セクション指定で取得
        result_section = simulate_fetch_artifact(artifact_id, section="あらすじ")
        assert result_section["success"] is True
        assert "主人公が冒険の旅に出る" in result_section["content"]

    def test_token_reduction_efficiency(self):
        """トークン削減効率のテスト"""
        # 大きなプロットコンテンツ（実際のプロットサイズを想定）
        large_content = "# プロット\n\n" + "これは長いプロット内容です。" * 1000
        content_size = len(large_content)

        # アーティファクトIDのサイズ
        artifact_id = self.artifact_store.store(content=large_content)
        id_size = len(artifact_id)

        # トークン削減率を計算（簡易的な計算）
        reduction_rate = (1 - id_size / content_size) * 100

        # 95%以上の削減率を達成していることを確認
        assert reduction_rate > 95, f"削減率が95%未満: {reduction_rate:.2f}%"

        # アーティファクトIDは常に固定長であることを確認
        assert len(artifact_id) == 21  # "artifact:" + 12文字


class TestWriteManuscriptDraftIntegration:
    """write_manuscript_draft関数の統合テスト"""

    @pytest.mark.asyncio
    async def test_write_manuscript_with_artifact_reference(self):
        """アーティファクト参照を使った原稿執筆のテスト"""
        from noveler.infrastructure.json.mcp.servers.json_conversion_server import JSONConversionServer

        # サーバーインスタンスを作成
        server = JSONConversionServer()

        # モックツールの作成
        with patch('noveler.infrastructure.json.mcp.servers.json_conversion_server.create_mcp_aware_path_service') as mock_path_service:
            with patch('noveler.infrastructure.json.mcp.servers.json_conversion_server.create_artifact_store') as mock_store:
                # モックの設定
                mock_path = MagicMock()
                mock_path.project_root = Path(tempfile.mkdtemp())
                mock_path.get_plots_dir.return_value = mock_path.project_root / "plots"
                mock_path.get_manuscript_dir.return_value = mock_path.project_root / "manuscripts"
                mock_path_service.return_value = mock_path

                # アーティファクトストアのモック
                mock_artifact_store = MagicMock()
                mock_artifact_store.store.return_value = "artifact:abc123def456"
                mock_store.return_value = mock_artifact_store

                # プロットファイルを作成
                plots_dir = mock_path.get_plots_dir()
                plots_dir.mkdir(parents=True)
                plot_file = plots_dir / "第001話_プロット.md"
                plot_file.write_text("テストプロット", encoding="utf-8")

                # write_manuscript_draftツールを登録
                server._register_staged_writing_tools()

                # ツールを実行（モック実行）
                tool_func = server.server._tools["write_manuscript_draft"]["handler"]
                result_json = await tool_func(episode=1, word_count_target=4000)
                result = json.loads(result_json)

                # 結果を確認
                assert result["success"] is True
                assert result["plot_artifact_id"] == "artifact:abc123def456"
                assert "fetch_artifact artifact:abc123def456" in result["prompt"]
                assert result["stage"] == "write_manuscript_draft"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
