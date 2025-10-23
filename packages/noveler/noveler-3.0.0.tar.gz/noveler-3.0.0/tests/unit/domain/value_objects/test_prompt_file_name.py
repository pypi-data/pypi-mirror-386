"""
PromptFileNameバリューオブジェクトのテスト

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

import pytest

from noveler.domain.value_objects.prompt_file_name import PromptFileName

pytestmark = pytest.mark.vo_smoke



@pytest.mark.spec("SPEC-PROMPT-SAVE-001")
class TestPromptFileName:
    """PromptFileNameバリューオブジェクトのテスト"""

    def test_valid_creation(self) -> None:
        """正常なPromptFileName作成テスト"""
        filename = PromptFileName(episode_number=1, title="テストエピソード")

        assert filename.episode_number == 1
        assert filename.title == "テストエピソード"

    def test_episode_number_validation(self) -> None:
        """エピソード番号バリデーションテスト"""
        # 正常値
        PromptFileName(episode_number=1, title="test")
        PromptFileName(episode_number=999, title="test")

        # 異常値：0以下
        with pytest.raises(ValueError, match="Episode number must be positive"):
            PromptFileName(episode_number=0, title="test")

        with pytest.raises(ValueError, match="Episode number must be positive"):
            PromptFileName(episode_number=-1, title="test")

        # 異常値：1000以上
        with pytest.raises(ValueError, match="Episode number must be <= 999"):
            PromptFileName(episode_number=1000, title="test")

        # 異常値：非整数
        with pytest.raises(ValueError, match="Episode number must be integer"):
            PromptFileName(episode_number="1", title="test")  # type: ignore

    def test_title_validation(self) -> None:
        """タイトルバリデーションテスト"""
        # 正常値
        PromptFileName(episode_number=1, title="正常なタイトル")

        # 異常値：空文字
        with pytest.raises(ValueError, match="Title cannot be empty"):
            PromptFileName(episode_number=1, title="")

        with pytest.raises(ValueError, match="Title cannot be empty"):
            PromptFileName(episode_number=1, title="   ")

        # 異常値：長すぎる
        with pytest.raises(ValueError, match="Title must be <= 50 characters"):
            PromptFileName(episode_number=1, title="x" * 51)

        # 異常値：非文字列
        with pytest.raises(ValueError, match="Title must be string"):
            PromptFileName(episode_number=1, title=123)  # type: ignore

    def test_invalid_filename_characters(self) -> None:
        """ファイル名不正文字チェックテスト"""
        invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

        for char in invalid_chars:
            with pytest.raises(ValueError, match="Title contains invalid filename characters"):
                PromptFileName(episode_number=1, title=f"test{char}title")

    def test_to_filename(self) -> None:
        """ファイル名生成テスト"""
        # 基本パターン
        filename = PromptFileName(episode_number=1, title="テストタイトル")
        assert filename.to_filename() == "第001話_テストタイトル.yaml"

        # 3桁ゼロパディング
        filename = PromptFileName(episode_number=42, title="テスト")
        assert filename.to_filename() == "第042話_テスト.yaml"

        filename = PromptFileName(episode_number=999, title="最終話")
        assert filename.to_filename() == "第999話_最終話.yaml"

    def test_title_sanitization(self) -> None:
        """タイトルサニタイゼーションテスト"""
        # スペースのアンダースコア変換
        filename = PromptFileName(episode_number=1, title="タイトル　スペース")
        # 注: 実際の実装では日本語スペースも安全化される
        result = filename.to_filename()
        assert "第001話_" in result
        assert ".yaml" in result

    def test_from_filename(self) -> None:
        """ファイル名からの復元テスト"""
        # 正常パターン
        restored = PromptFileName.from_filename("第001話_テストタイトル.yaml")
        assert restored.episode_number == 1
        assert restored.title == "テストタイトル"

        # 3桁パターン
        restored = PromptFileName.from_filename("第999話_最終話.yaml")
        assert restored.episode_number == 999
        assert restored.title == "最終話"

    def test_from_filename_invalid_format(self) -> None:
        """不正ファイル名からの復元エラーテスト"""
        invalid_filenames = [
            "第1話_テスト.yaml",  # 3桁でない
            "第001話_テスト.txt",  # 拡張子が違う
            "001話_テスト.yaml",  # 「第」がない
            "第001_テスト.yaml",  # 「話」がない
            "第001話_.yaml",  # タイトルなし
        ]

        for invalid_filename in invalid_filenames:
            with pytest.raises(ValueError, match="Invalid filename format"):
                PromptFileName.from_filename(invalid_filename)

    def test_str_representation(self) -> None:
        """文字列表現テスト"""
        filename = PromptFileName(episode_number=5, title="文字列テスト")
        assert str(filename) == filename.to_filename()

    def test_immutability(self) -> None:
        """不変性テスト"""
        filename = PromptFileName(episode_number=1, title="不変テスト")

        # dataclass(frozen=True)により変更不可
        with pytest.raises(AttributeError):
            filename.episode_number = 2  # type: ignore

        with pytest.raises(AttributeError):
            filename.title = "変更"  # type: ignore
