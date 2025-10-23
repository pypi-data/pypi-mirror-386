#!/usr/bin/env python3
"""ProgressStatus値オブジェクト群のユニットテスト

仕様書: specs/progress_status.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

import pytest

from noveler.domain.value_objects.progress_status import NextAction, ProgressStatus
from noveler.domain.value_objects.time_estimation import TimeEstimation

pytestmark = pytest.mark.vo_smoke



class TestProgressStatus:
    """ProgressStatusのテストクラス"""

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_all_status(self) -> None:
        """すべてのステータスが定義されていることを確認"""
        # Act & Assert
        assert ProgressStatus.NOT_STARTED.value == "未開始"
        assert ProgressStatus.IN_PROGRESS.value == "進行中"
        assert ProgressStatus.COMPLETED.value == "完了"
        assert ProgressStatus.NEEDS_REVIEW.value == "要確認"
        assert ProgressStatus.BLOCKED.value == "阻害"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_emoji(self) -> None:
        """各ステータスに対応する絵文字が正しく返されることを確認"""
        # Act & Assert
        assert ProgressStatus.NOT_STARTED.emoji() == "⚪"
        assert ProgressStatus.IN_PROGRESS.emoji() == "🟡"
        assert ProgressStatus.COMPLETED.emoji() == "✅"
        assert ProgressStatus.NEEDS_REVIEW.emoji() == "⚠️"
        assert ProgressStatus.BLOCKED.emoji() == "🚫"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_state_start_from(self) -> None:
        """NOT_STARTEDからの状態遷移を確認"""
        # Arrange
        status = ProgressStatus.NOT_STARTED

        # Act & Assert
        assert status.can_transition_to(ProgressStatus.IN_PROGRESS) is True
        assert status.can_transition_to(ProgressStatus.BLOCKED) is True
        assert status.can_transition_to(ProgressStatus.COMPLETED) is False
        assert status.can_transition_to(ProgressStatus.NEEDS_REVIEW) is False
        assert status.can_transition_to(ProgressStatus.NOT_STARTED) is False

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_state_from(self) -> None:
        """IN_PROGRESSからの状態遷移を確認"""
        # Arrange
        status = ProgressStatus.IN_PROGRESS

        # Act & Assert
        assert status.can_transition_to(ProgressStatus.COMPLETED) is True
        assert status.can_transition_to(ProgressStatus.NEEDS_REVIEW) is True
        assert status.can_transition_to(ProgressStatus.BLOCKED) is True
        assert status.can_transition_to(ProgressStatus.NOT_STARTED) is False
        assert status.can_transition_to(ProgressStatus.IN_PROGRESS) is False

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_state_complete_from(self) -> None:
        """COMPLETEDからの状態遷移を確認"""
        # Arrange
        status = ProgressStatus.COMPLETED

        # Act & Assert
        assert status.can_transition_to(ProgressStatus.NEEDS_REVIEW) is True
        assert status.can_transition_to(ProgressStatus.NOT_STARTED) is False
        assert status.can_transition_to(ProgressStatus.IN_PROGRESS) is False
        assert status.can_transition_to(ProgressStatus.BLOCKED) is False
        assert status.can_transition_to(ProgressStatus.COMPLETED) is False

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_state_verification_from(self) -> None:
        """NEEDS_REVIEWからの状態遷移を確認"""
        # Arrange
        status = ProgressStatus.NEEDS_REVIEW

        # Act & Assert
        assert status.can_transition_to(ProgressStatus.IN_PROGRESS) is True
        assert status.can_transition_to(ProgressStatus.COMPLETED) is True
        assert status.can_transition_to(ProgressStatus.NOT_STARTED) is False
        assert status.can_transition_to(ProgressStatus.BLOCKED) is False
        assert status.can_transition_to(ProgressStatus.NEEDS_REVIEW) is False


@pytest.mark.spec("SPEC-WORKFLOW-001")
class TestNextAction:
    """NextActionのテストクラス"""

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_init(self) -> None:
        """正常なパラメータで初期化できることを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=150)

        # Act
        action = NextAction(
            title="プロット作成", command="novel plot master", time_estimation=time_est, priority="high"
        )

        # Assert
        assert action.title == "プロット作成"
        assert action.command == "novel plot master"
        assert action.time_estimation == time_est
        assert action.priority == "high"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_unnamed(self) -> None:
        """priorityを指定しない場合にデフォルト値が設定されることを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=60)

        # Act
        action = NextAction(title="品質チェック", command="novel check", time_estimation=time_est)

        # Assert
        assert action.priority == "medium"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_value_error(self) -> None:
        """空のタイトルでValueErrorが発生することを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=30)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            NextAction(title="", command="novel check", time_estimation=time_est)

        assert str(exc_info.value) == "アクションタイトルは必須です"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_value_error_1(self) -> None:
        """空白のみのタイトルでValueErrorが発生することを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=30)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            NextAction(title="   ", command="novel check", time_estimation=time_est)

        assert str(exc_info.value) == "アクションタイトルは必須です"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_value_error_2(self) -> None:
        """空のコマンドでValueErrorが発生することを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=30)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            NextAction(title="品質チェック", command="", time_estimation=time_est)

        assert str(exc_info.value) == "実行コマンドは必須です"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_value_error_3(self) -> None:
        """空白のみのコマンドでValueErrorが発生することを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=30)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            NextAction(title="品質チェック", command="   ", time_estimation=time_est)

        assert str(exc_info.value) == "実行コマンドは必須です"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_value_error_4(self) -> None:
        """無効な優先度でValueErrorが発生することを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=30)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            NextAction(
                title="品質チェック",
                command="novel check",
                time_estimation=time_est,
                priority="urgent",  # 無効な値
            )

        assert str(exc_info.value) == "優先度は high, medium, low のいずれかである必要があります"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_display_text(self) -> None:
        """display_text()が分単位で正しく表示されることを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=45)
        action = NextAction(title="品質チェック", command="novel check", time_estimation=time_est)

        # Act
        display = action.display_text()

        # Assert
        assert display == "品質チェック (所要時間: 45分)"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_display_text_1(self) -> None:
        """display_text()が時間単位で正しく表示されることを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=120)
        action = NextAction(title="プロット作成", command="novel plot master", time_estimation=time_est)

        # Act
        display = action.display_text()

        # Assert
        assert display == "プロット作成 (所要時間: 2時間)"

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_verification(self) -> None:
        """frozen=Trueにより値の変更ができないことを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=60)
        action = NextAction(title="テスト", command="test", time_estimation=time_est)

        # Act & Assert
        with pytest.raises(AttributeError, match=".*"):
            action.title = "変更"  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            action.command = "変更"  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            action.priority = "high"  # type: ignore

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_basic_functionality(self) -> None:
        """同じ内容のインスタンスが等価と判定されることを確認"""
        # Arrange
        time_est1 = TimeEstimation(minutes=60)
        time_est2 = TimeEstimation(minutes=60)

        action1 = NextAction(title="テスト", command="test", time_estimation=time_est1, priority="high")
        action2 = NextAction(title="テスト", command="test", time_estimation=time_est2, priority="high")
        action3 = NextAction(title="異なる", command="test", time_estimation=time_est1, priority="high")

        # Act & Assert
        assert action1 == action2
        assert action1 != action3

    @pytest.mark.spec("SPEC-WORKFLOW-001")
    def test_edge_cases(self) -> None:
        """frozen=Trueによりハッシュ化可能なことを確認"""
        # Arrange
        time_est = TimeEstimation(minutes=60)
        action1 = NextAction(title="テスト", command="test", time_estimation=time_est)
        action2 = NextAction(title="テスト", command="test", time_estimation=time_est)

        # Act
        action_set = {action1, action2}

        # Assert
        assert len(action_set) == 1  # 同じ内容なので1つにまとまる
        assert hash(action1) == hash(action2)
