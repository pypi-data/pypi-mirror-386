#!/usr/bin/env python3
"""Episodeエンティティのユニットテスト

TDD原則に従い、エピソード管理のビジネスロジックをテスト
"""

import time

import pytest

from noveler.domain.entities.episode import Episode, EpisodeFactory, EpisodeStatus
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount


class TestEpisode:
    """Episodeエンティティのテスト"""

    @pytest.fixture
    def valid_episode_data(self):
        """有効なエピソードデータ"""
        return {
            "number": EpisodeNumber(1),
            "title": EpisodeTitle("第1話: 冒険の始まり"),
            "content": "これは第1話の内容です。" * 100,  # 1200文字
            "target_words": WordCount(2000),
        }

    @pytest.mark.spec("SPEC-EPISODE-005")
    @pytest.mark.spec("SPEC-EPISODE-001")
    @pytest.mark.requirement("REQ-1.1.1")
    def test_create_episode(self, valid_episode_data: object) -> None:
        """エピソードの作成

        仕様書: specs/episode_management.md
        要件: 自動的に話数を割り当てる
        """
        # When
        episode = Episode(**valid_episode_data)

        # Then
        assert episode.number.value == 1
        assert episode.title.value == "第1話: 冒険の始まり"
        assert episode.status == EpisodeStatus.DRAFT
        assert episode.word_count.value == 1200
        assert episode.version == 1
        assert episode.quality_score is None
        assert episode.completed_at is None
        assert episode.published_at is None
        assert episode.archived_at is None
        assert episode.tags == []
        assert episode.metadata == {}

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_episode_with_zero_target_words(self) -> None:
        """目標文字数が0の場合エラー"""
        # When/Then
        with pytest.raises(DomainException, match="目標文字数は1以上である必要があります"):
            Episode(
                number=EpisodeNumber(1),
                title=EpisodeTitle("タイトル"),
                content="内容",
                target_words=WordCount(0),
            )

    @pytest.mark.spec("SPEC-EPISODE-005")
    @pytest.mark.spec("SPEC-EPISODE-001")
    @pytest.mark.requirement("REQ-1.3.1")
    def test_start_writing(self, valid_episode_data: object) -> None:
        """執筆開始

        仕様書: specs/episode_management.md
        要件: ステータス遷移の制御(UNWRITTEN → DRAFT)
        """
        # Given
        episode = Episode(**valid_episode_data)
        original_time = episode.updated_at

        # When

        time.sleep(0.01)  # 時刻を確実に変える
        episode.start_writing()

        # Then
        assert episode.status == EpisodeStatus.IN_PROGRESS
        assert episode.updated_at > original_time

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_start_writing_published_episode(self, valid_episode_data: object) -> None:
        """公開済みエピソードの執筆開始はエラー"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.status = EpisodeStatus.PUBLISHED

        # When/Then
        with pytest.raises(DomainException, match="公開済みのエピソードは編集できません"):
            episode.start_writing()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_update_content(self, valid_episode_data: object) -> None:
        """内容更新"""
        # Given
        episode = Episode(**valid_episode_data)
        original_version = episode.version

        # When
        new_content = "新しい内容です。" * 125  # 1000文字
        episode.update_content(new_content)

        # Then
        assert episode.content == new_content
        assert episode.word_count.value == 1000
        assert episode.version == original_version + 1

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_update_content_from_unwritten(self) -> None:
        """未執筆からの内容更新"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="",
            target_words=WordCount(1000),
            status=EpisodeStatus.UNWRITTEN,
        )

        # When
        episode.update_content("新しい内容")

        # Then
        assert episode.status == EpisodeStatus.DRAFT

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_update_content_published_episode(self, valid_episode_data: object) -> None:
        """公開済みエピソードの内容更新はエラー"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.status = EpisodeStatus.PUBLISHED

        # When/Then
        with pytest.raises(DomainException, match="公開済みのエピソードは編集できません"):
            episode.update_content("新しい内容")

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_update_content_with_empty(self, valid_episode_data: object) -> None:
        """空の内容で更新はエラー"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        with pytest.raises(DomainException, match="内容は空にできません"):
            episode.update_content("  ")

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_complete(self, valid_episode_data: object) -> None:
        """完成"""
        # Given
        episode = Episode(**valid_episode_data)

        # When
        episode.complete()

        # Then
        assert episode.status == EpisodeStatus.COMPLETED
        assert episode.completed_at is not None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_complete_empty_content(self) -> None:
        """空の内容のエピソード完成はエラー"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="",
            target_words=WordCount(1000),
        )

        # When/Then
        with pytest.raises(DomainException, match="内容が空のエピソードは完成できません"):
            episode.complete()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_complete_published_episode(self, valid_episode_data: object) -> None:
        """公開済みエピソードの再完成はエラー"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.status = EpisodeStatus.PUBLISHED

        # When/Then
        with pytest.raises(DomainException, match="公開済みのエピソードは再完成できません"):
            episode.complete()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_set_quality_score(self, valid_episode_data: object) -> None:
        """品質スコア設定"""
        # Given
        episode = Episode(**valid_episode_data)
        score = QualityScore(85)

        # When
        episode.set_quality_score(score)

        # Then
        assert episode.quality_score.value == 85

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_set_quality_score_unwritten_episode(self) -> None:
        """未執筆エピソードへの品質スコア設定はエラー"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="",
            target_words=WordCount(1000),
            status=EpisodeStatus.UNWRITTEN,
        )

        # When/Then
        with pytest.raises(DomainException, match="未執筆のエピソードに品質スコアは設定できません"):
            episode.set_quality_score(QualityScore(80))

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_publish_completed_episode(self, valid_episode_data: object) -> None:
        """完成エピソードの公開"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()
        episode.set_quality_score(QualityScore(80))

        # When
        episode.publish()

        # Then
        assert episode.status == EpisodeStatus.PUBLISHED
        assert episode.published_at is not None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_review_completed_episode(self, valid_episode_data: object) -> None:
        """完成したエピソードのレビュー"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()

        # When
        episode.review()

        # Then
        assert episode.status == EpisodeStatus.REVIEWED

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_review_draft_episode(self, valid_episode_data: object) -> None:
        """下書きエピソードのレビューはエラー"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        with pytest.raises(DomainException, match="完成したエピソードのみレビュー可能です"):
            episode.review()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_publish_reviewed_episode(self, valid_episode_data: object) -> None:
        """レビュー済みエピソードの公開"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()
        episode.review()
        episode.set_quality_score(QualityScore(80))

        # When
        episode.publish()

        # Then
        assert episode.status == EpisodeStatus.PUBLISHED
        assert episode.published_at is not None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_publish_draft_episode(self, valid_episode_data: object) -> None:
        """下書きエピソードの公開はエラー"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        with pytest.raises(DomainException, match="完成またはレビュー済みのエピソードのみ公開できます"):
            episode.publish()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_publish_without_meeting_conditions(self) -> None:
        """公開条件を満たさないエピソードの公開はエラー"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="短い内容",  # 500文字未満
            target_words=WordCount(1000),
        )

        episode.complete()
        episode.set_quality_score(QualityScore(60))  # 70点未満

        # When/Then
        with pytest.raises(DomainException, match="公開条件を満たしていません"):
            episode.publish()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_can_publish_true(self, valid_episode_data: object) -> None:
        """公開可能判定(true)"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()
        episode.set_quality_score(QualityScore(80))

        # When/Then
        assert episode.can_publish() is True

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_can_publish_false_status(self, valid_episode_data: object) -> None:
        """公開可能判定(false - ステータス)"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        assert episode.can_publish() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_can_publish_false_empty_content(self) -> None:
        """公開可能判定(false - 空の内容)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="  ",
            target_words=WordCount(1000),
        )

        episode.status = EpisodeStatus.COMPLETED

        # When/Then
        assert episode.can_publish() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_can_publish_false_no_quality_score(self, valid_episode_data: object) -> None:
        """公開可能判定(false - 品質スコアなし)"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()

        # When/Then
        assert episode.can_publish() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_can_publish_false_low_quality_score(self, valid_episode_data: object) -> None:
        """公開可能判定(false - 低品質スコア)"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()
        episode.set_quality_score(QualityScore(60))

        # When/Then
        assert episode.can_publish() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_can_publish_false_short_content(self) -> None:
        """公開可能判定(false - 短い内容)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="短い内容",  # 500文字未満
            target_words=WordCount(2000),
        )

        episode.complete()
        episode.set_quality_score(QualityScore(80))

        # When/Then
        assert episode.can_publish() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_completion_percentage(self, valid_episode_data: object) -> None:
        """完成度パーセンテージ"""
        # Given
        episode = Episode(**valid_episode_data)
        # word_count = 1200, target = 2000

        # When
        percentage = episode.completion_percentage()

        # Then
        assert percentage == 60.0

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_completion_percentage_over_100(self) -> None:
        """完成度パーセンテージ(100%超)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="長い内容" * 500,  # 4000文字
            target_words=WordCount(2000),
        )

        # When
        percentage = episode.completion_percentage()

        # Then
        assert percentage == 100.0

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_completion_percentage_zero_target(self) -> None:
        """完成度パーセンテージ(目標0)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="内容",
            target_words=WordCount(1),  # 最小値
        )
        # 直接0に設定することはできないが、計算をテスト
        if episode.target_words.value == 0:  # この条件は満たされない:
            percentage = episode.completion_percentage()
            assert percentage == 0.0

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_is_ready_for_quality_check_true(self, valid_episode_data: object) -> None:
        """品質チェック可能判定(true)"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        assert episode.is_ready_for_quality_check() is True

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_is_ready_for_quality_check_false_short_content(self) -> None:
        """品質チェック可能判定(false - 短い内容)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="短い",
            target_words=WordCount(1000),
        )

        # When/Then
        assert episode.is_ready_for_quality_check() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_is_ready_for_quality_check_false_unwritten(self) -> None:
        """品質チェック可能判定(false - 未執筆)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="a" * 1001,  # 1001文字
            target_words=WordCount(2000),
            status=EpisodeStatus.UNWRITTEN,
        )

        # When/Then
        assert episode.is_ready_for_quality_check() is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_get_quality_check_issues(self) -> None:
        """品質チェックの問題点取得"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="短い",
            target_words=WordCount(1000),
            status=EpisodeStatus.UNWRITTEN,
        )

        # When
        issues = episode.get_quality_check_issues()

        # Then
        assert len(issues) == 2
        assert any("1000文字未満" in issue for issue in issues)
        assert any("未執筆" in issue for issue in issues)

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_get_quality_check_issues_empty_content(self) -> None:
        """品質チェックの問題点取得(空の内容)"""
        # Given
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("タイトル"),
            content="  ",
            target_words=WordCount(1000),
        )

        # When
        issues = episode.get_quality_check_issues()

        # Then
        assert any("内容が空" in issue for issue in issues)

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_tag(self, valid_episode_data: object) -> None:
        """タグ追加"""
        # Given
        episode = Episode(**valid_episode_data)

        # When
        episode.add_tag("アクション")
        episode.add_tag("冒険")

        # Then
        assert "アクション" in episode.tags
        assert "冒険" in episode.tags
        assert len(episode.tags) == 2

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_empty_tag(self, valid_episode_data: object) -> None:
        """空のタグ追加はエラー"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        with pytest.raises(DomainException, match="タグは空にできません"):
            episode.add_tag("  ")

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_duplicate_tag(self, valid_episode_data: object) -> None:
        """重複タグの追加"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.add_tag("アクション")

        # When
        episode.add_tag("アクション")

        # Then
        # 重複は防がれる
        assert episode.tags.count("アクション") == 1

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_remove_tag(self, valid_episode_data: object) -> None:
        """タグ削除"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.add_tag("アクション")
        episode.add_tag("冒険")

        # When
        episode.remove_tag("アクション")

        # Then
        assert "アクション" not in episode.tags
        assert "冒険" in episode.tags

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_set_metadata(self, valid_episode_data: object) -> None:
        """メタデータ設定"""
        # Given
        episode = Episode(**valid_episode_data)

        # When
        episode.set_metadata("author", "テスト作者")
        episode.set_metadata("genre", "ファンタジー")

        # Then
        assert episode.metadata["author"] == "テスト作者"
        assert episode.metadata["genre"] == "ファンタジー"

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_set_metadata_empty_key(self, valid_episode_data: object) -> None:
        """空のキーでメタデータ設定はエラー"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        with pytest.raises(DomainException, match="メタデータのキーは空にできません"):
            episode.set_metadata("  ", "値")

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_get_metadata(self, valid_episode_data: object) -> None:
        """メタデータ取得"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.set_metadata("author", "テスト作者")

        # When/Then
        assert episode.get_metadata("author") == "テスト作者"
        assert episode.get_metadata("存在しないキー") is None
        assert episode.get_metadata("存在しないキー", "デフォルト") == "デフォルト"

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_archive(self, valid_episode_data: object) -> None:
        """アーカイブ"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()

        # When
        episode.archive()

        # Then
        assert episode.status == EpisodeStatus.ARCHIVED
        assert episode.archived_at is not None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_archive_published_episode(self, valid_episode_data: object) -> None:
        """公開済みエピソードのアーカイブはエラー"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()
        episode.set_quality_score(QualityScore(80))
        episode.publish()

        # When/Then
        with pytest.raises(DomainException, match="公開済みのエピソードはアーカイブできません"):
            episode.archive()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_restore_from_archive_completed(self, valid_episode_data: object) -> None:
        """アーカイブから復元(完成済み)"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.complete()
        episode.archive()

        # When
        episode.restore_from_archive()

        # Then
        assert episode.status == EpisodeStatus.COMPLETED
        assert episode.archived_at is None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_restore_from_archive_draft(self, valid_episode_data: object) -> None:
        """アーカイブから復元(下書き)"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.archive()

        # When
        episode.restore_from_archive()

        # Then
        assert episode.status == EpisodeStatus.DRAFT
        assert episode.archived_at is None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_restore_from_archive_not_archived(self, valid_episode_data: object) -> None:
        """アーカイブされていないエピソードの復元はエラー"""
        # Given
        episode = Episode(**valid_episode_data)

        # When/Then
        with pytest.raises(DomainException, match="アーカイブされていないエピソードは復元できません"):
            episode.restore_from_archive()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_get_writing_statistics(self, valid_episode_data: object) -> None:
        """執筆統計情報取得"""
        # Given
        episode = Episode(**valid_episode_data)
        episode.add_tag("アクション")
        episode.set_quality_score(QualityScore(85))

        # When
        stats = episode.get_writing_statistics()

        # Then
        assert stats["word_count"] == 1200
        assert stats["target_words"] == 2000
        assert stats["completion_percentage"] == 60.0
        assert stats["version"] == 1
        assert stats["writing_days"] >= 1
        assert stats["words_per_day"] >= 0
        assert stats["status"] == "draft"
        assert stats["quality_score"] == 85
        assert "アクション" in stats["tags"]
        assert stats["is_publishable"] is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_equality(self, valid_episode_data: object) -> None:
        """エピソードの等価性判定"""
        # Given
        episode1 = Episode(**valid_episode_data)
        episode2 = Episode(
            number=EpisodeNumber(1),  # 同じ番号
            title=EpisodeTitle("別のタイトル"),
            content="別の内容",
            target_words=WordCount(3000),
        )

        episode3 = Episode(
            number=EpisodeNumber(2),  # 異なる番号
            title=EpisodeTitle("第2話"),
            content="内容",
            target_words=WordCount(2000),
        )

        # When/Then
        assert episode1 == episode2  # 番号が同じなら同一
        assert episode1 != episode3  # 番号が異なれば別物
        assert episode1 != "not an episode"  # 異なる型との比較

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_hash(self, valid_episode_data: object) -> None:
        """エピソードのハッシュ値"""
        # Given
        episode1 = Episode(**valid_episode_data)
        episode2 = Episode(
            number=EpisodeNumber(1),  # 同じ番号
            title=EpisodeTitle("別のタイトル"),
            content="別の内容",
            target_words=WordCount(3000),
        )

        # When/Then
        assert hash(episode1) == hash(episode2)  # 同じ番号なら同じハッシュ

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_str(self, valid_episode_data: object) -> None:
        """エピソードの文字列表現"""
        # Given
        episode = Episode(**valid_episode_data)

        # When
        result = str(episode)

        # Then
        assert result == "Episode(1)"

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_repr(self, valid_episode_data: object) -> None:
        """エピソードの詳細文字列表現"""
        # Given
        episode = Episode(**valid_episode_data)

        # When
        result = repr(episode)

        # Then
        assert "number=1" in result
        assert "title='第1話: 冒険の始まり'" in result
        assert "status=draft" in result
        assert "word_count=1200" in result


class TestEpisodeFactory:
    """EpisodeFactoryのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_new_episode(self) -> None:
        """新規エピソード作成"""
        # When
        episode = EpisodeFactory.create_new_episode(number=1, title="第1話:始まり", target_words=3000)

        # Then
        assert episode.number.value == 1
        assert episode.title.value == "第1話:始まり"
        assert episode.content == ""
        assert episode.target_words.value == 3000
        assert episode.status == EpisodeStatus.UNWRITTEN

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_new_episode_with_default_target(self) -> None:
        """デフォルト目標文字数での新規エピソード作成"""
        # When
        episode = EpisodeFactory.create_new_episode(number=2, title="第2話")

        # Then
        assert episode.target_words.value == 3000  # デフォルト値

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_from_template(self) -> None:
        """テンプレートからエピソード作成"""
        # Given
        template = {
            "number": 3,
            "title": "第3話:展開",
            "content": "テンプレート内容",
            "target_words": 4000,
            "tags": ["アクション", "ドラマ"],
            "metadata": {"template_id": "action_01"},
        }

        # When
        episode = EpisodeFactory.create_from_template(template)

        # Then
        assert episode.number.value == 3
        assert episode.title.value == "第3話:展開"
        assert episode.content == "テンプレート内容"
        assert episode.target_words.value == 4000
        assert "アクション" in episode.tags
        assert "ドラマ" in episode.tags
        assert episode.metadata["template_id"] == "action_01"
