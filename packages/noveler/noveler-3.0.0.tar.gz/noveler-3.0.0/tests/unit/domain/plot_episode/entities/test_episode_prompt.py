"""
EpisodePromptエンティティのテスト

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

import pytest
from datetime import datetime
pytestmark = pytest.mark.plot_episode



from noveler.domain.entities.episode_prompt import EpisodePrompt
from noveler.domain.value_objects.prompt_file_name import PromptFileName


@pytest.mark.spec("SPEC-PROMPT-SAVE-001")
class TestEpisodePrompt:
    """EpisodePromptエンティティのテスト"""

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-VALID_CREATION")
    def test_valid_creation(self) -> None:
        """正常なEpisodePrompt作成テスト"""
        prompt_content = "This is a detailed episode prompt with more than 100 characters for testing purposes. It should contain enough content to pass validation."

        prompt = EpisodePrompt(episode_number=1, title="テストエピソード", prompt_content=prompt_content)

        assert prompt.episode_number == 1
        assert prompt.title == "テストエピソード"
        assert prompt.prompt_content == prompt_content
        assert prompt.template_version == "1.0"
        assert prompt.generation_mode == "enhanced"
        assert prompt.quality_level == "detailed"
        assert isinstance(prompt.generation_timestamp, datetime)

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-BUSINESS_RULES_VALID")
    def test_business_rules_validation(self) -> None:
        """ビジネスルールバリデーションテスト"""
        long_content = "x" * 100  # 最小100文字

        # 正常値
        EpisodePrompt(episode_number=1, title="test", prompt_content=long_content)

        # 異常値：エピソード番号
        with pytest.raises(ValueError, match="Episode number must be positive"):
            EpisodePrompt(episode_number=0, title="test", prompt_content=long_content)

        # 異常値：タイトル
        with pytest.raises(ValueError, match="Episode title cannot be empty"):
            EpisodePrompt(episode_number=1, title="", prompt_content=long_content)

        with pytest.raises(ValueError, match="Episode title cannot be empty"):
            EpisodePrompt(episode_number=1, title="   ", prompt_content=long_content)

        # 異常値：プロンプト内容
        with pytest.raises(ValueError, match="Prompt content cannot be empty"):
            EpisodePrompt(episode_number=1, title="test", prompt_content="")

        with pytest.raises(ValueError, match="Prompt content too short"):
            EpisodePrompt(episode_number=1, title="test", prompt_content="short")

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-GET_FILE_NAME")
    def test_get_file_name(self) -> None:
        """ファイル名取得テスト"""
        prompt = EpisodePrompt(episode_number=5, title="ファイル名テスト", prompt_content="x" * 100)

        filename = prompt.get_file_name()
        assert isinstance(filename, PromptFileName)
        assert filename.episode_number == 5
        assert filename.title == "ファイル名テスト"

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-GET_YAML_CONTENT")
    def test_get_yaml_content(self) -> None:
        """YAML内容取得テスト"""
        prompt_content = "Test prompt content with sufficient length for validation purposes. This should be more than 100 characters."

        prompt = EpisodePrompt(
            episode_number=7,
            title="YAMLテスト",
            prompt_content=prompt_content,
            template_version="2.0",
            generation_mode="premium",
            quality_level="high",
        )

        yaml_content = prompt.get_yaml_content()

        # メタデータ検証
        assert yaml_content["metadata"]["spec_id"] == "SPEC-PROMPT-SAVE-001"
        assert yaml_content["metadata"]["episode_number"] == 7
        assert yaml_content["metadata"]["title"] == "YAMLテスト"
        assert yaml_content["metadata"]["template_version"] == "2.0"
        assert yaml_content["metadata"]["generation_mode"] == "premium"
        assert yaml_content["metadata"]["quality_level"] == "high"

        # コンテンツ検証
        assert yaml_content["prompt_content"] == prompt_content

        # バリデーション検証
        assert yaml_content["validation"]["content_length"] == len(prompt_content)
        assert yaml_content["validation"]["quality_validated"] is True

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-FROM_YAML_DATA")
    def test_from_yaml_data(self) -> None:
        """YAMLデータからの復元テスト"""
        yaml_data = {
            "metadata": {
                "episode_number": 10,
                "title": "復元テスト",
                "generation_timestamp": "2023-01-01T10:00:00",
                "template_version": "1.5",
                "generation_mode": "advanced",
                "quality_level": "ultra",
            },
            "prompt_content": "Restored prompt content with adequate length for testing restoration functionality from YAML data.",
            "content_sections": {"section1": "data1", "section2": "data2"},
        }

        prompt = EpisodePrompt.from_yaml_data(yaml_data)

        assert prompt.episode_number == 10
        assert prompt.title == "復元テスト"
        assert prompt.template_version == "1.5"
        assert prompt.generation_mode == "advanced"
        assert prompt.quality_level == "ultra"
        assert prompt.content_sections == {"section1": "data1", "section2": "data2"}

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-UPDATE_CONTENT")
    def test_update_content(self) -> None:
        """プロンプト内容更新テスト"""
        prompt = EpisodePrompt(episode_number=1, title="更新テスト", prompt_content="x" * 100)

        original_timestamp = prompt.generation_timestamp

        # 正常更新
        new_content = (
            "Updated content that is definitely longer than 100 characters for proper validation and testing purposes."
        )
        prompt.update_content(new_content)

        assert prompt.prompt_content == new_content
        assert prompt.generation_timestamp > original_timestamp

        # 異常値：空内容
        with pytest.raises(ValueError, match="New content cannot be empty"):
            prompt.update_content("")

        # 異常値：短すぎる
        with pytest.raises(ValueError, match="New content too short"):
            prompt.update_content("short")

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-ADD_CONTENT_SECTION")
    def test_add_content_section(self) -> None:
        """コンテンツセクション追加テスト"""
        prompt = EpisodePrompt(episode_number=1, title="セクションテスト", prompt_content="x" * 100)

        # 正常追加
        prompt.add_content_section("scenes", ["scene1", "scene2"])
        prompt.add_content_section("characters", {"main": "protagonist"})

        assert prompt.content_sections["scenes"] == ["scene1", "scene2"]
        assert prompt.content_sections["characters"] == {"main": "protagonist"}

        # 異常値：空セクション名
        with pytest.raises(ValueError, match="Section name cannot be empty"):
            prompt.add_content_section("", "data")

        with pytest.raises(ValueError, match="Section name cannot be empty"):
            prompt.add_content_section("   ", "data")

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-GET_CONTENT_QUALITY_")
    def test_get_content_quality_score(self) -> None:
        """コンテンツ品質スコア計算テスト"""
        # 基本品質
        prompt = EpisodePrompt(
            episode_number=1,
            title="品質テスト",
            prompt_content="x" * 1000,  # 1000文字
        )

        # セクション追加で品質向上
        for i in range(5):
            prompt.add_content_section(f"section{i}", f"data{i}")

        score = prompt.get_content_quality_score()
        assert 0.0 <= score <= 1.0

        # 高品質コンテンツ
        high_quality_prompt = EpisodePrompt(
            episode_number=1,
            title="高品質テスト",
            prompt_content="x" * 2000,  # 2000文字
        )

        for i in range(10):
            high_quality_prompt.add_content_section(f"section{i}", f"data{i}")

        high_score = high_quality_prompt.get_content_quality_score()
        assert high_score > score
        assert high_score >= 0.8

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-IS_HIGH_QUALITY")
    def test_is_high_quality(self) -> None:
        """高品質判定テスト"""
        # 低品質
        low_quality = EpisodePrompt(episode_number=1, title="低品質", prompt_content="x" * 100)

        assert not low_quality.is_high_quality()

        # 高品質
        high_quality = EpisodePrompt(episode_number=1, title="高品質テスト", prompt_content="x" * 2000)

        for i in range(10):
            high_quality.add_content_section(f"section{i}", f"data{i}")

        assert high_quality.is_high_quality()

    @pytest.mark.spec("SPEC-EPISODE_PROMPT-CONTENT_SECTIONS_DEF")
    def test_content_sections_default(self) -> None:
        """コンテンツセクションデフォルト値テスト"""
        prompt = EpisodePrompt(episode_number=1, title="デフォルトテスト", prompt_content="x" * 100)

        assert prompt.content_sections == {}
        assert isinstance(prompt.content_sections, dict)
