"""Quality check command use case.

Encapsulates the business logic executed by CLI-driven quality check commands.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
from noveler.domain.repositories.quality_record_repository import QualityRecordRepository
from noveler.domain.value_objects.completion_status import QualityCheckResult


class QualityCheckTarget(str, Enum):
    """Enumerates the supported quality check targets."""

    SINGLE = "single"
    BULK = "bulk"
    RANGE = "range"
    LATEST = "latest"


@dataclass
class QualityCheckCommandRequest:
    """Input payload describing which quality checks to run.

    Attributes:
        project_name: Name of the project to analyze.
        target: Target mode (single, bulk, range, or latest).
        project_root: Optional project root path used for LLM scoring cache.
        episode_number: Episode number when running a single check.
        start_episode: Start of the episode range.
        end_episode: End of the episode range.
        auto_fix: Whether to attempt automatic fixes.
        verbose: Enable verbose logging or output.
        adaptive: Enable adaptive checking (reserved for future use).
        save_records: Persist quality records after checks.
        use_llm_scoring: Enable LLM-based scoring overrides.
    """


    project_name: str
    target: QualityCheckTarget
    project_root: Path | None = None
    episode_number: int | None = None
    start_episode: int | None = None
    end_episode: int | None = None
    auto_fix: bool = False
    verbose: bool = False
    adaptive: bool = False
    save_records: bool = True
    use_llm_scoring: bool = True


@dataclass
class QualityCheckCommandResponse:
    """Response payload returned after executing quality check commands.

    Attributes:

        success: Indicates whether the command succeeded.
        checked_count: Number of episodes checked.
        passed_count: Number of episodes that passed.
        results: Formatted result information for each episode.
        error_message: Error detail when execution fails.
        extracted_data: Structured data for downstream processing.
    """

    success: bool
    checked_count: int = 0
    passed_count: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None
    # 追加: 統一I/O向けの構造化データ
    # 他ユースケース（Universal系）と整合するため、抽出済みデータを付与
    extracted_data: dict[str, Any] = field(default_factory=dict)


class QualityCheckCommandUseCase:
    """Manage quality check command execution at the application layer."""

    def __init__(
        self,
        quality_check_repository: QualityCheckRepository,
        quality_record_repository: QualityRecordRepository,
        episode_repository = None,
    ) -> None:
        """Initialize the quality check command use case.

        Args:
            episode_repository: Episode repository
            quality_check_repository: Quality check repository
            quality_record_repository: Quality record repository
        """
        self.episode_repository = episode_repository
        self.quality_check_repository = quality_check_repository
        self.quality_record_repository = quality_record_repository

    def execute(self, request: QualityCheckCommandRequest) -> QualityCheckCommandResponse:
        """Dispatch quality checks according to the requested target.

        Args:
            request: Command request payload.

        Returns:
            QualityCheckCommandResponse: Aggregated results of the quality checks.
        """
        try:
            # LLMスコア反映のために現在リクエスト情報をコンテキストに保持（スレッドローカル不要・同期実行想定）
            self._current_request_project_root = request.project_root
            self._current_request_use_llm_scoring = bool(request.use_llm_scoring)
            self._last_used_llm_scoring = False
            if request.target == QualityCheckTarget.SINGLE:
                return self._check_single_episode(request)
            if request.target == QualityCheckTarget.BULK:
                return self._check_bulk_episodes(request)
            if request.target == QualityCheckTarget.RANGE:
                return self._check_range_episodes(request)
            if request.target == QualityCheckTarget.LATEST:
                return self._check_latest_episode(request)
            return QualityCheckCommandResponse(success=False, error_message=f"不明なチェック対象: {request.target}")

        except Exception as e:
            return QualityCheckCommandResponse(success=False, error_message=str(e))
        finally:
            # 後始末
            if hasattr(self, "_current_request_project_root"):
                delattr(self, "_current_request_project_root")
            if hasattr(self, "_current_request_use_llm_scoring"):
                delattr(self, "_current_request_use_llm_scoring")
            if hasattr(self, "_last_used_llm_scoring"):
                delattr(self, "_last_used_llm_scoring")

    def _check_single_episode(self, request: QualityCheckCommandRequest) -> QualityCheckCommandResponse:
        """Check a single episode and optionally persist the result."""
        # Retrieve episode metadata
        episode_info = self.episode_repository.get_episode_info(request.project_name, request.episode_number)

        if not episode_info:
            return QualityCheckCommandResponse(success=False, error_message="エピソードが見つかりません")

        # Execute the core quality check
        result = self._perform_quality_check(episode_info, request.auto_fix, request.adaptive)

        # Persist a quality record when enabled
        if request.save_records and result:
            self._save_quality_record(episode_info, result)

        results: list[Any] = [self._format_result(episode_info, result)]

        # Build extracted_data structure
        extracted = {
            "summary": {
                "checked_count": 1,
                "passed_count": 1 if result.passed else 0,
            },
            "items": [self._build_extracted_item(episode_info, result)],
        }

        return QualityCheckCommandResponse(
            success=True,
            checked_count=1,
            passed_count=1 if result.passed else 0,
            results=results,
            extracted_data=extracted,
        )

    def _check_bulk_episodes(self, request: QualityCheckCommandRequest) -> QualityCheckCommandResponse:
        """Check all episodes in the project.

        Args:
            request: Command request payload.

        Returns:
            QualityCheckCommandResponse: Aggregated results of the quality checks.
        """
        # Retrieve all episodes in the project
        episodes = self.episode_repository.get_all_episodes(request.project_name)

        if not episodes:
            return QualityCheckCommandResponse(success=False, error_message="エピソードが見つかりません")

        results: list[Any] = []
        passed_count = 0
        extracted_items: list[dict[str, Any]] = []

        for episode_info in episodes:
            result = self._perform_quality_check(episode_info, request.auto_fix, request.adaptive)

            if request.save_records and result:
                self._save_quality_record(episode_info, result)

            results.append(self._format_result(episode_info, result))
            extracted_items.append(self._build_extracted_item(episode_info, result))

            if result.passed:
                passed_count += 1

        extracted = {
            "summary": {
                "checked_count": len(episodes),
                "passed_count": passed_count,
            },
            "items": extracted_items,
        }

        return QualityCheckCommandResponse(
            success=True,
            checked_count=len(episodes),
            passed_count=passed_count,
            results=results,
            extracted_data=extracted,
        )

    def _check_range_episodes(self, request: QualityCheckCommandRequest) -> QualityCheckCommandResponse:
        """Check episodes within the requested range.

        Args:
            request: Command request payload.

        Returns:
            QualityCheckCommandResponse: Aggregated results of the quality checks.
        """
        # Retrieve episodes within the requested range
        episodes = self.episode_repository.get_episodes_in_range(
            project_name=request.project_name, start_episode=request.start_episode, end_episode=request.end_episode
        )

        if not episodes:
            return QualityCheckCommandResponse(
                success=False,
                error_message=f"第{request.start_episode}話~第{request.end_episode}話の範囲でエピソードが見つかりません",
            )

        results: list[Any] = []
        passed_count = 0
        extracted_items: list[dict[str, Any]] = []

        for episode_info in episodes:
            result = self._perform_quality_check(episode_info, request.auto_fix, request.adaptive)

            if request.save_records and result:
                self._save_quality_record(episode_info, result)

            results.append(self._format_result(episode_info, result))
            extracted_items.append(self._build_extracted_item(episode_info, result))

            if result.passed:
                passed_count += 1

        extracted = {
            "summary": {
                "checked_count": len(episodes),
                "passed_count": passed_count,
            },
            "items": extracted_items,
        }

        return QualityCheckCommandResponse(
            success=True,
            checked_count=len(episodes),
            passed_count=passed_count,
            results=results,
            extracted_data=extracted,
        )

    def _check_latest_episode(self, request: QualityCheckCommandRequest) -> QualityCheckCommandResponse:
        """Check the latest episode available in the repository.

        Args:
            request: Command request payload.

        Returns:
            QualityCheckCommandResponse: Aggregated results of the quality checks.
        """
        # Retrieve the latest episode from the repository
        latest_episode = self.episode_repository.get_latest_episode(request.project_name)

        if not latest_episode:
            return QualityCheckCommandResponse(success=False, error_message="エピソードが見つかりません")

        # Reuse the single-episode path
        request.episode_number = latest_episode["number"]
        return self._check_single_episode(request)

    def _perform_quality_check(
        self,
        episode_info: dict[str, Any],
        auto_fix: bool,
        _adaptive: bool = False,
    ) -> QualityCheckResult:
        """Execute quality check.

        Args:
            episode_info: Episode information
            auto_fix: Whether to enable automatic fixes
            adaptive: Whether to enable adaptive checking

        Returns:
            Quality check result
        """
        content = episode_info.get("content", "")

        # 基本の品質チェック
        result = self.quality_check_repository.check_quality(
            project_name=episode_info.get("project_name", ""), episode_number=episode_info["number"], content=content
        )

        # 自動修正が有効な場合
        if auto_fix and not result.passed:
            fixed_content, fixed_result = self.quality_check_repository.auto_fix_content(
                content=content, issues=result.issues
            )

            if fixed_content != content:
                # 修正内容を保存
                self.episode_repository.update_content(
                    project_name=episode_info.get("project_name", ""),
                    episode_number=episode_info["number"],
                    new_content=fixed_content,
                )

                # 修正後の結果を返す
                result = fixed_result
                episode_info["auto_fixed"] = True
                content = fixed_content

        # LLM応答からのスコア反映（利用可能な場合）
        try:
            # リクエスト側で明示オプションが無効の場合はスキップ
            # project_root が不明な場合はスキップ
            req_root: Path | None = getattr(self, "_current_request_project_root", None)
            use_llm: bool = getattr(self, "_current_request_use_llm_scoring", False)
            if use_llm and req_root is not None:
                llm_override = self._try_override_with_llm_score(
                    project_root=req_root,
                    episode_number=episode_info["number"],
                )
                if llm_override is not None:
                    self._last_used_llm_scoring = True
                    return llm_override
        except Exception:
            # Ignore missing/invalid LLM outputs and fall back to local results
            pass

        return result

    def _save_quality_record(self, episode_info: dict[str, Any], result: QualityCheckResult) -> None:
        """Persist quality check results for future reference."""
        record = {
            "project_name": episode_info.get("project_name", ""),
            "episode_number": episode_info["number"],
            "score": result.score.value,
            "passed": result.passed,
            "issues": result.issues,
            "auto_fixed": episode_info.get("auto_fixed", False),
            "metadata": {"source": "llm" if getattr(self, "_last_used_llm_scoring", False) else "local"},
        }

        self.quality_record_repository.save_check_result(record)

    # ===== 追加: LLMログからのスコア反映（同期・フォールバック） =====
    def _try_override_with_llm_score(self, project_root: Path, episode_number: int) -> QualityCheckResult | None:
        """Override the local result with scores extracted from recent LLM outputs when available."""
        checks_dir = project_root / ".noveler" / "checks"
        if not checks_dir.exists():
            return None

        candidates = sorted(checks_dir.glob("LLM_quality_check_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in candidates:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            try:
                req = data.get("request", {})
                tsc = req.get("type_specific_config", {}) or {}
                ep = int(tsc.get("episode_number")) if tsc.get("episode_number") is not None else None
                if ep != episode_number:
                    continue

                resp = data.get("response", {}) or {}
                extracted = resp.get("extracted_data", {}) or {}

                score_val = extracted.get("score")
                issues_raw = extracted.get("issues", [])

                if score_val is None:
                    # response_contentからの解析を試行
                    rc = resp.get("response_content", "") or ""
                    try:
                        parsed = json.loads(rc)
                        score_val = parsed.get("score")
                        if not issues_raw:
                            issues_raw = parsed.get("issues", [])
                    except Exception:
                        pass

                if score_val is None:
                    continue

                # QualityCheckResult(Completion)へ変換
                from noveler.domain.value_objects.completion_status import (
                    QualityCheckResult as CompletionQualityCheckResult,
                )
                from noveler.domain.value_objects.quality_score import QualityScore

                try:
                    score_int = int(round(float(score_val)))
                except Exception:
                    continue

                # Use repository configuration for thresholds, matching existing behaviour
                threshold = float(self.quality_check_repository.get_quality_threshold().value)
                llm_result = CompletionQualityCheckResult.from_score(
                    QualityScore(score_int), threshold
                )

                # Normalize issues into strings
                issues: list[str] = []
                if isinstance(issues_raw, list):
                    for it in issues_raw:
                        if isinstance(it, str):
                            issues.append(it)
                        elif isinstance(it, dict):
                            msg = it.get("message") or it.get("detail") or str(it)
                            issues.append(str(msg))
                        else:
                            issues.append(str(it))

                # Follow the from_score verdict but override issues with the LLM-provided list
                return CompletionQualityCheckResult(score=llm_result.score, passed=llm_result.passed, issues=issues)

            except Exception:
                continue

        return None

    def _format_result(self, episode_info: dict[str, Any], result: QualityCheckResult) -> dict[str, Any]:
        """Format a quality check result for reporting.

        Args:
            episode_info: Episode information
            result: Quality check result

        Returns:
            Formatted result
        """
        return {
            "episode_number": episode_info["number"],
            "title": episode_info.get("title", ""),
            "score": result.score.value,
            "passed": result.passed,
            "issues": result.issues,
            "auto_fixed": episode_info.get("auto_fixed", False),
        }

    def _build_extracted_item(self, episode_info: dict[str, Any], result: QualityCheckResult) -> dict[str, Any]:
        """Build a structured extracted-data entry consistent with other use cases.

        Maintains existing result structure while aligning with extracted_data from other use cases.
        """
        return {
            "episode_number": episode_info["number"],
            "title": episode_info.get("title", ""),
            "score": result.score.value,
            "passed": result.passed,
            "issues": result.issues,
            "auto_fixed": episode_info.get("auto_fixed", False),
        }
