"""対立キャラクター個性化チェッカー

敵キャラの台詞独自性と印象度の定量評価

- 定型悪役台詞データベースとの差分分析
- 口調・語彙の独自性スコア算出
- キャラクター固有の癖・こだわりの検出
- 印象度メトリクス計算（記憶定着予測）
"""

import re
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.quality_checker import IQualityChecker


@dataclass
class AntagonistAnalysisResult:
    """対立キャラクター分析結果"""
    generic_phrases: list[str]      # 定型悪役台詞
    unique_expressions: list[str]   # 独自表現
    character_quirks: list[str]     # キャラクター特有の癖
    personality_score: float        # 個性スコア（0-100）
    memorability_score: float       # 印象度スコア（0-100）


class AntagonistPersonalityChecker(IQualityChecker):
    """対立キャラクター個性化チェッカー

    SPEC-QUALITY-023 v2.0準拠
    敵キャラの台詞独自性と印象度の定量評価
    """

    def __init__(self) -> None:
        """初期化

        B20準拠: 共有コンポーネント使用不要（ドメインサービス）
        定型悪役台詞データベースとパターンの初期化
        """
        # 定型悪役台詞パターン（避けるべき表現）
        self.generic_villain_patterns = [
            r"世界を(?:支配|征服|滅ぼ)",
            r"(?:お前|貴様|君)たちは無力だ",
            r"愚か者めが",
            r"これで終わりだ",
            r"(?:私|俺|我)の力を(?:見せ|思い知る)",
            r"(?:計画|作戦)通りだ",
            r"邪魔を(?:する|される)な",
            r"(?:負け|敗北)を認めろ",
            r"(?:復讐|恨み)を(?:晴ら|果た)",
            r"強者と弱者の(?:違い|差)",
            r"これが現実だ",
            r"諦めろ",
            r"(?:運命|宿命)を受け入れろ",
            r"(?:血|犠牲)を流す",
            r"(?:破滅|滅亡)の時だ"
        ]

        # 個性的表現のパターン（評価対象）
        self.unique_expression_patterns = [
            r"(?:システム|データベース|API|SQL).*?(?:美しい|エレガント|完璧)",  # 技術用語+美学
            r"(?:コード|プログラム|アルゴリズム).*?(?:詩|芸術|アート)",      # 技術+芸術
            r"(?:バックアップ|リカバリー|復旧).*?(?:愛|情|想い)",          # 技術+感情
            r"(?:最適化|効率|パフォーマンス).*?(?:哲学|美学|理念)",        # 技術+哲学
            r"(?:ハッキング|クラッキング|侵入).*?(?:ダンス|音楽|リズム|アート)",    # 技術+芸術
            r"(?:エラー|例外|バグ).*?(?:可愛い|愛おしい|チャーミング)",     # 技術+愛着
            r"(?:ログ|ファイル|記録|データベース).*?(?:宝物|財産|遺産)",              # 技術+価値観
            r"(?:セキュリティ|暗号化|保護).*?(?:やさしさ|思いやり)",       # 技術+人間性
            r"(?:コード|プログラム).*?(?:美しい|素晴らしい)",            # 技術+賞賛
        ]

        # キャラクター癖のパターン
        self.character_quirk_patterns = [
            r"〜である(?:な|ね|か|よ)",           # 堅い口調の語尾
            r"〜だから(?:な|ね)?",                # 解説癖
            r"(?:美しい|エレガント|完璧な)",         # 美学へのこだわり
            r"(?:実に|なるほど|興味深い)",          # 知的キャラ
            r"(?:ふむ|うむ|なれば)",              # 古風な口調
            r"です(?:わ|の|のよ)",                 # 丁寧語の崩し
            r"〜(?:かい|だい|さ)",                # 方言・語尾
            r"(?:数字|%|時間|データ)を.*?(?:言う|語る|述べ)",  # 数値へのこだわり
            r"(?:比喩|例え|たとえ).*(?:すると|れば)",   # 比喩好き
            r"(?:哲学的|抽象的|概念的).*(?:話|言葉)",   # 哲学好き
        ]

        # 敵キャラ特定パターン（台詞の前後から判定）
        self.antagonist_indicators = [
            r"[敵|悪役|ボス|リーダー|団長]",
            r"エクスプロイト団",
            r"[ハッカー|クラッカー|侵入者]",
            r"[攻撃|襲撃|侵入|破壊].*[する|した|予定]",
            r"[主人公|直人|あすか].*[邪魔|敵|標的]",
        ]

    def check_file(self, file_path: str) -> dict[str, Any]:
        """ファイルの対立キャラクター個性をチェック

        Args:
            file_path: チェック対象ファイルパス

        Returns:
            対立キャラクター分析結果辞書
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
        """テキストの対立キャラクター個性をチェック

        Args:
            text: チェック対象テキスト

        Returns:
            対立キャラクター分析結果辞書
        """
        cleaned_text = text or ""

        if not cleaned_text.strip():
            return self._build_empty_text_response()

        try:
            antagonist_dialogues, total_dialogues = self._extract_antagonist_dialogues(cleaned_text)

            if not antagonist_dialogues:
                return self._build_non_antagonist_response(cleaned_text, total_dialogues)

            result = self._analyze_antagonist_personality(antagonist_dialogues)
            total_expressions = (
                len(result.generic_phrases) + len(result.unique_expressions) + len(result.character_quirks)
            )

            return {
                "success": True,
                "checker_name": "AntagonistPersonalityChecker",
                "score": result.personality_score,
                "analysis": {
                    "antagonist_dialogues_found": len(antagonist_dialogues),
                    "generic_phrases": {
                        "count": len(result.generic_phrases),
                        "examples": result.generic_phrases[:3]
                    },
                    "unique_expressions": {
                        "count": len(result.unique_expressions),
                        "examples": result.unique_expressions[:3]
                    },
                    "character_quirks": {
                        "count": len(result.character_quirks),
                        "examples": result.character_quirks[:3]
                    },
                    "personality_score": result.personality_score,
                    "memorability_score": result.memorability_score,
                    "total_expressions": total_expressions,
                },
                "recommendations": self._generate_recommendations(result),
                "grade": self._calculate_grade(result.personality_score)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"対立キャラクター分析エラー: {e!s}",
                "score": 0
            }

    def _extract_antagonist_dialogues(self, text: str) -> tuple[list[str], int]:
        """対立キャラクターの台詞を抽出

        Args:
            text: テキスト

        Returns:
            (対立キャラクターの台詞リスト, 台詞総数)
        """
        dialogue_pattern = r"「([^」]+)」"
        all_dialogues = re.findall(dialogue_pattern, text)
        antagonist_dialogues = [dialogue for dialogue in all_dialogues if self._is_antagonist_dialogue(dialogue, text)]
        return antagonist_dialogues, len(all_dialogues)

    def _is_antagonist_dialogue(self, dialogue: str, full_text: str) -> bool:
        """台詞が対立キャラクターのものかを判定

        Args:
            dialogue: 台詞
            full_text: 全文（前後文脈の確認用）

        Returns:
            対立キャラクターの台詞かどうか
        """
        # 台詞自体に敵キャラ要素が含まれているか
        for pattern in self.antagonist_indicators:
            if re.search(pattern, dialogue):
                return True

        # 台詞の前後文脈で敵キャラかを判定
        dialogue_index = full_text.find(f"「{dialogue}」")
        if dialogue_index != -1:
            # 前後100文字の文脈を確認
            context_start = max(0, dialogue_index - 100)
            context_end = min(len(full_text), dialogue_index + len(dialogue) + 100)
            context = full_text[context_start:context_end]

            for pattern in self.antagonist_indicators:
                if re.search(pattern, context):
                    return True

        # 定型悪役台詞パターンにマッチするか
        return any(re.search(pattern, dialogue) for pattern in self.generic_villain_patterns)

    def _build_empty_text_response(self) -> dict[str, Any]:
        """空テキストに対するレスポンスを生成"""
        return {
            "success": True,
            "checker_name": "AntagonistPersonalityChecker",
            "score": 0,
            "analysis": {
                "message": "テキストが空のため分析できません",
                "antagonist_dialogues_found": 0,
                "total_dialogues": 0,
                "total_expressions": 0,
            },
            "recommendations": [
                "物語の内容を追加し、敵キャラクターの台詞や状況を描写してください",
            ],
            "grade": "D",
        }

    def _build_non_antagonist_response(self, text: str, total_dialogues: int) -> dict[str, Any]:
        """対立キャラの台詞が検出できなかった場合のレスポンス"""
        if total_dialogues > 0:
            return {
                "success": True,
                "checker_name": "AntagonistPersonalityChecker",
                "score": 50,
                "analysis": {
                    "message": "対立キャラクターの台詞が検出されませんでした",
                    "antagonist_dialogues_found": 0,
                    "total_dialogues": total_dialogues,
                    "total_expressions": 0,
                },
                "recommendations": [
                    "対立キャラクターを登場させる場合は、個性的な台詞を心がけてください",
                ],
                "grade": "B",
            }

        features = self._analyze_narrative_features(text)
        recommendations = []

        if not features["has_sensory_metaphor"]:
            recommendations.append("感覚的比喩を追加して敵キャラクターの印象を強めましょう")
        if not features["has_inner_monologue"]:
            recommendations.append("内面独白を追加して敵キャラクターの価値観を描写してください")
        if not features["has_body_reaction"]:
            recommendations.append("身体反応の表現を追加して緊張感を高めましょう")
        recommendations.append("対立キャラクターの台詞や明確な目的を描写すると個性が際立ちます")

        return {
            "success": True,
            "checker_name": "AntagonistPersonalityChecker",
            "score": 30,
            "analysis": {
                "message": "対立キャラクターの台詞が検出されませんでした",
                "antagonist_dialogues_found": 0,
                "total_dialogues": 0,
                "total_expressions": 0,
                "narrative_features": features,
            },
            "recommendations": recommendations,
            "grade": "C",
        }

    def _analyze_narrative_features(self, text: str) -> dict[str, bool]:
        """台詞がない場合のナラティブ要素分析"""
        features = {
            "has_body_reaction": bool(re.search(r"(心臓|鼓動|汗|震え|鳥肌|息が)", text)),
            "has_inner_monologue": bool(re.search(r"(と思った|と考えた|と感じた|心の中|自問した)", text)),
            "has_sensory_metaphor": bool(re.search(r"(ように|みたい|かのよう|比喩|喩え)", text)),
        }
        return features

    def _analyze_antagonist_personality(self, dialogues: list[str]) -> AntagonistAnalysisResult:
        """対立キャラクターの個性分析

        Args:
            dialogues: 対立キャラクターの台詞リスト

        Returns:
            分析結果
        """
        generic_phrases = []
        unique_expressions = []
        character_quirks = []

        all_dialogue_text = " ".join(dialogues)

        # 定型悪役台詞の検出
        for pattern in self.generic_villain_patterns:
            matches = re.findall(pattern, all_dialogue_text)
            generic_phrases.extend(matches)

        # 独自表現の検出
        for pattern in self.unique_expression_patterns:
            matches = re.findall(pattern, all_dialogue_text)
            unique_expressions.extend(matches)

        # キャラクター癖の検出
        for pattern in self.character_quirk_patterns:
            matches = re.findall(pattern, all_dialogue_text)
            character_quirks.extend(matches)

        # スコア計算
        personality_score = self._calculate_personality_score(
            len(generic_phrases), len(unique_expressions), len(character_quirks), len(dialogues)
        )

        memorability_score = self._calculate_memorability_score(
            len(unique_expressions), len(character_quirks), len(dialogues)
        )

        return AntagonistAnalysisResult(
            generic_phrases=self._unique_preserve_order(generic_phrases),
            unique_expressions=self._unique_preserve_order(unique_expressions),
            character_quirks=self._unique_preserve_order(character_quirks),
            personality_score=personality_score,
            memorability_score=memorability_score
        )

    def _calculate_personality_score(
        self, generic_count: int, unique_count: int, quirk_count: int, total_dialogues: int
    ) -> float:
        """個性スコア計算

        Args:
            generic_count: 定型台詞数
            unique_count: 独自表現数
            quirk_count: 個性的な癖数
            total_dialogues: 総台詞数

        Returns:
            個性スコア（0-100）
        """
        if total_dialogues == 0:
            return 0.0

        # 定型台詞は減点
        generic_penalty = min(50, (generic_count / total_dialogues) * 100)

        # 独自表現は加点
        unique_bonus = min(40, (unique_count / total_dialogues) * 200)

        # 個性的な癖は加点
        quirk_bonus = min(30, (quirk_count / total_dialogues) * 150)

        # ベーススコア50から計算
        base_score = 50.0
        final_score = base_score - generic_penalty + unique_bonus + quirk_bonus

        return min(100.0, max(0.0, final_score))

    def _calculate_memorability_score(
        self, unique_count: int, quirk_count: int, total_dialogues: int
    ) -> float:
        """印象度スコア計算

        Args:
            unique_count: 独自表現数
            quirk_count: 個性的な癖数
            total_dialogues: 総台詞数

        Returns:
            印象度スコア（0-100）
        """
        if total_dialogues == 0:
            return 0.0

        # 独自表現による印象度
        unique_impact = min(60, (unique_count / total_dialogues) * 300)

        # 癖による印象度
        quirk_impact = min(40, (quirk_count / total_dialogues) * 200)

        # 印象度は独自表現と癖の組み合わせで決まる
        total_impact = unique_impact + quirk_impact

        # 両方存在する場合はボーナス
        if unique_count > 0 and quirk_count > 0:
            total_impact += 20

        return min(100.0, total_impact)

    def _generate_recommendations(self, result: AntagonistAnalysisResult) -> list[str]:
        """改善提案生成

        Args:
            result: 分析結果

        Returns:
            改善提案リスト
        """
        recommendations = []

        if len(result.generic_phrases) > 2:
            recommendations.append(
                f"定型的な悪役台詞が{len(result.generic_phrases)}個見つかりました。"
                "より個性的な表現に置き換えてください"
            )

        if len(result.unique_expressions) == 0:
            recommendations.append(
                "独自の表現が見つかりませんでした。技術用語と美学の組み合わせなど、"
                "キャラクター固有の語彙を追加してください"
            )

        if len(result.character_quirks) == 0:
            recommendations.append(
                "キャラクター特有の話し方の癖が見つかりませんでした。"
                "口調や語尾に個性を付けてください"
            )

        if result.personality_score < 60:
            recommendations.append(
                "個性スコアが低いです。定型表現を減らし、"
                "そのキャラクターらしい独自の価値観や知識を台詞に反映させてください"
            )

        if result.memorability_score < 50:
            recommendations.append(
                "印象度が低いです。読者の記憶に残る特徴的な表現や癖を追加してください"
            )

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

    def _unique_preserve_order(self, items: list[str]) -> list[str]:
        """順序を維持したまま重複を除去"""
        seen: set[str] = set()
        ordered_items: list[str] = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                ordered_items.append(item)
        return ordered_items
