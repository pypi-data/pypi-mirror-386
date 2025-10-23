"""Claude品質チェックリクエスト値オブジェクト
仕様: Claude Code品質チェック統合システム
"""

from dataclasses import dataclass
from pathlib import Path

from noveler.domain.value_objects.episode_number import EpisodeNumber


@dataclass(frozen=True)
class ClaudeQualityCheckRequest:
    """Claude品質チェックリクエスト値オブジェクト

    Claude Codeによる品質チェック実行に必要な全情報を含む不変データ
    """

    episode_number: EpisodeNumber
    episode_title: str
    manuscript_path: Path
    word_count: int
    genre: str = "ファンタジー"
    viewpoint: str = "三人称単元視点"
    target_audience: str = "なろう読者層"
    custom_focus_areas: list[str] = None
    quality_threshold: int = 80

    def __post_init__(self) -> None:
        """値オブジェクト不変条件検証"""
        if self.custom_focus_areas is None:
            object.__setattr__(self, "custom_focus_areas", [])

        if not self.episode_title.strip():
            msg = "episode_titleは空にできません"
            raise ValueError(msg)

        if not self.manuscript_path.exists():
            msg = f"原稿ファイルが存在しません: {self.manuscript_path}"
            raise ValueError(msg)

        if self.word_count <= 0:
            msg = "word_countは正の整数である必要があります"
            raise ValueError(msg)

        if not (50 <= self.quality_threshold <= 100):
            msg = "quality_thresholdは50-100の範囲である必要があります"
            raise ValueError(msg)

    def get_manuscript_content(self) -> str:
        """原稿内容を取得"""
        try:
            return self.manuscript_path.read_text(encoding="utf-8")
        except Exception as e:
            msg = f"原稿ファイル読み込みエラー: {e}"
            raise ValueError(msg)

    def has_custom_focus_areas(self) -> bool:
        """カスタム重点評価項目存在判定"""
        return len(self.custom_focus_areas) > 0

    def get_context_summary(self) -> str:
        """評価コンテキスト要約"""
        return (
            f"第{self.episode_number.value:03d}話「{self.episode_title}」"
            f"({self.word_count}字, {self.viewpoint}, {self.genre})"
        )

    def is_high_priority_episode(self) -> bool:
        """高優先度エピソード判定（離脱リスク高）"""
        high_risk_episodes = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50]
        return self.episode_number.value in high_risk_episodes

    def get_quality_expectations(self) -> dict[str, int]:
        """品質期待値マッピング"""
        base_expectations = {"creative_quality": 40, "reader_experience": 35, "structural_coherence": 25}

        # 高優先度エピソードは基準を厳格化
        if self.is_high_priority_episode():
            return {k: min(v + 5, 50) for k, v in base_expectations.items()}

        return base_expectations


@dataclass(frozen=True)
class ClaudeQualityCheckResult:
    """Claude品質チェック結果値オブジェクト"""

    request: ClaudeQualityCheckRequest
    total_score: int
    creative_quality_score: int
    reader_experience_score: int
    structural_coherence_score: int
    detailed_feedback: str
    improvement_suggestions: list[str]
    execution_time_ms: float
    is_success: bool = True
    error_message: str | None = None

    def __post_init__(self) -> None:
        """値オブジェクト不変条件検証"""
        if self.improvement_suggestions is None:
            object.__setattr__(self, "improvement_suggestions", [])

        if not (0 <= self.total_score <= 100):
            msg = "total_scoreは0-100の範囲である必要があります"
            raise ValueError(msg)

        if not (0 <= self.creative_quality_score <= 40):
            msg = "creative_quality_scoreは0-40の範囲である必要があります"
            raise ValueError(msg)

        if not (0 <= self.reader_experience_score <= 35):
            msg = "reader_experience_scoreは0-35の範囲である必要があります"
            raise ValueError(msg)

        if not (0 <= self.structural_coherence_score <= 25):
            msg = "structural_coherence_scoreは0-25の範囲である必要があります"
            raise ValueError(msg)

        if self.execution_time_ms < 0:
            msg = "execution_time_msは0以上である必要があります"
            raise ValueError(msg)

    def meets_quality_threshold(self) -> bool:
        """品質基準達成判定"""
        return self.total_score >= self.request.quality_threshold

    def get_quality_grade(self) -> str:
        """品質グレード取得"""
        if self.total_score >= 90:
            return "S（出版レベル）"
        if self.total_score >= 80:
            return "A（高品質）"
        if self.total_score >= 70:
            return "B（標準的）"
        if self.total_score >= 60:
            return "C（要改善）"
        return "D（大幅修正必要）"

    def get_score_breakdown(self) -> dict[str, dict[str, int]]:
        """詳細スコア内訳"""
        return {
            "creative_quality": {
                "score": self.creative_quality_score,
                "max_score": 40,
                "percentage": int((self.creative_quality_score / 40) * 100),
            },
            "reader_experience": {
                "score": self.reader_experience_score,
                "max_score": 35,
                "percentage": int((self.reader_experience_score / 35) * 100),
            },
            "structural_coherence": {
                "score": self.structural_coherence_score,
                "max_score": 25,
                "percentage": int((self.structural_coherence_score / 25) * 100),
            },
        }

    def get_priority_improvements(self, limit: int = 3) -> list[str]:
        """優先改善提案（上位N件）"""
        return self.improvement_suggestions[:limit]

    def format_result_summary(self) -> str:
        """結果要約フォーマット"""
        status = "✅" if self.meets_quality_threshold() else "❌"
        return (
            f"{status} 総合スコア: {self.total_score}/100点 ({self.get_quality_grade()})\n"
            f"創作的品質: {self.creative_quality_score}/40点\n"
            f"読者体験: {self.reader_experience_score}/35点\n"
            f"構成妥当性: {self.structural_coherence_score}/25点\n"
            f"実行時間: {self.execution_time_ms:.0f}ms"
        )
