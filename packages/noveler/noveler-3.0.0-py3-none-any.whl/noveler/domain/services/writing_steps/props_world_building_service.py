"""STEP 11: 小道具・世界観設計サービス

A38執筆プロンプトガイドのSTEP11「小道具・世界観設計」を実装するサービス。
物語世界の細部を構築し、小道具や環境要素を通じて世界観の一貫性と
リアリティを確保する設計を行います。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from noveler.application.services.stepwise_execution_service import BaseWritingStep
from noveler.domain.models.project_model import ProjectModel
from noveler.domain.services.configuration_manager_service import ConfigurationManagerService


class PropCategory(Enum):
    """小道具カテゴリー"""
    PERSONAL = "personal"  # 個人的な小道具
    FUNCTIONAL = "functional"  # 機能的道具
    DECORATIVE = "decorative"  # 装飾品
    SYMBOLIC = "symbolic"  # 象徴的道具
    MAGICAL = "magical"  # 魔法的道具
    TECHNOLOGICAL = "technological"  # 技術的道具
    CULTURAL = "cultural"  # 文化的道具
    HISTORICAL = "historical"  # 歴史的道具


class PropImportance(Enum):
    """小道具の重要度"""
    PLOT_CRITICAL = "plot_critical"  # プロット上重要
    CHARACTER_DEFINING = "character_defining"  # キャラクター定義に重要
    WORLD_BUILDING = "world_building"  # 世界観構築に重要
    ATMOSPHERIC = "atmospheric"  # 雰囲気作りに重要
    BACKGROUND = "background"  # 背景的存在


class WorldElement(Enum):
    """世界観要素タイプ"""
    GEOGRAPHY = "geography"  # 地理
    ARCHITECTURE = "architecture"  # 建築
    TECHNOLOGY = "technology"  # 技術
    CULTURE = "culture"  # 文化
    POLITICS = "politics"  # 政治
    ECONOMICS = "economics"  # 経済
    RELIGION = "religion"  # 宗教
    HISTORY = "history"  # 歴史
    NATURAL_LAW = "natural_law"  # 自然法則
    SOCIAL_SYSTEM = "social_system"  # 社会システム


@dataclass
class PropDesign:
    """小道具設計"""
    prop_id: str
    name: str
    category: PropCategory
    importance: PropImportance
    description: str
    physical_properties: dict[str, str]  # 物理的特性
    functional_properties: dict[str, str]  # 機能的特性
    symbolic_meaning: str  # 象徴的意味
    cultural_significance: str  # 文化的意義
    historical_background: str  # 歴史的背景
    owner_relationship: dict[str, str]  # 所有者との関係
    usage_context: list[str]  # 使用文脈
    story_role: str  # 物語での役割
    visual_design: dict[str, Any]  # 視覚的デザイン
    interaction_rules: list[str]  # 相互作用ルール
    maintenance_requirements: list[str]  # メンテナンス要件
    degradation_pattern: str  # 劣化パターン


@dataclass
class WorldSystemDesign:
    """世界システム設計"""
    system_id: str
    system_name: str
    element_type: WorldElement
    core_principles: list[str]  # 核となる原理
    operational_rules: list[str]  # 運用ルール
    limitations: list[str]  # 制限事項
    exceptions: list[str]  # 例外事項
    historical_evolution: list[str]  # 歴史的発展
    current_state: str  # 現在の状態
    future_trajectory: str  # 将来の軌道
    interaction_with_other_systems: dict[str, str]  # 他システムとの相互作用
    character_impact: dict[str, str]  # キャラクターへの影響
    plot_integration: list[str]  # プロット統合点
    consistency_requirements: list[str]  # 一貫性要件


@dataclass
class EnvironmentDetail:
    """環境詳細設計"""
    detail_id: str
    location: str
    detail_type: str  # 詳細タイプ
    description: str
    sensory_aspects: dict[str, list[str]]  # 感覚的側面
    functional_aspects: list[str]  # 機能的側面
    aesthetic_aspects: list[str]  # 美的側面
    cultural_context: str  # 文化的文脈
    historical_significance: str  # 歴史的意義
    maintenance_state: str  # 保守状態
    change_patterns: list[str]  # 変化パターン
    interaction_possibilities: list[str]  # 相互作用可能性


@dataclass
class ConsistencyRule:
    """一貫性ルール"""
    rule_id: str
    rule_name: str
    scope: str  # 適用範囲
    description: str
    conditions: list[str]  # 条件
    requirements: list[str]  # 要求事項
    violations: list[str]  # 違反例
    enforcement_methods: list[str]  # 実施方法
    flexibility: float  # 柔軟性 (0-1)
    priority: int  # 優先度


@dataclass
class WorldBuildingReport:
    """世界観構築レポート"""
    report_id: str
    episode_number: int
    build_timestamp: datetime
    prop_designs: list[PropDesign]
    world_systems: list[WorldSystemDesign]
    environment_details: list[EnvironmentDetail]
    consistency_rules: list[ConsistencyRule]
    integration_analysis: dict[str, Any]  # 統合分析
    consistency_score: float  # 一貫性スコア
    immersion_score: float  # 没入感スコア
    realism_score: float  # リアリティスコア
    build_summary: str
    implementation_guidelines: list[str]
    build_metadata: dict[str, Any]


@dataclass
class WorldBuildingConfig:
    """世界観構築設定"""
    enable_prop_design: bool = True
    enable_world_system_design: bool = True
    enable_environment_detailing: bool = True
    enable_consistency_checking: bool = True
    prop_detail_level: str = "moderate"  # minimal, moderate, detailed
    world_system_complexity: str = "moderate"  # simple, moderate, complex
    consistency_strictness: float = 0.8  # 一貫性の厳格さ (0-1)
    cultural_authenticity: bool = True
    historical_depth: bool = True
    max_props_per_scene: int = 10
    max_world_systems: int = 8


class PropsWorldBuildingService(BaseWritingStep):
    """STEP 11: 小道具・世界観設計サービス

    物語世界の細部を構築し、小道具や環境要素を通じて
    世界観の一貫性とリアリティを確保するサービス。
    A38ガイドのSTEP11「小道具・世界観設計」を実装。
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
        self._build_config = WorldBuildingConfig()

        # 世界観構築テンプレート
        self._prop_templates = self._initialize_prop_templates()
        self._world_system_templates = self._initialize_world_system_templates()
        self._consistency_rules_db = self._initialize_consistency_rules()

    @abstractmethod
    def get_step_name(self) -> str:
        """ステップ名を取得"""
        return "小道具・世界観設計"

    @abstractmethod
    def get_step_description(self) -> str:
        """ステップの説明を取得"""
        return "物語世界の細部を構築し、小道具・環境要素による世界観の一貫性とリアリティを確保します"

    @abstractmethod
    def execute_step(self, context: dict[str, Any]) -> dict[str, Any]:
        """STEP 11: 小道具・世界観設計の実行

        Args:
            context: 実行コンテキスト

        Returns:
            小道具・世界観設計結果を含むコンテキスト
        """
        try:
            episode_number = context.get("episode_number")
            project = context.get("project")

            if not episode_number or not project:
                msg = "episode_numberまたはprojectが指定されていません"
                raise ValueError(msg)

            # 小道具・世界観設計の実行
            world_building = self._execute_world_building(
                episode_number=episode_number,
                project=project,
                context=context
            )

            # 結果をコンテキストに追加
            context["world_building"] = world_building
            context["world_building_completed"] = True

            return context

        except Exception as e:
            context["world_building_error"] = str(e)
            raise

    def _execute_world_building(
        self,
        episode_number: int,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> WorldBuildingReport:
        """小道具・世界観設計の実行"""

        # 既存世界観データの分析
        existing_world = self._analyze_existing_world_data(project, context)

        # シーン要件の分析
        scene_requirements = self._analyze_scene_requirements(context)

        # 小道具設計
        prop_designs = []
        if self._build_config.enable_prop_design:
            prop_designs = self._design_props(scene_requirements, existing_world)

        # 世界システム設計
        world_systems = []
        if self._build_config.enable_world_system_design:
            world_systems = self._design_world_systems(scene_requirements, existing_world)

        # 環境詳細設計
        environment_details = []
        if self._build_config.enable_environment_detailing:
            environment_details = self._design_environment_details(scene_requirements, existing_world)

        # 一貫性ルールの構築
        consistency_rules = []
        if self._build_config.enable_consistency_checking:
            consistency_rules = self._build_consistency_rules(
                prop_designs, world_systems, environment_details, existing_world
            )

        # 統合分析
        integration_analysis = self._perform_integration_analysis(
            prop_designs, world_systems, environment_details
        )

        # スコア計算
        consistency_score = self._calculate_consistency_score(
            prop_designs, world_systems, consistency_rules
        )
        immersion_score = self._calculate_immersion_score(
            prop_designs, environment_details, integration_analysis
        )
        realism_score = self._calculate_realism_score(
            prop_designs, world_systems, environment_details
        )

        # レポート生成
        return self._generate_world_building_report(
            episode_number=episode_number,
            prop_designs=prop_designs,
            world_systems=world_systems,
            environment_details=environment_details,
            consistency_rules=consistency_rules,
            integration_analysis=integration_analysis,
            consistency_score=consistency_score,
            immersion_score=immersion_score,
            realism_score=realism_score
        )

    def _analyze_existing_world_data(
        self,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """既存世界観データの分析"""
        existing_world = {
            "established_props": {},
            "established_systems": {},
            "established_locations": {},
            "established_rules": {},
            "world_history": {},
            "cultural_elements": {},
            "technological_level": "unknown",
            "magical_system": None,
            "political_structure": "unknown"
        }

        # プロジェクトデータから既存情報を抽出
        project_world = project.__dict__.get("world_data", {})
        if project_world:
            existing_world.update(project_world)

        # コンテキストから追加情報を抽出
        world_data = context.get("world_data", {})
        if world_data:
            existing_world.update(world_data)

        # シーン設定からの情報抽出
        scene_setting = context.get("scene_setting", {})
        if scene_setting:
            locations = scene_setting.get("locations", [])
            for location in locations:
                if location not in existing_world["established_locations"]:
                    existing_world["established_locations"][location] = {
                        "name": location,
                        "described": False,
                        "details": {}
                    }

        return existing_world

    def _analyze_scene_requirements(self, context: dict[str, Any]) -> dict[str, Any]:
        """シーン要件の分析"""
        requirements = {
            "required_props": [],
            "required_locations": [],
            "required_systems": [],
            "atmosphere_needs": [],
            "functional_needs": [],
            "symbolic_needs": [],
            "cultural_context": "modern_japanese",
            "technology_level": "contemporary",
            "realism_level": "high"
        }

        # プロットデータから要件を抽出
        plot_data = context.get("plot_data", {})
        if plot_data:
            # プロット要素から必要な小道具を推定
            plot_elements = plot_data.get("elements", [])
            for element in plot_elements:
                if "props" in element:
                    requirements["required_props"].extend(element["props"])

        # シーン設定から要件を抽出
        scene_setting = context.get("scene_setting", {})
        if scene_setting:
            requirements["required_locations"] = scene_setting.get("locations", [])
            requirements["atmosphere_needs"] = [scene_setting.get("mood", "neutral")]
            requirements["cultural_context"] = scene_setting.get("cultural_context", "modern_japanese")

        # キャラクターデータから要件を抽出
        character_data = context.get("character_data", {})
        for character in character_data.values():
            char_props = character.get("personal_items", [])
            requirements["required_props"].extend(char_props)

        return requirements

    def _design_props(
        self,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> list[PropDesign]:
        """小道具設計"""
        prop_designs = []

        # 必要な小道具リスト
        required_props = scene_requirements.get("required_props", [])

        # 各必要小道具について設計
        for prop_name in required_props:
            if prop_name not in existing_world.get("established_props", {}):
                prop_design = self._create_prop_design(
                    prop_name, scene_requirements, existing_world
                )
                prop_designs.append(prop_design)

        # 雰囲気作りのための小道具追加
        atmospheric_props = self._generate_atmospheric_props(
            scene_requirements, existing_world
        )
        prop_designs.extend(atmospheric_props)

        # 小道具数制限の適用
        max_props = self._build_config.max_props_per_scene
        if len(prop_designs) > max_props:
            prop_designs = self._prioritize_props(prop_designs, scene_requirements)[:max_props]

        return prop_designs

    def _create_prop_design(
        self,
        prop_name: str,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> PropDesign:
        """個別小道具設計の作成"""

        # テンプレートから基本設計を取得
        base_template = self._get_prop_template(prop_name, scene_requirements)

        # カテゴリーと重要度の決定
        category = self._determine_prop_category(prop_name, scene_requirements)
        importance = self._determine_prop_importance(prop_name, scene_requirements)

        return PropDesign(
            prop_id=f"prop_{prop_name.lower().replace(' ', '_')}",
            name=prop_name,
            category=category,
            importance=importance,
            description=base_template.get("description", f"{prop_name}の詳細な描写"),
            physical_properties=base_template.get("physical_properties", {
                "material": "不明",
                "size": "中程度",
                "weight": "軽量",
                "color": "自然色",
                "texture": "滑らか"
            }),
            functional_properties=base_template.get("functional_properties", {
                "primary_function": "基本機能",
                "secondary_functions": [],
                "durability": "標準",
                "maintenance": "低"
            }),
            symbolic_meaning=base_template.get("symbolic_meaning", "物語における意味"),
            cultural_significance=base_template.get("cultural_significance", "文化的な意義"),
            historical_background=base_template.get("historical_background", "歴史的な背景"),
            owner_relationship=base_template.get("owner_relationship", {"owner": "未定", "relationship": "所有"}),
            usage_context=base_template.get("usage_context", ["日常使用"]),
            story_role=base_template.get("story_role", "背景的存在"),
            visual_design=base_template.get("visual_design", {
                "distinctive_features": [],
                "wear_patterns": [],
                "decorative_elements": []
            }),
            interaction_rules=base_template.get("interaction_rules", ["通常の物理法則に従う"]),
            maintenance_requirements=base_template.get("maintenance_requirements", ["定期的な清掃"]),
            degradation_pattern=base_template.get("degradation_pattern", "通常の経年劣化")
        )

    def _design_world_systems(
        self,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> list[WorldSystemDesign]:
        """世界システム設計"""
        system_designs = []

        # 必要なシステムの特定
        scene_requirements.get("required_systems", [])

        # 基本的なシステムの追加
        basic_systems = ["social_system", "economic_system", "transportation_system"]
        for system in basic_systems:
            if system not in existing_world.get("established_systems", {}):
                system_design = self._create_world_system_design(
                    system, scene_requirements, existing_world
                )
                system_designs.append(system_design)

        # システム数制限の適用
        max_systems = self._build_config.max_world_systems
        if len(system_designs) > max_systems:
            system_designs = self._prioritize_systems(system_designs, scene_requirements)[:max_systems]

        return system_designs

    def _create_world_system_design(
        self,
        system_name: str,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> WorldSystemDesign:
        """個別世界システム設計の作成"""

        # システムタイプの決定
        element_type = self._determine_system_element_type(system_name)

        # テンプレートから基本設計を取得
        base_template = self._get_world_system_template(system_name, scene_requirements)

        return WorldSystemDesign(
            system_id=f"system_{system_name}",
            system_name=system_name,
            element_type=element_type,
            core_principles=base_template.get("core_principles", ["基本原理"]),
            operational_rules=base_template.get("operational_rules", ["運用ルール"]),
            limitations=base_template.get("limitations", ["制限事項"]),
            exceptions=base_template.get("exceptions", ["例外事項"]),
            historical_evolution=base_template.get("historical_evolution", ["歴史的発展"]),
            current_state=base_template.get("current_state", "現在の状態"),
            future_trajectory=base_template.get("future_trajectory", "将来の方向性"),
            interaction_with_other_systems=base_template.get("system_interactions", {}),
            character_impact=base_template.get("character_impact", {}),
            plot_integration=base_template.get("plot_integration", ["プロット統合点"]),
            consistency_requirements=base_template.get("consistency_requirements", ["一貫性要件"])
        )

    def _design_environment_details(
        self,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> list[EnvironmentDetail]:
        """環境詳細設計"""
        detail_designs = []

        # 必要な場所の詳細設計
        required_locations = scene_requirements.get("required_locations", [])

        for location in required_locations:
            if location not in existing_world.get("established_locations", {}):
                location_details = self._create_environment_details(
                    location, scene_requirements, existing_world
                )
                detail_designs.extend(location_details)

        return detail_designs

    def _create_environment_details(
        self,
        location: str,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> list[EnvironmentDetail]:
        """個別環境詳細の作成"""
        details = []

        # 基本的な環境要素
        basic_elements = ["lighting", "sound_environment", "spatial_layout", "decorative_elements"]

        for element in basic_elements:
            detail = EnvironmentDetail(
                detail_id=f"env_{location}_{element}",
                location=location,
                detail_type=element,
                description=self._generate_environment_description(location, element, scene_requirements),
                sensory_aspects=self._generate_sensory_aspects(location, element),
                functional_aspects=self._generate_functional_aspects(location, element),
                aesthetic_aspects=self._generate_aesthetic_aspects(location, element),
                cultural_context=scene_requirements.get("cultural_context", "現代日本"),
                historical_significance=self._generate_historical_significance(location, element),
                maintenance_state=self._determine_maintenance_state(location, element),
                change_patterns=self._generate_change_patterns(location, element),
                interaction_possibilities=self._generate_interaction_possibilities(location, element)
            )
            details.append(detail)

        return details

    def _build_consistency_rules(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail],
        existing_world: dict[str, Any]
    ) -> list[ConsistencyRule]:
        """一貫性ルールの構築"""
        rules = []

        # 小道具間の一貫性ルール
        prop_rules = self._build_prop_consistency_rules(prop_designs)
        rules.extend(prop_rules)

        # システム間の一貫性ルール
        system_rules = self._build_system_consistency_rules(world_systems)
        rules.extend(system_rules)

        # 環境の一貫性ルール
        environment_rules = self._build_environment_consistency_rules(environment_details)
        rules.extend(environment_rules)

        # 統合的一貫性ルール
        integration_rules = self._build_integration_consistency_rules(
            prop_designs, world_systems, environment_details
        )
        rules.extend(integration_rules)

        return rules

    def _perform_integration_analysis(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail]
    ) -> dict[str, Any]:
        """統合分析の実行"""

        return {
            "prop_integration": self._analyze_prop_integration(prop_designs),
            "system_integration": self._analyze_system_integration(world_systems),
            "environment_integration": self._analyze_environment_integration(environment_details),
            "cross_element_integration": self._analyze_cross_element_integration(
                prop_designs, world_systems, environment_details
            ),
            "narrative_integration": self._analyze_narrative_integration(
                prop_designs, world_systems, environment_details
            ),
            "thematic_coherence": self._analyze_thematic_coherence(
                prop_designs, world_systems, environment_details
            )
        }


    def _calculate_consistency_score(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        consistency_rules: list[ConsistencyRule]
    ) -> float:
        """一貫性スコアの計算"""

        # 基本一貫性 (0-0.4)
        base_consistency = 0.8  # デフォルト高スコア
        consistency_score = base_consistency * 0.4

        # ルール遵守度 (0-0.3)
        if consistency_rules:
            rule_compliance = sum(
                rule.flexibility for rule in consistency_rules
            ) / len(consistency_rules)
            consistency_score += rule_compliance * 0.3
        else:
            consistency_score += 0.3

        # 要素間整合性 (0-0.3)
        if prop_designs and world_systems:
            element_coherence = self._calculate_element_coherence(prop_designs, world_systems)
            consistency_score += element_coherence * 0.3
        else:
            consistency_score += 0.15

        return min(1.0, max(0.0, consistency_score))

    def _calculate_immersion_score(
        self,
        prop_designs: list[PropDesign],
        environment_details: list[EnvironmentDetail],
        integration_analysis: dict[str, Any]
    ) -> float:
        """没入感スコアの計算"""

        # 詳細度 (0-0.4)
        detail_score = 0.0
        if prop_designs:
            avg_detail = sum(
                len(prop.physical_properties) + len(prop.visual_design)
                for prop in prop_designs
            ) / len(prop_designs) / 10.0  # 正規化
            detail_score = min(avg_detail, 1.0) * 0.4

        # 環境の豊かさ (0-0.3)
        environment_score = 0.0
        if environment_details:
            avg_richness = sum(
                len(detail.sensory_aspects) + len(detail.aesthetic_aspects)
                for detail in environment_details
            ) / len(environment_details) / 8.0  # 正規化
            environment_score = min(avg_richness, 1.0) * 0.3

        # 統合性 (0-0.3)
        integration_score = integration_analysis.get("narrative_integration", {}).get("score", 0.5) * 0.3

        total_score = detail_score + environment_score + integration_score
        return min(1.0, max(0.0, total_score))

    def _calculate_realism_score(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail]
    ) -> float:
        """リアリティスコアの計算"""

        # 小道具のリアリティ (0-0.4)
        prop_realism = 0.0
        if prop_designs:
            realistic_props = sum(
                1 for prop in prop_designs
                if self._assess_prop_realism(prop) > 0.7
            )
            prop_realism = realistic_props / len(prop_designs) * 0.4

        # システムの現実性 (0-0.3)
        system_realism = 0.0
        if world_systems:
            realistic_systems = sum(
                1 for system in world_systems
                if self._assess_system_realism(system) > 0.7
            )
            system_realism = realistic_systems / len(world_systems) * 0.3

        # 環境の現実性 (0-0.3)
        env_realism = 0.0
        if environment_details:
            realistic_envs = sum(
                1 for detail in environment_details
                if self._assess_environment_realism(detail) > 0.7
            )
            env_realism = realistic_envs / len(environment_details) * 0.3

        total_score = prop_realism + system_realism + env_realism
        return min(1.0, max(0.0, total_score))

    def _generate_world_building_report(
        self,
        episode_number: int,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail],
        consistency_rules: list[ConsistencyRule],
        integration_analysis: dict[str, Any],
        consistency_score: float,
        immersion_score: float,
        realism_score: float
    ) -> WorldBuildingReport:
        """世界観構築レポートの生成"""

        # ビルドサマリーの生成
        build_summary = self._generate_build_summary(
            prop_designs, world_systems, environment_details,
            consistency_score, immersion_score, realism_score
        )

        # 実装ガイドラインの生成
        implementation_guidelines = self._generate_world_building_guidelines(
            prop_designs, world_systems, environment_details,
            consistency_score, immersion_score, realism_score
        )

        return WorldBuildingReport(
            report_id=f"world_building_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            episode_number=episode_number,
            build_timestamp=datetime.now(tz=datetime.timezone.utc),
            prop_designs=prop_designs,
            world_systems=world_systems,
            environment_details=environment_details,
            consistency_rules=consistency_rules,
            integration_analysis=integration_analysis,
            consistency_score=consistency_score,
            immersion_score=immersion_score,
            realism_score=realism_score,
            build_summary=build_summary,
            implementation_guidelines=implementation_guidelines,
            build_metadata={
                "build_config": self._build_config.__dict__,
                "total_props": len(prop_designs),
                "total_systems": len(world_systems),
                "total_details": len(environment_details),
                "total_rules": len(consistency_rules)
            }
        )

    # テンプレート初期化メソッド

    def _initialize_prop_templates(self) -> dict[str, Any]:
        """小道具テンプレートの初期化"""
        return {
            "personal_items": {
                "smartphone": {
                    "description": "現代的なスマートフォン",
                    "physical_properties": {
                        "material": "金属とガラス",
                        "size": "手のひらサイズ",
                        "weight": "軽量",
                        "color": "黒系",
                        "texture": "滑らか"
                    },
                    "functional_properties": {
                        "primary_function": "通信",
                        "secondary_functions": ["写真撮影", "情報検索", "娯楽"],
                        "durability": "標準",
                        "maintenance": "低"
                    },
                    "symbolic_meaning": "現代社会との繋がり",
                    "cultural_significance": "現代人の必需品",
                    "story_role": "コミュニケーション手段"
                }
            },
            "household_items": {
                "tea_set": {
                    "description": "伝統的な茶器セット",
                    "physical_properties": {
                        "material": "陶磁器",
                        "size": "中程度",
                        "weight": "中程度",
                        "color": "白系",
                        "texture": "滑らか"
                    },
                    "symbolic_meaning": "おもてなしの心",
                    "cultural_significance": "日本の茶文化",
                    "story_role": "雰囲気作り"
                }
            }
        }

    def _initialize_world_system_templates(self) -> dict[str, Any]:
        """世界システムテンプレートの初期化"""
        return {
            "social_system": {
                "core_principles": ["社会秩序の維持", "相互協力", "責任の分担"],
                "operational_rules": ["法的枠組み", "社会規範", "慣習的ルール"],
                "limitations": ["個人の自由との兼ね合い", "変化への適応性"],
                "current_state": "現代日本社会基準",
                "character_impact": {"behavior": "社会的期待に応じた行動"},
                "plot_integration": ["社会的制約", "人間関係の複雑さ"]
            },
            "economic_system": {
                "core_principles": ["市場経済", "需要と供給", "価値交換"],
                "operational_rules": ["通貨制度", "商取引規則", "労働規範"],
                "limitations": ["経済格差", "市場の不安定性"],
                "current_state": "現代資本主義経済",
                "character_impact": {"lifestyle": "経済状況による生活レベル"},
                "plot_integration": ["経済的動機", "資源をめぐる対立"]
            }
        }

    def _initialize_consistency_rules(self) -> dict[str, Any]:
        """一貫性ルールデータベースの初期化"""
        return {
            "temporal_consistency": {
                "description": "時間的一貫性の維持",
                "conditions": ["同一時代設定", "技術レベルの統一"],
                "requirements": ["時代考証の正確性", "技術的矛盾の回避"]
            },
            "cultural_consistency": {
                "description": "文化的一貫性の維持",
                "conditions": ["文化圏の統一", "社会制度の整合性"],
                "requirements": ["文化的背景の理解", "社会規範の反映"]
            },
            "physical_consistency": {
                "description": "物理的一貫性の維持",
                "conditions": ["物理法則の適用", "空間的制約の考慮"],
                "requirements": ["現実的な物理現象", "空間の論理的配置"]
            }
        }

    # ヘルパーメソッドのスタブ実装

    def _get_prop_template(self, prop_name: str, scene_requirements: dict[str, Any]) -> dict[str, Any]:
        """小道具テンプレートの取得"""
        # カテゴリーを推定してテンプレートを取得
        for templates in self._prop_templates.values():
            if prop_name.lower() in templates:
                return templates[prop_name.lower()]
        return {}

    def _determine_prop_category(self, prop_name: str, scene_requirements: dict[str, Any]) -> PropCategory:
        """小道具カテゴリーの決定"""
        # 名前とコンテキストから推定
        personal_items = ["smartphone", "wallet", "keys", "watch"]
        if prop_name.lower() in personal_items:
            return PropCategory.PERSONAL
        return PropCategory.FUNCTIONAL

    def _determine_prop_importance(self, prop_name: str, scene_requirements: dict[str, Any]) -> PropImportance:
        """小道具重要度の決定"""
        # プロット中心的な小道具を特定
        if prop_name in scene_requirements.get("plot_critical_items", []):
            return PropImportance.PLOT_CRITICAL
        return PropImportance.ATMOSPHERIC

    def _generate_atmospheric_props(
        self,
        scene_requirements: dict[str, Any],
        existing_world: dict[str, Any]
    ) -> list[PropDesign]:
        """雰囲気作りの小道具生成"""
        # スタブ実装
        return []

    def _prioritize_props(
        self,
        prop_designs: list[PropDesign],
        scene_requirements: dict[str, Any]
    ) -> list[PropDesign]:
        """小道具の優先順位付け"""
        importance_order = {
            PropImportance.PLOT_CRITICAL: 4,
            PropImportance.CHARACTER_DEFINING: 3,
            PropImportance.WORLD_BUILDING: 2,
            PropImportance.ATMOSPHERIC: 1,
            PropImportance.BACKGROUND: 0
        }
        return sorted(prop_designs, key=lambda p: importance_order.get(p.importance, 0), reverse=True)

    def _determine_system_element_type(self, system_name: str) -> WorldElement:
        """システム要素タイプの決定"""
        type_mapping = {
            "social_system": WorldElement.SOCIAL_SYSTEM,
            "economic_system": WorldElement.ECONOMICS,
            "transportation_system": WorldElement.TECHNOLOGY,
            "political_system": WorldElement.POLITICS,
            "cultural_system": WorldElement.CULTURE
        }
        return type_mapping.get(system_name, WorldElement.SOCIAL_SYSTEM)

    def _get_world_system_template(self, system_name: str, scene_requirements: dict[str, Any]) -> dict[str, Any]:
        """世界システムテンプレートの取得"""
        return self._world_system_templates.get(system_name, {})

    def _prioritize_systems(
        self,
        system_designs: list[WorldSystemDesign],
        scene_requirements: dict[str, Any]
    ) -> list[WorldSystemDesign]:
        """システムの優先順位付け"""
        # 重要度順にソート（スタブ実装）
        return system_designs

    # 環境関連ヘルパーメソッド（スタブ実装）
    def _generate_environment_description(self, location: str, element: str, scene_requirements: dict[str, Any]) -> str:
        return f"{location}の{element}に関する詳細な描写"

    def _generate_sensory_aspects(self, location: str, element: str) -> dict[str, list[str]]:
        return {"visual": ["視覚的要素"], "auditory": ["聴覚的要素"]}

    def _generate_functional_aspects(self, location: str, element: str) -> list[str]:
        return ["機能的側面"]

    def _generate_aesthetic_aspects(self, location: str, element: str) -> list[str]:
        return ["美的側面"]

    def _generate_historical_significance(self, location: str, element: str) -> str:
        return "歴史的意義"

    def _determine_maintenance_state(self, location: str, element: str) -> str:
        return "良好"

    def _generate_change_patterns(self, location: str, element: str) -> list[str]:
        return ["変化パターン"]

    def _generate_interaction_possibilities(self, location: str, element: str) -> list[str]:
        return ["相互作用可能性"]

    # 一貫性ルール構築メソッド（スタブ実装）
    def _build_prop_consistency_rules(self, prop_designs: list[PropDesign]) -> list[ConsistencyRule]:
        return []

    def _build_system_consistency_rules(self, world_systems: list[WorldSystemDesign]) -> list[ConsistencyRule]:
        return []

    def _build_environment_consistency_rules(self, environment_details: list[EnvironmentDetail]) -> list[ConsistencyRule]:
        return []

    def _build_integration_consistency_rules(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail]
    ) -> list[ConsistencyRule]:
        return []

    # 分析メソッド（スタブ実装）
    def _analyze_prop_integration(self, prop_designs: list[PropDesign]) -> dict[str, Any]:
        return {"integration_score": 0.8}

    def _analyze_system_integration(self, world_systems: list[WorldSystemDesign]) -> dict[str, Any]:
        return {"integration_score": 0.8}

    def _analyze_environment_integration(self, environment_details: list[EnvironmentDetail]) -> dict[str, Any]:
        return {"integration_score": 0.8}

    def _analyze_cross_element_integration(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail]
    ) -> dict[str, Any]:
        return {"cross_integration_score": 0.8}

    def _analyze_narrative_integration(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail]
    ) -> dict[str, Any]:
        return {"score": 0.8, "narrative_coherence": "高"}

    def _analyze_thematic_coherence(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail]
    ) -> dict[str, Any]:
        return {"thematic_score": 0.8}

    def _calculate_element_coherence(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign]
    ) -> float:
        return 0.8

    def _assess_prop_realism(self, prop: PropDesign) -> float:
        return 0.8

    def _assess_system_realism(self, system: WorldSystemDesign) -> float:
        return 0.8

    def _assess_environment_realism(self, detail: EnvironmentDetail) -> float:
        return 0.8

    def _generate_build_summary(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail],
        consistency_score: float,
        immersion_score: float,
        realism_score: float
    ) -> str:
        total_elements = len(prop_designs) + len(world_systems) + len(environment_details)

        summary_parts = [
            f"総計{total_elements}個の世界観要素を設計。",
            f"小道具{len(prop_designs)}個、システム{len(world_systems)}個、環境詳細{len(environment_details)}個。"
        ]

        if consistency_score >= 0.8 and immersion_score >= 0.8 and realism_score >= 0.8:
            summary_parts.append("高品質な世界観構築が完成しました。")
        elif min(consistency_score, immersion_score, realism_score) >= 0.6:
            summary_parts.append("バランスの良い世界観設計です。")
        else:
            summary_parts.append("世界観要素の調整が推奨されます。")

        return " ".join(summary_parts)

    def _generate_world_building_guidelines(
        self,
        prop_designs: list[PropDesign],
        world_systems: list[WorldSystemDesign],
        environment_details: list[EnvironmentDetail],
        consistency_score: float,
        immersion_score: float,
        realism_score: float
    ) -> list[str]:
        guidelines = [
            "🎯 各世界観要素を物語に適切に統合してください",
            "🔧 小道具の機能と象徴的意味を活用してください",
            "🌍 世界システムの一貫性を保ってください",
            "🏞️ 環境詳細で豊かな描写を心がけてください"
        ]

        if consistency_score < 0.6:
            guidelines.append("⚠️ 一貫性の向上が必要です")
        if immersion_score < 0.6:
            guidelines.append("📖 没入感を高める詳細の追加を検討してください")
        if realism_score < 0.6:
            guidelines.append("🔍 リアリティの向上を図ってください")

        return guidelines
