"""アーティファクト参照システムMCPツールの統合テスト

SPEC-ARTIFACT-001: アーティファクト参照システム実装仕様
JSONConversionServerのfetch_artifact/list_artifacts MCPツールの統合テスト
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from noveler.domain.services.artifact_store_service import create_artifact_store
from noveler.infrastructure.json.mcp.servers.json_conversion_server import JSONConversionServer


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def json_server(temp_output_dir):
    """JSONConversionServerインスタンス"""
    return JSONConversionServer(output_dir=temp_output_dir)


@pytest.fixture
def sample_plot_content():
    """サンプルプロットコンテンツ"""
    return """# 第001話 プロット

## あらすじ
新米冒険者のアリスが初めてダンジョンに挑戦する話。

## 主要イベント
1. ギルドでの依頼受理
2. ダンジョン入口での緊張
3. 初回戦闘での成長
4. 帰還と報告

## キャラクター
- アリス：主人公、16歳の新米冒険者
- ギルドマスター：経験豊富な元冒険者

## テーマ
成長、勇気、仲間との絆
"""


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactMCPTools:
    """アーティファクト参照システムMCPツールの統合テスト"""

    @pytest.mark.asyncio
    async def test_fetch_artifact_tool_basic(self, json_server, sample_plot_content, temp_output_dir):
        """fetch_artifact MCPツール基本動作テスト"""
        # GIVEN - アーティファクトを事前に保存

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")
        artifact_id = artifact_store.store(
            content=sample_plot_content,
            content_type="text",
            source_file="第001話_プロット.md",
            description="第001話プロット"
        )

        # MCPツール関数を直接取得（サーバー初期化後）
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        assert fetch_tool_func is not None, "fetch_artifact ツールが見つかりません"

        # WHEN
        result_json = await fetch_tool_func(
            artifact_id=artifact_id,
            project_root=str(temp_output_dir)
        )
        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert result["artifact_id"] == artifact_id
        assert result["content"] == sample_plot_content
        assert result["metadata"]["content_type"] == "text"
        assert result["metadata"]["source_file"] == "第001話_プロット.md"
        assert "第001話プロット" in result["instructions"]

    @pytest.mark.asyncio
    async def test_fetch_artifact_with_section(self, json_server, temp_output_dir):
        """fetch_artifact セクション指定テスト"""
        # GIVEN - JSONコンテンツをアーティファクトとして保存

        json_content = json.dumps({
            "title": "第001話",
            "plot": "プロット詳細内容",
            "characters": ["アリス", "ボブ"],
            "theme": "成長物語"
        }, ensure_ascii=False)

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")
        artifact_id = artifact_store.store(
            content=json_content,
            content_type="json",
            description="構造化プロット"
        )

        # MCPツール関数を取得
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        # WHEN
        result_json = await fetch_tool_func(
            artifact_id=artifact_id,
            section="plot",
            project_root=str(temp_output_dir)
        )
        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert result["content"] == "プロット詳細内容"
        assert result["section"] == "plot"

    @pytest.mark.asyncio
    async def test_fetch_artifact_nonexistent(self, json_server, temp_output_dir):
        """存在しないアーティファクト取得エラーテスト"""
        # GIVEN
        nonexistent_id = "artifact:nonexistent"

        # MCPツール関数を取得
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        # WHEN
        result_json = await fetch_tool_func(
            artifact_id=nonexistent_id,
            project_root=str(temp_output_dir)
        )
        result = json.loads(result_json)

        # THEN
        assert result["success"] is False
        assert "見つかりません" in result["error"]
        assert "available_artifacts" in result

    @pytest.mark.asyncio
    async def test_list_artifacts_tool_basic(self, json_server, sample_plot_content, temp_output_dir):
        """list_artifacts MCPツール基本動作テスト"""
        # GIVEN - 複数のアーティファクトを保存

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")
        artifact_id1 = artifact_store.store(
            content=sample_plot_content,
            description="第001話プロット"
        )
        artifact_id2 = artifact_store.store(
            content="別のコンテンツ",
            description="第002話プロット"
        )

        # MCPツール関数を取得
        list_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "list_artifacts":
                list_tool_func = tool_func.fn
                break

        assert list_tool_func is not None, "list_artifacts ツールが見つかりません"

        # WHEN
        result_json = await list_tool_func(project_root=str(temp_output_dir))
        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert result["total_artifacts"] == 2
        assert len(result["artifacts"]) == 2

        artifact_ids = [artifact["artifact_id"] for artifact in result["artifacts"]]
        assert artifact_id1 in artifact_ids
        assert artifact_id2 in artifact_ids

        # 説明がマッチすることを確認
        for artifact in result["artifacts"]:
            if artifact["artifact_id"] == artifact_id1:
                assert artifact["description"] == "第001話プロット"
            elif artifact["artifact_id"] == artifact_id2:
                assert artifact["description"] == "第002話プロット"

    @pytest.mark.asyncio
    async def test_list_artifacts_empty(self, json_server, temp_output_dir):
        """空のアーティファクトストア一覧テスト"""
        # GIVEN - 空のストレージ

        # MCPツール関数を取得
        list_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "list_artifacts":
                list_tool_func = tool_func.fn
                break

        # WHEN
        result_json = await list_tool_func(project_root=str(temp_output_dir))
        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert result["artifacts"] == []
        assert "ありません" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_artifact_format_json(self, json_server, temp_output_dir):
        """fetch_artifact JSON形式指定テスト"""
        # GIVEN

        json_data = {"title": "テスト", "content": "内容"}
        json_content = json.dumps(json_data, ensure_ascii=False)

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")
        artifact_id = artifact_store.store(
            content=json_content,
            content_type="json"
        )

        # MCPツール関数を取得
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        # WHEN
        result_json = await fetch_tool_func(
            artifact_id=artifact_id,
            format_type="json",
            project_root=str(temp_output_dir)
        )
        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert result["format"] == "json"

        # コンテンツがJSONとして整形されているかテスト
        parsed_content = json.loads(result["content"])
        assert parsed_content == json_data


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactMCPToolsErrorHandling:
    """アーティファクトMCPツールのエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_fetch_artifact_invalid_project_root(self, json_server):
        """無効なproject_root指定エラーテスト"""
        # GIVEN
        invalid_path = "/nonexistent/path"

        # MCPツール関数を取得
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        # WHEN
        result_json = await fetch_tool_func(
            artifact_id="artifact:test",
            project_root=invalid_path
        )
        result = json.loads(result_json)

        # THEN
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_list_artifacts_invalid_project_root(self, json_server):
        """無効なproject_root指定エラーテスト（list_artifacts）"""
        # GIVEN
        invalid_path = "/nonexistent/path"

        # MCPツール関数を取得
        list_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "list_artifacts":
                list_tool_func = tool_func.fn
                break

        # WHEN
        result_json = await list_tool_func(project_root=invalid_path)
        result = json.loads(result_json)

        # THEN
        assert result["success"] is False
        assert "error" in result


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactMCPToolsPerformance:
    """アーティファクトMCPツールのパフォーマンステスト"""

    @pytest.mark.asyncio
    async def test_fetch_large_artifact_performance(self, json_server, temp_output_dir):
        """大容量アーティファクト取得パフォーマンステスト"""
        # GIVEN

        # 1MBのコンテンツを作成
        large_content = "x" * (1024 * 1024)

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")
        artifact_id = artifact_store.store(
            content=large_content,
            description="大容量テスト"
        )

        # MCPツール関数を取得
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        # WHEN
        start_time = time.time()
        result_json = await fetch_tool_func(
            artifact_id=artifact_id,
            project_root=str(temp_output_dir)
        )
        end_time = time.time()

        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert len(result["content"]) == 1024 * 1024

        # パフォーマンス要件：1MBは2秒以内で処理
        execution_time = end_time - start_time
        assert execution_time < 2.0, f"取得に{execution_time}秒かかりました"

    @pytest.mark.asyncio
    async def test_list_many_artifacts_performance(self, json_server, temp_output_dir):
        """多数アーティファクト一覧取得パフォーマンステスト"""
        # GIVEN

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")

        # 100個のアーティファクトを作成
        artifact_ids = []
        for i in range(100):
            artifact_id = artifact_store.store(
                content=f"コンテンツ {i}",
                description=f"テスト{i:03d}"
            )
            artifact_ids.append(artifact_id)

        # MCPツール関数を取得
        list_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "list_artifacts":
                list_tool_func = tool_func.fn
                break

        # WHEN
        start_time = time.time()
        result_json = await list_tool_func(project_root=str(temp_output_dir))
        end_time = time.time()

        result = json.loads(result_json)

        # THEN
        assert result["success"] is True
        assert result["total_artifacts"] == 100
        assert len(result["artifacts"]) == 100

        # パフォーマンス要件：100個は1秒以内で処理
        execution_time = end_time - start_time
        assert execution_time < 1.0, f"一覧取得に{execution_time}秒かかりました"


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactMCPToolsIntegration:
    """アーティファクトMCPツールと他システムとの統合テスト"""

    @pytest.mark.asyncio
    async def test_artifact_reference_workflow_integration(self, json_server, sample_plot_content, temp_output_dir):
        """アーティファクト参照ワークフロー統合テスト"""
        # GIVEN - prepare_plot_dataシミュレーション

        artifact_store = create_artifact_store(storage_dir=temp_output_dir / "artifacts")
        plot_artifact_id = artifact_store.store(
            content=sample_plot_content,
            content_type="text",
            source_file="第001話_プロット.md",
            description="第001話プロット"
        )

        # write_manuscript_draftシミュレーション - 参照プロンプト生成
        manuscript_prompt = f"""# 第001話 原稿執筆段階（参照渡し版）

## アーティファクト参照情報
- **プロット**: {plot_artifact_id}

## 実行手順
1. `fetch_artifact {plot_artifact_id}` でプロット全文を取得し、内容を理解してください
2. 以下の要件に従って執筆してください

## 執筆要件
- 目標文字数: 4000文字
- ジャンル: ファンタジー
"""

        # MCPツールを使ってアーティファクトを取得（LLM実行シミュレーション）
        fetch_tool_func = None
        for tool_name, tool_func in json_server.server._tools.items():
            if tool_name == "fetch_artifact":
                fetch_tool_func = tool_func.fn
                break

        # WHEN - LLMがアーティファクトを取得
        fetch_result_json = await fetch_tool_func(
            artifact_id=plot_artifact_id,
            project_root=str(temp_output_dir)
        )
        fetch_result = json.loads(fetch_result_json)

        # THEN - 統合動作確認
        assert fetch_result["success"] is True
        assert fetch_result["content"] == sample_plot_content

        # プロンプト削減効果の確認
        original_size = len(sample_plot_content)
        reference_size = len(plot_artifact_id)
        reduction_ratio = (1 - reference_size / original_size) * 100

        assert reduction_ratio > 80, f"削減率{reduction_ratio:.1f}%が期待値80%を下回りました"

        # メタデータの一貫性確認
        assert fetch_result["metadata"]["source_file"] == "第001話_プロット.md"
        assert fetch_result["metadata"]["content_type"] == "text"
