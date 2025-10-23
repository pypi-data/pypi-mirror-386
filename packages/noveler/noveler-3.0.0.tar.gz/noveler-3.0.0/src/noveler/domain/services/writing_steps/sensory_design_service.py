"""STEP 10: 五感描写設計サービス

A38執筆プロンプトガイドのSTEP10「五感描写設計」を実装するサービス。
視覚・聴覚・嗅覚・味覚・触覚の五感を活用した豊かな描写設計を行い、
読者の没入感を高める表現を生成します。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from noveler.application.services.stepwise_execution_service import BaseWritingStep
from noveler.domain.models.project_model import ProjectModel
from noveler.domain.services.configuration_manager_service import ConfigurationManagerService


class SenseType(Enum):
    """五感の種類"""
    VISUAL = "visual"  # 視覚
    AUDITORY = "auditory"  # 聴覚
    OLFACTORY = "olfactory"  # 嗅覚
    GUSTATORY = "gustatory"  # 味覚
    TACTILE = "tactile"  # 触覚


class SensoryIntensity(Enum):
    """五感の強度"""
    SUBTLE = "subtle"  # 微細
    MODERATE = "moderate"  # 中程度
    STRONG = "strong"  # 強い
    OVERWHELMING = "overwhelming"  # 圧倒的


class SensoryContext(Enum):
    """五感描写のコンテキスト"""
    ENVIRONMENT = "environment"  # 環境描写
    CHARACTER = "character"  # キャラクター描写
    ACTION = "action"  # 行動描写
    EMOTION = "emotion"  # 感情描写
    ATMOSPHERE = "atmosphere"  # 雰囲気描写
    TENSION = "tension"  # 緊張感描写


@dataclass
class SensoryElement:
    """五感描写要素"""
    element_id: str
    sense_type: SenseType
    intensity: SensoryIntensity
    context: SensoryContext
    description: str
    trigger: str  # 何がこの感覚を引き起こすか
    effect: str  # 読者・キャラクターへの効果
    literary_device: str  # 使用する文学技法
    example_phrases: list[str]  # 実用例文
    emotional_impact: str  # 感情的影響
    scene_position: str  # シーン内での位置
    duration: str  # 持続時間
    associated_memories: list[str]  # 関連記憶


@dataclass
class SensoryLayer:
    """五感レイヤー"""
    layer_id: str
    layer_name: str
    primary_senses: list[SenseType]  # 主要感覚
    secondary_senses: list[SenseType]  # 補助感覚
    layering_purpose: str  # レイヤリングの目的
    interaction_effects: dict[SenseType, list[str]]  # 感覚間相互作用
    progression: list[SensoryElement]  # 感覚の進行
    climax_element: SensoryElement | None  # クライマックス要素


@dataclass
class SensoryPalette:
    """五感パレット"""
    palette_id: str
    scene_type: str
    dominant_sense: SenseType
    sense_distribution: dict[SenseType, float]  # 各感覚の割合
    color_scheme: list[str]  # 視覚の色彩
    sound_profile: list[str]  # 聴覚の音響プロファイル
    scent_profile: list[str]  # 嗅覚の香りプロファイル
    taste_profile: list[str]  # 味覚のプロファイル
    texture_profile: list[str]  # 触覚のテクスチャ
    synesthetic_connections: dict[str, str]  # 共感覚的つながり


@dataclass
class EmotionalSensoryMapping:
    """感情と五感のマッピング"""
    emotion: str
    primary_sensory_associations: dict[SenseType, list[str]]
    intensity_correlation: dict[SensoryIntensity, str]  # 強度と感情の相関
    contextual_variations: dict[SensoryContext, list[str]]
    cultural_considerations: list[str]  # 文化的配慮


@dataclass
class SensoryProgression:
    """五感描写の進行"""
    progression_id: str
    scene_phases: list[str]
    sensory_journey: list[SensoryElement]
    transition_techniques: list[str]  # 移行技法
    build_up_strategy: str  # 積み上げ戦略
    climax_design: SensoryElement
    resolution_approach: str  # 解決手法


@dataclass
class SensoryDesignReport:
    """五感描写設計レポート"""
    design_id: str
    episode_number: int
    design_timestamp: datetime
    sensory_elements: list[SensoryElement]
    sensory_layers: list[SensoryLayer]
    sensory_palettes: list[SensoryPalette]
    emotional_mappings: list[EmotionalSensoryMapping]
    sensory_progressions: list[SensoryProgression]
    balance_analysis: dict[SenseType, float]  # バランス分析
    immersion_score: float  # 没入感スコア
    design_summary: str
    implementation_guidelines: list[str]
    design_metadata: dict[str, Any]


@dataclass
class SensoryDesignConfig:
    """五感描写設計設定"""
    enable_visual_design: bool = True
    enable_auditory_design: bool = True
    enable_olfactory_design: bool = True
    enable_gustatory_design: bool = True
    enable_tactile_design: bool = True
    preferred_intensity: SensoryIntensity = SensoryIntensity.MODERATE
    balance_target: dict[SenseType, float] = None  # デフォルトのバランス目標
    enable_synesthesia: bool = True  # 共感覚表現
    cultural_sensitivity: bool = True  # 文化的感受性
    max_elements_per_scene: int = 15
    enable_layered_design: bool = True


class SensoryDesignService(BaseWritingStep):
    """STEP 10: 五感描写設計サービス

    五感（視覚・聴覚・嗅覚・味覚・触覚）を活用した豊かな描写設計を行い、
    読者の没入感を高める表現を生成するサービス。
    A38ガイドのSTEP10「五感描写設計」を実装。
    """

    def __init__(
        self,
        config_manager: ConfigurationManagerService | None = None,
        path_service: Any | None = None,
        file_system_service: Any | None = None
    ) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._path_service = path_service
        self._file_system = file_system_service

        # デフォルト設定の初期化
        self._design_config = SensoryDesignConfig()
        if self._design_config.balance_target is None:
            self._design_config.balance_target = {
                SenseType.VISUAL: 0.40,      # 視覚40%
                SenseType.AUDITORY: 0.25,    # 聴覚25%
                SenseType.TACTILE: 0.15,     # 触覚15%
                SenseType.OLFACTORY: 0.12,   # 嗅覚12%
                SenseType.GUSTATORY: 0.08    # 味覚8%
            }

        # 五感描写テンプレート
        self._sensory_templates = self._initialize_sensory_templates()
        self._emotional_sensory_db = self._initialize_emotional_sensory_database()

    @abstractmethod
    def get_step_name(self) -> str:
        """ステップ名を取得"""
        return "五感描写設計"

    @abstractmethod
    def get_step_description(self) -> str:
        """ステップの説明を取得"""
        return "五感を活用した豊かな描写設計を行い、読者の没入感を高める表現を生成します"

    @abstractmethod
    def execute_step(self, context: dict[str, Any]) -> dict[str, Any]:
        """STEP 10: 五感描写設計の実行

        Args:
            context: 実行コンテキスト

        Returns:
            五感描写設計結果を含むコンテキスト
        """
        try:
            episode_number = context.get("episode_number")
            project = context.get("project")

            if not episode_number or not project:
                msg = "episode_numberまたはprojectが指定されていません"
                raise ValueError(msg)

            # 五感描写設計の実行
            sensory_design = self._execute_sensory_design(
                episode_number=episode_number,
                project=project,
                context=context
            )

            # 結果をコンテキストに追加
            context["sensory_design"] = sensory_design
            context["sensory_design_completed"] = True

            return context

        except Exception as e:
            context["sensory_design_error"] = str(e)
            raise

    def _execute_sensory_design(
        self,
        episode_number: int,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> SensoryDesignReport:
        """五感描写設計の実行"""

        # シーンデータの分析
        scene_data = self._analyze_scene_data(context)

        # 感情データの分析
        emotion_data = self._analyze_emotion_data(context)

        # 五感要素の設計
        sensory_elements = self._design_sensory_elements(scene_data, emotion_data)

        # 五感レイヤーの構築
        sensory_layers = self._build_sensory_layers(sensory_elements, scene_data)

        # 五感パレットの生成
        sensory_palettes = self._generate_sensory_palettes(scene_data, sensory_elements)

        # 感情と五感のマッピング
        emotional_mappings = self._create_emotional_sensory_mappings(emotion_data, sensory_elements)

        # 五感描写の進行設計
        sensory_progressions = self._design_sensory_progressions(sensory_elements, scene_data)

        # バランス分析
        balance_analysis = self._analyze_sensory_balance(sensory_elements)

        # 没入感スコア計算
        immersion_score = self._calculate_immersion_score(
            sensory_elements, sensory_layers, balance_analysis
        )

        # レポート生成
        return self._generate_sensory_design_report(
            episode_number=episode_number,
            sensory_elements=sensory_elements,
            sensory_layers=sensory_layers,
            sensory_palettes=sensory_palettes,
            emotional_mappings=emotional_mappings,
            sensory_progressions=sensory_progressions,
            balance_analysis=balance_analysis,
            immersion_score=immersion_score
        )

    def _analyze_scene_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """シーンデータの分析"""
        scene_data = {
            "scene_settings": context.get("scene_setting", {}),
            "locations": [],
            "time_of_day": "unknown",
            "weather": "clear",
            "season": "spring",
            "indoor_outdoor": "unknown",
            "social_context": "private",
            "activity_type": "conversation",
            "mood": "neutral",
            "tension_level": "low"
        }

        # シーン設定からの情報抽出
        scene_setting = context.get("scene_setting", {})
        if scene_setting:
            scene_data.update({
                "locations": scene_setting.get("locations", []),
                "time_of_day": scene_setting.get("time_of_day", "unknown"),
                "weather": scene_setting.get("weather", "clear"),
                "season": scene_setting.get("season", "spring"),
                "indoor_outdoor": scene_setting.get("environment_type", "unknown"),
                "social_context": scene_setting.get("social_context", "private"),
                "mood": scene_setting.get("mood", "neutral")
            })

        # 他のコンテキストからの補完
        story_structure = context.get("story_structure", {})
        if story_structure:
            tension_info = story_structure.get("tension_arc", {})
            scene_data["tension_level"] = tension_info.get("current_level", "low")

        return scene_data

    def _analyze_emotion_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """感情データの分析"""
        emotion_data = {
            "character_emotions": {},
            "dominant_emotion": "neutral",
            "emotion_intensity": "moderate",
            "emotion_progression": [],
            "emotional_conflicts": [],
            "target_reader_emotion": "engagement"
        }

        # 感情曲線データから抽出
        emotion_curve = context.get("emotion_curve", {})
        if emotion_curve:
            emotion_data.update({
                "character_emotions": emotion_curve.get("character_emotions", {}),
                "dominant_emotion": emotion_curve.get("dominant_emotion", "neutral"),
                "emotion_intensity": emotion_curve.get("intensity", "moderate"),
                "emotion_progression": emotion_curve.get("progression", []),
                "target_reader_emotion": emotion_curve.get("reader_target", "engagement")
            })

        return emotion_data

    def _design_sensory_elements(
        self,
        scene_data: dict[str, Any],
        emotion_data: dict[str, Any]
    ) -> list[SensoryElement]:
        """五感要素の設計"""
        elements = []

        # 各感覚タイプごとに要素を生成
        for sense_type in SenseType:
            if self._is_sense_enabled(sense_type):
                sense_elements = self._generate_sense_specific_elements(
                    sense_type, scene_data, emotion_data
                )
                elements.extend(sense_elements)

        # 要素の優先順位付けと選択
        prioritized_elements = self._prioritize_sensory_elements(
            elements, scene_data, emotion_data
        )

        # 最大要素数での制限
        max_elements = self._design_config.max_elements_per_scene
        return prioritized_elements[:max_elements]


    def _generate_sense_specific_elements(
        self,
        sense_type: SenseType,
        scene_data: dict[str, Any],
        emotion_data: dict[str, Any]
    ) -> list[SensoryElement]:
        """特定の感覚タイプの要素生成"""
        elements = []

        # シーンタイプと感情に基づいたテンプレート選択
        templates = self._get_sensory_templates(sense_type, scene_data, emotion_data)

        for i, template in enumerate(templates[:3]):  # 最大3要素per感覚
            element = SensoryElement(
                element_id=f"{sense_type.value}_{i}",
                sense_type=sense_type,
                intensity=self._determine_intensity(sense_type, scene_data, emotion_data),
                context=self._determine_context(scene_data),
                description=template["description"],
                trigger=template["trigger"],
                effect=template["effect"],
                literary_device=template["literary_device"],
                example_phrases=template["example_phrases"],
                emotional_impact=self._calculate_emotional_impact(
                    sense_type, emotion_data, template
                ),
                scene_position=template["scene_position"],
                duration=template["duration"],
                associated_memories=template.get("associated_memories", [])
            )
            elements.append(element)

        return elements

    def _build_sensory_layers(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> list[SensoryLayer]:
        """五感レイヤーの構築"""
        layers = []

        # 基本レイヤー（環境）
        environment_layer = self._build_environment_layer(sensory_elements, scene_data)
        if environment_layer:
            layers.append(environment_layer)

        # キャラクターレイヤー
        character_layer = self._build_character_layer(sensory_elements, scene_data)
        if character_layer:
            layers.append(character_layer)

        # アクションレイヤー
        action_layer = self._build_action_layer(sensory_elements, scene_data)
        if action_layer:
            layers.append(action_layer)

        # 感情レイヤー
        emotion_layer = self._build_emotion_layer(sensory_elements, scene_data)
        if emotion_layer:
            layers.append(emotion_layer)

        return layers

    def _generate_sensory_palettes(
        self,
        scene_data: dict[str, Any],
        sensory_elements: list[SensoryElement]
    ) -> list[SensoryPalette]:
        """五感パレットの生成"""
        palettes = []

        # シーンタイプ別パレット生成
        scene_types = self._identify_scene_types(scene_data)

        for scene_type in scene_types:
            palette = self._create_scene_palette(scene_type, sensory_elements, scene_data)
            palettes.append(palette)

        return palettes

    def _create_emotional_sensory_mappings(
        self,
        emotion_data: dict[str, Any],
        sensory_elements: list[SensoryElement]
    ) -> list[EmotionalSensoryMapping]:
        """感情と五感のマッピング作成"""
        mappings = []

        # 主要感情のマッピング
        dominant_emotion = emotion_data.get("dominant_emotion", "neutral")
        main_mapping = self._create_emotion_mapping(dominant_emotion, sensory_elements)
        mappings.append(main_mapping)

        # キャラクター別感情マッピング
        character_emotions = emotion_data.get("character_emotions", {})
        for character, emotion in character_emotions.items():
            if emotion != dominant_emotion:
                char_mapping = self._create_emotion_mapping(
                    emotion, sensory_elements, character_context=character
                )
                mappings.append(char_mapping)

        return mappings

    def _design_sensory_progressions(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> list[SensoryProgression]:
        """五感描写の進行設計"""
        progressions = []

        # メインプログレッション
        main_progression = self._create_main_sensory_progression(sensory_elements, scene_data)
        progressions.append(main_progression)

        # サブプログレッション（必要に応じて）
        if len(sensory_elements) > 8:  # 要素が多い場合
            sub_progressions = self._create_sub_progressions(sensory_elements, scene_data)
            progressions.extend(sub_progressions)

        return progressions

    def _analyze_sensory_balance(
        self,
        sensory_elements: list[SensoryElement]
    ) -> dict[SenseType, float]:
        """五感バランスの分析"""
        balance = dict.fromkeys(SenseType, 0.0)

        if not sensory_elements:
            return balance

        # 各感覚の使用頻度計算
        for element in sensory_elements:
            balance[element.sense_type] += 1.0

        # 正規化（割合に変換）
        total = sum(balance.values())
        if total > 0:
            balance = {sense: count / total for sense, count in balance.items()}

        return balance

    def _calculate_immersion_score(
        self,
        sensory_elements: list[SensoryElement],
        sensory_layers: list[SensoryLayer],
        balance_analysis: dict[SenseType, float]
    ) -> float:
        """没入感スコアの計算"""

        # 要素の多様性スコア (0-0.3)
        diversity_score = len({element.sense_type for element in sensory_elements}) / len(SenseType) * 0.3

        # バランススコア (0-0.3)
        target_balance = self._design_config.balance_target
        balance_score = 1.0 - sum(
            abs(balance_analysis.get(sense, 0) - target_balance.get(sense, 0))
            for sense in SenseType
        ) / 2.0
        balance_score = max(0, balance_score) * 0.3

        # レイヤー複雑度スコア (0-0.2)
        layer_score = min(len(sensory_layers) / 4.0, 1.0) * 0.2

        # 強度バランススコア (0-0.2)
        intensities = [element.intensity for element in sensory_elements]
        intensity_variety = len(set(intensities)) / len(SensoryIntensity)
        intensity_score = intensity_variety * 0.2

        total_score = diversity_score + balance_score + layer_score + intensity_score
        return min(1.0, max(0.0, total_score))

    def _generate_sensory_design_report(
        self,
        episode_number: int,
        sensory_elements: list[SensoryElement],
        sensory_layers: list[SensoryLayer],
        sensory_palettes: list[SensoryPalette],
        emotional_mappings: list[EmotionalSensoryMapping],
        sensory_progressions: list[SensoryProgression],
        balance_analysis: dict[SenseType, float],
        immersion_score: float
    ) -> SensoryDesignReport:
        """五感描写設計レポートの生成"""

        # デザインサマリーの生成
        design_summary = self._generate_design_summary(
            sensory_elements, balance_analysis, immersion_score
        )

        # 実装ガイドラインの生成
        implementation_guidelines = self._generate_implementation_guidelines(
            sensory_elements, sensory_layers, immersion_score
        )

        return SensoryDesignReport(
            design_id=f"sensory_design_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            episode_number=episode_number,
            design_timestamp=datetime.now(tz=datetime.timezone.utc),
            sensory_elements=sensory_elements,
            sensory_layers=sensory_layers,
            sensory_palettes=sensory_palettes,
            emotional_mappings=emotional_mappings,
            sensory_progressions=sensory_progressions,
            balance_analysis=balance_analysis,
            immersion_score=immersion_score,
            design_summary=design_summary,
            implementation_guidelines=implementation_guidelines,
            design_metadata={
                "design_config": self._design_config.__dict__,
                "total_elements": len(sensory_elements),
                "total_layers": len(sensory_layers),
                "total_palettes": len(sensory_palettes)
            }
        )

    # ヘルパーメソッド実装

    def _initialize_sensory_templates(self) -> dict[str, Any]:
        """五感描写テンプレートの初期化"""
        return {
            SenseType.VISUAL: {
                "environment": [
                    {
                        "description": "自然光の美しい描写",
                        "trigger": "陽光・月光・星光",
                        "effect": "幻想的で神秘的な雰囲気",
                        "literary_device": "比喩・擬人法",
                        "example_phrases": ["金色に踊る陽だまり", "銀色の月光が頬を撫で"],
                        "scene_position": "シーン冒頭",
                        "duration": "継続的"
                    },
                    {
                        "description": "色彩豊かな風景描写",
                        "trigger": "季節・時間・天候",
                        "effect": "視覚的な美しさと情緒",
                        "literary_device": "色彩語・形容詞",
                        "example_phrases": ["深紅に染まる夕空", "新緑が風に揺れて"],
                        "scene_position": "背景設定",
                        "duration": "瞬間的"
                    }
                ],
                "character": [
                    {
                        "description": "表情・仕草の細やかな描写",
                        "trigger": "感情・心理状態",
                        "effect": "キャラクターの内面表現",
                        "literary_device": "動作動詞・形容詞",
                        "example_phrases": ["困ったように眉をひそめ", "安堵に満ちた微笑み"],
                        "scene_position": "対話中",
                        "duration": "瞬間的"
                    }
                ]
            },
            SenseType.AUDITORY: {
                "environment": [
                    {
                        "description": "自然音の豊かな表現",
                        "trigger": "風・雨・虫・鳥",
                        "effect": "環境の臨場感",
                        "literary_device": "擬音語・擬態語",
                        "example_phrases": ["さらさらと葉擦れの音", "ぽつりぽつりと雨粒が"],
                        "scene_position": "環境設定",
                        "duration": "継続的"
                    }
                ],
                "character": [
                    {
                        "description": "声の質感・トーン",
                        "trigger": "発話・感情表現",
                        "effect": "キャラクターの個性表現",
                        "literary_device": "音響表現・比喩",
                        "example_phrases": ["震える声で囁く", "張りのある明瞭な声"],
                        "scene_position": "対話",
                        "duration": "発話時"
                    }
                ]
            },
            # 他の感覚も同様に定義...
        }

    def _initialize_emotional_sensory_database(self) -> dict[str, Any]:
        """感情-五感データベースの初期化"""
        return {
            "happiness": {
                SenseType.VISUAL: ["明るい色彩", "輝き", "開放的な空間"],
                SenseType.AUDITORY: ["軽やかな音", "笑い声", "鈴の音"],
                SenseType.OLFACTORY: ["花の香り", "甘い香り", "新鮮な空気"],
                SenseType.GUSTATORY: ["甘味", "爽やかな味"],
                SenseType.TACTILE: ["暖かさ", "柔らかさ", "軽やかさ"]
            },
            "sadness": {
                SenseType.VISUAL: ["灰色", "暗さ", "下向きの視線"],
                SenseType.AUDITORY: ["雨音", "ため息", "静寂"],
                SenseType.OLFACTORY: ["湿った匂い", "古い匂い"],
                SenseType.GUSTATORY: ["苦味", "塩味"],
                SenseType.TACTILE: ["冷たさ", "重さ", "湿り気"]
            },
            "fear": {
                SenseType.VISUAL: ["影", "暗闇", "動くもの"],
                SenseType.AUDITORY: ["不気味な音", "心拍音", "足音"],
                SenseType.OLFACTORY: ["血の匂い", "腐敗臭", "金属臭"],
                SenseType.GUSTATORY: ["金属味", "酸味"],
                SenseType.TACTILE: ["冷や汗", "震え", "硬直"]
            }
        }

    def _is_sense_enabled(self, sense_type: SenseType) -> bool:
        """指定された感覚が有効かチェック"""
        return {
            SenseType.VISUAL: self._design_config.enable_visual_design,
            SenseType.AUDITORY: self._design_config.enable_auditory_design,
            SenseType.OLFACTORY: self._design_config.enable_olfactory_design,
            SenseType.GUSTATORY: self._design_config.enable_gustatory_design,
            SenseType.TACTILE: self._design_config.enable_tactile_design
        }.get(sense_type, True)

    def _get_sensory_templates(
        self,
        sense_type: SenseType,
        scene_data: dict[str, Any],
        emotion_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """五感テンプレートの取得"""
        templates = self._sensory_templates.get(sense_type, {})

        # シーンタイプに応じたテンプレート選択
        scene_context = self._determine_context(scene_data)
        context_templates = templates.get(scene_context.value, [])

        return context_templates if context_templates else []

    def _determine_intensity(
        self,
        sense_type: SenseType,
        scene_data: dict[str, Any],
        emotion_data: dict[str, Any]
    ) -> SensoryIntensity:
        """感覚強度の決定"""
        # 基本強度
        base_intensity = self._design_config.preferred_intensity

        # 緊張度による調整
        tension_level = scene_data.get("tension_level", "low")
        if tension_level == "high":
            return SensoryIntensity.STRONG
        if tension_level == "critical":
            return SensoryIntensity.OVERWHELMING

        # 感情強度による調整
        emotion_intensity = emotion_data.get("emotion_intensity", "moderate")
        if emotion_intensity == "high":
            return SensoryIntensity.STRONG
        if emotion_intensity == "overwhelming":
            return SensoryIntensity.OVERWHELMING

        return base_intensity

    def _determine_context(self, scene_data: dict[str, Any]) -> SensoryContext:
        """五感コンテキストの決定"""
        activity_type = scene_data.get("activity_type", "conversation")

        context_mapping = {
            "conversation": SensoryContext.CHARACTER,
            "action": SensoryContext.ACTION,
            "exploration": SensoryContext.ENVIRONMENT,
            "emotional": SensoryContext.EMOTION,
            "tense": SensoryContext.TENSION
        }

        return context_mapping.get(activity_type, SensoryContext.ATMOSPHERE)

    def _calculate_emotional_impact(
        self,
        sense_type: SenseType,
        emotion_data: dict[str, Any],
        template: dict[str, Any]
    ) -> str:
        """感情的影響の計算"""
        dominant_emotion = emotion_data.get("dominant_emotion", "neutral")

        # 感情-五感データベースから影響を取得
        emotion_sensory = self._emotional_sensory_db.get(dominant_emotion, {})
        sense_associations = emotion_sensory.get(sense_type, [])

        if sense_associations:
            return f"{dominant_emotion}を{', '.join(sense_associations[:2])}で表現し、読者の感情移入を促進"
        return "読者の感覚体験を豊かにし、物語への没入を深める"

    def _prioritize_sensory_elements(
        self,
        elements: list[SensoryElement],
        scene_data: dict[str, Any],
        emotion_data: dict[str, Any]
    ) -> list[SensoryElement]:
        """五感要素の優先順位付け"""

        def priority_score(element: SensoryElement) -> float:
            score = 0.0

            # 感覚タイプの基本重要度
            type_weights = {
                SenseType.VISUAL: 0.4,
                SenseType.AUDITORY: 0.25,
                SenseType.TACTILE: 0.15,
                SenseType.OLFACTORY: 0.12,
                SenseType.GUSTATORY: 0.08
            }
            score += type_weights.get(element.sense_type, 0.1)

            # 強度による重み
            intensity_weights = {
                SensoryIntensity.OVERWHELMING: 0.4,
                SensoryIntensity.STRONG: 0.3,
                SensoryIntensity.MODERATE: 0.2,
                SensoryIntensity.SUBTLE: 0.1
            }
            score += intensity_weights.get(element.intensity, 0.1)

            # コンテキストの適合性
            target_context = self._determine_context(scene_data)
            if element.context == target_context:
                score += 0.2

            return score

        # スコア順にソート
        return sorted(elements, key=priority_score, reverse=True)

    def _build_environment_layer(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> SensoryLayer | None:
        """環境レイヤーの構築"""
        env_elements = [e for e in sensory_elements if e.context == SensoryContext.ENVIRONMENT]
        if not env_elements:
            return None

        return SensoryLayer(
            layer_id="environment_layer",
            layer_name="環境描写レイヤー",
            primary_senses=[SenseType.VISUAL, SenseType.AUDITORY],
            secondary_senses=[SenseType.OLFACTORY, SenseType.TACTILE],
            layering_purpose="場面の雰囲気と環境設定の確立",
            interaction_effects={
                SenseType.VISUAL: ["色彩と光の相互作用"],
                SenseType.AUDITORY: ["環境音の重層化"]
            },
            progression=env_elements,
            climax_element=env_elements[0] if env_elements else None
        )

    def _build_character_layer(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> SensoryLayer | None:
        """キャラクターレイヤーの構築"""
        char_elements = [e for e in sensory_elements if e.context == SensoryContext.CHARACTER]
        if not char_elements:
            return None

        return SensoryLayer(
            layer_id="character_layer",
            layer_name="キャラクター描写レイヤー",
            primary_senses=[SenseType.VISUAL, SenseType.AUDITORY],
            secondary_senses=[SenseType.TACTILE],
            layering_purpose="キャラクターの個性と感情の表現",
            interaction_effects={
                SenseType.VISUAL: ["表情と仕草の連携"],
                SenseType.AUDITORY: ["声と言葉の調和"]
            },
            progression=char_elements,
            climax_element=char_elements[0] if char_elements else None
        )

    def _build_action_layer(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> SensoryLayer | None:
        """アクションレイヤーの構築"""
        action_elements = [e for e in sensory_elements if e.context == SensoryContext.ACTION]
        if not action_elements:
            return None

        return SensoryLayer(
            layer_id="action_layer",
            layer_name="アクション描写レイヤー",
            primary_senses=[SenseType.VISUAL, SenseType.AUDITORY, SenseType.TACTILE],
            secondary_senses=[SenseType.OLFACTORY],
            layering_purpose="動きと行動の臨場感創出",
            interaction_effects={
                SenseType.VISUAL: ["動きの視覚化"],
                SenseType.AUDITORY: ["動作音の表現"],
                SenseType.TACTILE: ["物理的感覚の伝達"]
            },
            progression=action_elements,
            climax_element=action_elements[0] if action_elements else None
        )

    def _build_emotion_layer(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> SensoryLayer | None:
        """感情レイヤーの構築"""
        emotion_elements = [e for e in sensory_elements if e.context == SensoryContext.EMOTION]
        if not emotion_elements:
            return None

        return SensoryLayer(
            layer_id="emotion_layer",
            layer_name="感情描写レイヤー",
            primary_senses=[SenseType.TACTILE, SenseType.VISUAL],
            secondary_senses=[SenseType.AUDITORY, SenseType.OLFACTORY],
            layering_purpose="感情の物理的表現と読者への伝達",
            interaction_effects={
                SenseType.TACTILE: ["身体感覚による感情表現"],
                SenseType.VISUAL: ["表情による内面描写"]
            },
            progression=emotion_elements,
            climax_element=emotion_elements[0] if emotion_elements else None
        )

    def _identify_scene_types(self, scene_data: dict[str, Any]) -> list[str]:
        """シーンタイプの特定"""
        scene_types = []

        # 基本タイプ
        activity_type = scene_data.get("activity_type", "conversation")
        scene_types.append(activity_type)

        # 環境タイプ
        indoor_outdoor = scene_data.get("indoor_outdoor", "unknown")
        if indoor_outdoor != "unknown":
            scene_types.append(indoor_outdoor)

        # 時間帯
        time_of_day = scene_data.get("time_of_day", "unknown")
        if time_of_day != "unknown":
            scene_types.append(time_of_day)

        return scene_types

    def _create_scene_palette(
        self,
        scene_type: str,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> SensoryPalette:
        """シーンパレットの作成"""

        # 感覚分布の計算
        sense_distribution = dict.fromkeys(SenseType, 0.0)
        for element in sensory_elements:
            sense_distribution[element.sense_type] += 1.0

        total = sum(sense_distribution.values())
        if total > 0:
            sense_distribution = {sense: count / total for sense, count in sense_distribution.items()}

        # 優勢感覚の特定
        dominant_sense = max(sense_distribution.keys(), key=lambda s: sense_distribution[s])

        return SensoryPalette(
            palette_id=f"palette_{scene_type}",
            scene_type=scene_type,
            dominant_sense=dominant_sense,
            sense_distribution=sense_distribution,
            color_scheme=self._generate_color_scheme(scene_type, scene_data),
            sound_profile=self._generate_sound_profile(scene_type, scene_data),
            scent_profile=self._generate_scent_profile(scene_type, scene_data),
            taste_profile=self._generate_taste_profile(scene_type, scene_data),
            texture_profile=self._generate_texture_profile(scene_type, scene_data),
            synesthetic_connections=self._generate_synesthetic_connections(scene_type)
        )

    def _create_emotion_mapping(
        self,
        emotion: str,
        sensory_elements: list[SensoryElement],
        character_context: str | None = None
    ) -> EmotionalSensoryMapping:
        """感情マッピングの作成"""

        # データベースから基本的な関連付けを取得
        emotion_sensory = self._emotional_sensory_db.get(emotion, {})

        return EmotionalSensoryMapping(
            emotion=emotion,
            primary_sensory_associations=emotion_sensory,
            intensity_correlation={
                SensoryIntensity.SUBTLE: "微細な感情の揺らぎ",
                SensoryIntensity.MODERATE: "明確な感情表現",
                SensoryIntensity.STRONG: "強い感情的インパクト",
                SensoryIntensity.OVERWHELMING: "感情の圧倒的表現"
            },
            contextual_variations={
                SensoryContext.ENVIRONMENT: [f"{emotion}を環境で表現"],
                SensoryContext.CHARACTER: [f"{emotion}をキャラクターの反応で表現"],
                SensoryContext.ACTION: [f"{emotion}を行動で表現"]
            },
            cultural_considerations=[
                "日本的な感性に配慮した表現",
                "読者の共感を呼ぶ普遍的な感覚"
            ]
        )

    def _create_main_sensory_progression(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> SensoryProgression:
        """メイン五感進行の作成"""

        # シーンフェーズの特定
        scene_phases = ["導入", "展開", "クライマックス", "解決"]

        # 要素の分散配置
        self._distribute_elements_to_phases(sensory_elements, scene_phases)

        return SensoryProgression(
            progression_id="main_progression",
            scene_phases=scene_phases,
            sensory_journey=sensory_elements,
            transition_techniques=[
                "感覚の重層化",
                "強度の段階的変化",
                "感覚の切り替え"
            ],
            build_up_strategy="段階的な感覚積み重ね",
            climax_design=self._select_climax_element(sensory_elements),
            resolution_approach="感覚の収束と余韻"
        )

    def _create_sub_progressions(
        self,
        sensory_elements: list[SensoryElement],
        scene_data: dict[str, Any]
    ) -> list[SensoryProgression]:
        """サブ進行の作成"""
        # 複雑なシーン用のサブ進行
        return []  # スタブ実装

    def _generate_design_summary(
        self,
        sensory_elements: list[SensoryElement],
        balance_analysis: dict[SenseType, float],
        immersion_score: float
    ) -> str:
        """デザインサマリーの生成"""

        total_elements = len(sensory_elements)
        dominant_sense = max(balance_analysis.keys(), key=lambda s: balance_analysis[s])

        summary_parts = [
            f"総計{total_elements}個の五感要素を設計。",
            f"主要感覚は{dominant_sense.value}（{balance_analysis[dominant_sense]:.1%}）。"
        ]

        if immersion_score >= 0.8:
            summary_parts.append("没入感の高い五感設計が完成しました。")
        elif immersion_score >= 0.6:
            summary_parts.append("バランスの良い五感設計です。")
        else:
            summary_parts.append("五感バランスの調整が推奨されます。")

        return " ".join(summary_parts)

    def _generate_implementation_guidelines(
        self,
        sensory_elements: list[SensoryElement],
        sensory_layers: list[SensoryLayer],
        immersion_score: float
    ) -> list[str]:
        """実装ガイドラインの生成"""
        guidelines = [
            "🎯 各五感要素を適切な場面で使用してください",
            "🎭 レイヤー構造を意識した描写の重層化を行ってください",
            "📝 例文を参考に具体的で魅力的な表現を心がけてください"
        ]

        if immersion_score < 0.6:
            guidelines.extend([
                "⚠️ 五感バランスの調整を検討してください",
                "🔄 感覚要素の追加や強度調整を行ってください"
            ])

        return guidelines

    # 各種プロファイル生成メソッド（スタブ実装）
    def _generate_color_scheme(self, scene_type: str, scene_data: dict[str, Any]) -> list[str]:
        return ["暖色系", "自然色"]

    def _generate_sound_profile(self, scene_type: str, scene_data: dict[str, Any]) -> list[str]:
        return ["環境音", "人の声"]

    def _generate_scent_profile(self, scene_type: str, scene_data: dict[str, Any]) -> list[str]:
        return ["花の香り", "自然の匂い"]

    def _generate_taste_profile(self, scene_type: str, scene_data: dict[str, Any]) -> list[str]:
        return ["甘味", "清涼感"]

    def _generate_texture_profile(self, scene_type: str, scene_data: dict[str, Any]) -> list[str]:
        return ["柔らかさ", "暖かさ"]

    def _generate_synesthetic_connections(self, scene_type: str) -> dict[str, str]:
        return {"color-sound": "色と音の協調", "texture-emotion": "質感と感情の連携"}

    def _distribute_elements_to_phases(
        self,
        elements: list[SensoryElement],
        phases: list[str]
    ) -> dict[str, list[SensoryElement]]:
        """要素のフェーズ分散配置"""
        distribution = {phase: [] for phase in phases}

        for i, element in enumerate(elements):
            phase_index = i % len(phases)
            distribution[phases[phase_index]].append(element)

        return distribution

    def _select_climax_element(
        self,
        sensory_elements: list[SensoryElement]
    ) -> SensoryElement:
        """クライマックス要素の選択"""
        # 最も強度の高い要素を選択
        return max(
            sensory_elements,
            key=lambda e: {
                SensoryIntensity.OVERWHELMING: 4,
                SensoryIntensity.STRONG: 3,
                SensoryIntensity.MODERATE: 2,
                SensoryIntensity.SUBTLE: 1
            }.get(e.intensity, 1),
            default=sensory_elements[0] if sensory_elements else None
        )
