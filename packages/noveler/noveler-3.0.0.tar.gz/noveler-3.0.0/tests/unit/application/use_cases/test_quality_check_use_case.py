#!/usr/bin/env python3
"""品質チェックユースケースのテスト(TDD RED段階)

アプリケーション層の品質チェックユースケースをテスト。
ドメインロジックの統合と外部システムとの調整を担当。


仕様書: SPEC-APPLICATION-USE-CASES
"""

from unittest.mock import Mock, create_autospec, patch

import pytest

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# 実装前なのでImportError が発生する(これが期待される動作)
try:
    from noveler.application.use_cases.quality_check_use_case import (
        QualityCheckRequest,
        QualityCheckResponse,
        QualityCheckUseCase,
    )
    from noveler.domain.entities.quality_check_aggregate import (
        QualityCheckAggregate,
        QualityRule,
        RuleCategory,
        Severity,
    )
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
    from noveler.domain.value_objects.quality_threshold import QualityThreshold
except ImportError as e:
    # TDD RED段階では実装が存在しないため、仮の定義を作成
    print(f"実装クラスが存在しません(TDD RED段階の期待動作): {e}")

    class QualityCheckUseCase:
        pass

    class QualityCheckRequest:
        pass

    class QualityCheckResponse:
        pass

    class QualityCheckAggregate:
        pass

    class QualityRule:
        pass

    class RuleCategory:
        BASIC_STYLE = "basic_style"
        COMPOSITION = "composition"

    class Severity:
        ERROR = "error"
        WARNING = "warning"

    class QualityCheckRepository:
        pass

    class EpisodeRepository:
        pass

    class QualityThreshold:
        pass


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestQualityCheckUseCase:
    """品質チェックユースケースのテスト

    ビジネスルール:
    1. エピソードに対して品質チェックを実行する
    2. 設定されたルールに基づいてチェックを行う
    3. 結果を永続化する
    4. 適切なレスポンスを返す
    """

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-QUALITY_CHECKEXECUTI")
    @pytest.mark.asyncio
    async def test_quality_checkexecution(self) -> None:
        """品質チェックが正常に実行されることを確認"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        # エピソードが存在する場合のモック
        episode_repo.find_by_id.return_value = Mock(
            episode_id="episode_001",
            content="これはテスト文章です。",
            title="テストエピソード",
            update_content=Mock(),
        )

        # 品質チェック設定のモック
        quality_repo.get_default_rules.return_value = [
            Mock(
                rule_id="rule_001",
                name="基本スタイル",
                category=RuleCategory.BASIC_STYLE,
                severity=Severity.WARNING,
                enabled=True,
                pattern=r"テスト",
                penalty_score=5.0,
                message_template="{line}行目: {message}",
            )
        ]

        # 品質閾値のモック
        threshold_mock = Mock()
        threshold_mock.value = 70.0
        threshold_mock.name = "最小品質スコア"
        quality_repo.get_quality_threshold.return_value = threshold_mock

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        request = QualityCheckRequest(
            episode_id="episode_001",
            project_id="project_001",
            check_options={
                "auto_fix": False,
                "categories": [RuleCategory.BASIC_STYLE],
            },
        )

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert isinstance(response, QualityCheckResponse)
        assert response.success is True
        assert response.check_id is not None
        assert response.total_score >= 0
        assert response.violations is not None

        # リポジトリ呼び出しの確認
        episode_repo.find_by_id.assert_called_once_with("episode_001", "project_001")
        quality_repo.get_default_rules.assert_called_once()
        quality_repo.save_result.assert_called_once()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-ERROR")
    @pytest.mark.asyncio
    async def test_error(self) -> None:
        """存在しないエピソードIDが指定された場合のエラー処理"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        # エピソードが存在しない場合
        episode_repo.find_by_id.return_value = None

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        request = QualityCheckRequest(episode_id="nonexistent_episode", project_id="project_001", check_options={})

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert response.success is False
        assert "エピソードが見つかりません" in response.error_message

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-QUALITY_CONFIGURATIO")
    @pytest.mark.asyncio
    async def test_quality_configuration_error(self) -> None:
        """品質ルールが設定されていない場合のエラー処理"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        episode_repo.find_by_id.return_value = Mock(
            episode_id="episode_001",
            content="テスト文章",
        )

        # ルールが設定されていない場合
        quality_repo.get_default_rules.return_value = []

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        request = QualityCheckRequest(episode_id="episode_001", project_id="project_001", check_options={})

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert response.success is False
        assert "品質ルールが設定されていません" in response.error_message

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-FILTERFEATURE")
    async def test_filterfeature(self) -> None:
        """特定カテゴリのみの品質チェック実行"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        episode_repo.find_by_id.return_value = Mock(
            episode_id="episode_001",
            content="テスト文章",
        )

        # 複数カテゴリのルールを用意
        all_rules = [
            Mock(
                rule_id="rule_001",
                category=RuleCategory.BASIC_STYLE,
                enabled=True,
                pattern=r"テスト",
                penalty_score=5.0,
                message_template="{line}行目: {message}",
            ),
            Mock(
                rule_id="rule_002",
                category=RuleCategory.COMPOSITION,
                enabled=True,
                pattern=r"文章",
                penalty_score=3.0,
                message_template="{line}行目: {message}",
            ),
        ]
        quality_repo.get_default_rules.return_value = all_rules

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        # 基本スタイルのみをチェック
        request = QualityCheckRequest(
            episode_id="episode_001",
            project_id="project_001",
            check_options={
                "categories": [RuleCategory.BASIC_STYLE],
            },
        )

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        # 実際の実装では、指定されたカテゴリのルールのみが使用されることを確認

    @patch("noveler.application.use_cases.quality_check_use_case.QualityCheckAggregate")
    async def test_autocheck(self, mock_aggregate_class: object) -> None:
        """自動修正オプション付きの品質チェック実行"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        episode = Mock()
        episode.episode_id = "episode_001"
        episode.content = "テスト文章です。。。間違え"  # 修正対象を含む
        episode.update_content = Mock()
        episode_repo.find_by_id.return_value = episode

        rule = Mock()
        rule.rule_id = "rule_001"
        rule.name = "三点リーダー"
        rule.pattern = r"\.\.\."
        rule.replacement = "…"
        rule.category = RuleCategory.BASIC_STYLE
        rule.severity = Severity.WARNING
        rule.enabled = True
        rule.auto_fixable = True

        quality_repo.get_default_rules.return_value = [rule]
        quality_repo.get_quality_threshold.return_value = Mock(
            name="最小品質スコア", value=80.0, min_value=0.0, max_value=100.0
        )

        # アグリゲートのモック設定
        mock_aggregate = Mock()
        mock_aggregate_class.return_value = mock_aggregate

        # add_rule メソッドをモック
        mock_aggregate.add_rule = Mock()

        # execute_check の結果に違反を含める
        mock_aggregate.execute_check.return_value = Mock(
            check_id="c8e1f464-c348-47da-92ca-1b89d05b597f",
            episode_id="episode_001",
            total_score=85.0,
            violations=[
                Mock(
                    rule_id="rule_001",
                    rule_name="三点リーダー",
                    line_number=1,
                    column_number=10,
                    message="「。。。」は「…」に置き換えてください",
                    severity=Severity.WARNING,
                )
            ],
            is_passed=True,
            executed_at=project_now().datetime,
        )

        # save_result メソッドをモック
        quality_repo.save_result = Mock()

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        request = QualityCheckRequest(
            episode_id="episode_001",
            project_id="project_001",
            check_options={
                "auto_fix": True,
            },
        )

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.auto_fix_applied is True
        assert response.fixed_content is not None
        assert "…" in response.fixed_content
        # エピソードの内容が修正されて保存されることを確認
        episode_repo.save.assert_called_once()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-QUALITY_VALUE_DETERM")
    async def test_quality_value_determine(self) -> None:
        """品質スコアに基づく合格・不合格判定"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        episode_repo.find_by_id.return_value = Mock(
            episode_id="episode_001",
            content="品質の良いテスト文章です。",
        )

        quality_repo.get_default_rules.return_value = [
            Mock(
                rule_id="rule_001",
                name="品質ルール",
                pattern=r"品質",
                category=RuleCategory.BASIC_STYLE,
                severity=Severity.WARNING,
                enabled=True,
                penalty_score=5.0,
                message_template="{line}行目: {message}",
            )
        ]

        # 品質閾値を設定
        # 品質闾値のモック
        threshold_mock = Mock()
        threshold_mock.value = 80.0
        threshold_mock.name = "最小品質スコア"
        quality_repo.get_quality_threshold.return_value = threshold_mock

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        request = QualityCheckRequest(episode_id="episode_001", project_id="project_001", check_options={})

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        assert hasattr(response, "is_passed")
        assert response.total_score >= 0

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-QUALITY_CHECK")
    async def test_quality_check(self) -> None:
        """品質チェック結果が正しく保存されることを確認"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        quality_repo = create_autospec(QualityCheckRepository)

        episode_repo.find_by_id.return_value = Mock(
            episode_id="episode_001",
            content="テスト文章",
        )

        quality_repo.get_default_rules.return_value = [
            Mock(
                rule_id="rule_001",
                name="テストルール",
                pattern=r"テスト",
                category=RuleCategory.BASIC_STYLE,
                severity=Severity.WARNING,
                enabled=True,
                penalty_score=5.0,
                message_template="{line}行目: {message}",
            )
        ]

        # Mockのlogger_serviceとunit_of_workを作成
        logger_service = Mock()
        unit_of_work = Mock()
        unit_of_work.transaction.return_value.__enter__ = Mock(return_value=unit_of_work)
        unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)

        use_case = QualityCheckUseCase(
            episode_repository=episode_repo,
            quality_check_repository=quality_repo,
            logger_service=logger_service,
            unit_of_work=unit_of_work,
        )

        request = QualityCheckRequest(episode_id="episode_001", project_id="project_001", check_options={})

        # Act
        import asyncio
        response = await use_case.execute(request)

        # Assert
        assert response.success is True

        # 品質チェック結果の保存が呼び出されることを確認
        quality_repo.save_result.assert_called_once()

        # 保存された結果の内容を確認
        saved_result = quality_repo.save_result.call_args[0][0]
        assert hasattr(saved_result, "check_id")
        assert hasattr(saved_result, "episode_id")
        assert hasattr(saved_result, "total_score")


class TestQualityCheckRequest:
    """品質チェック要求の値オブジェクトテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-QUALITY_CHECK_CREATI")
    def test_quality_check_creation(self) -> None:
        """品質チェック要求を作成できることを確認"""
        # Act
        request = QualityCheckRequest(
            episode_id="episode_001",
            project_id="project_001",
            check_options={
                "auto_fix": True,
                "categories": [RuleCategory.BASIC_STYLE],
                "threshold": 80.0,
            },
        )

        # Assert
        assert request.episode_id == "episode_001"
        assert request.check_options["auto_fix"] is True
        assert RuleCategory.BASIC_STYLE in request.check_options["categories"]

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-CONFIGURATION")
    def test_configuration(self) -> None:
        """デフォルトのチェックオプションが設定されることを確認"""
        # Act
        request = QualityCheckRequest(episode_id="episode_001", project_id="project_001", check_options={})

        # Assert
        assert request.episode_id == "episode_001"
        assert request.check_options is not None


class TestQualityCheckResponse:
    """品質チェック応答のテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_USE_CASE-CREATION")
    def test_creation(self) -> None:
        """成功レスポンスを作成できることを確認"""
        # Act
        response = QualityCheckResponse(
            success=True,
            check_id="check_001",
            episode_id="episode_001",
            total_score=85.0,
            violations=[],
            is_passed=True,
            executed_at=project_now().datetime,
        )

        # Assert
        assert response.success is True
        assert response.check_id == "check_001"
        assert response.total_score == 85.0
        assert response.is_passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
