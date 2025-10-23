"""エピソード作成ユースケースのテスト

DDD準拠テスト:
    - ユースケースロジックのテスト
- リポジトリパターンのモック化
- ビジネスルール検証の動作確認
"""

import pytest

from unittest.mock import Mock


from noveler.application.use_cases.create_episode_use_case import (
    CreateEpisodeRequest,
    CreateEpisodeResponse,
    CreateEpisodeUseCase,
    create_episode_from_template,
)
from noveler.domain.entities.episode import Episode
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.quality_score import QualityScore


class TestCreateEpisodeUseCase:
    """CreateEpisodeUseCaseのテスト"""

    @pytest.fixture
    def mock_episode_repository(self):
        """エピソードリポジトリのモック"""
        repo = Mock()
        repo.find_by_project_and_number.return_value = None  # デフォルトでは重複なし
        repo.save.return_value = None
        repo.get_next_episode_number.return_value = 1
        return repo

    @pytest.fixture
    def mock_project_repository(self):
        """プロジェクトリポジトリのモック"""
        repo = Mock()
        repo.exists.return_value = True  # デフォルトではプロジェクト存在
        return repo

    @pytest.fixture
    def mock_quality_repository(self):
        """品質リポジトリのモック"""
        repo = Mock()
        repo.save.return_value = None
        return repo

    @pytest.fixture
    def use_case(self, mock_episode_repository: object, mock_project_repository: object):
        """ユースケースインスタンス"""
        return CreateEpisodeUseCase(mock_episode_repository, mock_project_repository)

    @pytest.fixture
    def use_case_with_quality(
        self, mock_episode_repository: object, mock_project_repository: object, mock_quality_repository: object
    ):
        """品質リポジトリ付きユースケース"""
        return CreateEpisodeUseCase(
            mock_episode_repository,
            mock_project_repository,
            mock_quality_repository,
        )

    @pytest.fixture
    def valid_request(self):
        """有効なリクエスト"""
        return CreateEpisodeRequest(
            project_id="test_project",
            episode_number=1,
            title="第1話 始まり",
            target_words=2000,
            initial_content="これは第1話の内容です。物語の始まりを描きます。",
            tags=["導入", "キャラ紹介"],
            metadata={"author": "テスト作者", "created_date": "2024-01-01"},
        )

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_init(self, use_case: object, mock_episode_repository: object, mock_project_repository: object) -> None:
        """初期化のテスト"""
        assert use_case.episode_repository == mock_episode_repository
        assert use_case.project_repository == mock_project_repository
        assert use_case.quality_repository is None

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_init_with_quality_repository(self, use_case_with_quality: object, mock_quality_repository: object) -> None:
        """品質リポジトリ付き初期化のテスト"""
        assert use_case_with_quality.quality_repository == mock_quality_repository

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_success(self, use_case: object, valid_request: object, mock_episode_repository: object) -> None:
        """正常実行のテスト"""
        response = use_case.execute(valid_request)

        assert response.success is True
        assert response.episode is not None
        assert response.error_message is None
        assert isinstance(response.episode, Episode)

        # リポジトリが呼び出されているか確認
        mock_episode_repository.save.assert_called_once()

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_project_not_exists(
        self,
        use_case: CreateEpisodeUseCase,
        valid_request: CreateEpisodeRequest,
        mock_project_repository: Mock,
    ) -> None:
        """プロジェクトが存在しない場合のテスト"""
        mock_project_repository.exists.return_value = False

        response = use_case.execute(valid_request)

        assert response.success is False
        assert response.episode is None
        assert "プロジェクトが存在しません" in response.error_message

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_duplicate_episode_number(
        self,
        use_case: CreateEpisodeUseCase,
        valid_request: CreateEpisodeRequest,
        mock_episode_repository: Mock,
    ) -> None:
        """エピソード番号重複の場合のテスト"""
        # 既存のエピソードを返すように設定
        existing_episode = Mock()
        mock_episode_repository.find_by_project_and_number.return_value = existing_episode

        response = use_case.execute(valid_request)

        assert response.success is False
        assert response.episode is None
        assert "エピソード番号1は既に存在します" in response.error_message

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_with_initial_content(self, use_case_with_quality: object, valid_request: object) -> None:
        """初期内容付きでの実行テスト"""
        response = use_case_with_quality.execute(valid_request)

        assert response.success is True
        assert response.episode.content == valid_request.initial_content

        # 品質スコアが設定されているか確認
        assert response.episode.quality_score is not None
        assert response.episode.quality_score.value > 0

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_with_tags_and_metadata(self, use_case: object, valid_request: object) -> None:
        """タグとメタデータ付きでの実行テスト"""
        response = use_case.execute(valid_request)

        assert response.success is True

        # タグが設定されているか確認
        for tag in valid_request.tags:
            assert tag in response.episode.tags

        # メタデータが設定されているか確認
        for key, value in valid_request.metadata.items():
            assert response.episode.get_metadata(key) == value

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_domain_exception(
        self, use_case: object, valid_request: object, mock_episode_repository: object
    ) -> None:
        """ドメイン例外発生時のテスト"""
        mock_episode_repository.save.side_effect = DomainException("ドメインエラー")

        response = use_case.execute(valid_request)

        assert response.success is False
        assert response.episode is None
        assert "ドメインエラー" in response.error_message

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_value_error(
        self, use_case: object, valid_request: object, mock_episode_repository: object
    ) -> None:
        """値エラー発生時のテスト"""
        mock_episode_repository.save.side_effect = ValueError("値エラー")

        response = use_case.execute(valid_request)

        assert response.success is False
        assert response.episode is None
        assert "エピソード作成中にエラーが発生しました" in response.error_message

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_execute_general_exception(
        self, use_case: object, valid_request: object, mock_episode_repository: object
    ) -> None:
        """一般例外発生時のテスト"""
        mock_episode_repository.save.side_effect = Exception("予期しないエラー")

        response = use_case.execute(valid_request)

        assert response.success is False
        assert response.episode is None
        assert "エピソード作成中にエラーが発生しました" in response.error_message

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_quality_score_by_word_count(self, use_case: object) -> None:
        """文字数による品質スコア計算テスト"""
        # 短い内容
        short_score = use_case._calculate_quality_score("短い内容")
        assert short_score.value == 50  # 最低スコア

        # 中程度の内容(1000文字以上)
        medium_content = "あ" * 1500  # 1500文字
        medium_score = use_case._calculate_quality_score(medium_content)
        assert medium_score.value == 70

        # 長い内容(3000文字以上)
        long_content = "あ" * 3500  # 3500文字
        long_score = use_case._calculate_quality_score(long_content)
        assert long_score.value == 85

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_quality_score_with_dialogue(self, use_case: object) -> None:
        """会話文を含む場合の品質スコア計算テスト"""
        content_with_dialogue = "あ" * 1500 + "「こんにちは」と彼は言った。"
        score = use_case._calculate_quality_score(content_with_dialogue)

        # 基礎スコア70 + 会話文ボーナス10 = 80
        assert score.value == 80

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_quality_score_with_description(self, use_case: object) -> None:
        """描写を含む場合の品質スコア計算テスト"""
        content_with_description = "あ" * 1500 + "美しい夕日が山に沈んでいく。"
        score = use_case._calculate_quality_score(content_with_description)

        # 基礎スコア70 + 描写ボーナス5 = 75
        assert score.value == 75

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_quality_score_maximum(self, use_case: object) -> None:
        """最大品質スコアのテスト"""
        # 全ボーナス込みで100点上限
        perfect_content = "あ" * 3500 + "「素晴らしい!」彼女は感嘆した。美しい景色が広がっていた。"
        score = use_case._calculate_quality_score(perfect_content)

        # 基礎スコア85 + 会話文5 + 描写5 = 95 (100点上限なし)
        assert score.value == 95

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_repository_integration(
        self, use_case_with_quality: object, valid_request: object, mock_quality_repository: object
    ) -> None:
        """品質リポジトリ統合のテスト"""
        response = use_case_with_quality.execute(valid_request)

        assert response.success is True

        # 品質リポジトリに保存されているか確認
        mock_quality_repository.save.assert_called_once()

        # 保存された引数を確認
        call_args = mock_quality_repository.save.call_args
        episode_number, quality_score = call_args[0]
        assert isinstance(episode_number, EpisodeNumber)
        assert isinstance(quality_score, QualityScore)
        assert episode_number.value == valid_request.episode_number

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_empty_content_no_quality_calculation(self, use_case_with_quality: object) -> None:
        """空内容の場合は品質計算しないテスト"""
        request = CreateEpisodeRequest(
            project_id="test_project", episode_number=1, title="第1話", target_words=2000, initial_content=""
        )  # 空内容

        response = use_case_with_quality.execute(request)

        assert response.success is True
        assert response.episode.quality_score is None


class TestCreateEpisodeRequest:
    """CreateEpisodeRequestのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_init_required_fields(self) -> None:
        """必須フィールドでの初期化テスト"""
        request = CreateEpisodeRequest(
            project_id="test_project",
            episode_number=1,
            title="第1話",
            target_words=2000,
        )

        assert request.project_id == "test_project"
        assert request.episode_number == 1
        assert request.title == "第1話"
        assert request.target_words == 2000
        assert request.initial_content == ""
        assert request.tags == []
        assert request.metadata == {}

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_init_all_fields(self) -> None:
        """全フィールドでの初期化テスト"""
        request = CreateEpisodeRequest(
            project_id="test_project",
            episode_number=1,
            title="第1話",
            target_words=2000,
            initial_content="初期内容",
            tags=["タグ1", "タグ2"],
            metadata={"key": "value"},
        )

        assert request.project_id == "test_project"
        assert request.episode_number == 1
        assert request.title == "第1話"
        assert request.target_words == 2000
        assert request.initial_content == "初期内容"
        assert request.tags == ["タグ1", "タグ2"]
        assert request.metadata == {"key": "value"}

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_frozen_dataclass(self) -> None:
        """フローズンデータクラスのテスト"""
        request = CreateEpisodeRequest(
            project_id="test_project",
            episode_number=1,
            title="第1話",
            target_words=2000,
        )

        with pytest.raises(AttributeError, match=".*"):
            request.project_id = "modified"


class TestCreateEpisodeResponse:
    """CreateEpisodeResponseのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_success_response_creation(self) -> None:
        """成功レスポンス作成のテスト"""
        episode = Mock(spec=Episode)
        response = CreateEpisodeResponse.success_response(episode)

        assert response.success is True
        assert response.episode == episode
        assert response.error_message is None

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_error_response_creation(self) -> None:
        """エラーレスポンス作成のテスト"""
        error_message = "エラーが発生しました"
        response = CreateEpisodeResponse.error_response(error_message)

        assert response.success is False
        assert response.episode is None
        assert response.error_message == error_message

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_init_success(self) -> None:
        """成功時の初期化テスト"""
        episode = Mock(spec=Episode)
        response = CreateEpisodeResponse(success=True, episode=episode)

        assert response.success is True
        assert response.episode == episode
        assert response.error_message is None

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_init_error(self) -> None:
        """エラー時の初期化テスト"""
        response = CreateEpisodeResponse(success=False, error_message="エラー")

        assert response.success is False
        assert response.episode is None
        assert response.error_message == "エラー"


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    @pytest.fixture
    def mock_repositories(self):
        """モックリポジトリセット"""
        episode_repo = Mock()
        project_repo = Mock()
        episode_repo.find_by_project_and_number.return_value = None
        episode_repo.save.return_value = None
        project_repo.exists.return_value = True
        return episode_repo, project_repo

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_episode_from_template(self, mock_repositories: object) -> None:
        """テンプレートからのエピソード作成テスト"""
        episode_repo, project_repo = mock_repositories

        template = {
            "number": 1,
            "title": "第1話",
            "target_words": 2000,
            "initial_content": "内容",
            "tags": ["タグ1"],
            "metadata": {"key": "value"},
        }

        response = create_episode_from_template(
            "test_project",
            template,
            episode_repo,
            project_repo,
        )

        assert response.success is True
        assert response.episode is not None

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_episode_from_template_minimal(self, mock_repositories: object) -> None:
        """最小限のテンプレートからの作成テスト"""
        episode_repo, project_repo = mock_repositories

        template = {
            "number": 1,
            "title": "第1話",
        }

        response = create_episode_from_template(
            "test_project",
            template,
            episode_repo,
            project_repo,
        )

        assert response.success is True
        # デフォルト値が適用されているか確認
        assert response.episode.target_words.value == 3000

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_episode_with_auto_numbering(self, mock_repositories: object) -> None:
        """自動番号付きエピソード作成テスト"""
        episode_repo, project_repo = mock_repositories
        episode_repo.get_next_episode_number.return_value = 5

        response = create_episode_with_auto_numbering(
            "test_project",
            "第5話",
            2000,
            episode_repo,
            project_repo,
        )

        assert response.success is True
        assert response.episode.number.value == 5

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_episode_with_auto_numbering_all_params(self, mock_repositories: object) -> None:
        """自動番号付き(全パラメータ)のテスト"""
        episode_repo, project_repo = mock_repositories
        episode_repo.get_next_episode_number.return_value = 3

        response = create_episode_with_auto_numbering(
            "test_project",
            "第3話",
            2500,
            episode_repo,
            project_repo,
            initial_content="初期内容",
            tags=["タグ1", "タグ2"],
            metadata={"author": "作者"},
        )

        assert response.success is True
        assert response.episode.number.value == 3
        assert response.episode.content == "初期内容"
        assert "タグ1" in response.episode.tags
        assert response.episode.get_metadata("author") == "作者"

    @pytest.mark.spec("SPEC-EPISODE-015")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_episode_with_auto_numbering_none_defaults(self, mock_repositories: object) -> None:
        """Noneデフォルト値の処理テスト"""
        episode_repo, project_repo = mock_repositories
        episode_repo.get_next_episode_number.return_value = 1

        response = create_episode_with_auto_numbering(
            "test_project",
            "第1話",
            2000,
            episode_repo,
            project_repo,
            tags=None,  # Noneを明示的に渡す
            metadata=None,
        )

        assert response.success is True
        assert response.episode.tags == []
        assert len(response.episode.metadata) == 0
