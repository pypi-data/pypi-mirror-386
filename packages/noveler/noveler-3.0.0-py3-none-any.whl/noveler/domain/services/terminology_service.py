"""用語統一ドメインサービス

プロジェクト固有の用語辞書を管理し、表記ゆれの検出・修正を行う。
CLAUDE.mdガイド準拠:統合インポート管理システム使用、型安全性確保。
"""

from dataclasses import dataclass

from noveler.domain.value_objects.project_path import ProjectPath


@dataclass(frozen=True)
class TerminologyEntry:
    """用語エントリー"""

    canonical: str
    variants: list[str]
    category: str = "general"
    context_hints: list[str] = None

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.context_hints is None:
            object.__setattr__(self, "context_hints", [])


@dataclass(frozen=True)
class TerminologyFix:
    """用語修正結果"""

    original: str
    corrected: str
    category: str
    confidence: float = 1.0


class TerminologyService:
    """用語統一ドメインサービス

    プロジェクト固有の用語辞書を参照し、表記ゆれの検出・修正を実行。
    文脈を考慮した高精度な用語統一を提供。
    """

    def __init__(self) -> None:
        """用語統一サービスの初期化"""
        self._default_terminology: dict[str, TerminologyEntry] = {}
        self._load_default_terminology()

    def detect_terminology_issues(self, content: str, project_path: ProjectPath | None = None) -> list[TerminologyFix]:
        """用語統一問題の検出

        Args:
            content: 検査対象のコンテンツ
            project_path: プロジェクトパス(用語辞書参照用)

        Returns:
            list[TerminologyFix]: 検出された用語統一問題のリスト
        """
        fixes = []
        terminology_dict = self._get_terminology_dict(project_path)

        for canonical, entry in terminology_dict.items():
            for variant in entry.variants:
                if variant in content and variant != canonical:
                    # 文脈チェック
                    confidence = self._calculate_confidence(content, variant, entry)
                    if confidence > 0.7:  # 信頼度閾値:
                        fixes.append(
                            TerminologyFix(
                                original=variant, corrected=canonical, category=entry.category, confidence=confidence
                            )
                        )

        return fixes

    def apply_terminology_fixes(self, content: str, fixes: list[TerminologyFix]) -> tuple[str, list[str]]:
        """用語修正の適用

        Args:
            content: 修正対象のコンテンツ
            fixes: 適用する修正リスト

        Returns:
            Tuple[str, list[str]]: (修正後コンテンツ, 修正内容説明リスト)
        """
        fixed_content = content
        changes = []

        # 信頼度順にソート(高信頼度から適用)
        sorted_fixes = sorted(fixes, key=lambda f: f.confidence, reverse=True)

        for fix in sorted_fixes:
            if fix.original in fixed_content:
                fixed_content = fixed_content.replace(fix.original, fix.corrected)
                category_name = self._get_category_display_name(fix.category)
                detail_label = f"{category_name}統一"
                changes.append(f"用語統一/{detail_label}: {fix.original} → {fix.corrected}")

        return fixed_content, changes

    def _get_terminology_dict(self, project_path: ProjectPath | None = None) -> dict[str, TerminologyEntry]:
        """用語辞書の取得

        Args:
            project_path: プロジェクトパス

        Returns:
            Dict[str, TerminologyEntry]: 用語辞書
        """
        terminology_dict = self._default_terminology.copy()

        if project_path:
            # プロジェクト固有の用語辞書を読み込み(実装予定)
            project_terminology = self._load_project_terminology(project_path)
            terminology_dict.update(project_terminology)

        return terminology_dict

    def _load_project_terminology(self, project_path: ProjectPath) -> dict[str, TerminologyEntry]:
        """プロジェクト固有用語辞書の読み込み

        Args:
            project_path: プロジェクトパス

        Returns:
            Dict[str, TerminologyEntry]: プロジェクト固有用語辞書
        """
        # 用語辞書YAMLファイルの読み込み実装が必要
        # 現在はサンプルデータを返却
        return {
            "太郎": TerminologyEntry(canonical="太郎", variants=["タロウ", "たろう", "TARO"], category="character"),
            "魔法学院": TerminologyEntry(
                canonical="魔法学院", variants=["魔法学園", "魔導学院", "魔術学院"], category="location"
            ),
            "ファイアボール": TerminologyEntry(
                canonical="ファイアボール", variants=["火球", "炎球", "ファイヤーボール"], category="spell"
            ),
            "冒険者ギルド": TerminologyEntry(
                canonical="冒険者ギルド", variants=["冒険者組合", "冒険者協会"], category="organization"
            ),
        }

    def _load_default_terminology(self) -> None:
        """デフォルト用語辞書の読み込み"""
        self._default_terminology = {
            "魔法使い": TerminologyEntry(
                canonical="魔法使い", variants=["魔導師", "魔術師", "マジシャン"], category="general"
            ),
            "モンスター": TerminologyEntry(
                canonical="モンスター", variants=["怪物", "魔物", "魔獣"], category="general"
            ),
        }

    def _calculate_confidence(self, content: str, variant: str, entry: TerminologyEntry) -> float:
        """修正信頼度の計算

        Args:
            content: コンテンツ
            variant: 変換候補
            entry: 用語エントリー

        Returns:
            float: 信頼度(0.0-1.0)
        """
        confidence = 0.8  # 基本信頼度

        # 文脈ヒントによる信頼度調整
        for hint in entry.context_hints:
            if hint in content:
                confidence += 0.1

        # カテゴリ別信頼度調整
        if entry.category == "character":
            confidence += 0.1  # キャラクター名は高信頼度
        elif entry.category == "spell":
            confidence += 0.05  # 魔法名は中程度

        # 文字数による調整(短い語は誤修正リスク高)
        if len(variant) <= 2:
            confidence -= 0.2

        return min(1.0, max(0.0, confidence))

    def _get_category_display_name(self, category: str) -> str:
        """カテゴリー表示名の取得

        Args:
            category: カテゴリー名

        Returns:
            str: 表示用カテゴリー名
        """
        category_names = {
            "character": "キャラクター名",
            "location": "地名",
            "organization": "組織名",
            "spell": "魔法名",
            "general": "用語",
        }
        return category_names.get(category, "用語")

    def get_terminology_stats(self, project_path: ProjectPath | None = None) -> dict[str, int]:
        """用語統計の取得

        Args:
            project_path: プロジェクトパス

        Returns:
            Dict[str, int]: 用語統計
        """
        terminology_dict = self._get_terminology_dict(project_path)

        stats = {
            "total_entries": len(terminology_dict),
            "character_entries": 0,
            "location_entries": 0,
            "spell_entries": 0,
            "organization_entries": 0,
            "general_entries": 0,
        }

        for entry in terminology_dict.values():
            if entry.category == "character":
                stats["character_entries"] += 1
            elif entry.category == "location":
                stats["location_entries"] += 1
            elif entry.category == "spell":
                stats["spell_entries"] += 1
            elif entry.category == "organization":
                stats["organization_entries"] += 1
            else:
                stats["general_entries"] += 1

        return stats
