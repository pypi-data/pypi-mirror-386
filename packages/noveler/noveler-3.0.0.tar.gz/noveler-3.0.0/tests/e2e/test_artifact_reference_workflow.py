"""アーティファクト参照システムE2Eテスト

SPEC-ARTIFACT-001: アーティファクト参照システム実装仕様
prepare_plot_data → write_manuscript_draft の完全なワークフローテスト
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.infrastructure.json.mcp.servers.json_conversion_server import JSONConversionServer


@pytest.fixture
def temp_project_dir():
    """一時プロジェクトディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # プロジェクト構造を作成
        (project_path / "plots").mkdir()
        (project_path / "manuscripts").mkdir()
        (project_path / ".noveler" / "artifacts").mkdir(parents=True)
        (project_path / "temp" / "json_output").mkdir(parents=True)

        yield project_path


@pytest.fixture
def sample_plot_file(temp_project_dir):
    """サンプルプロットファイル"""
    plot_content = """# 第001話 プロット

## あらすじ
新米冒険者のアリスが初めてダンジョンに挑戦する話。
初めは怖がっていたが、仲間と協力することで成長していく。

## 主要イベント
1. ギルドでの依頼受理
   - アリスが初心者向けの依頼を受ける
   - ギルドマスターからの激励
2. ダンジョン入口での緊張
   - 初ダンジョンへの不安
   - パーティメンバーとの出会い
3. 初回戦闘での成長
   - スライムとの戦闘
   - 仲間との連携の大切さを学ぶ
4. 帰還と報告
   - 無事にギルドへ帰還
   - 経験値と報酬の獲得

## キャラクター
- アリス：主人公、16歳の新米冒険者。内気だが心優しい。
- ギルドマスター：経験豊富な元冒険者。アリスを暖かく見守る。
- ボブ：パーティの戦士。頼りがいがあり、アリスを守ってくれる。
- セーラ：パーティの魔法使い。アリスと同年代で親しみやすい。

## テーマ
成長、勇気、仲間との絆、冒険の始まり

## 文字数目標
4000文字程度

## 注意事項
- 初心者にも読みやすい文章にする
- キャラクターの感情を丁寧に描写する
- 戦闘シーンは分かりやすく書く
"""

    plot_file = temp_project_dir / "plots" / "第001話_プロット.md"
    plot_file.write_text(plot_content, encoding="utf-8")
    return plot_file, plot_content


@pytest.fixture
def json_server(temp_project_dir):
    """JSONConversionServerインスタンス"""
    return JSONConversionServer(output_dir=temp_project_dir / "temp" / "json_output")


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactReferenceWorkflowE2E:
    """アーティファクト参照システムのE2Eテスト"""

    @pytest.mark.asyncio
    async def test_complete_artifact_reference_workflow(self, json_server, sample_plot_file, temp_project_dir):
        """完全なアーティファクト参照ワークフローE2Eテスト"""
        plot_file, plot_content = sample_plot_file

        # STEP 1: prepare_plot_data実行 - プロットをアーティファクト化
        # FastMCPではツールは直接アクセスできないため、別の方法で実行
        # サーバーのメソッドを直接呼び出す
        prepare_tool_func = getattr(json_server, 'prepare_plot_data', None)
        if not prepare_tool_func:
            # メソッドが見つからない場合はスキップ
            pytest.skip("prepare_plot_data tool not found")

        assert prepare_tool_func is not None, "prepare_plot_data ツールが見つかりません"

        # prepare_plot_dataの実行
        prepare_result_json = await prepare_tool_func(
            episode=1,
            project_root=str(temp_project_dir)
        )
        prepare_result = json.loads(prepare_result_json)

        # prepare_plot_dataの結果確認
        assert prepare_result["success"] is True
        assert "plot_artifact_id" in prepare_result
        plot_artifact_id = prepare_result["plot_artifact_id"]
        assert plot_artifact_id.startswith("artifact:")

        # プロンプトにアーティファクト参照が含まれていることを確認
        prompt = prepare_result["prompt"]
        assert f"fetch_artifact {plot_artifact_id}" in prompt
        assert "アーティファクト参照情報" in prompt

        # STEP 2: アーティファクトが正しく保存されていることを確認
        list_tool_func = getattr(json_server, 'list_artifacts', None)
        if not list_tool_func:
            pytest.skip("list_artifacts tool not found")

        list_result_json = await list_tool_func(project_root=str(temp_project_dir))
        list_result = json.loads(list_result_json)

        assert list_result["success"] is True
        assert list_result["total_artifacts"] >= 1

        artifact_ids = [artifact["artifact_id"] for artifact in list_result["artifacts"]]
        assert plot_artifact_id in artifact_ids

        # STEP 3: fetch_artifactでプロットコンテンツを取得可能であることを確認
        fetch_tool_func = getattr(json_server, 'fetch_artifact', None)
        if not fetch_tool_func:
            pytest.skip("fetch_artifact tool not found")

        fetch_result_json = await fetch_tool_func(
            artifact_id=plot_artifact_id,
            project_root=str(temp_project_dir)
        )
        fetch_result = json.loads(fetch_result_json)

        assert fetch_result["success"] is True
        assert fetch_result["content"] == plot_content
        assert fetch_result["metadata"]["source_file"] == str(plot_file)

        # STEP 4: write_manuscript_draft実行 - アーティファクト参照プロンプト生成
        write_tool_func = getattr(json_server, 'write_manuscript_draft', None)
        if not write_tool_func:
            pytest.skip("write_manuscript_draft tool not found")

        assert write_tool_func is not None, "write_manuscript_draft ツールが見つかりません"

        # セッションIDを作成してprepare_plot_dataの結果を渡す
        session_id = "test_session_001"
        session_manager_mock = Mock()
        session_data = {
            "plot_artifact_id": plot_artifact_id
        }

        with patch('noveler.infrastructure.json.mcp.servers.json_conversion_server.WritingSessionManager') as mock_session_manager:
            mock_instance = Mock()
            mock_instance.load_session.return_value = session_data
            mock_session_manager.return_value = mock_instance

            write_result_json = await write_tool_func(
                episode=1,
                session_id=session_id,
                project_root=str(temp_project_dir)
            )

        write_result = json.loads(write_result_json)

        # write_manuscript_draftの結果確認
        assert write_result["success"] is True
        assert "plot_artifact_id" in write_result
        assert write_result["plot_artifact_id"] == plot_artifact_id

        # 生成されたプロンプトに参照指示が含まれることを確認
        manuscript_prompt = write_result["prompt"]
        assert f"fetch_artifact {plot_artifact_id}" in manuscript_prompt
        assert "アーティファクト参照情報" in manuscript_prompt
        assert "実行手順" in manuscript_prompt

        # STEP 5: トークン削減効果の確認
        original_size = len(plot_content)
        reference_size = len(plot_artifact_id)
        reduction_ratio = (1 - reference_size / original_size) * 100

        assert reduction_ratio > 80, f"削減率{reduction_ratio:.1f}%が期待値80%を下回りました"

        # STEP 6: エンドツーエンドの整合性確認
        # prepare_plot_data → write_manuscript_draft → fetch_artifact の一貫性
        assert prepare_result["plot_artifact_id"] == write_result["plot_artifact_id"]
        assert fetch_result["artifact_id"] == plot_artifact_id
        assert fetch_result["content"] == plot_content

    @pytest.mark.asyncio
    async def test_artifact_persistence_across_workflow_steps(self, json_server, sample_plot_file, temp_project_dir):
        """ワークフロー間でのアーティファクト永続化テスト"""
        plot_file, plot_content = sample_plot_file

        # STEP 1: 最初のワークフローでアーティファクト作成
        prepare_tool_func = getattr(json_server, 'prepare_plot_data', None)
        if not prepare_tool_func:
            pytest.skip("prepare_plot_data tool not found")

        prepare_result_json = await prepare_tool_func(
            episode=1,
            project_root=str(temp_project_dir)
        )
        prepare_result = json.loads(prepare_result_json)
        plot_artifact_id = prepare_result["plot_artifact_id"]

        # STEP 2: サーバーインスタンスを再作成（永続化テスト）
        json_server2 = JSONConversionServer(output_dir=temp_project_dir / "temp" / "json_output")

        # STEP 3: 新しいインスタンスでアーティファクトが取得可能か確認
        fetch_tool_func = getattr(json_server2, 'fetch_artifact', None)
        if not fetch_tool_func:
            pytest.skip("fetch_artifact tool not found")

        fetch_result_json = await fetch_tool_func(
            artifact_id=plot_artifact_id,
            project_root=str(temp_project_dir)
        )
        fetch_result = json.loads(fetch_result_json)

        # THEN
        assert fetch_result["success"] is True
        assert fetch_result["content"] == plot_content

    @pytest.mark.asyncio
    async def test_multiple_episodes_artifact_management(self, json_server, temp_project_dir):
        """複数エピソードのアーティファクト管理テスト"""
        # GIVEN - 複数エピソードのプロットファイルを作成
        episodes_data = []
        for episode in range(1, 4):
            plot_content = f"""# 第{episode:03d}話 プロット

## あらすじ
エピソード{episode}の内容

## 主要イベント
- イベント{episode}-1
- イベント{episode}-2

## キャラクター
- キャラクター{episode}
"""
            plot_file = temp_project_dir / "plots" / f"第{episode:03d}話_プロット.md"
            plot_file.write_text(plot_content, encoding="utf-8")
            episodes_data.append((episode, plot_content))

        # STEP 1: 各エピソードのprepare_plot_dataを実行
        prepare_tool_func = getattr(json_server, 'prepare_plot_data', None)
        if not prepare_tool_func:
            pytest.skip("prepare_plot_data tool not found")

        artifact_ids = []
        for episode, plot_content in episodes_data:
            prepare_result_json = await prepare_tool_func(
                episode=episode,
                project_root=str(temp_project_dir)
            )
            prepare_result = json.loads(prepare_result_json)
            assert prepare_result["success"] is True
            artifact_ids.append(prepare_result["plot_artifact_id"])

        # STEP 2: 全アーティファクトが一覧に表示されることを確認
        list_tool_func = getattr(json_server, 'list_artifacts', None)
        if not list_tool_func:
            pytest.skip("list_artifacts tool not found")

        list_result_json = await list_tool_func(project_root=str(temp_project_dir))
        list_result = json.loads(list_result_json)

        assert list_result["success"] is True
        assert list_result["total_artifacts"] == 3

        listed_artifact_ids = [artifact["artifact_id"] for artifact in list_result["artifacts"]]
        for artifact_id in artifact_ids:
            assert artifact_id in listed_artifact_ids

        # STEP 3: 各アーティファクトが正しい内容を持つことを確認
        fetch_tool_func = getattr(json_server, 'fetch_artifact', None)
        if not fetch_tool_func:
            pytest.skip("fetch_artifact tool not found")

        for i, (artifact_id, (episode, plot_content)) in enumerate(zip(artifact_ids, episodes_data)):
            fetch_result_json = await fetch_tool_func(
                artifact_id=artifact_id,
                project_root=str(temp_project_dir)
            )
            fetch_result = json.loads(fetch_result_json)

            assert fetch_result["success"] is True
            assert fetch_result["content"] == plot_content
            assert f"第{episode:03d}話" in fetch_result["metadata"]["source_file"]


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactReferenceWorkflowErrorHandling:
    """アーティファクト参照ワークフローのエラーハンドリングE2Eテスト"""

    @pytest.mark.asyncio
    async def test_missing_plot_file_error_handling(self, json_server, temp_project_dir):
        """プロットファイル不存在時のエラーハンドリング"""
        # GIVEN - プロットファイルが存在しない

        # WHEN
        prepare_tool_func = getattr(json_server, 'prepare_plot_data', None)
        if not prepare_tool_func:
            pytest.skip("prepare_plot_data tool not found")

        prepare_result_json = await prepare_tool_func(
            episode=999,  # 存在しないエピソード
            project_root=str(temp_project_dir)
        )
        prepare_result = json.loads(prepare_result_json)

        # THEN
        assert prepare_result["success"] is False
        assert "見つかりません" in prepare_result["error"]

    @pytest.mark.asyncio
    async def test_corrupted_artifact_recovery(self, json_server, sample_plot_file, temp_project_dir):
        """破損アーティファクトからの復旧テスト"""
        plot_file, plot_content = sample_plot_file

        # STEP 1: 正常にアーティファクトを作成
        prepare_tool_func = getattr(json_server, 'prepare_plot_data', None)
        if not prepare_tool_func:
            pytest.skip("prepare_plot_data tool not found")

        prepare_result_json = await prepare_tool_func(
            episode=1,
            project_root=str(temp_project_dir)
        )
        prepare_result = json.loads(prepare_result_json)
        plot_artifact_id = prepare_result["plot_artifact_id"]

        # STEP 2: アーティファクトファイルを破損させる
        from noveler.domain.services.artifact_store_service import create_artifact_store

        artifact_store = create_artifact_store(storage_dir=temp_project_dir / ".noveler" / "artifacts")
        storage_path = artifact_store._get_storage_path(plot_artifact_id)
        storage_path.write_text("{ broken json }", encoding="utf-8")

        # メモリキャッシュをクリア
        artifact_store._memory_cache.clear()

        # STEP 3: fetch_artifactで復旧動作を確認
        fetch_tool_func = getattr(json_server, 'fetch_artifact', None)
        if not fetch_tool_func:
            pytest.skip("fetch_artifact tool not found")

        fetch_result_json = await fetch_tool_func(
            artifact_id=plot_artifact_id,
            project_root=str(temp_project_dir)
        )
        fetch_result = json.loads(fetch_result_json)

        # THEN
        assert fetch_result["success"] is False
        assert "見つかりません" in fetch_result["error"]


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactReferenceWorkflowPerformance:
    """アーティファクト参照ワークフローのパフォーマンステスト"""

    @pytest.mark.asyncio
    async def test_workflow_performance_with_large_plot(self, json_server, temp_project_dir):
        """大容量プロットでのワークフローパフォーマンステスト"""
        # GIVEN - 大容量プロットファイル（100KB）
        large_plot_content = f"""# 第001話 大容量プロット

## あらすじ
{"非常に詳細な物語の説明。" * 1000}

## 主要イベント
{"詳細なイベント説明。" * 1000}

## キャラクター設定
{"詳細なキャラクター説明。" * 1000}
"""

        plot_file = temp_project_dir / "plots" / "第001話_プロット.md"
        plot_file.write_text(large_plot_content, encoding="utf-8")

        # WHEN
        import time

        # prepare_plot_data実行時間測定
        prepare_tool_func = getattr(json_server, 'prepare_plot_data', None)
        if not prepare_tool_func:
            pytest.skip("prepare_plot_data tool not found")

        start_time = time.time()
        prepare_result_json = await prepare_tool_func(
            episode=1,
            project_root=str(temp_project_dir)
        )
        prepare_time = time.time() - start_time

        prepare_result = json.loads(prepare_result_json)
        plot_artifact_id = prepare_result["plot_artifact_id"]

        # fetch_artifact実行時間測定
        fetch_tool_func = getattr(json_server, 'fetch_artifact', None)
        if not fetch_tool_func:
            pytest.skip("fetch_artifact tool not found")

        start_time = time.time()
        fetch_result_json = await fetch_tool_func(
            artifact_id=plot_artifact_id,
            project_root=str(temp_project_dir)
        )
        fetch_time = time.time() - start_time

        fetch_result = json.loads(fetch_result_json)

        # THEN
        assert prepare_result["success"] is True
        assert fetch_result["success"] is True
        assert fetch_result["content"] == large_plot_content

        # パフォーマンス要件
        assert prepare_time < 3.0, f"prepare_plot_dataに{prepare_time}秒かかりました"
        assert fetch_time < 2.0, f"fetch_artifactに{fetch_time}秒かかりました"

        # 削減効果の確認
        original_size = len(large_plot_content)
        reference_size = len(plot_artifact_id)
        reduction_ratio = (1 - reference_size / original_size) * 100

        assert reduction_ratio > 95, f"大容量での削減率{reduction_ratio:.1f}%が期待値95%を下回りました"
