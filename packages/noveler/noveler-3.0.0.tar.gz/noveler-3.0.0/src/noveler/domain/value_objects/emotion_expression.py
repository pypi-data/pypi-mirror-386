#!/usr/bin/env python3
"""感情表現5層システム関連のValue Objects

A38執筆プロンプトガイドSTEP8で定義される感情表現5層システムを実装。
直接的な感情表現を避け、身体化描写を強化した豊かな表現体系を提供。
"""

from dataclasses import dataclass
from enum import Enum


class EmotionCategory(Enum):
    """基本感情カテゴリ（喜怒哀楽の細分化）"""
    # 喜び系
    JOY = "joy"              # 純粋な喜び
    EXCITEMENT = "excitement"  # 興奮・高揚
    RELIEF = "relief"        # 安堵・安心
    SATISFACTION = "satisfaction"  # 満足・達成感

    # 怒り系
    ANGER = "anger"          # 純粋な怒り
    IRRITATION = "irritation"  # 苛立ち・不満
    INDIGNATION = "indignation"  # 義憤・憤慨
    FRUSTRATION = "frustration"  # 挫折感・焦燥

    # 哀しみ系
    SADNESS = "sadness"      # 純粋な悲しみ
    DESPAIR = "despair"      # 絶望・落胆
    MELANCHOLY = "melancholy"  # 憂鬱・物悲しさ
    REGRET = "regret"        # 後悔・自責

    # 楽しみ系
    PLEASURE = "pleasure"    # 快楽・楽しさ
    AMUSEMENT = "amusement"  # 面白さ・滑稽
    CURIOSITY = "curiosity"  # 好奇心・興味
    ANTICIPATION = "anticipation"  # 期待・楽しみ

    # 複合感情
    CONFUSION = "confusion"  # 困惑・混乱
    ANXIETY = "anxiety"      # 不安・心配
    EMBARRASSMENT = "embarrassment"  # 恥ずかしさ
    ENVY = "envy"           # 妬み・羨望


class ExpressionLayer(Enum):
    """感情表現の5層分類"""
    PHYSICAL_REACTION = "physical_reaction"    # 身体反応（基本）
    VISCERAL_SENSATION = "visceral_sensation"  # 内臓感覚
    CARDIO_RESPIRATORY = "cardio_respiratory"  # 心拍・呼吸系
    NEUROLOGICAL_DISTORTION = "neurological_distortion"  # 神経系・感覚歪み
    METAPHORICAL_SYMBOLIC = "metaphorical_symbolic"  # 比喻・象徴


@dataclass
class EmotionExpression:
    """単一感情の表現パターン

    Attributes:
        emotion: 感情カテゴリ
        intensity: 感情強度（1-10）
        layer: 表現層
        description: 具体的な表現内容
        literary_effect: 文学的効果
    """

    emotion: EmotionCategory
    intensity: int
    layer: ExpressionLayer
    description: str
    literary_effect: str = ""

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 1 <= self.intensity <= 10:
            msg = f"Intensity must be 1-10, got {self.intensity}"
            raise ValueError(msg)

    def get_intensity_modifier(self) -> str:
        """強度に応じた修飾語を取得"""
        if self.intensity <= 3:
            return "かすかに"
        if self.intensity <= 6:
            return "はっきりと"
        return "激しく"


@dataclass
class LayeredEmotionSystem:
    """感情表現5層システムの実装クラス

    直接的な感情表現（「眉間にしわ」「ため息」）を
    内的感覚（「胃が冷える」「心臓が嫌なリズム」）に置換する
    """

    def __init__(self) -> None:
        """5層別の表現パターンを初期化"""
        self.expression_patterns = self._initialize_expression_patterns()

    def _initialize_expression_patterns(self) -> dict[ExpressionLayer, dict[EmotionCategory, list[str]]]:
        """5層別の表現パターンを初期化"""
        return {
            ExpressionLayer.PHYSICAL_REACTION: {
                EmotionCategory.JOY: [
                    "頬の筋肉がじんわりと緩む",
                    "肩の力がふっと抜ける",
                    "足音が軽やかになる"
                ],
                EmotionCategory.ANGER: [
                    "拳がじりじりと震える",
                    "顎の筋肉がこわばる",
                    "歩幅が荒くなる"
                ],
                EmotionCategory.SADNESS: [
                    "肩がくたりと落ちる",
                    "視線が自然と下を向く",
                    "身体が小さく縮こまる"
                ],
                EmotionCategory.ANXIETY: [
                    "指先がそわそわと動く",
                    "足がむずむずとする",
                    "姿勢が前のめりになる"
                ]
            },

            ExpressionLayer.VISCERAL_SENSATION: {
                EmotionCategory.JOY: [
                    "胸の奥が暖かく広がる",
                    "お腹がふんわりと軽くなる",
                    "背中にじんわりとした暖かさが宿る"
                ],
                EmotionCategory.ANGER: [
                    "腹の底でマグマが煮えたぎる",
                    "胃袋がぎゅうぎゅうと縮む",
                    "内臓が重く沈み込む"
                ],
                EmotionCategory.SADNESS: [
                    "胸の真ん中がずうんと重くなる",
                    "お腹の底が冷たく空虚になる",
                    "胃が石のように固まる"
                ],
                EmotionCategory.ANXIETY: [
                    "胃が冷えるような感覚",
                    "腹の底がずんと重くなる",
                    "内臓がひっくり返りそうになる"
                ]
            },

            ExpressionLayer.CARDIO_RESPIRATORY: {
                EmotionCategory.JOY: [
                    "心臓が軽やかなリズムで跳ねる",
                    "呼吸が深く、ゆったりとなる",
                    "鼓動が穏やかで力強い"
                ],
                EmotionCategory.ANGER: [
                    "心臓が嫌なリズムで跳ねた",
                    "呼吸が荒く、浅くなる",
                    "脈拍がドクドクと耳に響く"
                ],
                EmotionCategory.SADNESS: [
                    "心臓がゆっくりと沈む",
                    "呼吸が細く、途切れがちになる",
                    "鼓動が遠くかすかに聞こえる"
                ],
                EmotionCategory.ANXIETY: [
                    "心臓がバクバクと不規則に打つ",
                    "息が浅く、早くなる",
                    "鼓動が妙に大きく感じられる"
                ]
            },

            ExpressionLayer.NEUROLOGICAL_DISTORTION: {
                EmotionCategory.JOY: [
                    "世界がキラキラと輝いて見える",
                    "時間がゆったりと流れる感覚",
                    "音がクリアに、美しく聞こえる"
                ],
                EmotionCategory.ANGER: [
                    "視界の端がぼんやりと赤く染まる",
                    "音が妙にとがって聞こえる",
                    "時間がぎこちなく進む感じ"
                ],
                EmotionCategory.SADNESS: [
                    "世界がモノクロに見える錯覚",
                    "音が遠くくぐもって聞こえる",
                    "時間が重たく引き延ばされる"
                ],
                EmotionCategory.ANXIETY: [
                    "時間が止まったような錯覚",
                    "音が遠くなる感じ",
                    "周囲がぼんやりとかすんで見える"
                ]
            },

            ExpressionLayer.METAPHORICAL_SYMBOLIC: {
                EmotionCategory.JOY: [
                    "心の中で花が咲く音がした",
                    "胸に小さな太陽が宿る",
                    "魂が軽やかに舞い踊る"
                ],
                EmotionCategory.ANGER: [
                    "頭の中を嵐が駆け抜ける",
                    "胸で炎が燃え盛る",
                    "心の奥で雷が轟く"
                ],
                EmotionCategory.SADNESS: [
                    "心の奥で何かが崩れ落ちる音がした",
                    "魂に霧がかかる",
                    "胸に重い石が積まれる"
                ],
                EmotionCategory.ANXIETY: [
                    "頭の中で警報が鳴り響く",
                    "心に暗い雲がたちこめる",
                    "胸で小さな竜巻が渦巻く"
                ]
            }
        }

    def get_expression(
        self,
        emotion: EmotionCategory,
        intensity: int,
        preferred_layer: ExpressionLayer | None = None
    ) -> EmotionExpression:
        """指定された感情・強度に適した表現を生成

        Args:
            emotion: 感情カテゴリ
            intensity: 強度（1-10）
            preferred_layer: 優先する表現層

        Returns:
            適切な感情表現
        """
        # 強度に応じて表現層を決定
        if preferred_layer is None:
            if intensity <= 3:
                preferred_layer = ExpressionLayer.PHYSICAL_REACTION
            elif intensity <= 6:
                preferred_layer = ExpressionLayer.VISCERAL_SENSATION
            elif intensity <= 8:
                preferred_layer = ExpressionLayer.CARDIO_RESPIRATORY
            else:
                preferred_layer = ExpressionLayer.NEUROLOGICAL_DISTORTION

        # 表現パターンから選択
        patterns = self.expression_patterns[preferred_layer].get(emotion, ["（表現パターン未定義）"])
        description = patterns[0] if patterns else "（表現なし）"

        return EmotionExpression(
            emotion=emotion,
            intensity=intensity,
            layer=preferred_layer,
            description=description,
            literary_effect=f"{preferred_layer.value}による{emotion.value}の{intensity}レベル表現"
        )

    def get_layered_expressions(
        self,
        emotion: EmotionCategory,
        intensity: int,
        layer_count: int = 3
    ) -> list[EmotionExpression]:
        """複数層を組み合わせた表現を生成

        Args:
            emotion: 感情カテゴリ
            intensity: 強度（1-10）
            layer_count: 使用する層数（1-5）

        Returns:
            複数層の表現リスト
        """
        expressions = []

        # 強度に応じて使用する層を決定
        if layer_count >= 1:
            expressions.append(self.get_expression(emotion, intensity, ExpressionLayer.VISCERAL_SENSATION))
        if layer_count >= 2 and intensity >= 4:
            expressions.append(self.get_expression(emotion, intensity, ExpressionLayer.CARDIO_RESPIRATORY))
        if layer_count >= 3 and intensity >= 6:
            expressions.append(self.get_expression(emotion, intensity, ExpressionLayer.NEUROLOGICAL_DISTORTION))
        if layer_count >= 4 and intensity >= 8:
            expressions.append(self.get_expression(emotion, intensity, ExpressionLayer.METAPHORICAL_SYMBOLIC))
        if layer_count >= 5:
            expressions.append(self.get_expression(emotion, intensity, ExpressionLayer.PHYSICAL_REACTION))

        return expressions

    def convert_direct_to_embodied(self, direct_expression: str) -> list[str]:
        """直接的表現を身体化描写に変換

        Args:
            direct_expression: 直接的な表現（例：「眉間にしわ」「ため息」）

        Returns:
            身体化された表現のリスト
        """
        conversion_map = {
            "眉間にしわ": [
                "額の奥が重く沈む",
                "頭蓋骨の中で何かが締め付けられる感覚",
                "こめかみがじんじんと疼く"
            ],
            "ため息": [
                "胸の中の空気がゆっくりと抜けていく",
                "肺の底から重いものが湧き上がる",
                "呼吸が深く、長くなる"
            ],
            "肩を落とす": [
                "背骨に重いものがのしかかる感覚",
                "肩甲骨がゆっくりと沈んでいく",
                "上半身が自重に引かれる"
            ],
            "頭を抱える": [
                "頭蓋骨の中で嵐が巻いている感じ",
                "こめかみが脈打つように痛む",
                "思考が重い靄に包まれる"
            ],
            "胸が痛い": [
                "胸の中央で何かがきゅっと縮む",
                "心臓の周りが冷たく締め付けられる",
                "胸骨の裏側がずきんと疼く"
            ]
        }

        return conversion_map.get(direct_expression, [f"《{direct_expression}の身体化表現》"])

    def generate_complex_emotion_expression(
        self,
        primary_emotion: EmotionCategory,
        secondary_emotion: EmotionCategory,
        intensity: int
    ) -> list[EmotionExpression]:
        """複合感情の表現を生成

        Args:
            primary_emotion: 主感情
            secondary_emotion: 副感情
            intensity: 全体強度

        Returns:
            複合感情を表現するExpressionのリスト
        """
        expressions = []

        # 主感情の表現
        primary_expr = self.get_expression(primary_emotion, intensity)
        expressions.append(primary_expr)

        # 副感情の表現（強度を少し下げる）
        secondary_intensity = max(1, intensity - 2)
        secondary_expr = self.get_expression(secondary_emotion, secondary_intensity)
        expressions.append(secondary_expr)

        # 複合感情特有の表現を追加
        if primary_emotion == EmotionCategory.JOY and secondary_emotion == EmotionCategory.SADNESS:
            complex_expr = EmotionExpression(
                emotion=primary_emotion,
                intensity=intensity,
                layer=ExpressionLayer.METAPHORICAL_SYMBOLIC,
                description="嬉しいはずなのに胸の奥が痛む",
                literary_effect="喜びと悲しみの複合表現"
            )
            expressions.append(complex_expr)

        return expressions


@dataclass
class EmotionExpressionLibrary:
    """感情表現ライブラリの統合管理クラス

    A38で定義される感情表現リファレンスを実装・管理
    """

    def __init__(self) -> None:
        """ライブラリを初期化"""
        self.layered_system = LayeredEmotionSystem()
        self.forbidden_expressions = self._initialize_forbidden_expressions()
        self.golden_expressions = self._initialize_golden_expressions()

    def _initialize_forbidden_expressions(self) -> list[str]:
        """禁止表現リストを初期化（直接的すぎる表現）"""
        return [
            "嬉しそうに笑った",
            "悲しそうな顔をした",
            "怒ったように言った",
            "困ったような表情",
            "眉間にしわを寄せた",
            "ため息をついた",
            "首をかしげた",
            "肩をすくめた"
        ]

    def _initialize_golden_expressions(self) -> dict[str, list[str]]:
        """Golden Sample由来の効果的表現パターンを初期化"""
        return {
            "承認への渇望": [
                "胸の奥で何かが乾いている",
                "心の隙間が風を呼ぶ",
                "魂に小さな穴が空いている感じ"
            ],
            "承認の充足": [
                "胸の奥が暖かい光で満たされる",
                "心の器がゆっくりと満ちていく",
                "魂の隙間がじんわりと埋まっていく"
            ],
            "ギャップからくる困惑": [
                "頭の中で何かの歯車が外れた音がする",
                "思考の回路がショートする感覚",
                "理解という道筋が霧に包まれる"
            ],
            "即断への確信": [
                "心の芯が一本筋として通る",
                "迷いという霧が晴れ渡る",
                "決断の重さが背骨に宿る"
            ]
        }

    def validate_expression(self, expression: str) -> tuple[bool, str]:
        """表現の妥当性をチェック

        Args:
            expression: チェックする表現

        Returns:
            (妥当性, フィードバックメッセージ)
        """
        # 禁止表現チェック
        for forbidden in self.forbidden_expressions:
            if forbidden in expression:
                alternatives = self.layered_system.convert_direct_to_embodied(forbidden)
                return False, f"直接的表現「{forbidden}」は避けてください。代替案: {alternatives[0]}"

        # 長さチェック
        if len(expression) < 5:
            return False, "表現が短すぎます。具体的な身体感覚を含めてください"

        # 身体化要素の確認
        body_keywords = ["胸", "心", "胃", "腹", "頭", "背", "肺", "心臓", "内臓", "骨"]
        has_body_element = any(keyword in expression for keyword in body_keywords)

        if not has_body_element:
            return False, "身体感覚が含まれていません。内臓感覚や身体反応を追加してください"

        return True, "適切な表現です"

    def get_expression_recommendations(
        self,
        emotion: EmotionCategory,
        intensity: int,
        context: str = ""
    ) -> dict:
        """表現推奨を生成

        Args:
            emotion: 感情カテゴリ
            intensity: 強度
            context: 文脈情報

        Returns:
            推奨表現の辞書
        """
        recommendations = {
            "layered_expressions": self.layered_system.get_layered_expressions(emotion, intensity),
            "golden_patterns": [],
            "context_specific": []
        }

        # Golden Sample由来の推奨
        if emotion in [EmotionCategory.JOY, EmotionCategory.SATISFACTION]:
            recommendations["golden_patterns"].extend(self.golden_expressions["承認の充足"])
        elif emotion in [EmotionCategory.ANXIETY, EmotionCategory.DESPAIR]:
            recommendations["golden_patterns"].extend(self.golden_expressions["承認への渇望"])

        # 文脈特化推奨
        if "会話" in context:
            recommendations["context_specific"].extend([
                "言葉が胸の中で重く響く",
                "声が心の奥深くに染み込む",
                "台詞が頭の中でリフレインする"
            ])

        return recommendations

    def add_expression(
        self,
        category: str,
        expression: str,
        layer: str = "VISCERAL_SENSATION",
        intensity: int = 5
    ) -> bool:
        """感情表現をライブラリに追加

        conversation_design_service.py:211で呼び出される表現追加メソッド

        Args:
            category: 感情カテゴリ
            expression: 追加する表現
            layer: 表現レイヤー（デフォルト: VISCERAL_SENSATION）
            intensity: 強度（デフォルト: 5）

        Returns:
            追加成功可否
        """
        # 表現の妥当性チェック
        is_valid, feedback = self.validate_expression(expression)
        if not is_valid:
            return False

        # カテゴリが存在しない場合は新規追加
        if category not in self.golden_expressions:
            self.golden_expressions[category] = []

        # 重複チェック
        if expression not in self.golden_expressions[category]:
            self.golden_expressions[category].append(expression)

        return True
