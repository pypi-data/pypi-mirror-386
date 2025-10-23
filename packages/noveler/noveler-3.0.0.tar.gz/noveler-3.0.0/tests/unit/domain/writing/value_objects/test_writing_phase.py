#!/usr/bin/env python3
"""WritingPhase列挙型のユニットテスト

仕様書: specs/writing_phase.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

import pytest

from noveler.domain.writing.value_objects.writing_phase import PublicationStatus, WritingPhase


class TestWritingPhase:
    """WritingPhaseのテストクラス"""

    def test_all(self) -> None:
        """すべてのフェーズが定義されていることを確認"""
        # Assert
        assert WritingPhase.DRAFT.value == "draft"
        assert WritingPhase.REVISION.value == "revision"
        assert WritingPhase.FINAL_CHECK.value == "final_check"
        assert WritingPhase.PUBLISHED.value == "published"

    def test_name(self) -> None:
        """name属性が正しい値を返すことを確認"""
        # Assert
        assert WritingPhase.DRAFT.name == "DRAFT"
        assert WritingPhase.REVISION.name == "REVISION"
        assert WritingPhase.FINAL_CHECK.name == "FINAL_CHECK"
        assert WritingPhase.PUBLISHED.name == "PUBLISHED"

    def test_value_from_enum_get(self) -> None:
        """文字列値からEnumを取得できることを確認"""
        # Act & Assert
        assert WritingPhase("draft") == WritingPhase.DRAFT
        assert WritingPhase("revision") == WritingPhase.REVISION
        assert WritingPhase("final_check") == WritingPhase.FINAL_CHECK
        assert WritingPhase("published") == WritingPhase.PUBLISHED

    def test_value_value_error(self) -> None:
        """無効な値でValueErrorが発生することを確認"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            WritingPhase("invalid_phase")

        assert "'invalid_phase' is not a valid WritingPhase" in str(exc_info.value)

    def test_unnamed(self) -> None:
        """すべてのメンバーを列挙できることを確認"""
        # Act
        all_phases = list(WritingPhase)

        # Assert
        assert len(all_phases) == 4
        assert WritingPhase.DRAFT in all_phases
        assert WritingPhase.REVISION in all_phases
        assert WritingPhase.FINAL_CHECK in all_phases
        assert WritingPhase.PUBLISHED in all_phases


class TestPublicationStatus:
    """PublicationStatusのテストクラス"""

    def test_all_status(self) -> None:
        """すべてのステータスが定義されていることを確認"""
        # Assert
        assert PublicationStatus.UNPUBLISHED.value == "unpublished"
        assert PublicationStatus.SCHEDULED.value == "scheduled"
        assert PublicationStatus.PUBLISHED.value == "published"
        assert PublicationStatus.WITHDRAWN.value == "withdrawn"

    def test_name(self) -> None:
        """name属性が正しい値を返すことを確認"""
        # Assert
        assert PublicationStatus.UNPUBLISHED.name == "UNPUBLISHED"
        assert PublicationStatus.SCHEDULED.name == "SCHEDULED"
        assert PublicationStatus.PUBLISHED.name == "PUBLISHED"
        assert PublicationStatus.WITHDRAWN.name == "WITHDRAWN"

    def test_value_from_enum_get(self) -> None:
        """文字列値からEnumを取得できることを確認"""
        # Act & Assert
        assert PublicationStatus("unpublished") == PublicationStatus.UNPUBLISHED
        assert PublicationStatus("scheduled") == PublicationStatus.SCHEDULED
        assert PublicationStatus("published") == PublicationStatus.PUBLISHED
        assert PublicationStatus("withdrawn") == PublicationStatus.WITHDRAWN

    def test_value_value_error(self) -> None:
        """無効な値でValueErrorが発生することを確認"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            PublicationStatus("invalid_status")

        assert "'invalid_status' is not a valid PublicationStatus" in str(exc_info.value)

    def test_basic_functionality(self) -> None:
        """すべてのメンバーを列挙できることを確認"""
        # Act
        all_statuses = list(PublicationStatus)

        # Assert
        assert len(all_statuses) == 4
        assert PublicationStatus.UNPUBLISHED in all_statuses
        assert PublicationStatus.SCHEDULED in all_statuses
        assert PublicationStatus.PUBLISHED in all_statuses
        assert PublicationStatus.WITHDRAWN in all_statuses

    def test_edge_cases(self) -> None:
        """Enumの等価性比較が正しく動作することを確認"""
        # Arrange
        status1 = PublicationStatus.PUBLISHED
        status2 = PublicationStatus("published")
        status3 = PublicationStatus.UNPUBLISHED

        # Assert
        assert status1 == status2
        assert status1 != status3
        assert status1 is PublicationStatus.PUBLISHED
