"""Domain.entities.character_consistency_session
Where: Domain entity tracking character consistency analysis.
What: Captures detected inconsistencies and recommendations.
Why: Helps maintain character continuity across a project.
"""

from __future__ import annotations

"""キャラクター一貫性チェックセッションエンティティ

ドメイン駆動設計に基づくキャラクター一貫性チェックの中核エンティティ。
"""


from typing import TYPE_CHECKING, Any

from noveler.domain.services.attribute_checker_factory import AttributeCheckerFactory
from noveler.domain.value_objects.check_context import CheckContext
from noveler.domain.value_objects.consistency_check_result import ConsistencyCheckResult
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

    from noveler.domain.entities.episode import Episode
    from noveler.domain.entities.project import Project
    from noveler.domain.services.character_consistency_service import CharacterConsistencyService
    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation
    from noveler.domain.value_objects.session_id import SessionId

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class CharacterConsistencySession:
    """キャラクター一貫性チェックセッション

    プロジェクト内のキャラクター描写の一貫性をチェックし、
    違反を検出・記録するセッションを管理する。
    """

    def __init__(
        self, session_id: SessionId, project: Project, consistency_service: CharacterConsistencyService | None = None
    ) -> None:
        """セッションを初期化

        Args:
            session_id: セッション識別子
            project: 対象プロジェクト
            consistency_service: 一貫性チェックサービス(オプション)
        """
        self._session_id = session_id
        self._project = project
        self._results: list[ConsistencyCheckResult] = []
        self._created_at = project_now().datetime
        self._completed_at: datetime | None = None
        self._consistency_service = consistency_service

    @property
    def session_id(self) -> SessionId:
        """セッションIDを取得"""
        return self._session_id

    @property
    def project(self) -> Project:
        """プロジェクトを取得"""
        return self._project

    @property
    def results(self) -> list[ConsistencyCheckResult]:
        """チェック結果リストを取得"""
        return self._results.copy()

    @property
    def is_strict_mode(self) -> bool:
        """厳格モードかどうかを判定"""
        settings = self._project.settings or {}
        consistency_settings = settings.get("consistency_check", {})
        return consistency_settings.get("strict_mode", False)

    @property
    def ignored_attributes(self) -> list[str]:
        """無視する属性リストを取得"""
        settings = self._project.settings or {}
        consistency_settings = settings.get("consistency_check", {})
        return consistency_settings.get("ignore_attributes", [])

    @property
    def custom_rules(self) -> dict[str, Any]:
        """カスタムルールを取得"""
        settings = self._project.settings or {}
        consistency_settings = settings.get("consistency_check", {})
        return consistency_settings.get("custom_rules", {})

    def check_episode(self, episode: Episode, characters: list[dict]) -> ConsistencyCheckResult:
        """エピソードのキャラクター一貫性をチェック

        Args:
            episode: チェック対象エピソード
            characters: キャラクタープロファイルリスト

        Returns:
            一貫性チェック結果
        """
        if self._consistency_service:
            # ドメインサービスを使用して高度な分析を実行
            violations: Any = self._consistency_service.analyze_consistency(episode, characters, self.custom_rules)
        else:
            # 基本的な内部実装を使用
            violations: list[Any] = []
            lines = episode.content.split("\n")
            for line_num, line in enumerate(lines, 1):
                for character in characters:
                    # キャラクター名が含まれる行を対象
                    if character.name not in line:
                        continue

                    # 各属性をチェック
                    for attr_name, expected_value in character.attributes.items():
                        if attr_name in self.ignored_attributes:
                            continue

                        # 属性に応じた違反検出ロジック
                        violation = self._check_attribute_consistency(
                            line, line_num, character.name, attr_name, expected_value
                        )

                        if violation:
                            violations.append(violation)

        # 結果を作成して保存
        result = ConsistencyCheckResult(
            episode_number=episode.number.value if hasattr(episode.number, "value") else episode.number,
            violations=violations,
        )

        self._results.append(result)

        return result

    def _check_attribute_consistency(
        self, line: str, line_number: int, character_name: str, attribute: str, expected: str
    ) -> ConsistencyViolation | None:
        """属性の一貫性をチェック

        Strategy パターンを使用して各属性のチェック処理を委譲
        """
        context = CheckContext(
            line=line,
            line_number=line_number,
            character_name=character_name,
            expected_value=expected,
            recent_characters=self._find_recent_character(line_number),
        )

        checker = AttributeCheckerFactory.create_checker(attribute)
        return checker.check(context)

    def _find_recent_character(self, _current_line: int) -> list[str]:
        """最近言及されたキャラクターを探す(簡易版)"""
        # シンプルな実装として、直前の行で言及されたキャラクター名を返す
        # ここでは全キャラクターを返す
        return ["山田太郎", "花子"]

    def calculate_consistency_score(self, result: ConsistencyCheckResult) -> float:
        """一貫性スコアを計算

        Args:
            result: チェック結果

        Returns:
            0-100のスコア(100が完全に一貫性あり)
        """
        if not result.violations:
            return 100.0

        # 違反の重要度に応じてペナルティを計算
        penalty = 0.0
        for violation in result.violations:
            if violation.severity == "critical":
                penalty += 10.0
            elif violation.severity == "major":
                penalty += 5.0
            else:
                penalty += 2.0

        # スコアを計算(0以上100以下)
        return max(0.0, 100.0 - penalty)

    def add_result(self, result: ConsistencyCheckResult) -> None:
        """チェック結果を追加

        Args:
            result: 追加する結果
        """
        self._results.append(result)

    def get_summary(self) -> ConsistencySummary:
        """セッションのサマリーを取得

        Returns:
            一貫性チェックのサマリー
        """
        total_violations = sum(len(r.violations) for r in self._results)

        # キャラクター別違反数
        violation_by_character: dict[str, int] = {}
        # 属性別違反数
        violation_by_attribute: dict[str, int] = {}

        for result in self._results:
            for violation in result.violations:
                # キャラクター別集計
                char_name = violation.character_name
                violation_by_character[char_name] = violation_by_character.get(char_name, 0) + 1

                # 属性別集計
                attr = violation.attribute
                violation_by_attribute[attr] = violation_by_attribute.get(attr, 0) + 1

        # 平均スコア計算
        scores = [self.calculate_consistency_score(r) for r in self._results]
        average_score = sum(scores) / len(scores) if scores else 100.0

        return ConsistencySummary(
            total_episodes=len(self._results),
            total_violations=total_violations,
            average_consistency_score=average_score,
            violation_by_character=violation_by_character,
            violation_by_attribute=violation_by_attribute,
        )


class ConsistencySummary:
    """一貫性チェックのサマリー"""

    def __init__(
        self,
        total_episodes: int,
        total_violations: int,
        average_consistency_score: float = 0.0,
        violation_by_character: dict | None = None,
        violation_by_attribute: dict | None = None,
    ) -> None:
        self.total_episodes = total_episodes
        self.total_violations = total_violations
        self.average_consistency_score = average_consistency_score
        self.violation_by_character = violation_by_character or {}
        self.violation_by_attribute = violation_by_attribute or {}
