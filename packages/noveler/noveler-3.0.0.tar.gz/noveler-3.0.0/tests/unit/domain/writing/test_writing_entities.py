"""執筆管理ドメインエンティティのテスト

TDD準拠テスト:
    - Episode
- WritingRecord
- WritingSession
- EpisodeStatus (Enum)


仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime, timedelta

import pytest

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.writing.entities import (
    Episode,
    EpisodeStatus,
    WritingRecord,
    WritingSession,
)
from noveler.domain.writing.value_objects import (
    EpisodeNumber,
    EpisodeTitle,
    PublicationSchedule,
    PublicationStatus,
    WordCount,
    WritingDuration,
    WritingPhase,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestEpisodeStatus:
    """EpisodeStatus(Enum)のテストクラス"""

    def test_episode_status_values(self) -> None:
        """エピソードステータス値テスト"""
        assert EpisodeStatus.UNWRITTEN.value == "未執筆"
        assert EpisodeStatus.IN_PROGRESS.value == "執筆中"
        assert EpisodeStatus.DRAFT_COMPLETE.value == "初稿完了"
        assert EpisodeStatus.REVISED.value == "推敲済み"
        assert EpisodeStatus.PUBLISHED.value == "公開済み"

    def test_episode_status_enum_count(self) -> None:
        """エピソードステータス数テスト"""
        assert len(EpisodeStatus) == 5


class TestEpisode:
    """Episodeエンティティのテストクラス"""

    @pytest.fixture
    def basic_episode(self) -> Episode:
        """基本エピソード"""
        return Episode(
            project_id="test_project",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("第1話:始まり"),
            content="これは小説の内容です。",
        )

    @pytest.fixture
    def publishable_episode(self) -> Episode:
        """公開可能エピソード(2000文字以上)"""
        content = "これは十分な長さの小説内容です。" * 100  # 2000文字以上になるよう
        episode = Episode(
            project_id="test_project",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("第1話:長編"),
            content=content,
        )

        episode.status = EpisodeStatus.REVISED
        return episode

    def test_episode_creation_with_defaults(self) -> None:
        """デフォルト値でのエピソード作成テスト"""
        episode = Episode()

        assert episode.id is not None
        assert episode.project_id == ""
        assert episode.episode_number is None
        assert episode.title is None
        assert episode.content == ""
        assert episode.word_count is None  # 空コンテンツなので None
        assert episode.status == EpisodeStatus.UNWRITTEN
        assert episode.phase == WritingPhase.DRAFT
        assert episode.publication_status == PublicationStatus.UNPUBLISHED
        assert isinstance(episode.created_at, datetime)
        assert isinstance(episode.updated_at, datetime)
        assert episode.published_at is None
        assert episode.publication_schedule is None
        assert episode.plot_info == {}

    def test_episode_creation_with_values(self, basic_episode: Episode) -> None:
        """値指定でのエピソード作成テスト"""
        assert basic_episode.project_id == "test_project"
        assert basic_episode.episode_number.value == 1
        assert basic_episode.title.value == "第1話:始まり"
        assert basic_episode.content == "これは小説の内容です。"
        assert basic_episode.status == EpisodeStatus.UNWRITTEN

    def test_episode_post_init_word_count_calculation(self) -> None:
        """__post_init__での文字数自動計算テスト"""
        content = "テスト内容"
        episode = Episode(content=content)

        assert episode.word_count is not None
        assert episode.word_count.value == len(content)

    def test_episode_post_init_no_word_count_for_empty_content(self) -> None:
        """空コンテンツでの文字数計算なしテスト"""
        episode = Episode(content="")

        assert episode.word_count is None

    def test_update_content(self, basic_episode: Episode) -> None:
        """内容更新テスト"""
        new_content = "新しい小説の内容です。これはより長い内容です。"
        original_updated_at = basic_episode.updated_at

        basic_episode.update_content(new_content)

        assert basic_episode.content == new_content
        assert basic_episode.word_count.value == len(new_content)
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_update_title(self, basic_episode: Episode) -> None:
        """タイトル更新テスト"""
        new_title = EpisodeTitle("第1話:新しいタイトル")
        original_updated_at = basic_episode.updated_at

        basic_episode.update_title(new_title)

        assert basic_episode.title == new_title
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_advance_phase_progression(self, basic_episode: Episode) -> None:
        """フェーズ進行テスト"""
        original_updated_at = basic_episode.updated_at

        # DRAFT → REVISION
        assert basic_episode.phase == WritingPhase.DRAFT
        basic_episode.advance_phase()
        assert basic_episode.phase == WritingPhase.REVISION
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

        updated_at_after_first = basic_episode.updated_at

        # REVISION → FINAL_CHECK
        basic_episode.advance_phase()
        assert basic_episode.phase == WritingPhase.FINAL_CHECK
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        updated_at_after_first_jst = updated_at_after_first.astimezone(JST) if updated_at_after_first.tzinfo else updated_at_after_first.replace(tzinfo=JST)
        assert updated_at_jst > updated_at_after_first_jst

        # FINAL_CHECK → PUBLISHED
        basic_episode.advance_phase()
        assert basic_episode.phase == WritingPhase.PUBLISHED

    def test_advance_phase_no_change_at_end(self, basic_episode: Episode) -> None:
        """最終フェーズでの進行無しテスト"""
        basic_episode.phase = WritingPhase.PUBLISHED

        basic_episode.advance_phase()

        # 最終フェーズなので変更されない
        assert basic_episode.phase == WritingPhase.PUBLISHED

    def test_revert_phase_regression(self, basic_episode: Episode) -> None:
        """フェーズ退行テスト"""
        basic_episode.phase = WritingPhase.FINAL_CHECK
        original_updated_at = basic_episode.updated_at

        # FINAL_CHECK → REVISION
        basic_episode.revert_phase()
        assert basic_episode.phase == WritingPhase.REVISION
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

        # REVISION → DRAFT
        basic_episode.revert_phase()
        assert basic_episode.phase == WritingPhase.DRAFT

    def test_revert_phase_no_change_at_start(self, basic_episode: Episode) -> None:
        """最初フェーズでの退行無しテスト"""
        assert basic_episode.phase == WritingPhase.DRAFT

        basic_episode.revert_phase()

        # 最初フェーズなので変更されない
        assert basic_episode.phase == WritingPhase.DRAFT

    def test_schedule_publication_success(self, basic_episode: Episode) -> None:
        """公開スケジュール設定成功テスト"""
        basic_episode.phase = WritingPhase.FINAL_CHECK
        schedule = PublicationSchedule(project_now().datetime + timedelta(days=1))
        original_updated_at = basic_episode.updated_at

        basic_episode.schedule_publication(schedule)

        assert basic_episode.publication_schedule == schedule
        assert basic_episode.publication_status == PublicationStatus.SCHEDULED
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_schedule_publication_wrong_phase_error(self, basic_episode: Episode) -> None:
        """間違ったフェーズでの公開スケジュール設定エラーテスト"""
        assert basic_episode.phase == WritingPhase.DRAFT  # FINAL_CHECKではない
        schedule = PublicationSchedule(project_now().datetime + timedelta(days=1))

        with pytest.raises(ValueError, match="最終チェックフェーズでのみ公開スケジュールを設定できます"):
            basic_episode.schedule_publication(schedule)

    def test_start_writing_success(self, basic_episode: Episode) -> None:
        """執筆開始成功テスト"""
        assert basic_episode.status == EpisodeStatus.UNWRITTEN
        original_updated_at = basic_episode.updated_at

        basic_episode.start_writing()

        assert basic_episode.status == EpisodeStatus.IN_PROGRESS
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_start_writing_wrong_status_error(self, basic_episode: Episode) -> None:
        """間違ったステータスでの執筆開始エラーテスト"""
        basic_episode.status = EpisodeStatus.IN_PROGRESS

        with pytest.raises(ValueError, match="執筆開始できません。現在のステータス: 執筆中"):
            basic_episode.start_writing()

    def test_complete_draft_success(self, basic_episode: Episode) -> None:
        """初稿完了成功テスト"""
        basic_episode.status = EpisodeStatus.IN_PROGRESS
        basic_episode.content = "十分な内容がある小説です。"
        original_updated_at = basic_episode.updated_at

        basic_episode.complete_draft()

        assert basic_episode.status == EpisodeStatus.DRAFT_COMPLETE
        assert basic_episode.word_count is not None
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_complete_draft_wrong_status_error(self, basic_episode: Episode) -> None:
        """間違ったステータスでの初稿完了エラーテスト"""
        assert basic_episode.status == EpisodeStatus.UNWRITTEN  # IN_PROGRESSではない

        with pytest.raises(ValueError, match="初稿完了できません。現在のステータス: 未執筆"):
            basic_episode.complete_draft()

    def test_complete_draft_empty_content_error(self, basic_episode: Episode) -> None:
        """空コンテンツでの初稿完了エラーテスト"""
        basic_episode.status = EpisodeStatus.IN_PROGRESS
        basic_episode.content = "   "  # 空白のみ

        with pytest.raises(ValueError, match="内容が空のため初稿完了できません"):
            basic_episode.complete_draft()

    def test_complete_revision_success(self, basic_episode: Episode) -> None:
        """推敲完了成功テスト"""
        basic_episode.status = EpisodeStatus.DRAFT_COMPLETE
        basic_episode.content = "推敲された小説内容です。"
        original_updated_at = basic_episode.updated_at

        basic_episode.complete_revision()

        assert basic_episode.status == EpisodeStatus.REVISED
        assert basic_episode.word_count is not None
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_complete_revision_wrong_status_error(self, basic_episode: Episode) -> None:
        """間違ったステータスでの推敲完了エラーテスト"""
        assert basic_episode.status == EpisodeStatus.UNWRITTEN  # DRAFT_COMPLETEではない

        with pytest.raises(ValueError, match="推敲完了できません。現在のステータス: 未執筆"):
            basic_episode.complete_revision()

    def test_publish_success(self, publishable_episode: Episode) -> None:
        """公開成功テスト"""
        original_updated_at = publishable_episode.updated_at

        publishable_episode.publish()

        assert publishable_episode.status == EpisodeStatus.PUBLISHED
        assert publishable_episode.phase == WritingPhase.PUBLISHED
        assert publishable_episode.publication_status == PublicationStatus.PUBLISHED
        assert publishable_episode.published_at is not None
        # タイムゾーンを統一して比較
        updated_at_jst = publishable_episode.updated_at.astimezone(JST) if publishable_episode.updated_at.tzinfo else publishable_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_publish_not_ready_error(self, basic_episode: Episode) -> None:
        """公開準備未完了での公開エラーテスト"""
        # basic_episodeは文字数不足で公開不可
        with pytest.raises(ValueError, match="公開条件を満たしていません"):
            basic_episode.publish()

    def test_can_publish_revised_status_sufficient_content(self, publishable_episode: Episode) -> None:
        """推敲済み・十分な内容での公開可能判定テスト"""
        assert publishable_episode.status == EpisodeStatus.REVISED
        assert publishable_episode.can_publish() is True

    def test_can_publish_draft_complete_status_sufficient_content(self) -> None:
        """初稿完了・十分な内容での公開可能判定テスト"""
        content = "これは十分な長さの初稿完了小説です。" * 100  # 2000文字以上
        episode = Episode(content=content)
        episode.status = EpisodeStatus.DRAFT_COMPLETE

        assert episode.can_publish() is True

    def test_can_publish_wrong_status(self, basic_episode: Episode) -> None:
        """間違ったステータスでの公開不可判定テスト"""
        basic_episode.content = "十分な長さの内容" * 100  # 内容は十分
        assert basic_episode.status == EpisodeStatus.UNWRITTEN  # 不適切なステータス

        assert basic_episode.can_publish() is False

    def test_can_publish_insufficient_word_count(self, basic_episode: Episode) -> None:
        """文字数不足での公開不可判定テスト"""
        basic_episode.status = EpisodeStatus.REVISED  # ステータスは適切
        basic_episode.content = "短い内容"  # 2000文字未満
        basic_episode.word_count = WordCount(len(basic_episode.content))

        assert basic_episode.can_publish() is False

    def test_can_publish_no_word_count(self, basic_episode: Episode) -> None:
        """文字数未設定での公開不可判定テスト"""
        basic_episode.status = EpisodeStatus.REVISED
        basic_episode.word_count = None

        assert basic_episode.can_publish() is False

    def test_can_publish_empty_content(self, basic_episode: Episode) -> None:
        """空コンテンツでの公開不可判定テスト"""
        basic_episode.status = EpisodeStatus.REVISED
        basic_episode.content = "   "  # 空白のみ
        basic_episode.word_count = WordCount(2500)  # 文字数は十分だが内容が空

        assert basic_episode.can_publish() is False

    def test_withdraw_success(self, publishable_episode: Episode) -> None:
        """公開取り下げ成功テスト"""
        publishable_episode.publication_status = PublicationStatus.PUBLISHED
        original_updated_at = publishable_episode.updated_at

        publishable_episode.withdraw()

        assert publishable_episode.publication_status == PublicationStatus.WITHDRAWN
        # タイムゾーンを統一して比較
        updated_at_jst = publishable_episode.updated_at.astimezone(JST) if publishable_episode.updated_at.tzinfo else publishable_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

    def test_withdraw_not_published_error(self, basic_episode: Episode) -> None:
        """未公開での取り下げエラーテスト"""
        assert basic_episode.publication_status == PublicationStatus.UNPUBLISHED

        with pytest.raises(ValueError, match="公開済みのエピソードのみ取り下げ可能です"):
            basic_episode.withdraw()

    def test_update_plot_info(self, basic_episode: Episode) -> None:
        """プロット情報更新テスト"""
        plot_info = {"chapter": 1, "scene": "導入部", "word_count_target": 3500}
        original_updated_at = basic_episode.updated_at

        basic_episode.update_plot_info(plot_info)

        assert basic_episode.plot_info == plot_info
        # タイムゾーンを統一して比較
        updated_at_jst = basic_episode.updated_at.astimezone(JST) if basic_episode.updated_at.tzinfo else basic_episode.updated_at.replace(tzinfo=JST)
        original_updated_at_jst = original_updated_at.astimezone(JST) if original_updated_at.tzinfo else original_updated_at.replace(tzinfo=JST)
        assert updated_at_jst > original_updated_at_jst

        # 元のdict が変更されても影響を受けない(コピーされている)
        plot_info["new_key"] = "new_value"
        assert "new_key" not in basic_episode.plot_info

    def test_get_target_word_count_with_plot_info(self, basic_episode: Episode) -> None:
        """プロット情報ありでの目標文字数取得テスト"""
        basic_episode.plot_info = {"word_count_target": 4000}

        target = basic_episode.get_target_word_count()

        assert target == 4000

    def test_get_target_word_count_without_plot_info(self, basic_episode: Episode) -> None:
        """プロット情報なしでの目標文字数取得テスト(デフォルト値)"""
        assert basic_episode.plot_info == {}

        target = basic_episode.get_target_word_count()

        assert target == 3000  # デフォルト値

    def test_get_completion_rate_normal_case(self, basic_episode: Episode) -> None:
        """通常ケースでの完成度計算テスト"""
        basic_episode.plot_info = {"word_count_target": 2000}
        basic_episode.word_count = WordCount(1000)

        completion_rate = basic_episode.get_completion_rate()

        assert completion_rate == 50.0  # 1000/2000 * 100

    def test_get_completion_rate_over_target(self, basic_episode: Episode) -> None:
        """目標超過での完成度計算テスト(上限100%)"""
        basic_episode.plot_info = {"word_count_target": 1000}
        basic_episode.word_count = WordCount(1500)

        completion_rate = basic_episode.get_completion_rate()

        assert completion_rate == 100.0  # 上限100%

    def test_get_completion_rate_zero_target(self, basic_episode: Episode) -> None:
        """目標0での完成度計算テスト"""
        basic_episode.plot_info = {"word_count_target": 0}
        basic_episode.word_count = WordCount(1000)

        completion_rate = basic_episode.get_completion_rate()

        assert completion_rate == 0.0  # ゼロ除算回避

    def test_get_completion_rate_no_word_count(self, basic_episode: Episode) -> None:
        """文字数未設定での完成度計算テスト"""
        basic_episode.plot_info = {"word_count_target": 2000}
        basic_episode.word_count = None

        completion_rate = basic_episode.get_completion_rate()

        assert completion_rate == 0.0

    def test_is_over_target_true(self, basic_episode: Episode) -> None:
        """目標文字数超過判定(True)テスト"""
        basic_episode.plot_info = {"word_count_target": 1000}
        basic_episode.word_count = WordCount(1500)

        assert basic_episode.is_over_target() is True

    def test_is_over_target_false(self, basic_episode: Episode) -> None:
        """目標文字数超過判定(False)テスト"""
        basic_episode.plot_info = {"word_count_target": 2000}
        basic_episode.word_count = WordCount(1500)

        assert basic_episode.is_over_target() is False

    def test_is_over_target_no_word_count(self, basic_episode: Episode) -> None:
        """文字数未設定での目標超過判定テスト"""
        basic_episode.plot_info = {"word_count_target": 1000}
        basic_episode.word_count = None

        assert basic_episode.is_over_target() is False

    def test_calculate_actual_word_count_normal_content(self, basic_episode: Episode) -> None:
        """通常コンテンツでの実際文字数計算テスト"""
        basic_episode.content = "これは小説の内容です。\n\nさらに続きます。"

        actual_count = basic_episode._calculate_actual_word_count()

        expected_content = "これは小説の内容です。さらに続きます。"
        assert actual_count.value == len(expected_content)

    def test_calculate_actual_word_count_with_meta_info(self, basic_episode: Episode) -> None:
        """メタ情報含みコンテンツでの実際文字数計算テスト"""
        basic_episode.content = """# ch01

これは小説の内容です。

**注意:この部分はメタ情報**

--- 区切り線 ---

- リスト項目

実際の小説内容が続きます。"""

        actual_count = basic_episode._calculate_actual_word_count()

        # メタ情報行(#, **, ---, - で始まる行)と空行を除外
        expected_content = "これは小説の内容です。実際の小説内容が続きます。"
        assert actual_count.value == len(expected_content)

    def test_calculate_actual_word_count_empty_content(self, basic_episode: Episode) -> None:
        """空コンテンツでの実際文字数計算テスト"""
        basic_episode.content = ""

        actual_count = basic_episode._calculate_actual_word_count()

        assert actual_count.value == 0

    def test_is_ready_to_publish_compatibility(self, publishable_episode: Episode) -> None:
        """公開準備チェック互換性テスト"""
        # is_ready_to_publish() は can_publish() と同じ結果を返すべき
        assert publishable_episode.is_ready_to_publish() == publishable_episode.can_publish()
        assert publishable_episode.is_ready_to_publish() is True


class TestWritingRecord:
    """WritingRecordエンティティのテストクラス"""

    @pytest.fixture
    def basic_record(self) -> WritingRecord:
        """基本執筆記録"""
        return WritingRecord(episode_id="episode_001", phase=WritingPhase.DRAFT, word_count_before=WordCount(1000))

    def test_writing_record_creation_with_defaults(self) -> None:
        """デフォルト値での執筆記録作成テスト"""
        record = WritingRecord()

        assert record.id is not None
        assert record.episode_id == ""
        assert record.phase == WritingPhase.DRAFT
        assert isinstance(record.started_at, datetime)
        assert record.ended_at is None
        assert record.duration is None
        assert record.word_count_before is None
        assert record.word_count_after is None
        assert record.notes == ""

    def test_writing_record_creation_with_values(self, basic_record: WritingRecord) -> None:
        """値指定での執筆記録作成テスト"""
        assert basic_record.episode_id == "episode_001"
        assert basic_record.phase == WritingPhase.DRAFT
        assert basic_record.word_count_before.value == 1000

    def test_end_session_success(self, basic_record: WritingRecord) -> None:
        """執筆セッション終了成功テスト"""
        word_count_after = WordCount(1200)
        started_at = basic_record.started_at

        basic_record.end_session(word_count_after)

        assert basic_record.ended_at is not None
        assert basic_record.word_count_after == word_count_after
        assert basic_record.duration is not None
        assert basic_record.duration.minutes >= 0  # 実行時間による

        # 実際の経過時間を確認
        actual_duration_seconds = (basic_record.ended_at - started_at).total_seconds()
        expected_minutes = int(actual_duration_seconds / 60)
        assert basic_record.duration.minutes == expected_minutes

    def test_end_session_already_ended_error(self, basic_record: WritingRecord) -> None:
        """既に終了済みセッションの終了エラーテスト"""
        word_count_after = WordCount(1200)

        # 最初の終了は成功
        basic_record.end_session(word_count_after)

        # 2回目の終了はエラー
        with pytest.raises(ValueError, match="既に終了済みのセッションです"):
            basic_record.end_session(WordCount(1300))

    def test_get_words_written_success(self, basic_record: WritingRecord) -> None:
        """執筆文字数取得成功テスト"""
        basic_record.word_count_before = WordCount(1000)
        basic_record.word_count_after = WordCount(1250)

        words_written = basic_record.get_words_written()

        assert words_written == 250

    def test_get_words_written_no_before_count(self, basic_record: WritingRecord) -> None:
        """開始時文字数未設定での執筆文字数取得テスト"""
        basic_record.word_count_before = None
        basic_record.word_count_after = WordCount(1200)

        words_written = basic_record.get_words_written()

        assert words_written is None

    def test_get_words_written_no_after_count(self, basic_record: WritingRecord) -> None:
        """終了時文字数未設定での執筆文字数取得テスト"""
        basic_record.word_count_before = WordCount(1000)
        basic_record.word_count_after = None

        words_written = basic_record.get_words_written()

        assert words_written is None

    def test_get_writing_speed_success(self, basic_record: WritingRecord) -> None:
        """執筆速度取得成功テスト"""
        basic_record.word_count_before = WordCount(1000)
        basic_record.word_count_after = WordCount(1200)
        basic_record.duration = WritingDuration(60)  # 60分

        speed = basic_record.get_writing_speed()

        assert speed == 200 / 60  # 200文字/60分 ≈ 3.33文字/分

    def test_get_writing_speed_no_words_written(self, basic_record: WritingRecord) -> None:
        """執筆文字数なしでの執筆速度取得テスト"""
        basic_record.word_count_before = None  # words_written = None
        basic_record.duration = WritingDuration(60)

        speed = basic_record.get_writing_speed()

        assert speed is None

    def test_get_writing_speed_no_duration(self, basic_record: WritingRecord) -> None:
        """執筆時間なしでの執筆速度取得テスト"""
        basic_record.word_count_before = WordCount(1000)
        basic_record.word_count_after = WordCount(1200)
        basic_record.duration = None

        speed = basic_record.get_writing_speed()

        assert speed is None

    def test_get_writing_speed_zero_duration(self, basic_record: WritingRecord) -> None:
        """執筆時間0での執筆速度取得テスト"""
        basic_record.word_count_before = WordCount(1000)
        basic_record.word_count_after = WordCount(1200)
        basic_record.duration = WritingDuration(0)  # 0分

        speed = basic_record.get_writing_speed()

        assert speed is None  # ゼロ除算回避


class TestWritingSession:
    """WritingSessionエンティティのテストクラス"""

    @pytest.fixture
    def basic_session(self) -> WritingSession:
        """基本執筆セッション"""
        return WritingSession(project_id="test_project", episode_id="episode_001")

    @pytest.fixture
    def sample_records(self) -> list[WritingRecord]:
        """サンプル執筆記録リスト"""
        record1 = WritingRecord(
            episode_id="episode_001",
            phase=WritingPhase.DRAFT,
            word_count_before=WordCount(1000),
            word_count_after=WordCount(1200),
            duration=WritingDuration(30),
        )

        record2 = WritingRecord(
            episode_id="episode_001",
            phase=WritingPhase.REVISION,
            word_count_before=WordCount(1200),
            word_count_after=WordCount(1350),
            duration=WritingDuration(45),
        )

        record3 = WritingRecord(
            episode_id="episode_001",
            phase=WritingPhase.DRAFT,
            word_count_before=WordCount(1350),
            word_count_after=WordCount(1300),  # 削減(推敲で文字数減)
            duration=WritingDuration(25),
        )

        return [record1, record2, record3]

    def test_writing_session_creation_with_defaults(self) -> None:
        """デフォルト値での執筆セッション作成テスト"""
        session = WritingSession()

        assert session.id is not None
        assert session.project_id == ""
        assert session.episode_id == ""
        assert session.date == project_now().datetime.date()
        assert session.records == []

    def test_writing_session_creation_with_values(self, basic_session: WritingSession) -> None:
        """値指定での執筆セッション作成テスト"""
        assert basic_session.project_id == "test_project"
        assert basic_session.episode_id == "episode_001"

    def test_add_record_success(self, basic_session: WritingSession) -> None:
        """記録追加成功テスト"""
        record = WritingRecord(episode_id="episode_001", phase=WritingPhase.DRAFT)

        basic_session.add_record(record)

        assert len(basic_session.records) == 1
        assert basic_session.records[0] == record

    def test_add_record_wrong_episode_error(self, basic_session: WritingSession) -> None:
        """異なるエピソードの記録追加エラーテスト"""
        record = WritingRecord(episode_id="different_episode", phase=WritingPhase.DRAFT)

        with pytest.raises(ValueError, match="異なるエピソードの記録は追加できません"):
            basic_session.add_record(record)

    def test_get_total_duration(self, basic_session: WritingSession, sample_records: list[WritingRecord]) -> None:
        """合計執筆時間取得テスト"""
        for record in sample_records:
            basic_session.add_record(record)

        total_duration = basic_session.get_total_duration()

        # 30 + 45 + 25 = 100分
        assert total_duration.minutes == 100

    def test_get_total_duration_empty_records(self, basic_session: WritingSession) -> None:
        """空記録での合計執筆時間取得テスト"""
        total_duration = basic_session.get_total_duration()

        assert total_duration.minutes == 0

    def test_get_total_duration_some_without_duration(self, basic_session: WritingSession) -> None:
        """一部時間なし記録での合計執筆時間取得テスト"""
        record_with_duration = WritingRecord(episode_id="episode_001", duration=WritingDuration(30))
        record_without_duration = WritingRecord(episode_id="episode_001", duration=None)

        basic_session.add_record(record_with_duration)
        basic_session.add_record(record_without_duration)

        total_duration = basic_session.get_total_duration()

        assert total_duration.minutes == 30  # duration=Noneは合計から除外

    def test_get_total_words_written(self, basic_session: WritingSession, sample_records: list[WritingRecord]) -> None:
        """合計執筆文字数取得テスト"""
        for record in sample_records:
            basic_session.add_record(record)

        total_words = basic_session.get_total_words_written()

        # record1: 200文字増, record2: 150文字増, record3: -50文字(削減)
        # 正の増加分のみカウント: 200 + 150 = 350
        assert total_words == 350

    def test_get_total_words_written_empty_records(self, basic_session: WritingSession) -> None:
        """空記録での合計執筆文字数取得テスト"""
        total_words = basic_session.get_total_words_written()

        assert total_words == 0

    def test_get_total_words_written_only_negative_changes(self, basic_session: WritingSession) -> None:
        """負の変化のみでの合計執筆文字数取得テスト"""
        record = WritingRecord(
            episode_id="episode_001",
            word_count_before=WordCount(1000),
            word_count_after=WordCount(800),  # 200文字削減
        )

        basic_session.add_record(record)

        total_words = basic_session.get_total_words_written()

        assert total_words == 0  # 負の変化は合計に含めない

    def test_get_average_writing_speed(
        self, basic_session: WritingSession, sample_records: list[WritingRecord]
    ) -> None:
        """平均執筆速度取得テスト"""
        for record in sample_records:
            basic_session.add_record(record)

        average_speed = basic_session.get_average_writing_speed()

        # 合計350文字 / 合計100分 = 3.5文字/分
        assert average_speed == 3.5

    def test_get_average_writing_speed_zero_duration(self, basic_session: WritingSession) -> None:
        """執筆時間0での平均執筆速度取得テスト"""
        record = WritingRecord(
            episode_id="episode_001",
            word_count_before=WordCount(1000),
            word_count_after=WordCount(1200),
            duration=WritingDuration(0),
        )

        basic_session.add_record(record)

        average_speed = basic_session.get_average_writing_speed()

        assert average_speed is None  # ゼロ除算回避

    def test_get_average_writing_speed_empty_records(self, basic_session: WritingSession) -> None:
        """空記録での平均執筆速度取得テスト"""
        average_speed = basic_session.get_average_writing_speed()

        assert average_speed is None

    def test_writing_session_with_mixed_record_qualities(self, basic_session: WritingSession) -> None:
        """様々な品質の記録混在でのセッション統計テスト"""
        records = [
            # 有効な記録
            WritingRecord(
                episode_id="episode_001",
                word_count_before=WordCount(1000),
                word_count_after=WordCount(1100),
                duration=WritingDuration(30),
            ),
            # 時間なし記録
            WritingRecord(
                episode_id="episode_001",
                word_count_before=WordCount(1100),
                word_count_after=WordCount(1200),
                duration=None,
            ),
            # 文字数情報なし記録
            WritingRecord(episode_id="episode_001", duration=WritingDuration(15)),
        ]

        for record in records:
            basic_session.add_record(record)

        # 合計時間:30 + 0 + 15 = 45分(duration=Noneは除外)
        assert basic_session.get_total_duration().minutes == 45

        # 合計文字数:100 + 100 + 0 = 200文字
        assert basic_session.get_total_words_written() == 200

        # 平均速度:200文字 / 45分 ≈ 4.44文字/分
        expected_speed = 200 / 45
        assert abs(basic_session.get_average_writing_speed() - expected_speed) < 0.01
