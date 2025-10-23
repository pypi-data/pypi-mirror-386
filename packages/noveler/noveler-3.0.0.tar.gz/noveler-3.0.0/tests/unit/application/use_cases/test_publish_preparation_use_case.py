"""Tests.tests.unit.application.use_cases.test_publish_preparation_use_case
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from noveler.application.use_cases.backup_use_case import BackupResponse, BackupStatus, BackupUseCase

"""
公開準備ユースケースのテスト

TDD RED フェーズ: 公開準備機能の要件をテストで表現


仕様書: SPEC-APPLICATION-USE-CASES
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# まだ存在しないクラスをインポート(RED状態)
from noveler.application.use_cases.publish_preparation_use_case import (
    PublishFormat,
    PublishPreparationRequest,
    PublishPreparationUseCase,
    PublishStatus,
)
from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber


class TestPublishPreparationUseCase:
    """公開準備ユースケースのテスト"""

    @pytest.fixture
    def mock_project_repository(self):
        """プロジェクトリポジトリのモック"""
        return Mock()

    @pytest.fixture
    def mock_episode_repository(self):
        """エピソードリポジトリのモック"""
        repo = Mock()
        repo.find_by_number = Mock()
        repo.find_latest = Mock()
        return repo

    @pytest.fixture
    def mock_backup_use_case(self):
        """バックアップユースケースのモック"""

        use_case = Mock(spec=BackupUseCase)

        # デフォルトのレスポンスを設定
        mock_response = Mock(spec=BackupResponse)
        mock_response.status = BackupStatus.COMPLETED
        mock_response.backup_path = Path("/backups/test_backup.zip")
        use_case.execute.return_value = mock_response

        return use_case

    @pytest.fixture
    def use_case(self, mock_project_repository: object, mock_episode_repository: object, mock_backup_use_case: object):
        """ユースケースのインスタンス"""
        return PublishPreparationUseCase(
            project_repository=mock_project_repository,
            episode_repository=mock_episode_repository,
            backup_use_case=mock_backup_use_case,
        )

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-CREATION")
    def test_creation(self) -> None:
        """公開準備リクエストが正しく作成されることを確認"""
        # Given: プロジェクト名とエピソード番号
        project_name = "テストプロジェクト"
        episode_number = 5
        format_type = PublishFormat.NAROU
        include_quality_check = True
        create_backup = True

        # When: リクエストを作成
        request = PublishPreparationRequest(
            project_name=project_name,
            episode_number=episode_number,
            format_type=format_type,
            include_quality_check=include_quality_check,
            create_backup=create_backup,
        )

        # Then: 属性が正しく設定されている
        assert request.project_name == project_name
        assert request.episode_number == 5
        assert request.format_type == PublishFormat.NAROU
        assert request.include_quality_check is True
        assert request.create_backup is True

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-UNNAMED")
    def test_unnamed(self, use_case: object, mock_project_repository: object, mock_episode_repository: object) -> None:
        """指定したエピソードの公開準備が実行されることを確認"""
        # Given: エピソード5の公開準備
        project_name = "テストプロジェクト"
        episode_number = 5

        # エピソードモックを設定
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(5)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "テストタイトル"
        mock_episode.title = mock_title

        mock_episode.content = "エピソード内容"
        mock_episode.status = EpisodeStatus.REVIEWED
        mock_episode.quality_score = 85.0

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = mock_episode

        request = PublishPreparationRequest(project_name=project_name, episode_number=episode_number)

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: 準備が成功すること
        assert response.status == PublishStatus.READY
        assert response.episode_path is not None
        assert response.quality_score == 85.0
        mock_episode_repository.find_by_number.assert_called_once()

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-NEW_AUTO")
    def test_new_auto(self, use_case: object, mock_project_repository: object, mock_episode_repository: object) -> None:
        """エピソード番号未指定時に最新エピソードが選択されることを確認"""
        # Given: エピソード番号なしのリクエスト
        project_name = "テストプロジェクト"

        # 最新エピソードモックを設定
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(10)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "最新エピソード"
        mock_episode.title = mock_title

        mock_episode.content = "最新内容"
        mock_episode.status = EpisodeStatus.COMPLETED
        mock_episode.quality_score = 80.0

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_latest.return_value = mock_episode

        request = PublishPreparationRequest(
            project_name=project_name,
            episode_number=None,  # 番号指定なし
        )

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: 最新エピソードが選択されること
        assert response.status in [PublishStatus.READY, PublishStatus.NEEDS_REVIEW]
        assert response.episode_path is not None
        mock_episode_repository.find_latest.assert_called_once()

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-QUALITY_CHECK")
    def test_quality_check(
        self, use_case: object, mock_project_repository: object, mock_episode_repository: object
    ) -> None:
        """品質チェックを含む公開準備が実行されることを確認"""
        # Given: 品質チェック付きリクエスト
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(1)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "品質チェックテスト"
        mock_episode.title = mock_title

        mock_episode.content = "テスト内容"
        mock_episode.quality_score = 75.0
        mock_episode.status = EpisodeStatus.DRAFT

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = mock_episode

        request = PublishPreparationRequest(
            project_name="テストプロジェクト", episode_number=1, include_quality_check=True, quality_threshold=80.0
        )

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: 品質チェックが実行されること
        assert response.status == PublishStatus.NEEDS_IMPROVEMENT
        assert response.quality_score == 75.0
        assert any(step.name == "品質チェック" for step in response.preparation_steps)

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-TO_FORMAT")
    def test_to_format(
        self, use_case: object, mock_project_repository: object, mock_episode_repository: object
    ) -> None:
        """なろう形式へのフォーマットが実行されることを確認"""
        # Given: なろう形式指定
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(1)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "フォーマットテスト"
        mock_episode.title = mock_title

        mock_episode.content = "# タイトル\n\n本文です。\n\n## セクション\n\n内容"
        mock_episode.status = EpisodeStatus.REVIEWED
        mock_episode.quality_score = 85.0

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = mock_episode

        request = PublishPreparationRequest(
            project_name="テストプロジェクト", episode_number=1, format_type=PublishFormat.NAROU
        )

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: フォーマットが適用されること
        assert response.formatted_content is not None
        assert "##" not in response.formatted_content  # Markdownヘッダーが除去される
        assert response.format_type == PublishFormat.NAROU

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-CREATION")
    def test_creation_1(self, use_case: object, mock_project_repository: object, mock_episode_repository: object) -> None:
        """バックアップ作成を含む公開準備が実行されることを確認"""
        # Given: バックアップ作成付きリクエスト
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(3)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "バックアップテスト"
        mock_episode.title = mock_title

        mock_episode.content = "エピソード3の内容"
        mock_episode.status = EpisodeStatus.REVIEWED
        mock_episode.quality_score = 90.0

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = mock_episode

        request = PublishPreparationRequest(project_name="テストプロジェクト", episode_number=3, create_backup=True)

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: バックアップが作成されること
        assert response.backup_path is not None
        assert any(step.name == "バックアップ作成" for step in response.preparation_steps)

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-ERROR")
    def test_error(self, use_case: object, mock_project_repository: object, mock_episode_repository: object) -> None:
        """エラー時に適切な応答が返されることを確認"""
        # Given: 存在しないエピソード
        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = None

        request = PublishPreparationRequest(project_name="テストプロジェクト", episode_number=999)

        # When/Then: エラーが発生すること
        with pytest.raises(ValueError, match="エピソード 999 が見つかりません"):
            use_case.execute(request)

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-UNNAMED")
    def test_basic_functionality(self, use_case: object, mock_project_repository: object, mock_episode_repository: object) -> None:
        """異なるフォーマットがサポートされることを確認"""
        # Given: カクヨム形式指定
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(1)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "カクヨムテスト"
        mock_episode.title = mock_title

        mock_episode.content = "本文内容"
        mock_episode.status = EpisodeStatus.REVIEWED
        mock_episode.quality_score = 85.0

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = mock_episode

        request = PublishPreparationRequest(
            project_name="テストプロジェクト", episode_number=1, format_type=PublishFormat.KAKUYOMU
        )

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: カクヨム形式が適用されること
        assert response.format_type == PublishFormat.KAKUYOMU
        assert response.formatted_content is not None

    @pytest.mark.spec("SPEC-PUBLISH_PREPARATION_USE_CASE-STATUS_JUDGE")
    def test_status_judge(
        self, use_case: object, mock_project_repository: object, mock_episode_repository: object
    ) -> None:
        """エピソードの状態に応じた適切なステータスが返されることを確認"""
        # Given: 下書き状態のエピソード
        mock_episode = MagicMock(spec=Episode)
        mock_episode.number = EpisodeNumber(1)

        # titleのモックを設定
        mock_title = Mock()
        mock_title.value = "ステータステスト"
        mock_episode.title = mock_title

        mock_episode.status = EpisodeStatus.DRAFT
        mock_episode.quality_score = 50.0
        mock_episode.content = "下書き内容"

        # プロジェクトディレクトリモックの設定
        mock_project_path = Mock(spec=Path)
        mock_project_path.exists.return_value = True
        mock_project_path.__truediv__ = Mock(return_value=mock_project_path)  # Support / operator
        mock_project_repository.get_project_directory.return_value = mock_project_path
        mock_episode_repository.find_by_number.return_value = mock_episode

        request = PublishPreparationRequest(
            project_name="テストプロジェクト", episode_number=1, include_quality_check=True
        )

        # When: 公開準備を実行
        response = use_case.execute(request)

        # Then: 改善が必要なステータスが返ること
        assert response.status == PublishStatus.NEEDS_IMPROVEMENT
        assert "下書き" in response.message or "品質" in response.message
