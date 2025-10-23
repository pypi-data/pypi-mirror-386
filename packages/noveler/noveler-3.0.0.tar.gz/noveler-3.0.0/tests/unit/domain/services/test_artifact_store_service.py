"""ArtifactStoreServiceのユニットテスト

SPEC-ARTIFACT-001: アーティファクト参照システム実装仕様
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.domain.services.artifact_store_service import (
    ArtifactStoreService,
    ArtifactMetadata,
    StoredArtifact,
    create_artifact_store,
)


@pytest.fixture
def temp_storage_dir():
    """一時ストレージディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def artifact_store(temp_storage_dir):
    """ArtifactStoreServiceインスタンス"""
    return create_artifact_store(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_content():
    """テスト用サンプルコンテンツ"""
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
"""


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactStoreService:
    """ArtifactStoreServiceのテストクラス"""

    def test_initialization(self, temp_storage_dir):
        """初期化テスト"""
        # GIVEN
        logger_mock = Mock()

        # WHEN
        store = ArtifactStoreService(
            logger_service=logger_mock,
            storage_dir=temp_storage_dir
        )

        # THEN
        assert store._storage_dir == temp_storage_dir
        assert store._logger == logger_mock
        assert len(store._memory_cache) == 0
        assert temp_storage_dir.exists()

    def test_store_content(self, artifact_store, sample_content):
        """コンテンツストアテスト"""
        # GIVEN
        content_type = "text"
        source_file = "第001話_プロット.md"
        description = "第001話プロット"

        # WHEN
        artifact_id = artifact_store.store(
            content=sample_content,
            content_type=content_type,
            source_file=source_file,
            description=description
        )

        # THEN
        assert artifact_id.startswith("artifact:")
        assert len(artifact_id) == 21  # "artifact:" + 12文字のハッシュ

        # メモリキャッシュに保存されていることを確認
        assert artifact_id in artifact_store._memory_cache

        # ストレージファイルが作成されていることを確認
        storage_path = artifact_store._get_storage_path(artifact_id)
        assert storage_path.exists()

    def test_fetch_content(self, artifact_store, sample_content):
        """コンテンツ取得テスト"""
        # GIVEN
        artifact_id = artifact_store.store(sample_content, description="テストコンテンツ")

        # WHEN
        retrieved_content = artifact_store.fetch(artifact_id)

        # THEN
        assert retrieved_content == sample_content

    def test_fetch_nonexistent_artifact(self, artifact_store):
        """存在しないアーティファクト取得テスト"""
        # GIVEN
        nonexistent_id = "artifact:nonexistent"

        # WHEN
        result = artifact_store.fetch(nonexistent_id)

        # THEN
        assert result is None

    def test_get_metadata(self, artifact_store, sample_content):
        """メタデータ取得テスト"""
        # GIVEN
        source_file = "test.md"
        description = "テストファイル"
        tags = {"type": "plot", "episode": "001"}

        artifact_id = artifact_store.store(
            content=sample_content,
            source_file=source_file,
            description=description,
            tags=tags
        )

        # WHEN
        metadata = artifact_store.get_metadata(artifact_id)

        # THEN
        assert metadata is not None
        assert metadata.artifact_id == artifact_id
        assert metadata.content_type == "text"
        assert metadata.source_file == source_file
        assert metadata.description == description
        assert metadata.tags == tags
        assert metadata.size_bytes == len(sample_content.encode('utf-8'))

    def test_list_artifacts(self, artifact_store, sample_content):
        """アーティファクト一覧取得テスト"""
        # GIVEN
        artifact_id1 = artifact_store.store(sample_content, description="コンテンツ1")
        artifact_id2 = artifact_store.store("別のコンテンツ", description="コンテンツ2")

        # WHEN
        artifacts = artifact_store.list_artifacts()

        # THEN
        assert len(artifacts) == 2
        assert artifact_id1 in artifacts
        assert artifact_id2 in artifacts
        assert artifacts[artifact_id1].description == "コンテンツ1"
        assert artifacts[artifact_id2].description == "コンテンツ2"

    def test_delete_artifact(self, artifact_store, sample_content):
        """アーティファクト削除テスト"""
        # GIVEN
        artifact_id = artifact_store.store(sample_content, description="削除テスト")
        storage_path = artifact_store._get_storage_path(artifact_id)

        # 保存されていることを確認
        assert artifact_id in artifact_store._memory_cache
        assert storage_path.exists()

        # WHEN
        success = artifact_store.delete_artifact(artifact_id)

        # THEN
        assert success is True
        assert artifact_id not in artifact_store._memory_cache
        assert not storage_path.exists()

    def test_section_extraction_json(self, artifact_store):
        """JSONセクション抽出テスト"""
        # GIVEN
        json_content = json.dumps({
            "title": "第001話",
            "plot": "プロット内容",
            "characters": ["アリス", "ボブ"]
        }, ensure_ascii=False)

        artifact_id = artifact_store.store(
            content=json_content,
            content_type="json"
        )

        # WHEN
        title_section = artifact_store.fetch(artifact_id, section="title")
        plot_section = artifact_store.fetch(artifact_id, section="plot")

        # THEN
        assert title_section == "第001話"
        assert plot_section == "プロット内容"

    def test_section_extraction_text(self, artifact_store):
        """テキストセクション抽出テスト"""
        # GIVEN
        text_content = """# タイトル
タイトル内容

## プロット
プロット内容ここ

## キャラクター
キャラクター説明
"""

        artifact_id = artifact_store.store(
            content=text_content,
            content_type="text"
        )

        # WHEN
        plot_section = artifact_store.fetch(artifact_id, section="プロット")

        # THEN
        assert "プロット内容ここ" in plot_section

    def test_artifact_id_normalization(self, artifact_store):
        """アーティファクトID正規化テスト"""
        # GIVEN
        test_cases = [
            ("artifact:abc123", "artifact:abc123"),
            ("ref:abc123", "artifact:abc123"),
            ("abc123", "artifact:abc123")
        ]

        # WHEN & THEN
        for input_id, expected_id in test_cases:
            normalized = artifact_store._normalize_artifact_id(input_id)
            assert normalized == expected_id

    def test_create_reference(self, artifact_store, sample_content):
        """参照情報作成テスト"""
        # GIVEN
        alias = "plot001"

        # WHEN
        reference = artifact_store.create_reference(
            content=sample_content,
            alias=alias,
            description="参照テスト"
        )

        # THEN
        assert "artifact_id" in reference
        assert reference["alias"] == alias
        assert "content_preview" in reference
        assert "size_bytes" in reference
        assert reference["size_bytes"] == len(sample_content.encode('utf-8'))

    def test_persistence_across_instances(self, temp_storage_dir, sample_content):
        """インスタンス間での永続化テスト"""
        # GIVEN
        store1 = create_artifact_store(storage_dir=temp_storage_dir)
        artifact_id = store1.store(sample_content, description="永続化テスト")

        # WHEN - 新しいインスタンスを作成
        store2 = create_artifact_store(storage_dir=temp_storage_dir)
        retrieved_content = store2.fetch(artifact_id)

        # THEN
        assert retrieved_content == sample_content

    def test_large_content_handling(self, artifact_store):
        """大きなコンテンツの処理テスト"""
        # GIVEN
        large_content = "x" * 100000  # 100KB

        # WHEN
        artifact_id = artifact_store.store(large_content, description="大容量テスト")
        retrieved_content = artifact_store.fetch(artifact_id)

        # THEN
        assert retrieved_content == large_content

        metadata = artifact_store.get_metadata(artifact_id)
        assert metadata.size_bytes == 100000

    def test_unicode_content_handling(self, artifact_store):
        """Unicode文字の処理テスト"""
        # GIVEN
        unicode_content = """
        日本語コンテンツ 🎌
        中文内容 🇨🇳
        Español 🇪🇸
        Русский 🇷🇺
        العربية 🌍
        """

        # WHEN
        artifact_id = artifact_store.store(unicode_content, description="Unicode テスト")
        retrieved_content = artifact_store.fetch(artifact_id)

        # THEN
        assert retrieved_content == unicode_content


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactStoreServiceFactory:
    """create_artifact_store ファクトリ関数のテスト"""

    def test_factory_function_default(self):
        """ファクトリ関数デフォルト引数テスト"""
        # WHEN
        store = create_artifact_store()

        # THEN
        assert isinstance(store, ArtifactStoreService)
        assert store._storage_dir == Path.cwd() / ".noveler" / "artifacts"

    def test_factory_function_with_params(self, temp_storage_dir):
        """ファクトリ関数パラメータ指定テスト"""
        # GIVEN
        logger_mock = Mock()

        # WHEN
        store = create_artifact_store(
            logger_service=logger_mock,
            storage_dir=temp_storage_dir
        )

        # THEN
        assert isinstance(store, ArtifactStoreService)
        assert store._storage_dir == temp_storage_dir
        assert store._logger == logger_mock


@pytest.mark.spec("SPEC-ARTIFACT-001")
class TestArtifactStoreServiceErrorHandling:
    """ArtifactStoreServiceのエラーハンドリングテスト"""

    def test_invalid_json_section_extraction(self, artifact_store):
        """不正JSONのセクション抽出エラーハンドリング"""
        # GIVEN
        invalid_json = "{ invalid json }"
        artifact_id = artifact_store.store(
            content=invalid_json,
            content_type="json"
        )

        # WHEN
        result = artifact_store.fetch(artifact_id, section="test")

        # THEN
        assert "Error extracting section" in result

    def test_corrupted_storage_file_handling(self, artifact_store, sample_content, temp_storage_dir):
        """破損ストレージファイルのハンドリング"""
        # GIVEN
        artifact_id = artifact_store.store(sample_content, description="破損テスト")
        storage_path = artifact_store._get_storage_path(artifact_id)

        # ストレージファイルを破損させる
        storage_path.write_text("{ broken json }", encoding="utf-8")

        # メモリキャッシュをクリア
        artifact_store._memory_cache.clear()

        # WHEN
        result = artifact_store.fetch(artifact_id)

        # THEN
        assert result is None
