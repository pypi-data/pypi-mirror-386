"""感情表現深度チェッカー

身体反応・感覚比喻・内面独白の三層構造による臨場感分析

- 身体反応パターンの検出（心臓、呼吸、筋肉の緊張等）
- 感覚的比喻の使用率測定（冷たい刃物のように、胸を締め付けるように等）
- 内面独白の頻度・質の評価
- 三層構造バランススコア算出（0-100点）
"""

import re
from dataclasses import dataclass
from typing import Any

from noveler.domain.interfaces.quality_checker import IQualityChecker


@dataclass
class EmotionAnalysisResult:
    """感情表現分析結果"""
    physical_reactions: list[str]  # 身体反応表現
    sensory_metaphors: list[str]   # 感覚的比喩
    inner_monologues: list[str]    # 内面独白
    balance_score: float           # バランススコア（0-100）
    total_expressions: int         # 総感情表現数


class EmotionExpressionChecker(IQualityChecker):
    """感情表現深度チェッカー

    SPEC-QUALITY-023 v2.0準拠
    身体反応・感覚比喻・内面独白の三層構造分析
    """

    def __init__(self) -> None:
        """初期化

        B20準拠: 共有コンポーネント使用不要（ドメインサービス）
        パターンデータベースの初期化
        """
        # 身体反応パターン
        self.physical_reaction_patterns = [
            r"心臓.*[跳び|跳ね|鼓動|ドキドキ|バクバク]",
            r"[息|呼吸].*[切れ|苦し|止ま|荒く|速く]",
            r"筋肉.*[緊張|こわば|強ば|硬直]",
            r"手.*[震え|汗|握り|こぶし]",
            r"[喉|のど].*[渇|干|詰ま|引きつ]",
            r"[背筋|背中].*[凍|冷|ゾクゾク|ぞく]",
            r"[頭|脳].*[クラクラ|くらくら|ガンガン]",
            r"[胃|腹].*[きり|締め|重く|沈む]",
            r"[血|血液].*[冷|凍|沸騰|逆流]",
            r"[肌|皮膚].*[粟立|鳥肌|ざわざわ]"
        ]
        self.physical_reaction_patterns = [
            r"(心臓|胸|鼓動).*(跳び|跳ね|鼓動|ドキドキ|バクバク)",
            r"(息|呼吸).*(切れ|苦し|止ま|荒く|速く)",
            r"筋肉.*(緊張|こわば|強ば|硬直)",
            r"手.*(震え|汗|握り|こぶし)",
            r"(喉|のど).*(渇|干|詰ま|引きつ)",
            r"(背筋|背中).*(凍|冷|ゾクゾク|ぞく)",
            r"(頭|脳).*(クラクラ|くらくら|ガンガン)",
            r"(胃|腹).*(きり|締め|重く|沈む)",
            r"(血|血液).*(冷|凍|沸騰|逆流)",
            r"(肌|皮膚).*(粟立|鳥肌|ざわざわ)"
        ]

        # 感覚的比喩パターン
        self.sensory_metaphor_patterns = [
            r"冷たい[^。]*刃物[^。]*のように",
            r"冷たい[^。]*刃物[^。]*ような",
            r"鋭い[^。]*(?:刃物|ナイフ|剣)[^。]*のように",
            r"熱い[^。]*(?:刃物|ナイフ|剣)[^。]*のように",
            r"(?:胸|心)[^。]*締め付ける[^。]*ように",
            r"(?:胸|心)[^。]*圧迫する[^。]*ように",
            r"(?:胸|心)[^。]*押し潰す[^。]*ように",
            r"(?:頭|脳)[^。]*割れる[^。]*ような",
            r"(?:頭|脳)[^。]*砕ける[^。]*ような",
            r"(?:頭|脳)[^。]*爆発[^。]*ような",
            r"(?:嵐|雷|稲妻)[^。]*(?:走る|駆け巡る|突き抜ける)",
            r"(?:氷|氷塊|氷柱)[^。]*突き刺さる[^。]*ような",
            r"(?:氷|氷塊|氷柱)[^。]*貫く[^。]*ような",
            r"(?:火|炎|熱)[^。]*燃える[^。]*ような",
            r"(?:火|炎|熱)[^。]*焼ける[^。]*ような",
            r"(?:火|炎|熱)[^。]*焦がす[^。]*ような",
            r"重い[^。]*(?:塊|重り|石)[^。]*のような",
            r"鉛の[^。]*(?:塊|重り|石)[^。]*のような",
            r"(?:針|とげ|棘)[^。]*刺す[^。]*ような",
            r"(?:針|とげ|棘)[^。]*突く[^。]*ような",
            r"(?:針|とげ|棘)[^。]*貫く[^。]*ような",
            r"(?:電気|電流)[^。]*走る",
            r"(?:電気|電流)[^。]*流れる",
            r"(?:電気|電流)[^。]*びりびり",
            r"(?:蜂蜜|シロップ)[^。]*ような[^。]*(?:甘い|とろり)",
            r"(?:蜂蜜|シロップ)[^。]*みたい[^。]*(?:甘い|とろり)"
        ]
        self.sensory_metaphor_patterns = [
            r"冷たい[^。]*(刃物|ナイフ)[^。]*のよう(?:に|な)",
            r"鋭い[^。]*(刃物|ナイフ|剣)[^。]*のよう(?:に|な)",
            r"熱い[^。]*(刃物|ナイフ|剣)[^。]*のよう(?:に|な)",
            r"(胸|心)[^。]*(締め付ける|圧迫する|押し潰す)[^。]*ように",
            r"(頭|脳)[^。]*(割れる|砕ける|爆発)[^。]*ような",
            r"(嵐|雷|稲妻)[^。]*(走る|駆け巡る|突き抜ける)",
            r"(氷|氷塊|氷柱)[^。]*(突き刺さる|貫く)[^。]*ような",
            r"(火|炎|熱)[^。]*(燃える|焼ける|焦がす)[^。]*ような",
            r"重い[^。]*(塊|重り|石)[^。]*のような",
            r"鉛の[^。]*(塊|重り|石)[^。]*のような",
            r"(針|とげ|棘)[^。]*(刺す|突く|貫く)[^。]*ような",
            r"(電気|電流)[^。]*(走る|流れる|びりびり)",
            r"(蜂蜜|シロップ)[^。]*(ような|みたいな)[^。]*(甘い|とろり)"
        ]

        # 内面独白パターン
        self.inner_monologue_patterns = [
            r"（.*思.*）",
            r"「.*」.*[思う|感じる|考える]",
            r"[私|僕|俺|自分].*[思う|感じる|考える]",
            r"どう.*[だろう|かな|のか]",
            r"なぜ.*[だろう|のか]",
            r"もしかして.*[かもしれない|だろうか]",
            r"きっと.*[だろう|に違いない]",
            r"[心の中|胸の内|内心].*[呟|つぶや|叫]",
            r"[そう|こう].*[思い|感じ].*ながら",
            r"[理解|分かる|気づく].*[した|できない]"
        ]
        self.inner_monologue_patterns = [
            r"（[^）]+）",
            r"（[^）]*(思|感じ|考)[^）]*）",
            r"「[^」]+」[^。]*(思う|感じる|考える)",
            r"(私|僕|俺|自分)[^。]*(思う|感じる|考える)",
            r"[一-龯ぁ-んァ-ン]+は[^。]*(思った|考えた|思考した|思考する)",
            r"どう[^。]*(だろう|かな|のか)",
            r"なぜ[^。]*(だろう|のか)",
            r"もしかして[^。]*(かもしれない|だろうか)",
            r"きっと[^。]*(だろう|に違いない)",
            r"(心の中|胸の内|内心)[^。]*(呟|つぶや|叫)",
            r"(そう|こう)[^。]*(思い|感じ)[^。]*ながら",
            r"(理解|分かる|気づく)[^。]*(した|できない)"
        ]

    def check_file(self, file_path: str) -> dict[str, Any]:
        """ファイルの感情表現深度をチェック

        Args:
            file_path: チェック対象ファイルパス

        Returns:
            感情表現分析結果辞書
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
        """テキストの感情表現深度をチェック

        Args:
            text: チェック対象テキスト

        Returns:
            感情表現分析結果辞書
        """
        try:
            result = self._analyze_emotion_expressions(text)

            return {
                "success": True,
                "checker_name": "EmotionExpressionChecker",
                "score": result.balance_score,
                "analysis": {
                    "physical_reactions": {
                        "count": len(result.physical_reactions),
                        "expressions": result.physical_reactions[:5]  # 最初の5件のみ
                    },
                    "sensory_metaphors": {
                        "count": len(result.sensory_metaphors),
                        "expressions": result.sensory_metaphors[:5]
                    },
                    "inner_monologues": {
                        "count": len(result.inner_monologues),
                        "expressions": result.inner_monologues[:5]
                    },
                    "balance_score": result.balance_score,
                    "total_expressions": result.total_expressions
                },
                "recommendations": self._generate_recommendations(result),
                "grade": self._calculate_grade(result.balance_score)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"感情表現分析エラー: {e!s}",
                "score": 0
            }

    def _analyze_emotion_expressions(self, text: str) -> EmotionAnalysisResult:
        """感情表現の分析実行

        Args:
            text: 分析対象テキスト

        Returns:
            感情表現分析結果
        """
        # 各カテゴリの表現を検出
        physical_reactions = self._extract_expressions(text, self.physical_reaction_patterns)
        sensory_metaphors = self._extract_expressions(text, self.sensory_metaphor_patterns)
        inner_monologues = self._extract_expressions(text, self.inner_monologue_patterns)

        # バランススコア計算
        balance_score = self._calculate_balance_score(
            len(physical_reactions),
            len(sensory_metaphors),
            len(inner_monologues),
            len(text)
        )

        total_expressions = len(physical_reactions) + len(sensory_metaphors) + len(inner_monologues)

        return EmotionAnalysisResult(
            physical_reactions=physical_reactions,
            sensory_metaphors=sensory_metaphors,
            inner_monologues=inner_monologues,
            balance_score=balance_score,
            total_expressions=total_expressions
        )

    def _extract_expressions(self, text: str, patterns: list[str]) -> list[str]:
        """パターンマッチによる表現抽出

        Args:
            text: 検索対象テキスト
            patterns: 検索パターンリスト

        Returns:
            マッチした表現のリスト
        """
        expressions = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                expressions.append(match.group(0))
        return list({expr: None for expr in expressions}.keys())

    def _calculate_balance_score(
        self,
        physical_count: int,
        metaphor_count: int,
        monologue_count: int,
        text_length: int
    ) -> float:
        """三層構造バランススコア計算

        Args:
            physical_count: 身体反応表現数
            metaphor_count: 感覚比喩数
            monologue_count: 内面独白数
            text_length: テキスト長

        Returns:
            バランススコア（0-100）
        """
        if text_length == 0:
            return 0.0

        # テキスト長あたりの密度計算（1000文字あたり）
        density_factor = 1000.0 / text_length if text_length > 0 else 0

        physical_density = physical_count * density_factor
        metaphor_density = metaphor_count * density_factor
        monologue_density = monologue_count * density_factor

        # 理想的な比率（身体反応:比喩:独白 = 2:1:3）
        ideal_physical = 2.0
        ideal_metaphor = 1.0
        ideal_monologue = 3.0

        # 各層の適切性スコア
        physical_score = min(100, (physical_density / ideal_physical) * 100) if physical_density > 0 else 0
        metaphor_score = min(100, (metaphor_density / ideal_metaphor) * 100) if metaphor_density > 0 else 0
        monologue_score = min(100, (monologue_density / ideal_monologue) * 100) if monologue_density > 0 else 0

        # バランススコア（三層がバランスよく存在することを評価）
        if physical_count > 0 and metaphor_count > 0 and monologue_count > 0:
            # 全層存在時は重み付け平均
            balance_bonus = 20.0  # ボーナス点
            weighted_average = (physical_score * 0.3 + metaphor_score * 0.2 + monologue_score * 0.5)
            return min(100.0, weighted_average + balance_bonus)
        if (physical_count > 0 and metaphor_count > 0) or (physical_count > 0 and monologue_count > 0) or (metaphor_count > 0 and monologue_count > 0):
            # 二層存在時
            return (physical_score + metaphor_score + monologue_score) / 2
        if physical_count > 0 or metaphor_count > 0 or monologue_count > 0:
            # 一層のみ存在時
            return (physical_score + metaphor_score + monologue_score) / 3
        # 何も存在しない場合
        return 0.0

    def _generate_recommendations(self, result: EmotionAnalysisResult) -> list[str]:
        """改善提案生成

        Args:
            result: 分析結果

        Returns:
            改善提案リスト
        """
        recommendations = []

        if len(result.physical_reactions) == 0:
            recommendations.append("身体反応の表現を追加してください")

        if len(result.sensory_metaphors) == 0:
            recommendations.append("感覚的比喩を追加してください")

        if len(result.inner_monologues) == 0:
            recommendations.append("内面独白を追加してください")

        if result.balance_score < 50:
            recommendations.append("感情表現の三層構造（身体・比喩・独白）のバランスを改善してください")

        if result.total_expressions < 3:
            recommendations.append("感情表現の総数が少なすぎます。臨場感向上のため表現を増やしてください")

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
