"""Infrastructure.services.change_impact_analyzer
Where: Infrastructure service analysing change impact for project files.
What: Computes affected modules, generates impact reports, and logs results.
Why: Helps teams understand the consequences of file changes before deployment.
"""

from noveler.presentation.shared.shared_utilities import console

"変更影響範囲分析システム\n\n仕様書: SPEC-CHANGE-IMPACT-001\nGit変更情報に基づく動的品質チェック強度調整\n\n設計原則:\n    - Git変更差分からの影響範囲特定\n- 変更の性質に応じた適応的チェック\n- 効率的なリソース利用\n"
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger


class ValidationLevel(Enum):
    """検証レベル（循環依存解消）"""

    STRICT = "STRICT"
    MODERATE = "MODERATE"
    BASIC = "BASIC"


class ChangeType(Enum):
    """変更タイプ"""

    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"


class ImpactLevel(Enum):
    """影響レベル"""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FileChange:
    """ファイル変更情報"""

    file_path: Path
    change_type: ChangeType
    lines_added: int
    lines_deleted: int
    impact_score: float


@dataclass
class ChangeImpactAnalysis:
    """変更影響分析結果"""

    changed_files: list[FileChange]
    overall_impact_level: ImpactLevel
    recommended_validation_level: ValidationLevel
    affected_layers: set[str]
    critical_changes: list[str]
    analysis_summary: dict[str, any]


class ChangeImpactAnalyzer:
    """変更影響範囲分析器

    責務:
        - Git変更差分の解析
        - 変更の影響度評価
        - 動的品質チェック強度決定
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self.layer_patterns = {
            "domain": "noveler/domain/",
            "application": "noveler/application/",
            "infrastructure": "noveler/infrastructure/",
            "presentation": "noveler/presentation/",
            "tools": "noveler/tools/",
            "tests": "noveler/tests/",
        }
        self.critical_patterns = [
            ".*_compliance_engine\\.py$",
            ".*dependency.*\\.py$",
            ".*/interfaces/.*\\.py$",
            ".*/factories/.*\\.py$",
            ".*requirements.*\\.txt$",
            ".*setup\\.py$",
            ".*pyproject\\.toml$",
        ]
        self.minimal_change_patterns = [
            "^\\s*#",
            '^\\s*"""',
            "^\\s*'''",
            "^\\s*$",
            "^\\s*import ",
            "^\\s*from .* import",
        ]

    def analyze_changes(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> ChangeImpactAnalysis:
        """変更影響分析の実行

        Args:
            base_ref: 比較基準リビジョン
            target_ref: 比較対象リビジョン

        Returns:
            変更影響分析結果
        """
        console.print(f"変更影響分析開始: {(base_ref, target_ref)} -> %s")
        changed_files = self._get_changed_files(base_ref, target_ref)
        if not changed_files:
            return self._create_minimal_analysis()
        file_changes = []
        for file_path, change_type in changed_files.items():
            file_change = self._analyze_file_change(file_path, change_type, base_ref, target_ref)
            if file_change:
                file_changes.append(file_change)
        overall_impact = self._calculate_overall_impact(file_changes)
        validation_level = self._determine_validation_level(overall_impact)
        affected_layers = self._identify_affected_layers(file_changes)
        critical_changes = self._identify_critical_changes(file_changes)
        analysis_summary = self._generate_analysis_summary(file_changes, overall_impact)
        return ChangeImpactAnalysis(
            changed_files=file_changes,
            overall_impact_level=overall_impact,
            recommended_validation_level=validation_level,
            affected_layers=affected_layers,
            critical_changes=critical_changes,
            analysis_summary=analysis_summary,
        )

    def _get_changed_files(self, base_ref: str, target_ref: str) -> dict[Path, ChangeType]:
        """Git差分からの変更ファイル取得

        Args:
            base_ref: 比較基準リビジョン
            target_ref: 比較対象リビジョン

        Returns:
            変更ファイルと変更タイプのマッピング
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{base_ref}..{target_ref}"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode != 0:
                console.print(f"Git diff実行エラー: {result.stderr}")
                return {}
            changed_files = {}
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0][0]
                    file_path = Path(parts[1])
                    if file_path.suffix == ".py":
                        changed_files[file_path] = ChangeType(status)
            return changed_files
        except subprocess.SubprocessError as e:
            self.logger.exception("Git操作エラー: %s", e)
            return {}

    def _analyze_file_change(
        self, file_path: Path, change_type: ChangeType, base_ref: str, target_ref: str
    ) -> FileChange | None:
        """単一ファイル変更分析

        Args:
            file_path: 変更ファイルパス
            change_type: 変更タイプ
            base_ref: 比較基準リビジョン
            target_ref: 比較対象リビジョン

        Returns:
            ファイル変更情報
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--numstat", f"{base_ref}..{target_ref}", "--", str(file_path)],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            (lines_added, lines_deleted) = (0, 0)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split("\t")
                if len(parts) >= 2:
                    lines_added = int(parts[0]) if parts[0].isdigit() else 0
                    lines_deleted = int(parts[1]) if parts[1].isdigit() else 0
            impact_score = self._calculate_impact_score(file_path, change_type, lines_added, lines_deleted)
            return FileChange(
                file_path=file_path,
                change_type=change_type,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                impact_score=impact_score,
            )
        except (subprocess.SubprocessError, ValueError) as e:
            console.print(f"ファイル変更分析エラー: {file_path} - {e}")
            return None

    def _calculate_impact_score(
        self, file_path: Path, change_type: ChangeType, lines_added: int, lines_deleted: int
    ) -> float:
        """影響スコア計算

        Args:
            file_path: ファイルパス
            change_type: 変更タイプ
            lines_added: 追加行数
            lines_deleted: 削除行数

        Returns:
            影響スコア（0.0-10.0）
        """
        base_score = 0.0
        change_scores = {
            ChangeType.ADDED: 2.0,
            ChangeType.MODIFIED: 1.0,
            ChangeType.DELETED: 3.0,
            ChangeType.RENAMED: 1.5,
            ChangeType.COPIED: 1.5,
        }
        base_score += change_scores.get(change_type, 1.0)
        total_changes = lines_added + lines_deleted
        if total_changes > 100:
            base_score *= 2.0
        elif total_changes > 50:
            base_score *= 1.5
        elif total_changes > 10:
            base_score *= 1.2
        file_path_str = str(file_path)
        for pattern in self.critical_patterns:
            if re.search(pattern, file_path_str):
                base_score *= 2.5
                break
        if "domain" in file_path_str:
            base_score *= 2.0
        elif "infrastructure" in file_path_str:
            base_score *= 1.5
        elif "application" in file_path_str:
            base_score *= 1.3
        return min(base_score, 10.0)

    def _calculate_overall_impact(self, file_changes: list[FileChange]) -> ImpactLevel:
        """全体影響レベル計算

        Args:
            file_changes: ファイル変更リスト

        Returns:
            全体影響レベル
        """
        if not file_changes:
            return ImpactLevel.MINIMAL
        total_score = sum(change.impact_score for change in file_changes)
        average_score = total_score / len(file_changes)
        max_score = max(change.impact_score for change in file_changes)
        file_count = len(file_changes)
        if max_score >= 8.0 or average_score >= 6.0:
            return ImpactLevel.CRITICAL
        if max_score >= 6.0 or average_score >= 4.0 or file_count >= 10:
            return ImpactLevel.HIGH
        if max_score >= 4.0 or average_score >= 2.0 or file_count >= 5:
            return ImpactLevel.MEDIUM
        if max_score >= 2.0 or average_score >= 1.0:
            return ImpactLevel.LOW
        return ImpactLevel.MINIMAL

    def _determine_validation_level(self, impact_level: ImpactLevel) -> ValidationLevel:
        """推奨検証レベル決定

        Args:
            impact_level: 影響レベル

        Returns:
            推奨検証レベル
        """
        validation_mapping = {
            ImpactLevel.CRITICAL: ValidationLevel.STRICT,
            ImpactLevel.HIGH: ValidationLevel.STRICT,
            ImpactLevel.MEDIUM: ValidationLevel.MODERATE,
            ImpactLevel.LOW: ValidationLevel.MODERATE,
            ImpactLevel.MINIMAL: ValidationLevel.BASIC,
        }
        return validation_mapping[impact_level]

    def _identify_affected_layers(self, file_changes: list[FileChange]) -> set[str]:
        """影響を受ける層の特定

        Args:
            file_changes: ファイル変更リスト

        Returns:
            影響を受ける層名のセット
        """
        affected_layers = set()
        for change in file_changes:
            file_path_str = str(change.file_path)
            for layer, pattern in self.layer_patterns.items():
                if re.search(pattern, file_path_str):
                    affected_layers.add(layer)
                    break
        return affected_layers

    def _identify_critical_changes(self, file_changes: list[FileChange]) -> list[str]:
        """重要変更の特定

        Args:
            file_changes: ファイル変更リスト

        Returns:
            重要変更の説明リスト
        """
        critical_changes = []
        for change in file_changes:
            if change.impact_score >= 7.0:
                critical_changes.append(
                    f"{change.change_type.value}: {change.file_path} (スコア: {change.impact_score:.1f})"
                )
        return critical_changes

    def _generate_analysis_summary(self, file_changes: list[FileChange], overall_impact: ImpactLevel) -> dict[str, any]:
        """分析サマリー生成

        Args:
            file_changes: ファイル変更リスト
            overall_impact: 全体影響レベル

        Returns:
            分析サマリー
        """
        if not file_changes:
            return {"total_files": 0, "total_score": 0.0, "average_score": 0.0}
        total_score = sum(change.impact_score for change in file_changes)
        return {
            "total_files": len(file_changes),
            "total_score": round(total_score, 2),
            "average_score": round(total_score / len(file_changes), 2),
            "max_score": round(max(change.impact_score for change in file_changes), 2),
            "impact_level": overall_impact.value,
            "change_types": {
                change_type.value: sum(1 for c in file_changes if c.change_type == change_type)
                for change_type in ChangeType
            },
        }

    def _create_minimal_analysis(self) -> ChangeImpactAnalysis:
        """変更なしの場合の最小分析結果

        Returns:
            最小影響分析結果
        """
        return ChangeImpactAnalysis(
            changed_files=[],
            overall_impact_level=ImpactLevel.MINIMAL,
            recommended_validation_level=ValidationLevel.BASIC,
            affected_layers=set(),
            critical_changes=[],
            analysis_summary={"total_files": 0, "total_score": 0.0},
        )
