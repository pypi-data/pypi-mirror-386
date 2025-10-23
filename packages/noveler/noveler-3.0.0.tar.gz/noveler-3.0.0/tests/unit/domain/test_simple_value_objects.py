#!/usr/bin/env python3
"""シンプルな値オブジェクトのユニットテスト

TDD+DDD原則に基づく基本的な値オブジェクトテスト
実行時間目標: < 0.01秒/テスト


仕様書: SPEC-UNIT-TEST
"""

import time
from typing import NoReturn

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.progress_status import ProgressStatus
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestTimeEstimation:
    """時間見積もり値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-CREATES_TIME_ESTIMAT")
    def test_creates_time_estimation_with_valid_minutes(self) -> None:
        """有効な分数で時間見積もりを作成"""
        # Arrange & Act
        estimation = TimeEstimation(30)

        # Assert
        assert estimation.minutes == 30
        assert estimation.in_hours() == 0.5

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-VALIDATES_POSITIVE_M")
    def test_validates_positive_minutes(self) -> None:
        """正の分数を検証"""
        # Act & Assert
        with pytest.raises(DomainException) as exc_info:
            TimeEstimation(-5)
        assert "0分以上" in str(exc_info.value)

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-DISPLAY_TEXT_FORMAT")
    def test_display_text_format(self) -> None:
        """表示テキストの形式"""
        # Arrange
        short_time = TimeEstimation(15)
        long_time = TimeEstimation(90)

        # Act & Assert
        assert short_time.display_text() == "15分"
        assert long_time.display_text() == "1時間30分"

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-FROM_HOURS_CLASS_MET")
    def test_from_hours_class_method(self) -> None:
        """時間からの作成クラスメソッド"""
        # Act
        estimation = TimeEstimation.from_hours(2)

        # Assert
        assert estimation.minutes == 120
        assert estimation.in_hours() == 2.0


class TestWorkflowStageType:
    """ワークフロー段階タイプのテスト"""

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_VALUES_EXIST")
    def test_enum_values_exist(self) -> None:
        """列挙値が存在する"""
        # Act & Assert
        assert WorkflowStageType.MASTER_PLOT is not None
        assert WorkflowStageType.CHAPTER_PLOT is not None
        assert WorkflowStageType.EPISODE_PLOT is not None

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_STRING_REPRESEN")
    def test_enum_string_representation(self) -> None:
        """列挙値の文字列表現"""
        # Act & Assert
        assert str(WorkflowStageType.MASTER_PLOT) == "WorkflowStageType.MASTER_PLOT"

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_VALUE_COMPARISO")
    def test_enum_value_comparison(self) -> None:
        """列挙値の比較"""
        # Act & Assert
        assert WorkflowStageType.MASTER_PLOT != WorkflowStageType.CHAPTER_PLOT
        assert WorkflowStageType.MASTER_PLOT == WorkflowStageType.MASTER_PLOT


class TestProgressStatus:
    """進捗ステータスのテスト"""

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_VALUES_EXIST")
    def test_enum_values_exist(self) -> None:
        """列挙値が存在する"""
        # Act & Assert
        assert ProgressStatus.NOT_STARTED is not None
        assert ProgressStatus.IN_PROGRESS is not None
        assert ProgressStatus.COMPLETED is not None
        assert ProgressStatus.NEEDS_REVIEW is not None

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_ORDERING")
    def test_enum_ordering(self) -> None:
        """列挙値の順序"""
        # Act & Assert
        assert ProgressStatus.NOT_STARTED != ProgressStatus.IN_PROGRESS
        assert ProgressStatus.IN_PROGRESS != ProgressStatus.COMPLETED

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_IN_CONTAINER")
    def test_enum_in_container(self) -> None:
        """列挙値のコンテナ内使用"""
        # Arrange
        status_set = {
            ProgressStatus.NOT_STARTED,
            ProgressStatus.IN_PROGRESS,
            ProgressStatus.COMPLETED,
        }

        # Act & Assert
        assert ProgressStatus.NOT_STARTED in status_set
        assert ProgressStatus.NEEDS_REVIEW not in status_set
        assert len(status_set) == 3


class TestDomainException:
    """ドメイン例外のテスト"""

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-CREATES_DOMAIN_EXCEP")
    def test_creates_domain_exception_with_message(self) -> NoReturn:
        """メッセージ付きドメイン例外を作成"""
        # Arrange
        message = "テスト用例外メッセージ"

        # Act & Assert
        with pytest.raises(DomainException) as exc_info:
            raise DomainException(message)
        assert str(exc_info.value) == message

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-DOMAIN_EXCEPTION_IS_")
    def test_domain_exception_is_exception_subclass(self) -> None:
        """ドメイン例外がExceptionのサブクラス"""
        # Act & Assert
        assert issubclass(DomainException, Exception)

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-DOMAIN_EXCEPTION_WIT")
    def test_domain_exception_with_empty_message(self) -> NoReturn:
        """空メッセージのドメイン例外"""
        # Act & Assert
        with pytest.raises(DomainException) as exc_info:
            msg = ""
            raise DomainException(msg)
        assert str(exc_info.value) == ""


class TestSimpleValueObjectPerformance:
    """シンプルな値オブジェクトのパフォーマンステスト"""

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-TIME_ESTIMATION_CREA")
    def test_time_estimation_creation_performance(self) -> None:
        """時間見積もり作成のパフォーマンス"""

        # Arrange
        start_time = time.time()

        # Act: 1000個の時間見積もりを作成
        estimations = []
        for i in range(1000):
            estimation = TimeEstimation(i + 1)
            estimations.append(estimation)

        # Assert: 0.01秒以内に完了すべき
        elapsed = time.time() - start_time
        assert elapsed < 0.01, f"1000個の時間見積もり作成に{elapsed:.3f}秒かかりました(目標: < 0.01秒)"
        assert len(estimations) == 1000

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-ENUM_COMPARISON_PERF")
    def test_enum_comparison_performance(self) -> None:
        """列挙値比較のパフォーマンス"""

        # Arrange
        statuses = [
            ProgressStatus.NOT_STARTED,
            ProgressStatus.IN_PROGRESS,
            ProgressStatus.COMPLETED,
            ProgressStatus.NEEDS_REVIEW,
        ]

        start_time = time.time()

        # Act: 10000回の列挙値比較
        comparison_results = []
        for i in range(10000):
            status = statuses[i % len(statuses)]
            result = status == ProgressStatus.IN_PROGRESS
            comparison_results.append(result)

        # Assert: 0.01秒以内に完了すべき
        elapsed = time.time() - start_time
        assert elapsed < 0.01, f"10000回の列挙値比較に{elapsed:.3f}秒かかりました(目標: < 0.01秒)"
        assert len(comparison_results) == 10000

    @pytest.mark.spec("SPEC-SIMPLE_VALUE_OBJECTS-EXCEPTION_HANDLING_P")
    def test_exception_handling_performance(self) -> None:
        """例外処理のパフォーマンス"""

        # Arrange
        start_time = time.time()

        # Act: 100回の例外発生・キャッチ
        exception_count = 0
        for i in range(100):
            try:
                msg = f"テスト例外{i}"
                raise DomainException(msg)
            except DomainException:
                exception_count += 1

        # Assert: 0.01秒以内に完了すべき
        elapsed = time.time() - start_time
        assert elapsed < 0.01, f"100回の例外処理に{elapsed:.3f}秒かかりました(目標: < 0.01秒)"
        assert exception_count == 100
