#!/usr/bin/env python3

"""Tests.tests.unit.application.test_quality_check_command_use_case_minimal
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

import types

from noveler.application.use_cases.quality_check_command_use_case import (
    QualityCheckCommandRequest,
    QualityCheckCommandUseCase,
    QualityCheckTarget,
)
from noveler.domain.value_objects.completion_status import (
    QualityCheckResult as CompletionQualityCheckResult,
)
from noveler.domain.value_objects.quality_score import QualityScore


class _FakeEpisodeRepository:
    def __init__(self) -> None:
        self.called_with: tuple[str, int] | None = None

    def get_episode_info(self, project_name: str, episode_number: int):
        self.called_with = (project_name, episode_number)
        return {"number": episode_number, "title": "テスト", "content": "テスト本文"}


class _FakeQualityCheckRepository:
    def check_quality(self, project_name: str, episode_number: int, content: str | None = None):  # type: ignore[override]
        # 合格ケースを返す
        return CompletionQualityCheckResult(score=QualityScore(80), passed=True, issues=[])


class _FakeQualityRecordRepository:
    def __init__(self) -> None:
        self.saved_record: dict | None = None

    def save_check_result(self, record: dict) -> None:
        self.saved_record = record


def test_quality_check_use_case_calls_episode_repo_with_correct_args():
    episode_repo = _FakeEpisodeRepository()
    quality_repo = _FakeQualityCheckRepository()
    record_repo = _FakeQualityRecordRepository()

    use_case = QualityCheckCommandUseCase(
        quality_check_repository=quality_repo,  # type: ignore[arg-type]
        quality_record_repository=record_repo,  # type: ignore[arg-type]
        episode_repository=episode_repo,  # type: ignore[arg-type]
    )

    req = QualityCheckCommandRequest(
        project_name="proj",
        target=QualityCheckTarget.SINGLE,
        episode_number=1,
        auto_fix=False,
        verbose=False,
        adaptive=False,
        save_records=True,
    )

    resp = use_case.execute(req)

    # 正常終了
    assert resp.success is True
    # EpisodeRepo への引数が正しい
    assert episode_repo.called_with == ("proj", 1)
    # 記録保存が呼ばれている
    assert record_repo.saved_record is not None
    assert record_repo.saved_record.get("episode_number") == 1
