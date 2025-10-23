"""Domain.versioning.entities
Where: Domain entities modelling versioned artifacts and metadata.
What: Store version information, change sets, and audit data.
Why: Support version tracking across the platform.
"""

#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

"""自動バージョニングのドメインエンティティ
優先順位ルールとビジネスロジックを実装
"""


import re
from collections import defaultdict
from dataclasses import dataclass, field

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.versioning.value_objects import (
    BidirectionalForeshadowingImpact,
    ChangeScope,
    ChangeSignificance,
    ChapterForeshadowingImpact,
    ChapterImpact,
    ConsistencyImpact,
    ForeshadowingImpact,
    MultiChapterImpact,
    VersionCalculator,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class VersionDeterminer:
    """バージョン判定器エンティティ"""

    def __init__(self) -> None:
        # 優先順位ルール(重要な順)
        self.major_triggers = [
            "20_プロット/全体構成.yaml",
            "20_プロット/リソース配分.yaml",
        ]

        self.minor_triggers = [
            "20_プロット/章別プロット/",
        ]

    def determine_version_type(self, changed_files: list[str]) -> str:
        """変更ファイルからバージョンタイプを判定(優先順位適用)"""

        # 優先度1: メジャー変更をチェック
        for file in changed_files:
            if any(file == trigger or file.startswith(trigger) for trigger in self.major_triggers):
                return "major"

        # 優先度2: マイナー変更をチェック
        for file in changed_files:
            if any(file.startswith(trigger) for trigger in self.minor_triggers):
                return "minor"

        # 優先度3: その他はパッチ
        return "patch"


class FileChangeAnalyzer:
    """ファイル変更分析器エンティティ"""

    def extract_plot_changes(self, changed_files: list[str]) -> list[str]:
        """プロット関連ファイルの変更のみを抽出"""
        plot_prefixes = [
            "20_プロット/",
            "30_設定集/",  # 設定変更もプロット変更として扱う
        ]

        return [file for file in changed_files if any(file.startswith(prefix) for prefix in plot_prefixes)]

    def categorize_by_scope(self, changed_files: list[str]) -> dict[ChangeScope, list[str]]:
        """変更をスコープ別に分類"""
        categorized = defaultdict(list)

        major_patterns = [
            "20_プロット/全体構成.yaml",
            "20_プロット/リソース配分.yaml",
        ]

        minor_patterns = [
            "20_プロット/章別プロット/",
        ]

        for file in changed_files:
            if any(file == pattern or file.startswith(pattern) for pattern in major_patterns):
                categorized[ChangeScope.MAJOR].append(file)
            elif any(file.startswith(pattern) for pattern in minor_patterns):
                categorized[ChangeScope.MINOR].append(file)
            else:
                categorized[ChangeScope.PATCH].append(file)

        return categorized


@dataclass(init=False)
class VersionSuggestion:
    """バージョン提案エンティティ"""

    current_version: str
    suggested_version: str
    version_type: str
    changed_files: list[str]
    explanation: str
    description: str | None

    def __init__(
        self,
        current_version: str,
        suggested_version: str,
        version_type: str,
        changed_files: list[str] | None = None,
        explanation: str | None = None,
        justification: str | None = None,
        description: str | None = None,
    ) -> None:
        self.current_version = current_version
        self.suggested_version = suggested_version
        self.version_type = version_type
        self.changed_files = list(changed_files or [])
        expl = explanation if explanation is not None else justification
        if expl is None or not str(expl).strip():
            expl = "変更内容の詳細が提供されていません。"
        self.explanation = str(expl)
        self.description = description

    @property
    def justification(self) -> str:
        return self.explanation

    @classmethod
    def create_suggestion(cls, version_data: dict[str, Any]) -> VersionSuggestion | None:
        current_version = version_data.get("current_version")
        version_type = (version_data.get("version_type") or "patch").lower()
        changed_files = version_data.get("changed_files") or []
        plot_data = version_data.get("plot_data") or {}

        calculator = VersionCalculator()
        normalized_current = current_version if str(current_version).startswith("v") else f"v{current_version}"

        try:
            suggested_version = calculator.calculate_next_version(normalized_current, version_type)
        except Exception:
            # 無効なバージョン形式の場合はNoneを返す
            return None

        suggested_version = suggested_version.lstrip("v")

        justification = cls._build_justification(version_type, plot_data)

        return cls(
            current_version=current_version,
            suggested_version=suggested_version,
            version_type=version_type,
            changed_files=changed_files,
            explanation=justification,
        )

    @staticmethod
    def _build_justification(version_type: str, plot_data: dict[str, Any]) -> str:
        title = plot_data.get("basic_info", {}).get("title", "プロジェクト")
        if version_type == "major":
            return f"{title}の全体構成に大きな変更が加えられました。"
        if version_type == "minor":
            return f"{title}の章別プロットに調整が加えられました。"
        return f"{title}の軽微な修正が実施されました。"

    def get_formatted_message(self, impact_info: dict[str, Any] | None = None) -> str:
        heading = f"バージョン更新提案: {self.current_version} → {self.suggested_version} ({self.version_type})"
        message = f"{heading}\n理由: {self.justification}"
        if impact_info:
            chapters = impact_info.get("affected_chapters") or []
            episode_count = impact_info.get("affected_episodes", 0) or 0
            message += f"\n影響: 章数 {len(chapters)}, エピソード数 {episode_count}"
        return message

    @classmethod
    def create_major_bump(
        cls, current_version: str, changed_files: list[str], description: str | None = None
    ) -> VersionSuggestion:
        """メジャーバージョンアップの提案を作成"""
        calculator = VersionCalculator()
        suggested = calculator.calculate_next_version(current_version, "major")

        explanation = "全体構成の変更によりメジャーバージョンアップが必要です。"

        return cls(
            current_version=current_version,
            suggested_version=suggested,
            version_type="major",
            changed_files=changed_files,
            explanation=explanation,
            description=description,
        )

    @classmethod
    def create_minor_bump(
        cls, current_version: str, changed_files: list[str], description: str | None = None
    ) -> VersionSuggestion:
        """マイナーバージョンアップの提案を作成"""
        calculator = VersionCalculator()
        suggested = calculator.calculate_next_version(current_version, "minor")

        explanation = "章別プロットの変更によりマイナーバージョンアップが必要です。"

        return cls(
            current_version=current_version,
            suggested_version=suggested,
            version_type="minor",
            changed_files=changed_files,
            explanation=explanation,
            description=description,
        )

    @classmethod
    def create_patch_bump(
        cls, current_version: str, changed_files: list[str], description: str | None = None
    ) -> VersionSuggestion:
        """パッチバージョンアップの提案を作成"""
        calculator = VersionCalculator()
        suggested = calculator.calculate_next_version(current_version, "patch")

        explanation = "設定の微調整によりパッチバージョンアップが推奨されます。"

        return cls(
            current_version=current_version,
            suggested_version=suggested,
            version_type="patch",
            changed_files=changed_files,
            explanation=explanation,
            description=description,
        )


@dataclass
class PlotCommitImpact:
    """プロットコミット影響のサマリー."""

    commit_hash: str
    changed_files: list[str]
    plot_files: list[str]
    version_type: str
    affected_chapters: list[int]

    @property
    def has_plot_changes(self) -> bool:
        return bool(self.plot_files)


@dataclass
class PlotConsistencyResult:
    """プロット整合性解析結果."""

    is_consistent: bool
    consistency_score: float
    issues: list[str]


@dataclass
class CommitAnalysis:
    """コミット分析結果エンティティ"""

    significance: ChangeSignificance
    changed_files: list[str]
    requires_versioning: bool
    plot_files: list[str] = None
    scope_categories: dict[ChangeScope, list[str]] | None = None

    def __post_init__(self) -> None:
        if self.plot_files is None:
            object.__setattr__(self, "plot_files", [])
        if self.scope_categories is None:
            object.__setattr__(
                self,
                "scope_categories",
                {scope: [] for scope in ChangeScope},
            )

    @property
    def reason(self) -> str:
        """分析理由を取得"""
        return self.significance.reason

    @classmethod
    def create_analysis(
        cls,
        changed_files: list[str],
        file_analyzer: FileChangeAnalyzer | None = None,
    ) -> CommitAnalysis:
        analyzer = file_analyzer or FileChangeAnalyzer()
        plot_files = analyzer.extract_plot_changes(changed_files)
        categorized = analyzer.categorize_by_scope(changed_files)
        normalized_scope = {scope: list(categorized.get(scope, [])) for scope in ChangeScope}

        if normalized_scope[ChangeScope.MAJOR]:
            significance = ChangeSignificance.HIGH
        elif normalized_scope[ChangeScope.MINOR]:
            significance = ChangeSignificance.MEDIUM
        else:
            significance = ChangeSignificance.LOW

        requires_versioning = significance.level in {"major", "minor"}

        return cls(
            significance=significance,
            changed_files=list(changed_files),
            requires_versioning=requires_versioning,
            plot_files=plot_files,
            scope_categories=normalized_scope,
        )

    def get_significance(self) -> ChangeSignificance:
        """変更重要度を返す."""
        return self.significance


class PlotCommitAnalyzer:
    """プロットコミット分析器エンティティ"""

    _git_service: Any | None = None

    def __init__(self) -> None:
        # 構造的変更を示すキーワード
        self.structural_keywords = [
            "ending_type",
            "structure",
            "flow",
            "sequence",
            "main_plot",
            "sub_plot",
            "climax",
            "resolution",
            "character_arc",
            "theme",
            "genre",
        ]

        # 軽微な変更を示すキーワード
        self.minor_keywords = [
            "description",
            "comment",
            "note",
            "memo",
            "typo",
            "fix",
            "correction",
            "adjustment",
        ]

    def analyze_commit(self, changed_files: list[str], git_diff_content: str) -> CommitAnalysis:
        """コミット内容を分析して重要度を判定"""

        # プロット関連ファイルのみを対象
        plot_files = self._extract_plot_files(changed_files)

        if not plot_files:
            # プロット変更なし
            significance = ChangeSignificance.patch("プロット変更なし")
            return CommitAnalysis(significance, changed_files, False)

        # 変更内容の重要度を分析
        if self._has_structural_changes(git_diff_content):
            if self._is_major_plot_file(plot_files):
                significance = ChangeSignificance.major("構造的変更")
                requires_versioning = True
            else:
                significance = ChangeSignificance.major("重要な章別変更")
                requires_versioning = True
        elif self._is_minor_change(git_diff_content):
            significance = ChangeSignificance.minor("軽微な修正")
            requires_versioning = False
        else:
            # 中程度の変更
            significance = ChangeSignificance.minor("章別プロット更新")
            requires_versioning = True

        return CommitAnalysis(significance, plot_files, requires_versioning)

    def analyze_commit_impact(self, commit_hash: str) -> PlotCommitImpact:
        """Gitコミットの影響を高レベルで要約する."""
        git_service = self._git_service
        if git_service is None:
            raise RuntimeError("Gitサービスが未設定です")

        changed_files = git_service.get_changed_files(commit_hash)
        plot_files = self._extract_plot_files(changed_files)

        version_determiner = VersionDeterminer()
        version_type = version_determiner.determine_version_type(changed_files)

        affected_chapters = self._extract_affected_chapters(plot_files)
        if not affected_chapters and version_type == "major":
            affected_chapters = [1]

        return PlotCommitImpact(
            commit_hash=commit_hash,
            changed_files=changed_files,
            plot_files=plot_files,
            version_type=version_type,
            affected_chapters=affected_chapters,
        )

    def analyze_plot_consistency(self, plot_data: dict[str, Any]) -> PlotConsistencyResult:
        """簡易的なプロット整合性解析を実施する."""
        metadata_present = bool(plot_data.get("metadata"))
        structure = plot_data.get("structure", {})
        chapters = structure.get("chapters", []) if isinstance(structure, dict) else []

        issues: list[str] = []
        if not metadata_present:
            issues.append("metadata_missing")
        if not chapters:
            issues.append("structure_missing")

        is_consistent = metadata_present
        base_score = 1.0 if metadata_present else 0.5
        if not chapters:
            base_score -= 0.2
        bonus = min(len(chapters) * 0.05, 0.3)
        consistency_score = max(0.0, min(base_score + bonus, 1.0))

        return PlotConsistencyResult(
            is_consistent=is_consistent,
            consistency_score=consistency_score,
            issues=issues,
        )

    def _extract_plot_files(self, changed_files: list[str]) -> list[str]:
        """プロット関連ファイルを抽出"""
        plot_prefixes = ["20_プロット/", "30_設定集/"]
        return [f for f in changed_files if any(f.startswith(prefix) for prefix in plot_prefixes)]

    def _has_structural_changes(self, diff_content: str) -> bool:
        """構造的変更があるかチェック"""
        return any(keyword in diff_content.lower() for keyword in self.structural_keywords)

    def _is_minor_change(self, diff_content: str) -> bool:
        """軽微な変更かチェック"""
        return any(keyword in diff_content.lower() for keyword in self.minor_keywords)

    def _is_major_plot_file(self, plot_files: list[str]) -> bool:
        """メジャーなプロットファイルかチェック"""
        major_files = ["20_プロット/全体構成.yaml", "20_プロット/リソース配分.yaml"]
        return any(f in major_files for f in plot_files)

    def _extract_affected_chapters(self, plot_files: list[str]) -> list[int]:
        chapters: set[int] = set()
        chapter_pattern = re.compile(r"第(\d+)章")
        for path in plot_files:
            match = chapter_pattern.search(path)
            if match:
                try:
                    chapters.add(int(match.group(1)))
                except ValueError:
                    continue
        return sorted(chapters)


class PlotVersionConsistencyAnalyzer:
    """プロットバージョン整合性分析器エンティティ"""

    def analyze_consistency_impact(self, version_change: dict[str, str]) -> ConsistencyImpact:
        """バージョン変更の整合性影響を分析"""
        return ConsistencyImpact(version_change["type"])

    def check_version_consistency(self, plot_data: dict[str, Any]) -> PlotConsistencyResult:
        """プロットデータの整合性を簡易評価する."""
        helper = PlotCommitAnalyzer()
        return helper.analyze_plot_consistency(plot_data)

    def calculate_impact_significance(self, impact_data: dict[str, Any]) -> ChangeSignificance:
        """影響度から変更重要度を推定する."""
        chapters = impact_data.get("affected_chapters", []) or []
        episodes = int(impact_data.get("affected_episodes", 0) or 0)

        if len(chapters) >= 5 or episodes >= 20:
            return ChangeSignificance.HIGH
        if len(chapters) >= 2 or episodes >= 8:
            return ChangeSignificance.MEDIUM
        return ChangeSignificance.LOW


class EpisodeStatusUpdater:
    """話数管理ステータス更新器エンティティ"""

    def mark_episodes_for_revision(
        self, episodes_data: dict, affected_chapters: list[int], new_version: str = "Unknown"
    ) -> dict:
        """影響を受けた話数をリビジョン必要としてマーク"""
        updated_data: dict[str, Any] = episodes_data.copy()

        for episode_id, episode_info in updated_data.items():
            episode_chapter = episode_info.get("chapter")
            episode_status = episode_info.get("status")

            # 影響章の公開済み話数のみリビジョン必要に変更
            if episode_chapter in affected_chapters and episode_status == "PUBLISHED":
                updated_data[episode_id]["status"] = "REVISION_NEEDED"
                updated_data[episode_id]["plot_version_at_revision"] = new_version
                updated_data[episode_id]["revision_reason"] = f"プロット{new_version}の影響により要確認"

        return updated_data


class ForeshadowingImpactAnalyzer:
    """伏線影響分析器エンティティ"""

    def analyze_foreshadowing_validity(
        self, foreshadowing_data: dict, affected_chapters: list[int]
    ) -> ForeshadowingImpact:
        """伏線の有効性を分析"""
        impact = ForeshadowingImpact()

        for foreshadow_id, foreshadow_info in foreshadowing_data.items():
            target_chapter = foreshadow_info.get("target_chapter")
            resolution_chapter = foreshadow_info.get("resolution_chapter")

            # 伏線の対象章または解決章が影響範囲に含まれる場合
            if target_chapter in affected_chapters or resolution_chapter in affected_chapters:
                reason = f"第{target_chapter}-{resolution_chapter}章の構成変更により伏線の見直しが必要"
                impact.add_invalidated_foreshadowing(foreshadow_id, reason)

        # 全体的な推奨アクション
        if impact.potentially_invalidated:
            chapter_range = f"第{min(affected_chapters)}-{max(affected_chapters)}章"
            impact.review_recommendations.append(
                f"{chapter_range}の構成変更により伏線の見直しが必要",
            )

        return impact


class ChapterPlotImpactAnalyzer:
    """章別プロット影響分析器エンティティ"""

    def analyze_chapter_impact(self, changed_file: str) -> ChapterImpact:
        """単一章変更の影響を分析"""
        chapter_number = self._extract_chapter_number(changed_file)
        return ChapterImpact(chapter_number)

    def analyze_multiple_chapters_impact(self, changed_files: list[str]) -> MultiChapterImpact:
        """複数章変更の影響を分析"""
        chapter_numbers = []
        for file in changed_files:
            if "章別プロット" in file:
                chapter_number = self._extract_chapter_number(file)
                if chapter_number not in chapter_numbers:
                    chapter_numbers.append(chapter_number)

        return MultiChapterImpact(chapter_numbers)

    def _extract_chapter_number(self, file_path: str) -> int:
        """ファイルパスから章番号を抽出"""

        match = re.search(r"chapter(\d+)", file_path)
        return int(match.group(1)) if match else 1


class ChapterSpecificEpisodeUpdater:
    """章固有の話数更新器エンティティ"""

    def update_chapter_episodes(
        self, episodes_data: dict, affected_chapter: int, new_version: str = "Unknown", change_description: str = "変更"
    ) -> dict:
        """特定章の話数のみ更新"""
        updated_data: dict[str, Any] = episodes_data.copy()

        for episode_id, episode_info in updated_data.items():
            episode_chapter = episode_info.get("chapter")
            episode_status = episode_info.get("status")

            # 影響章の公開済み話数のみリビジョン必要に変更
            if episode_chapter == affected_chapter and episode_status == "PUBLISHED":
                updated_data[episode_id]["status"] = "REVISION_NEEDED"
                updated_data[episode_id]["plot_version_at_revision"] = new_version
                updated_data[episode_id]["revision_reason"] = change_description

        return updated_data


class ChapterForeshadowingAnalyzer:
    """章別伏線分析器エンティティ"""

    def analyze_chapter_foreshadowing(
        self, foreshadowing_data: dict, affected_chapter: int
    ) -> ChapterForeshadowingImpact:
        """特定章に関連する伏線を分析"""
        impact = ChapterForeshadowingImpact(affected_chapter)

        for foreshadow_id, foreshadow_info in foreshadowing_data.items():
            target_chapter = foreshadow_info.get("target_chapter")
            resolution_chapter = foreshadow_info.get("resolution_chapter")

            # 対象章または解決章が影響章と一致する場合
            if affected_chapter in (target_chapter, resolution_chapter):
                impact.add_affected_foreshadowing(foreshadow_id)

        return impact


class BidirectionalForeshadowingAnalyzer:
    """双方向伏線分析器エンティティ(新規追加)"""

    def analyze_bidirectional_impact(
        self, foreshadowing_data: dict, affected_chapter: int
    ) -> BidirectionalForeshadowingImpact:
        """伏線の双方向影響を分析"""
        impact = BidirectionalForeshadowingImpact(affected_chapter)

        for foreshadow_id, foreshadow_info in foreshadowing_data.items():
            target_chapter = foreshadow_info.get("target_chapter")
            resolution_chapter = foreshadow_info.get("resolution_chapter")

            # 仕込み章が変更された場合
            if target_chapter == affected_chapter:
                impact.add_setup_modified(foreshadow_id, resolution_chapter)

            # 回収章が変更された場合
            if resolution_chapter == affected_chapter:
                impact.add_resolution_modified(foreshadow_id, target_chapter)

        return impact

    def get_reverse_check_chapters(self, impact: BidirectionalForeshadowingImpact) -> set[int]:
        """逆方向でチェックが必要な章を取得"""
        chapters_to_check = set()

        # 仕込みが変更されたら回収章をチェック
        for _, resolution_chapter in impact.setup_modified:
            chapters_to_check.add(resolution_chapter)

        # 回収が変更されたら仕込み章をチェック
        for _, target_chapter in impact.resolution_modified:
            chapters_to_check.add(target_chapter)

        # 変更された章自体は除外
        chapters_to_check.discard(impact.affected_chapter)

        return chapters_to_check


class ForeshadowingStatusUpdater:
    """伏線ステータス更新器エンティティ(新規追加)"""

    def update_foreshadowing_status(
        self, foreshadowing_data: dict, impact: BidirectionalForeshadowingImpact, new_version: str = "Unknown"
    ) -> dict:
        """双方向影響に基づいて伏線ステータスを更新"""
        updated_data: dict[str, Any] = foreshadowing_data.copy()

        # 仕込み変更の処理
        for foreshadow_id, _ in impact.setup_modified:
            if foreshadow_id in updated_data:
                self._update_single_foreshadowing(
                    updated_data[foreshadow_id],
                    new_version,
                    "setup_modified",
                    impact.affected_chapter,
                )

        # 回収変更の処理
        for foreshadow_id, _ in impact.resolution_modified:
            if foreshadow_id in updated_data:
                self._update_single_foreshadowing(
                    updated_data[foreshadow_id],
                    new_version,
                    "resolution_modified",
                    impact.affected_chapter,
                )

        return updated_data

    def _update_single_foreshadowing(
        self, foreshadowing_info: dict, version: str, change_type: str, affected_chapter: int
    ) -> None:
        """単一の伏線情報を更新"""
        if foreshadowing_info.get("status") in ["ACTIVE", "RESOLVED"]:
            foreshadowing_info["status"] = "REVIEW_REQUIRED"

        if "chapter_impacts" not in foreshadowing_info:
            foreshadowing_info["chapter_impacts"] = []

        severity = self._calculate_severity(change_type)
        foreshadowing_info["chapter_impacts"].append(
            {
                "version": version,
                "affected_chapter": affected_chapter,
                "impact_type": change_type,
                "severity": severity,
                "review_status": "pending",
                "timestamp": self._get_current_timestamp(),
            }
        )

        if "status_history" not in foreshadowing_info:
            foreshadowing_info["status_history"] = []

        reason = f"第{affected_chapter}章の{self._get_impact_description(change_type)}"
        foreshadowing_info["status_history"].append(
            {
                "version": version,
                "status": foreshadowing_info["status"],
                "reason": reason,
                "timestamp": self._get_current_timestamp(),
            }
        )

    def _calculate_severity(self, impact_type: str) -> str:
        """影響の重要度を計算"""
        # 回収章の変更は仕込み章より重要度が高い
        if impact_type == "resolution_modified":
            return "major"
        return "minor"

    def _get_impact_description(self, impact_type: str) -> str:
        """影響タイプの説明を取得"""
        descriptions = {
            "setup_modified": "伏線仕込みの変更",
            "resolution_modified": "伏線回収の変更",
        }
        return descriptions.get(impact_type, "変更")

    def _get_current_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""

        return project_now().datetime.isoformat()
