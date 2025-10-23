"""キャラクター一貫性チェックユースケース

キャラクター描写の一貫性をチェックするアプリケーション層のユースケース。
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.entities.character_consistency_session import CharacterConsistencySession, ConsistencySummary
from noveler.domain.entities.episode import Episode
from noveler.domain.entities.project import Project
from noveler.domain.repositories.character_repository import CharacterRepository
from noveler.domain.repositories.episode_repository import EpisodeRepository
from noveler.domain.services.character_consistency_service import CharacterConsistencyService
from noveler.domain.value_objects.character_profile import CharacterProfile
from noveler.domain.value_objects.consistency_check_result import ConsistencyCheckResult
from noveler.domain.value_objects.consistency_violation import CorrectionSuggestion
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.session_id import SessionId

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class CharacterConsistencyRequest:
    """一貫性チェックリクエスト"""

    project_name: str
    episode_numbers: list[int] | None = None
    target_characters: list[str] | None = None
    generate_detailed_report: bool = False
    generate_suggestions: bool = False
    timeout_seconds: int = 300


@dataclass
class CharacterConsistencyResponse:
    """一貫性チェックレスポンス"""

    success: bool
    reports: list[ConsistencyCheckResult]
    summary: ConsistencySummary
    suggestions: list[CorrectionSuggestion] = None
    detailed_report: str | None = None
    error_message: str | None = None
    warnings: list[str] = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ConsistencyReport:
    """一貫性レポート"""

    def __init__(self) -> None:
        self._violations: list[dict[str, Any]] = []

    def add_violation(self, character_name: str, attribute: str) -> None:
        """違反を追加"""
        self._violations.append({"character": character_name, "attribute": attribute})

    def get_statistics(self) -> "ConsistencyStatistics":
        """統計情報を取得"""
        by_character = {}
        by_attribute = {}

        for v in self._violations:
            # キャラクター別
            char = v["character"]
            by_character[char] = by_character.get(char, 0) + 1

            # 属性別
            attr = v["attribute"]
            by_attribute[attr] = by_attribute.get(attr, 0) + 1

        return ConsistencyStatistics(
            total_violations=len(self._violations), by_character=by_character, by_attribute=by_attribute
        )

    def get_violations_by_severity(self) -> dict[str, list[dict]]:
        """重要度別に違反を取得"""
        by_severity = {"critical": [], "major": [], "minor": []}

        for v in self._violations:
            severity = v.get("severity", "major")
            if severity in by_severity:
                by_severity[severity].append(v)

        return by_severity


@dataclass
class ConsistencyStatistics:
    """一貫性統計"""

    total_violations: int
    by_character: dict[str, int]
    by_attribute: dict[str, int]


class CheckCharacterConsistencyUseCase:
    """キャラクター一貫性チェックユースケース

    プロジェクトのエピソードに対してキャラクター描写の
    一貫性をチェックし、結果を返す。
    """

    def __init__(
        self,
        character_repo: CharacterRepository,
        episode_repository: EpisodeRepository,
        consistency_service: CharacterConsistencyService,
    ) -> None:
        """ユースケースを初期化

        Args:
            character_repo: キャラクターリポジトリ
            episode_repository: エピソードリポジトリ
            consistency_service: 一貫性チェックサービス
        """
        self._character_repo = character_repo
        self._episode_repo = episode_repository
        self._consistency_service = consistency_service

    def execute(self, request: CharacterConsistencyRequest) -> CharacterConsistencyResponse:
        """一貫性チェックを実行

        Args:
            request: チェックリクエスト

        Returns:
            チェック結果レスポンス
        """
        try:
            # エピソードを取得
            episodes = self._get_episodes(request)
            if not episodes:
                return CharacterConsistencyResponse(
                    success=False,
                    reports=[],
                    summary=ConsistencySummary(0, 0, 100.0, {}, {}),
                    error_message="プロジェクトが見つかりません",
                )

            # キャラクターを取得
            characters = self._get_characters(request)
            if not characters:
                return CharacterConsistencyResponse(
                    success=True,
                    reports=[],
                    summary=ConsistencySummary(0, 0, 100.0, {}, {}),
                    warnings=["キャラクターが定義されていません"],
                )

            # セッションを作成
            project = Project(name=request.project_name)
            session = CharacterConsistencySession(SessionId(), project)

            # 各エピソードをチェック
            reports = []
            all_suggestions = []

            for episode in episodes:
                # 一貫性チェック実行
                violations: Any = self._consistency_service.analyze_consistency(episode, characters)

                # 結果を作成
                result = ConsistencyCheckResult(episode_number=episode.number.value, violations=violations)
                reports.append(result)
                session.add_result(result)

                # 修正提案を生成
                if request.generate_suggestions:
                    for violation in violations:
                        suggestion = violation.get_correction_suggestion()
                        all_suggestions.append(suggestion)

            # サマリーを生成
            summary = session.get_summary()

            # 詳細レポートを生成
            detailed_report = None
            if request.generate_detailed_report:
                detailed_report = self._generate_detailed_report(reports, characters, summary)

            return CharacterConsistencyResponse(
                success=True,
                reports=reports,
                summary=summary,
                suggestions=all_suggestions if request.generate_suggestions else [],
                detailed_report=detailed_report,
            )

        except Exception as e:
            return CharacterConsistencyResponse(
                success=False, reports=[], summary=ConsistencySummary(0, 0, 0.0, {}, {}), error_message=str(e)
            )

    def _get_episodes(self, request: CharacterConsistencyRequest) -> list[Episode]:
        """エピソードを取得"""
        if request.episode_numbers:
            # 指定されたエピソードを取得
            episodes = []
            for num in request.episode_numbers:
                episode = self._episode_repo.find_by_project_and_number(request.project_name, num)
                if episode:
                    episodes.append(episode)
            return episodes
        # 全エピソードを取得
        return self._episode_repo.find_all(request.project_name)

    def _get_characters(self, request: CharacterConsistencyRequest) -> list[CharacterProfile]:
        """キャラクターを取得"""
        if request.target_characters:
            # 指定されたキャラクターのみ
            characters = []
            for name in request.target_characters:
                char = self._character_repo.find_by_name(request.project_name, name)
                if char:
                    characters.append(char)
            return characters
        # 全キャラクター
        return self._character_repo.find_all_by_project(request.project_name)

    def _generate_detailed_report(
        self, reports: list[ConsistencyCheckResult], _characters: list[CharacterProfile]
    ) -> str:
        """詳細レポートを生成"""
        lines = []
        self._add_report_header(lines)
        self._add_summary_statistics(lines, reports)
        self._add_character_violation_statistics(lines, reports)
        self._add_detailed_episodes(lines, reports)
        return "\n".join(lines)

    def _add_report_header(self, lines: list[str]) -> None:
        """レポートヘッダーを追加"""
        lines.append("# キャラクター一貫性チェックレポート")
        lines.append(f"生成日時: {project_now().format_timestamp('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

    def _add_summary_statistics(self, lines: list[str], reports: list[ConsistencyCheckResult]) -> None:
        """サマリー統計を追加"""
        total_violations = sum(len(r.violations) for r in reports)
        avg_score = sum(r.consistency_score for r in reports) / len(reports) if reports else 0
        lines.append("## サマリー")
        lines.append(f"- チェックエピソード数: {len(reports)}")
        lines.append(f"- 総違反数: {total_violations}")
        lines.append(f"- 平均一貫性スコア: {avg_score:.2f}")
        lines.append("")

    def _add_character_violation_statistics(self, lines: list[str], reports: list[ConsistencyCheckResult]) -> None:
        """キャラクター別違反統計を追加"""
        char_violations = {}
        attr_violations = {}
        for report in reports:
            for violation in report.violations:
                char_name = violation.get("character", "unknown")
                attr_name = violation.get("attribute", "unknown")
                char_violations[char_name] = char_violations.get(char_name, 0) + 1
                attr_violations[attr_name] = attr_violations.get(attr_name, 0) + 1
        self._add_character_violations(lines, char_violations)
        self._add_attribute_violations(lines, attr_violations)

    def _add_character_violations(self, lines: list[str], char_violations: dict[str, int]) -> None:
        """キャラクター別違反を追加"""
        if char_violations:
            lines.append("## キャラクター別違反")
            for char, count in sorted(char_violations.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {char}: {count}件")
            lines.append("")

    def _add_attribute_violations(self, lines: list[str], attr_violations: dict[str, int]) -> None:
        """属性別違反統計を追加"""
        if attr_violations:
            lines.append("## 属性別違反統計")
            for attr, count in sorted(attr_violations.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {attr}: {count}件")
            lines.append("")

    def _add_detailed_episodes(self, lines: list[str], reports: list[ConsistencyCheckResult]) -> None:
        """詳細エピソード情報を追加"""
        lines.append("## 修正提案")
        for report in reports:
            if report.violations:
                lines.append(f"\n### エピソード {report.episode_number}")
                for violation in report.violations:
                    line_num = getattr(violation, "line_number", "N/A")
                    desc = getattr(violation, "description", str(violation))
                    lines.append(f"- 行{line_num}: {desc}")
                    expected = getattr(violation, "expected", "N/A")
                    actual = getattr(violation, "actual", "N/A")
                    lines.append(f"  - 期待値: {expected}")
                    lines.append(f"  - 実際: {actual}")
                    if hasattr(violation, "context") and violation.context:
                        lines.append(f"  - コンテキスト: {violation.context}")
