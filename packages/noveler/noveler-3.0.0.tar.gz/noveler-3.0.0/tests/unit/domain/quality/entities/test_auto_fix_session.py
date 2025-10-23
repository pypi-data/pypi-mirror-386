#!/usr/bin/env python3
"""AutoFixSessionエンティティのユニットテスト

SPEC-QUALITY-001に基づく自動修正セッションエンティティのテスト
"""

from pathlib import Path

import pytest
pytestmark = pytest.mark.quality_domain

from noveler.domain.entities.auto_fix_session import AutoFixSession
from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.domain.value_objects.a31_fix_result import FixResult
from noveler.domain.value_objects.a31_session_id import SessionId


@pytest.mark.spec("SPEC-QUALITY-001")
class TestAutoFixSession:
    """AutoFixSessionエンティティのテスト"""

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-CREATE_AUTO_FIX_SESS")
    def test_create_auto_fix_session(self) -> None:
        """自動修正セッションの作成テスト"""
        session_id = SessionId.generate()
        target_file = Path("/test/project/40_原稿/第001話_テスト.md")
        fix_level = FixLevel.SAFE
        items_to_fix = ["A31-045", "A31-035", "A31-031"]

        session = AutoFixSession(
            session_id=session_id, target_file=target_file, fix_level=fix_level, items_to_fix=items_to_fix, results=[]
        )

        assert session.session_id == session_id
        assert session.target_file == target_file
        assert session.fix_level == FixLevel.SAFE
        assert session.items_to_fix == items_to_fix
        assert len(session.results) == 0

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-ADD_FIX_RESULT")
    def test_add_fix_result(self) -> None:
        """修正結果追加テスト"""
        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=Path("/test/file.md"),
            fix_level=FixLevel.SAFE,
            items_to_fix=["A31-045"],
            results=[],
        )

        fix_result = FixResult(
            item_id="A31-045",
            fix_applied=True,
            fix_type="format_indentation",
            changes_made=["段落頭に全角スペース追加: 5箇所"],
            before_score=80.0,
            after_score=100.0,
        )

        session.add_result(fix_result)

        assert len(session.results) == 1
        assert session.results[0].item_id == "A31-045"
        assert session.results[0].fix_applied is True

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-GET_SUCCESSFUL_FIXES")
    def test_get_successful_fixes(self) -> None:
        """成功した修正の取得テスト"""
        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=Path("/test/file.md"),
            fix_level=FixLevel.STANDARD,
            items_to_fix=["A31-045", "A31-035", "A31-022"],
            results=[],
        )

        # 成功した修正
        successful_fix = FixResult(
            item_id="A31-045",
            fix_applied=True,
            fix_type="format_indentation",
            changes_made=["段落頭修正"],
            before_score=80.0,
            after_score=100.0,
        )

        # 失敗した修正
        failed_fix = FixResult(
            item_id="A31-022",
            fix_applied=False,
            fix_type="dialogue_balance",
            changes_made=[],
            before_score=65.0,
            after_score=65.0,
        )

        session.add_result(successful_fix)
        session.add_result(failed_fix)

        successful_fixes = session.get_successful_fixes()

        assert len(successful_fixes) == 1
        assert successful_fixes[0].item_id == "A31-045"

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-GET_FAILED_FIXES")
    def test_get_failed_fixes(self) -> None:
        """失敗した修正の取得テスト"""
        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=Path("/test/file.md"),
            fix_level=FixLevel.INTERACTIVE,
            items_to_fix=["A31-022", "A31-033"],
            results=[],
        )

        failed_fix1 = FixResult(
            item_id="A31-022",
            fix_applied=False,
            fix_type="dialogue_balance",
            changes_made=[],
            before_score=65.0,
            after_score=65.0,
        )

        failed_fix2 = FixResult(
            item_id="A31-033",
            fix_applied=False,
            fix_type="character_consistency",
            changes_made=[],
            before_score=70.0,
            after_score=70.0,
        )

        session.add_result(failed_fix1)
        session.add_result(failed_fix2)

        failed_fixes = session.get_failed_fixes()

        assert len(failed_fixes) == 2
        assert all(not fix.fix_applied for fix in failed_fixes)

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-CALCULATE_OVERALL_IM")
    def test_calculate_overall_improvement(self) -> None:
        """全体的な改善度計算テスト"""
        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=Path("/test/file.md"),
            fix_level=FixLevel.STANDARD,
            items_to_fix=["A31-045", "A31-035"],
            results=[],
        )

        fix1 = FixResult(
            item_id="A31-045",
            fix_applied=True,
            fix_type="format_indentation",
            changes_made=["修正1"],
            before_score=80.0,
            after_score=100.0,
        )

        fix2 = FixResult(
            item_id="A31-035",
            fix_applied=True,
            fix_type="symbol_unification",
            changes_made=["修正2"],
            before_score=70.0,
            after_score=90.0,
        )

        session.add_result(fix1)
        session.add_result(fix2)

        improvement = session.calculate_overall_improvement()

        # (20.0 + 20.0) / 2 = 20.0点の改善
        assert improvement == 20.0

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-IS_COMPLETED")
    def test_is_completed(self) -> None:
        """セッション完了判定テスト"""
        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=Path("/test/file.md"),
            fix_level=FixLevel.SAFE,
            items_to_fix=["A31-045", "A31-035"],
            results=[],
        )

        # 初期状態では未完了
        assert session.is_completed() is False

        # 1つ目の結果を追加
        session.add_result(
            FixResult(
                item_id="A31-045",
                fix_applied=True,
                fix_type="format",
                changes_made=["修正"],
                before_score=80.0,
                after_score=100.0,
            )
        )

        # まだ未完了
        assert session.is_completed() is False

        # 2つ目の結果を追加
        session.add_result(
            FixResult(
                item_id="A31-035",
                fix_applied=True,
                fix_type="symbol",
                changes_made=["修正"],
                before_score=70.0,
                after_score=95.0,
            )
        )

        # 完了
        assert session.is_completed() is True

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-GET_EPISODE_INFO")
    def test_get_episode_info(self) -> None:
        """エピソード情報取得テスト"""
        target_file = Path("/test/project/40_原稿/第001話_冒険の始まり.md")

        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=target_file,
            fix_level=FixLevel.SAFE,
            items_to_fix=["A31-045"],
            results=[],
        )

        episode_number, episode_title = session.get_episode_info()

        assert episode_number == 1
        assert episode_title == "冒険の始まり"

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-GET_EPISODE_INFO_INV")
    def test_get_episode_info_invalid_format(self) -> None:
        """不正なファイル名形式のテスト"""
        target_file = Path("/test/project/invalid_filename.md")

        session = AutoFixSession(
            session_id=SessionId.generate(),
            target_file=target_file,
            fix_level=FixLevel.SAFE,
            items_to_fix=["A31-045"],
            results=[],
        )

        with pytest.raises(ValueError, match="Invalid episode filename format"):
            session.get_episode_info()

    @pytest.mark.spec("SPEC-AUTO_FIX_SESSION-TO_DICT")
    def test_to_dict(self) -> None:
        """辞書形式への変換テスト"""
        session_id = SessionId.generate()
        session = AutoFixSession(
            session_id=session_id,
            target_file=Path("/test/file.md"),
            fix_level=FixLevel.STANDARD,
            items_to_fix=["A31-045", "A31-035"],
            results=[],
        )

        session.add_result(
            FixResult(
                item_id="A31-045",
                fix_applied=True,
                fix_type="format",
                changes_made=["修正"],
                before_score=80.0,
                after_score=100.0,
            )
        )

        result = session.to_dict()

        assert result["session_id"] == str(session_id)
        assert result["target_file"] == str(session.target_file)
        assert result["fix_level"] == "standard"
        assert len(result["items_to_fix"]) == 2
        assert len(result["results"]) == 1
