# File: src/noveler/domain/services/tension_relief_balance_checker.py
# Purpose: Analyse narrative passages for tension versus relief balance and surface recommendations.
# Context: Invoked by quality workflows and tests to score chapters and produce adjustment suggestions.

"""緊張緩和バランスチェッカー

シーン別緊張度と緊張緩和の最適タイミング評価

- シーン別緊張度の自動判定
- コメディ要素（ギャップ会話等）の検出
- 緊張持続時間と緩和タイミングの分析
- エピソード全体のペース配分スコア化
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.interfaces.quality_checker import IQualityChecker


class TensionLevel(Enum):
    """緊張レベル"""
    HIGH = 5       # 高緊張（戦闘、危機等）
    MEDIUM_HIGH = 4  # 中高緊張（対立、発見等）
    MEDIUM = 3     # 中緊張（日常の問題等）
    LOW = 2        # 低緊張（平穏な会話等）
    MINIMAL = 1    # 最低緊張（完全リラックス）


@dataclass
class SceneAnalysis:
    """シーン分析結果"""
    start_position: int      # 開始位置
    end_position: int        # 終了位置
    content: str            # シーン内容
    tension_level: TensionLevel  # 緊張レベル
    comedy_elements: list[str]   # コメディ要素
    tension_duration: int    # 緊張持続文字数


@dataclass
class TensionBalanceResult:
    """緊張緩和バランス分析結果"""
    scenes: list[SceneAnalysis]    # シーン分析リスト
    tension_curve_score: float     # 緊張曲線スコア（0-100）
    relief_timing_score: float     # 緊張緩和タイミングスコア（0-100）
    overall_balance_score: float   # 全体バランススコア（0-100）
    peak_tension_count: int        # 高緊張シーン数
    relief_count: int              # 緊張緩和シーン数


class TensionReliefBalanceChecker(IQualityChecker):
    """緊張緩和バランスチェッカー

    SPEC-QUALITY-023 v2.0準拠
    シーン別緊張度と緊張緩和の最適タイミング評価
    """

    def __init__(self) -> None:
        """初期化

        B20準拠: 共有コンポーネント使用不要（ドメインサービス）
        緊張・緊張緩和パターンの定義
        """
        # 高緊張パターン
        raw_high_tension_patterns = [
            r"[戦闘|戦い|攻撃|襲撃|侵入|激戦]",
            r"[危険|危機|ピンチ|絶体絶命]",
            r"[急|急い|緊急|至急]",
            r"[爆発|破壊|崩壊|倒壊]",
            r"[血|流血|負傷|怪我]",
            r"[死|死ぬ|殺|命がけ]",
            r"[叫|悲鳴|うめき|うなり声]",
            r"[必死|必死に|全力で|命がけ]",
            r"[恐怖|恐|恐ろしい|怖い]",
            r"[震え|汗|息切れ|動悸]"
        ]
        self.high_tension_patterns = [self._normalize_pattern(p) for p in raw_high_tension_patterns]

        # 中緊張パターン
        raw_medium_tension_patterns = [
            r"[問題|困|困った|トラブル]",
            r"[発見|見つ|発覚|判明]",
            r"[対立|言い合い|口論|揉める]",
            r"[焦|イライラ|もどか|不安]",
            r"[心配|気がかり|懸念|憂]",
            r"[秘密|隠|内緒|バレ]",
            r"[計画|作戦|準備|用意]",
            r"[決断|決|選択|判断]",
            r"[謎|不思議|疑問|なぜ]",
            r"[違和感|おかしい|変|異常]"
        ]
        self.medium_tension_patterns = [self._normalize_pattern(p) for p in raw_medium_tension_patterns]

        # コメディ・緊張緩和パターン
        raw_comedy_relief_patterns = [
            # 知識差ギャップパターン（A38執筆プロンプトから）
            r"SQL.*[呪文|魔法]",
            r"[データベース|DB].*[料理|食べ物]",
            r"[API|アクセス|接続].*[魔法陣|儀式]",
            r"[プログラム|コード].*[詩|芸術]",
            r"[システム|サーバー].*[生き物|動物]",

            # 勘違い・誤解パターン
            r"[勘違い|誤解|間違い].*[する|した]",
            r"[え？|あれ？|ん？].*[だったの|だった]",
            r"[そういう意味|そんな|まさか].*[じゃない|ではない]",
            r"[違う|そうじゃなくて|そうじゃない]",

            # 日常的な軽快さ
            r"[笑|笑い|クスクス|ニヤニヤ]",
            r"[冗談|ジョーク|からかい]",
            r"[軽口|おどけ|ふざけ]",
            r"[のんき|暢気|のほほん|マイペース]",

            # 突然のリラックス要素
            r"[お茶|コーヒー|食事|おやつ]",
            r"[一息|休憩|ほっと|安堵]",
            r"[平和|平穏|穏やか|静か]",
            r"[日常|普通|当たり前|いつも通り]",

            # ギャップ表現
            r"[実は|本当は|意外と].*[優し|可愛い|弱い]",
            r"[強面|怖そう].*[だが|でも|しかし].*[優し|親切]"
        ]
        self.comedy_relief_patterns = [self._normalize_pattern(p) for p in raw_comedy_relief_patterns]

        # シーン区切りパターン
        self.scene_break_patterns = [
            r"\n\n\n+",      # 空行複数
            r"---+",         # 区切り線
            r"＊＊＊+",      # アスタリスク区切り
            r"　　＊",       # インデント＋アスタリスク
            r"[○●◯]",       # 箇条書き記号
        ]

        # 敵対台詞検出パターン
        self.antagonist_dialogue_keywords = [
            "計画通り",
            "俺の力を見せてやる",
            "屈服",
            "支配",
            "滅ぼ",
            "制圧"
        ]

        # 技術的表現と美的表現の組み合わせ検出キーワード
        self.tech_expression_keywords = [
            "API",
            "システム",
            "SQL",
            "データベース",
            "アルゴリズム"
        ]
        self.aesthetic_expression_keywords = [
            "エレガント",
            "美しく",
            "美しい",
            "哲学",
            "芸術",
            "洗練"
        ]

    def check_file(self, file_path: str) -> dict[str, Any]:
        """ファイルの緊張緩和バランスをチェック

        Args:
            file_path: チェック対象ファイルパス

        Returns:
            緊張緩和バランス分析結果辞書
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return self.check_text(content)
        except Exception as e:
            return {
                "success": False,
                "error": f"ファイル読み込みエラー: {e!s}",
                "score": 0
            }

    def check_text(self, text: str) -> dict[str, Any]:
        """テキストの緊張緩和バランスをチェック

        Args:
            text: チェック対象テキスト

        Returns:
            緊張緩和バランス分析結果辞書
        """
        try:
            result = self._analyze_tension_balance(text)

            return {
                "success": True,
                "checker_name": "TensionReliefBalanceChecker",
                "score": result.overall_balance_score,
                "analysis": {
                    "scenes_found": len(result.scenes),
                    "peak_tension_scenes": result.peak_tension_count,
                    "relief_scenes": result.relief_count,
                    "tension_curve_score": result.tension_curve_score,
                    "relief_timing_score": result.relief_timing_score,
                    "overall_balance_score": result.overall_balance_score,
                    "tension_distribution": self._get_tension_distribution(result.scenes),
                    "antagonist_dialogues_found": self._detect_antagonist_dialogues(text),
                    "unique_expressions": self._detect_unique_expressions(text)
                },
                "recommendations": self._generate_recommendations(result),
                "grade": self._calculate_grade(result.overall_balance_score)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"緊張緩和バランス分析エラー: {e!s}",
                "score": 0
            }

    def _analyze_tension_balance(self, text: str) -> TensionBalanceResult:
        """緊張緩和バランス分析実行

        Args:
            text: 分析対象テキスト

        Returns:
            緊張緩和バランス分析結果
        """
        # シーン分割
        scenes = self._split_into_scenes(text)

        # 各シーンの分析
        scene_analyses = []
        for scene in scenes:
            analysis = self._analyze_scene(scene)
            scene_analyses.append(analysis)

        # 全体バランス評価
        tension_curve_score = self._evaluate_tension_curve(scene_analyses)
        relief_timing_score = self._evaluate_relief_timing(scene_analyses)
        overall_balance_score = (tension_curve_score + relief_timing_score) / 2

        # 統計計算
        peak_tension_count = sum(1 for s in scene_analyses
                                if s.tension_level in [TensionLevel.HIGH, TensionLevel.MEDIUM_HIGH])
        relief_count = sum(1 for s in scene_analyses if len(s.comedy_elements) > 0)

        return TensionBalanceResult(
            scenes=scene_analyses,
            tension_curve_score=tension_curve_score,
            relief_timing_score=relief_timing_score,
            overall_balance_score=overall_balance_score,
            peak_tension_count=peak_tension_count,
            relief_count=relief_count
        )

    def _split_into_scenes(self, text: str) -> list[tuple[int, int, str]]:
        """テキストをシーンに分割"""
        scenes = []
        break_positions = [0]

        for pattern in self.scene_break_patterns:
            for match in re.finditer(pattern, text):
                break_positions.append(match.end())

        for match in re.finditer(r"\n\n+", text):
            break_positions.append(match.end())

        break_positions = sorted(set(break_positions))
        break_positions.append(len(text))

        for i in range(len(break_positions) - 1):
            start = break_positions[i]
            end = break_positions[i + 1]
            content = text[start:end].strip()
            if len(content) >= 5:
                scenes.append((start, end, content))

        if not scenes and text.strip():
            scenes.append((0, len(text), text.strip()))

        return scenes

    def _analyze_scene(self, scene_data: tuple[int, int, str]) -> SceneAnalysis:
        """個別シーンの分析"""
        start, end, content = scene_data

        tension_level = self._determine_tension_level(content)
        comedy_elements = self._extract_comedy_elements(content)

        if comedy_elements:
            if tension_level.value >= TensionLevel.MEDIUM_HIGH.value:
                tension_level = TensionLevel.MEDIUM
            else:
                tension_level = TensionLevel.LOW

        tension_duration = end - start

        return SceneAnalysis(
            start_position=start,
            end_position=end,
            content=content,
            tension_level=tension_level,
            comedy_elements=comedy_elements,
            tension_duration=tension_duration
        )

    def _determine_tension_level(self, content: str) -> TensionLevel:
        """シーンの緊張レベルを判定

        Args:
            content: シーン内容

        Returns:
            緊張レベル
        """
        high_tension_count = sum(1 for pattern in self.high_tension_patterns
                                if re.search(pattern, content))
        medium_tension_count = sum(1 for pattern in self.medium_tension_patterns
                                  if re.search(pattern, content))

        # 高緊張パターンが2つ以上ある場合
        if high_tension_count >= 2:
            return TensionLevel.HIGH
        if high_tension_count >= 1 or medium_tension_count >= 2:
            return TensionLevel.MEDIUM_HIGH
        if medium_tension_count >= 1:
            return TensionLevel.MEDIUM
        return TensionLevel.LOW

    def _extract_comedy_elements(self, content: str) -> list[str]:
        """コメディ要素の抽出

        Args:
            content: シーン内容

        Returns:
            コメディ要素リスト
        """
        comedy_elements = []

        for pattern in self.comedy_relief_patterns:
            matches = re.findall(pattern, content)
            comedy_elements.extend(matches)

        return list(set(comedy_elements))

    def _evaluate_tension_curve(self, scenes: list[SceneAnalysis]) -> float:
        """緊張曲線の評価

        Args:
            scenes: シーン分析リスト

        Returns:
            緊張曲線スコア（0-100）
        """
        if not scenes:
            return 0.0

        # 理想的な緊張曲線：開始低→中盤高→終盤中高→結末低
        ideal_curve = []
        scene_count = len(scenes)

        for i in range(scene_count):
            position_ratio = i / (scene_count - 1) if scene_count > 1 else 0

            if position_ratio < 0.2:  # 開始（20%）
                ideal_curve.append(TensionLevel.LOW.value)
            elif position_ratio < 0.6:  # 中盤（20-60%）
                ideal_curve.append(TensionLevel.HIGH.value)
            elif position_ratio < 0.8:  # 終盤（60-80%）
                ideal_curve.append(TensionLevel.MEDIUM_HIGH.value)
            else:  # 結末（80-100%）
                ideal_curve.append(TensionLevel.MEDIUM.value)

        # 実際の緊張曲線
        actual_curve = [scene.tension_level.value for scene in scenes]

        # 理想と実際の差を計算
        total_deviation = sum(abs(ideal - actual)
                            for ideal, actual in zip(ideal_curve, actual_curve, strict=False))
        max_possible_deviation = len(scenes) * (TensionLevel.HIGH.value - TensionLevel.MINIMAL.value)

        if max_possible_deviation == 0:
            return 100.0

        deviation_ratio = total_deviation / max_possible_deviation
        return max(0.0, 100.0 - (deviation_ratio * 100))

    def _evaluate_relief_timing(self, scenes: list[SceneAnalysis]) -> float:
        """緊張緩和タイミングの評価"""
        if not scenes:
            return 0.0

        score = 70.0
        high_tension_streak = 0
        relief_scenes = 0

        for scene in scenes:
            if scene.tension_level in [TensionLevel.HIGH, TensionLevel.MEDIUM_HIGH]:
                high_tension_streak += 1
            else:
                high_tension_streak = 0

            if scene.comedy_elements:
                relief_scenes += 1
                if high_tension_streak >= 2:
                    score += 15
                else:
                    score += 5
                high_tension_streak = 0

            if high_tension_streak >= 4:
                score -= 20

        if relief_scenes == 0:
            score -= 40
        elif relief_scenes >= 1:
            score += 10

        return max(0.0, min(100.0, score))


    def _get_tension_distribution(self, scenes: list[SceneAnalysis]) -> dict[str, int]:
        """緊張レベルの分布を取得

        Args:
            scenes: シーン分析リスト

        Returns:
            緊張レベル別シーン数
        """
        distribution = {
            "high": 0,
            "medium_high": 0,
            "medium": 0,
            "low": 0,
            "minimal": 0
        }

        for scene in scenes:
            if scene.tension_level == TensionLevel.HIGH:
                distribution["high"] += 1
            elif scene.tension_level == TensionLevel.MEDIUM_HIGH:
                distribution["medium_high"] += 1
            elif scene.tension_level == TensionLevel.MEDIUM:
                distribution["medium"] += 1
            elif scene.tension_level == TensionLevel.LOW:
                distribution["low"] += 1
            else:
                distribution["minimal"] += 1

        return distribution

    def _detect_antagonist_dialogues(self, text: str) -> int:
        """Detect antagonist-toned dialogue snippets within the text.

        Args:
            text: Narrative text that may contain quoted dialogue.

        Returns:
            Number of dialogue lines that satisfy antagonist cues.
        """
        dialogues = re.findall(r'「([^」]+)」', text)
        antagonist_dialogues = [
            dialogue for dialogue in dialogues
            if any(keyword in dialogue for keyword in self.antagonist_dialogue_keywords)
        ]
        return len(antagonist_dialogues)

    def _detect_unique_expressions(self, text: str) -> dict[str, Any]:
        """Detect rare technical-and-aesthetic expression combinations.

        Args:
            text: Narrative text that may contain quoted dialogue.

        Returns:
            Dictionary containing the detected count and representative examples.
        """
        dialogues = re.findall(r'「([^」]+)」', text)
        unique_candidates: list[str] = []
        for dialogue in dialogues:
            has_tech = any(keyword in dialogue for keyword in self.tech_expression_keywords)
            has_aesthetic = any(keyword in dialogue for keyword in self.aesthetic_expression_keywords)
            if has_tech and has_aesthetic:
                cleaned = dialogue.strip()
                if cleaned and cleaned not in unique_candidates:
                    unique_candidates.append(cleaned)

        return {
            "count": len(unique_candidates),
            "examples": unique_candidates[:5]
        }

    def _generate_recommendations(self, result: TensionBalanceResult) -> list[str]:
        """改善提案生成

        Args:
            result: 分析結果

        Returns:
            改善提案リスト
        """
        recommendations = []

        if result.peak_tension_count == 0:
            recommendations.append("高緊張シーンが不足しています。クライマックスや危機的状況を追加してください")

        if result.relief_count == 0:
            recommendations.append("緊張緩和要素が不足しています。ギャップ会話や軽い笑いを追加してください")

        if result.tension_curve_score < 60:
            recommendations.append("緊張の構成が理想的でありません。序盤は軽く、中盤に高緊張、終盤は適度な緊張にしてください")

        if result.relief_timing_score < 60:
            recommendations.append("緊張緩和のタイミングが適切ではありません。高緊張の後に息抜きを入れてください")

        # 高緊張が長時間続いている場合
        consecutive_high = 0
        max_consecutive = 0
        for scene in result.scenes:
            if scene.tension_level in [TensionLevel.HIGH, TensionLevel.MEDIUM_HIGH]:
                consecutive_high += 1
                max_consecutive = max(max_consecutive, consecutive_high)
            else:
                consecutive_high = 0

        if max_consecutive >= 4:
            recommendations.append("高緊張状態が長時間続きすぎています。適度な緊張緩和を挟んでください")

        return recommendations

    def _calculate_grade(self, score: float) -> str:
        """グレード判定

        Args:
            score: スコア

        Returns:
            グレード文字列
        """
        if score >= 95:
            return "S"
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 50:
            return "C"
        return "D"

    def _normalize_pattern(self, pattern: str) -> str:
        """Convert shorthand option blocks into valid regex alternatives.

        Args:
            pattern: Pattern string that may include option blocks wrapped in square brackets.

        Returns:
            Regex pattern string safe for use with Python's re module.
        """
        def replace_block(match) -> str:
            options = [option for option in match.group(1).split('|') if option]
            return f"(?:{'|'.join(options)})"

        return re.sub(r"\[([^\[\]]+)\]", replace_block, pattern)
