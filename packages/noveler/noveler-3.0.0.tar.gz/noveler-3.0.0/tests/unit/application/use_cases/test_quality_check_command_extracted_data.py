"""Tests.tests.unit.application.use_cases.test_quality_check_command_extracted_data
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import pytest

from noveler.application.use_cases.quality_check_command_use_case import (
    QualityCheckCommandRequest,
    QualityCheckCommandUseCase,
    QualityCheckTarget,
)
from noveler.domain.value_objects.completion_status import QualityCheckResult
from noveler.domain.value_objects.quality_score import QualityScore


class DummyEpisodeRepository:
    def __init__(self, single=None, all_eps=None, range_eps=None):
        self._single = single
        self._all = all_eps or []
        self._range = range_eps or []
        self.updated = []

    def get_episode_info(self, project_name, episode_number):
        if self._single is not None:
            return self._single
        # fallback find in all
        for e in self._all:
            if e.get("number") == episode_number:
                return e
        return None

    def get_all_episodes(self, project_name):
        return list(self._all)

    def get_episodes_in_range(self, project_name, start_episode, end_episode):
        return [e for e in self._range if start_episode <= e.get("number", 0) <= end_episode]

    def update_content(self, project_name, episode_number, new_content):
        self.updated.append((project_name, episode_number, new_content))


class DummyQualityCheckRepository:
    def __init__(self, result_by_number=None, default=None, auto_fix=None):
        # result_by_number: dict[int, QualityCheckResult]
        self._by_no = result_by_number or {}
        self._default = default
        self._auto_fix = auto_fix  # tuple[str, QualityCheckResult]

    def check_quality(self, project_name: str, episode_number: int, content: str | None = None):
        return self._by_no.get(episode_number) or self._default

    def auto_fix_content(self, content: str, issues: list[str]):
        return self._auto_fix or (content, self._default)


class DummyQualityRecordRepository:
    def __init__(self):
        self.saved = []

    def save_check_result(self, record):
        self.saved.append(record)


def _make_episode(project_name: str, num: int, title: str = "T", content: str = "C"):
    return {"project_name": project_name, "number": num, "title": title, "content": content}


def test_single_episode_extracted_data_success():
    project = "proj"
    ep = _make_episode(project, 1, "Ep1", "text")
    episode_repo = DummyEpisodeRepository(single=ep)

    qc_result = QualityCheckResult(score=QualityScore.from_float(85), passed=True, issues=[])
    qc_repo = DummyQualityCheckRepository(default=qc_result)

    record_repo = DummyQualityRecordRepository()

    use_case = QualityCheckCommandUseCase(qc_repo, record_repo, episode_repo)
    req = QualityCheckCommandRequest(project_name=project, target=QualityCheckTarget.SINGLE, episode_number=1)

    resp = use_case.execute(req)

    assert resp.success is True
    assert resp.checked_count == 1
    assert resp.passed_count == 1
    # extracted_data
    assert isinstance(resp.extracted_data, dict)
    summary = resp.extracted_data.get("summary", {})
    assert summary.get("checked_count") == 1
    assert summary.get("passed_count") == 1
    items = resp.extracted_data.get("items")
    assert isinstance(items, list) and len(items) == 1
    item = items[0]
    assert item.get("episode_number") == 1
    assert item.get("title") == "Ep1"
    assert item.get("score") == 85
    assert item.get("passed") is True
    assert item.get("issues") == []


def test_bulk_episodes_extracted_data_mixed_results():
    project = "proj"
    eps = [_make_episode(project, 1, "Ep1"), _make_episode(project, 2, "Ep2")]
    episode_repo = DummyEpisodeRepository(all_eps=eps)

    res1 = QualityCheckResult(score=QualityScore.from_float(80), passed=True, issues=[])
    res2 = QualityCheckResult(score=QualityScore.from_float(60), passed=False, issues=["x"])
    qc_repo = DummyQualityCheckRepository(result_by_number={1: res1, 2: res2})
    record_repo = DummyQualityRecordRepository()

    use_case = QualityCheckCommandUseCase(qc_repo, record_repo, episode_repo)
    req = QualityCheckCommandRequest(project_name=project, target=QualityCheckTarget.BULK)

    resp = use_case.execute(req)

    assert resp.success is True
    assert resp.checked_count == 2
    assert resp.passed_count == 1
    extracted = resp.extracted_data
    assert extracted["summary"]["checked_count"] == 2
    assert extracted["summary"]["passed_count"] == 1
    assert len(extracted["items"]) == 2
    # ordering follows repo order
    i1, i2 = extracted["items"][0], extracted["items"][1]
    assert i1["episode_number"] == 1 and i1["passed"] is True and i1["score"] == 80
    assert i2["episode_number"] == 2 and i2["passed"] is False and i2["score"] == 60


def test_range_episodes_extracted_data_and_auto_fix_flag():
    project = "proj"
    eps = [_make_episode(project, 3, "Ep3", "bad... text!! です。 です。")]
    episode_repo = DummyEpisodeRepository(range_eps=eps)

    # initial result: fail, then auto-fix -> pass
    initial = QualityCheckResult(score=QualityScore.from_float(60), passed=False, issues=["bad"])
    fixed = QualityCheckResult(score=QualityScore.from_float(90), passed=True, issues=[])
    qc_repo = DummyQualityCheckRepository(default=initial, auto_fix=("fixed text", fixed))
    record_repo = DummyQualityRecordRepository()

    use_case = QualityCheckCommandUseCase(qc_repo, record_repo, episode_repo)
    req = QualityCheckCommandRequest(
        project_name=project,
        target=QualityCheckTarget.RANGE,
        start_episode=3,
        end_episode=3,
        auto_fix=True,
    )

    resp = use_case.execute(req)

    assert resp.success is True
    assert resp.checked_count == 1
    assert resp.passed_count == 1
    item = resp.extracted_data["items"][0]
    assert item["episode_number"] == 3
    assert item["passed"] is True
    assert item["score"] == 90
    # auto_fix後は auto_fixed フラグがTrueで返る
    assert item.get("auto_fixed") is True
