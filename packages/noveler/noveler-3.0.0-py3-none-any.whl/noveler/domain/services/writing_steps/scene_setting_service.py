"""Domain.services.writing_steps.scene_setting_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""情景設計サービス

A38執筆プロンプトガイド STEP 9: 情景設計の実装。
場面の雰囲気、環境設定、視覚的・感覚的要素の構築。
"""

import time
from typing import Any

from noveler.domain.services.writing_steps.base_writing_step import (
    BaseWritingStep,
    WritingStepResponse,
)


class SceneSettingService(BaseWritingStep):
    """情景設計サービス

    A38 STEP 9: 各場面の具体的な情景を設計し、
    読者の没入感を高める環境描写を構築する。
    """

    def __init__(self) -> None:
        super().__init__(
            step_number=9,
            step_name="情景設計"
        )

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> WritingStepResponse:
        """情景設計を実行

        Args:
            episode_number: エピソード番号
            previous_results: 前のステップの実行結果

        Returns:
            情景設計結果
        """
        start_time = time.time()

        try:
            # 前ステップから必要情報を抽出
            scene_structure = self._extract_scene_structure(previous_results)
            emotion_curve = self._extract_emotion_curve(previous_results)
            characters = self._extract_characters(previous_results)

            # 情景設計の実行
            scene_designs = self._design_scene_settings(
                scene_structure, emotion_curve, characters, episode_number
            )

            # 環境設定の詳細化
            environmental_details = self._create_environmental_details(scene_designs)

            # 雰囲気設定
            atmosphere_design = self._design_atmosphere(scene_designs, emotion_curve)

            # 視覚的要素の構築
            visual_elements = self._construct_visual_elements(scene_designs)

            # 実行時間計算
            execution_time = (time.time() - start_time) * 1000

            return WritingStepResponse(
                success=True,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                data={
                    "scene_designs": scene_designs,
                    "environmental_details": environmental_details,
                    "atmosphere_design": atmosphere_design,
                    "visual_elements": visual_elements,
                    "designed_scenes": len(scene_designs),
                    "atmosphere_variety": len({scene["atmosphere_type"] for scene in scene_designs.values()})
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return WritingStepResponse(
                success=False,
                step_number=self.step_number,
                step_name=self.step_name,
                execution_time_ms=execution_time,
                error_message=str(e)
            )

    def _extract_scene_structure(self, previous_results: dict[int, Any] | None) -> dict[str, Any]:
        """前ステップからシーン構造を抽出"""
        if not previous_results:
            return {}

        scene_info = {}

        # STEP 4（小骨）やその他のステップからシーン情報を収集
        for step_num, result in previous_results.items():
            if hasattr(result, "data") and result.data:
                if "scene_structure" in result.data:
                    scene_info.update(result.data["scene_structure"])
                elif "scenes" in result.data:
                    scene_info["scenes"] = result.data["scenes"]
                elif step_num == 4 and "beats" in result.data:  # STEP 4結果
                    scene_info["beats"] = result.data["beats"]

        return scene_info

    def _extract_emotion_curve(self, previous_results: dict[int, Any] | None) -> dict[str, Any]:
        """STEP 8から感情曲線を抽出"""
        if not previous_results or 8 not in previous_results:
            return {}

        step8_result = previous_results[8]
        if hasattr(step8_result, "data") and step8_result.data:
            return step8_result.data.get("emotion_curve", {})

        return {}

    def _extract_characters(self, previous_results: dict[int, Any] | None) -> dict[str, Any]:
        """キャラクター情報を抽出"""
        if not previous_results:
            return {}

        characters = {}

        for result in previous_results.values():
            if hasattr(result, "data") and result.data:
                if "characters" in result.data:
                    characters.update(result.data["characters"])

        return characters

    def _design_scene_settings(
        self,
        scene_structure: dict[str, Any],
        emotion_curve: dict[str, Any],
        characters: dict[str, Any],
        episode_number: int
    ) -> dict[str, Any]:
        """情景設計を実行"""

        scene_designs = {}

        # 基本シーン数の決定
        scenes = scene_structure.get("scenes", [])
        if not scenes:
            # デフォルトのシーン構成
            scenes = [
                {"name": "opening", "purpose": "導入"},
                {"name": "development", "purpose": "展開"},
                {"name": "climax", "purpose": "山場"},
                {"name": "resolution", "purpose": "結末"}
            ]

        # 各シーンの情景設計
        for i, scene in enumerate(scenes):
            scene_id = f"scene_{i+1}"
            scene_name = scene.get("name", f"シーン{i+1}")

            design = self._design_single_scene(
                scene_id,
                scene_name,
                scene,
                emotion_curve,
                characters,
                episode_number
            )

            scene_designs[scene_id] = design

        return scene_designs

    def _design_single_scene(
        self,
        scene_id: str,
        scene_name: str,
        scene_info: dict[str, Any],
        emotion_curve: dict[str, Any],
        characters: dict[str, Any],
        episode_number: int
    ) -> dict[str, Any]:
        """単一シーンの情景設計"""

        design = {
            "scene_id": scene_id,
            "scene_name": scene_name,
            "location": {},
            "time_setting": {},
            "weather_conditions": {},
            "atmosphere_type": "neutral",
            "mood_elements": [],
            "sensory_focus": [],
            "lighting": {},
            "space_description": {},
            "interactive_elements": []
        }

        # シーンの目的に基づく基本設定
        scene_purpose = scene_info.get("purpose", "一般")
        design["location"] = self._determine_location(scene_purpose, episode_number)
        design["time_setting"] = self._determine_time_setting(scene_purpose)
        design["weather_conditions"] = self._determine_weather(scene_purpose, emotion_curve)

        # 雰囲気タイプの決定
        design["atmosphere_type"] = self._determine_atmosphere_type(
            scene_purpose, emotion_curve, scene_id
        )

        # ムード要素の設定
        design["mood_elements"] = self._create_mood_elements(
            design["atmosphere_type"],
            design["location"]
        )

        # 感覚的焦点の決定
        design["sensory_focus"] = self._determine_sensory_focus(
            design["atmosphere_type"]
        )

        # 照明設定
        design["lighting"] = self._design_lighting(
            design["time_setting"],
            design["atmosphere_type"],
            design["location"]
        )

        # 空間描写
        design["space_description"] = self._create_space_description(
            design["location"],
            design["atmosphere_type"]
        )

        # インタラクティブ要素
        design["interactive_elements"] = self._identify_interactive_elements(
            design["location"],
            characters
        )

        return design

    def _determine_location(self, scene_purpose: str, episode_number: int) -> dict[str, Any]:
        """ロケーション決定"""

        location_templates = {
            "導入": {
                "type": "日常空間",
                "setting": "キャラクターの居住空間または日常活動場所",
                "examples": ["自宅", "学校", "職場", "カフェ"],
                "atmosphere_base": "安定感"
            },
            "展開": {
                "type": "活動空間",
                "setting": "物語展開の舞台となる場所",
                "examples": ["街中", "公園", "会議室", "移動中"],
                "atmosphere_base": "動的"
            },
            "山場": {
                "type": "対立空間",
                "setting": "緊張感のあるクライマックス的場所",
                "examples": ["屋上", "廃墟", "密室", "橋の上"],
                "atmosphere_base": "緊張感"
            },
            "結末": {
                "type": "解決空間",
                "setting": "物語の決着・解決の場所",
                "examples": ["元の場所", "新しい場所", "開放的な場所"],
                "atmosphere_base": "解放感"
            }
        }

        template = location_templates.get(scene_purpose, location_templates["展開"])

        return {
            "location_type": template["type"],
            "setting_description": template["setting"],
            "suggested_locations": template["examples"],
            "base_atmosphere": template["atmosphere_base"],
            "episode_context": f"第{episode_number}話の{scene_purpose}部分"
        }

    def _determine_time_setting(self, scene_purpose: str) -> dict[str, Any]:
        """時間設定決定"""

        time_associations = {
            "導入": {"time": "朝", "feeling": "始まり", "energy": "静かな活力"},
            "展開": {"time": "昼", "feeling": "活動的", "energy": "動的エネルギー"},
            "山場": {"time": "夕方〜夜", "feeling": "劇的", "energy": "高い緊張"},
            "結末": {"time": "夜〜翌朝", "feeling": "落ち着き", "energy": "安らぎ"}
        }

        setting = time_associations.get(scene_purpose, time_associations["展開"])

        return {
            "time_of_day": setting["time"],
            "emotional_association": setting["feeling"],
            "energy_level": setting["energy"],
            "lighting_implications": self._get_lighting_implications(setting["time"]),
            "mood_impact": self._get_mood_impact(setting["time"])
        }

    def _determine_weather(self, scene_purpose: str, emotion_curve: dict[str, Any]) -> dict[str, Any]:
        """天候設定決定"""

        # 感情曲線から天候を推測
        weather_mood_map = {
            "joy": {"weather": "晴れ", "details": "爽やかな青空"},
            "tension": {"weather": "曇り", "details": "重い雲、風強め"},
            "conflict": {"weather": "雨", "details": "激しい雨または雷雨"},
            "sadness": {"weather": "小雨", "details": "しとしと降る雨"},
            "mystery": {"weather": "霧", "details": "立ち込める霧"},
            "resolution": {"weather": "晴れ間", "details": "雲の切れ間から差す光"}
        }

        # デフォルト天候
        default_weather = {"weather": "普通", "details": "特に印象的でない天候"}

        # 感情曲線から天候パターンを選択
        peaks = emotion_curve.get("peak_moments", [])
        if peaks:
            emotion_type = peaks[0].get("type", "neutral")
            weather = weather_mood_map.get(emotion_type, default_weather)
        else:
            weather = default_weather

        return {
            "condition": weather["weather"],
            "description": weather["details"],
            "mood_enhancement": weather != default_weather,
            "sensory_elements": self._get_weather_sensory_elements(weather["weather"])
        }

    def _determine_atmosphere_type(
        self,
        scene_purpose: str,
        emotion_curve: dict[str, Any],
        scene_id: str
    ) -> str:
        """雰囲気タイプ決定"""

        purpose_atmosphere_map = {
            "導入": ["peaceful", "curious", "anticipatory"],
            "展開": ["dynamic", "engaging", "progressive"],
            "山場": ["tense", "dramatic", "intense"],
            "結末": ["resolution", "satisfying", "conclusive"]
        }

        # 感情曲線から雰囲気を調整
        emotion_adjustments = {
            "excitement": "energetic",
            "tension": "tense",
            "sadness": "melancholic",
            "joy": "uplifting",
            "mystery": "mysterious",
            "conflict": "confrontational"
        }

        base_atmospheres = purpose_atmosphere_map.get(scene_purpose, ["neutral"])

        # 感情曲線による調整
        peaks = emotion_curve.get("peak_moments", [])
        if peaks:
            emotion_type = peaks[0].get("type", "neutral")
            if emotion_type in emotion_adjustments:
                return emotion_adjustments[emotion_type]

        return base_atmospheres[0]

    def _create_mood_elements(self, atmosphere_type: str, location: dict[str, Any]) -> list[dict[str, Any]]:
        """ムード要素作成"""

        mood_libraries = {
            "peaceful": [
                {"element": "soft_sounds", "description": "優しい音響効果"},
                {"element": "warm_colors", "description": "暖かみのある色調"},
                {"element": "gentle_movement", "description": "ゆったりとした動き"}
            ],
            "tense": [
                {"element": "sharp_contrasts", "description": "鋭いコントラスト"},
                {"element": "silence_emphasis", "description": "効果的な沈黙"},
                {"element": "restricted_space", "description": "窮屈感のある空間"}
            ],
            "dramatic": [
                {"element": "dynamic_lighting", "description": "劇的な照明効果"},
                {"element": "powerful_imagery", "description": "印象的な視覚要素"},
                {"element": "emotional_triggers", "description": "感情を刺激する要素"}
            ],
            "mysterious": [
                {"element": "shadows", "description": "意味深な影"},
                {"element": "hidden_elements", "description": "隠された要素"},
                {"element": "ambiguous_details", "description": "曖昧な詳細"}
            ]
        }

        return mood_libraries.get(atmosphere_type, mood_libraries["peaceful"])

    def _determine_sensory_focus(self, atmosphere_type: str) -> list[dict[str, Any]]:
        """感覚的焦点決定"""

        sensory_emphasis = {
            "peaceful": [
                {"sense": "hearing", "focus": "自然音", "description": "鳥のさえずり、風の音"},
                {"sense": "touch", "focus": "温度", "description": "心地よい暖かさや涼しさ"}
            ],
            "tense": [
                {"sense": "hearing", "focus": "鋭い音", "description": "金属音、足音、心音"},
                {"sense": "sight", "focus": "細部", "description": "神経質な視線の動き"}
            ],
            "dramatic": [
                {"sense": "sight", "focus": "強烈な印象", "description": "劇的な光景"},
                {"sense": "hearing", "focus": "迫力ある音", "description": "雷鳴、怒声、音楽"}
            ],
            "mysterious": [
                {"sense": "sight", "focus": "不明確な形", "description": "薄暗がりの中の影"},
                {"sense": "hearing", "focus": "不可解な音", "description": "正体不明の物音"}
            ]
        }

        return sensory_emphasis.get(atmosphere_type, sensory_emphasis["peaceful"])

    def _design_lighting(
        self,
        time_setting: dict[str, Any],
        atmosphere_type: str,
        location: dict[str, Any]
    ) -> dict[str, Any]:
        """照明設計"""

        base_time = time_setting["time_of_day"]

        lighting_base = {
            "朝": {"quality": "soft", "direction": "horizontal", "color": "warm_gold"},
            "昼": {"quality": "bright", "direction": "overhead", "color": "white"},
            "夕方": {"quality": "dramatic", "direction": "low_angle", "color": "orange_red"},
            "夜": {"quality": "artificial", "direction": "point_sources", "color": "varied"}
        }

        base = lighting_base.get(base_time, lighting_base["昼"])

        # 雰囲気による調整
        atmosphere_adjustments = {
            "tense": {"intensity": "harsh", "shadows": "deep"},
            "peaceful": {"intensity": "gentle", "shadows": "soft"},
            "dramatic": {"intensity": "contrasted", "shadows": "bold"},
            "mysterious": {"intensity": "dim", "shadows": "concealing"}
        }

        adjustment = atmosphere_adjustments.get(atmosphere_type, {"intensity": "normal", "shadows": "natural"})

        return {
            "base_lighting": base,
            "atmosphere_adjustment": adjustment,
            "overall_effect": f"{adjustment['intensity']}な{base['quality']}光",
            "shadow_character": adjustment["shadows"],
            "mood_contribution": self._assess_lighting_mood(base, adjustment)
        }

    def _create_space_description(self, location: dict[str, Any], atmosphere_type: str) -> dict[str, Any]:
        """空間描写作成"""

        return {
            "spatial_layout": self._describe_spatial_layout(location, atmosphere_type),
            "key_features": self._identify_key_features(location),
            "scale_impression": self._determine_scale_impression(location, atmosphere_type),
            "accessibility": self._assess_accessibility(location),
            "symbolic_meaning": self._extract_symbolic_meaning(location, atmosphere_type)
        }

    def _describe_spatial_layout(self, location: dict[str, Any], atmosphere_type: str) -> dict[str, Any]:
        """空間レイアウト描写"""

        location_type = location.get("location_type", "一般空間")

        layout_patterns = {
            "日常空間": {
                "structure": "親しみやすい構造",
                "accessibility": "容易にアクセス可能",
                "privacy": "プライベート感あり"
            },
            "活動空間": {
                "structure": "動的な構造",
                "accessibility": "開放的",
                "privacy": "公共性がある"
            },
            "対立空間": {
                "structure": "緊張感のある構造",
                "accessibility": "制限的",
                "privacy": "孤立感あり"
            },
            "解決空間": {
                "structure": "調和的な構造",
                "accessibility": "解放的",
                "privacy": "開かれた感覚"
            }
        }

        return layout_patterns.get(location_type, layout_patterns["活動空間"])

    def _identify_key_features(self, location: dict[str, Any]) -> list[str]:
        """主要特徴特定"""

        location_type = location.get("location_type", "一般空間")

        feature_sets = {
            "日常空間": ["家具配置", "個人的な物品", "生活感のある詳細"],
            "活動空間": ["人の流れ", "機能的な設備", "活動に適した構造"],
            "対立空間": ["制約的要素", "緊張を高める配置", "心理的圧迫要素"],
            "解決空間": ["開放的要素", "安心感を与える配置", "調和的な雰囲気"]
        }

        return feature_sets.get(location_type, feature_sets["活動空間"])

    def _determine_scale_impression(self, location: dict[str, Any], atmosphere_type: str) -> str:
        """スケール印象決定"""

        scale_map = {
            "peaceful": "適度でリラックスした空間感",
            "tense": "圧迫感のある狭さ",
            "dramatic": "印象的な広がりまたは高さ",
            "mysterious": "不明確な境界を持つ空間"
        }

        return scale_map.get(atmosphere_type, "標準的な空間スケール")

    def _assess_accessibility(self, location: dict[str, Any]) -> dict[str, str]:
        """アクセス性評価"""

        location_type = location.get("location_type", "一般空間")

        accessibility_profiles = {
            "日常空間": {
                "entry": "容易",
                "movement": "自由",
                "exit": "制限なし"
            },
            "活動空間": {
                "entry": "開放的",
                "movement": "流動的",
                "exit": "自然"
            },
            "対立空間": {
                "entry": "制限的",
                "movement": "制約あり",
                "exit": "困難"
            },
            "解決空間": {
                "entry": "歓迎的",
                "movement": "自由",
                "exit": "選択可能"
            }
        }

        return accessibility_profiles.get(location_type, accessibility_profiles["活動空間"])

    def _extract_symbolic_meaning(self, location: dict[str, Any], atmosphere_type: str) -> dict[str, str]:
        """象徴的意味抽出"""

        return {
            "primary_symbol": self._identify_primary_symbol(location, atmosphere_type),
            "emotional_resonance": self._assess_emotional_resonance(atmosphere_type),
            "narrative_function": self._determine_narrative_function(location)
        }

    def _identify_primary_symbol(self, location: dict[str, Any], atmosphere_type: str) -> str:
        """主要象徴特定"""

        symbol_combinations = {
            ("日常空間", "peaceful"): "安定した基盤",
            ("日常空間", "tense"): "脅かされる日常",
            ("活動空間", "dramatic"): "人生の舞台",
            ("対立空間", "tense"): "試練の場",
            ("解決空間", "peaceful"): "新たな始まり"
        }

        location_type = location.get("location_type", "一般空間")
        key = (location_type, atmosphere_type)

        return symbol_combinations.get(key, "物語の展開場所")

    def _assess_emotional_resonance(self, atmosphere_type: str) -> str:
        """感情的共鳴評価"""

        resonance_map = {
            "peaceful": "安らぎと調和",
            "tense": "不安と緊張",
            "dramatic": "興奮と感動",
            "mysterious": "好奇心と畏怖",
            "energetic": "活力と希望",
            "melancholic": "郷愁と静寂"
        }

        return resonance_map.get(atmosphere_type, "中性的な感情")

    def _determine_narrative_function(self, location: dict[str, Any]) -> str:
        """物語的機能決定"""

        location_type = location.get("location_type", "一般空間")

        function_map = {
            "日常空間": "キャラクター性格表現",
            "活動空間": "物語推進",
            "対立空間": "葛藤具現化",
            "解決空間": "物語完結"
        }

        return function_map.get(location_type, "物語展開支援")

    def _identify_interactive_elements(self, location: dict[str, Any], characters: dict[str, Any]) -> list[dict[str, Any]]:
        """インタラクティブ要素特定"""

        elements = []
        location_type = location.get("location_type", "一般空間")

        # ロケーションタイプ別の基本要素
        base_elements = {
            "日常空間": [
                {"element": "personal_items", "interaction": "触れる、見る", "significance": "キャラクター理解"},
                {"element": "furniture", "interaction": "座る、寄りかかる", "significance": "リラックス表現"}
            ],
            "活動空間": [
                {"element": "functional_objects", "interaction": "使用する", "significance": "目的達成"},
                {"element": "other_people", "interaction": "会話、観察", "significance": "社会的交流"}
            ],
            "対立空間": [
                {"element": "barriers", "interaction": "乗り越える、回避", "significance": "障害克服"},
                {"element": "weapons_tools", "interaction": "活用する", "significance": "問題解決"}
            ],
            "解決空間": [
                {"element": "symbolic_objects", "interaction": "受け取る、渡す", "significance": "解決の象徴"},
                {"element": "connection_points", "interaction": "つながる", "significance": "関係修復"}
            ]
        }

        elements.extend(base_elements.get(location_type, base_elements["活動空間"]))

        # キャラクター特性による追加要素
        for char_name, char_data in characters.items():
            char_role = char_data.get("role", "support")
            if char_role == "protagonist":
                elements.append({
                    "element": f"{char_name}_focus_object",
                    "interaction": "特別な関わり",
                    "significance": "主人公の成長象徴"
                })

        return elements

    def _create_environmental_details(self, scene_designs: dict[str, Any]) -> dict[str, Any]:
        """環境設定詳細を作成"""

        environmental_summary = {
            "location_variety": [],
            "time_distribution": {},
            "weather_patterns": {},
            "atmosphere_flow": [],
            "sensory_emphasis": {},
            "lighting_progression": []
        }

        # シーン設計から環境詳細を集約
        for scene_id, design in scene_designs.items():
            # ロケーション多様性
            location_type = design["location"]["location_type"]
            if location_type not in environmental_summary["location_variety"]:
                environmental_summary["location_variety"].append(location_type)

            # 時間分布
            time = design["time_setting"]["time_of_day"]
            environmental_summary["time_distribution"][time] = environmental_summary["time_distribution"].get(time, 0) + 1

            # 天候パターン
            weather = design["weather_conditions"]["condition"]
            environmental_summary["weather_patterns"][weather] = environmental_summary["weather_patterns"].get(weather, 0) + 1

            # 雰囲気の流れ
            environmental_summary["atmosphere_flow"].append(design["atmosphere_type"])

            # 感覚的強調
            for sensory in design["sensory_focus"]:
                sense = sensory["sense"]
                environmental_summary["sensory_emphasis"][sense] = environmental_summary["sensory_emphasis"].get(sense, 0) + 1

            # 照明進行
            environmental_summary["lighting_progression"].append({
                "scene": scene_id,
                "lighting": design["lighting"]["overall_effect"]
            })

        return environmental_summary

    def _design_atmosphere(self, scene_designs: dict[str, Any], emotion_curve: dict[str, Any]) -> dict[str, Any]:
        """雰囲気設計"""

        atmosphere_design = {
            "overall_mood_arc": [],
            "atmosphere_transitions": [],
            "mood_consistency": {},
            "emotional_support": {},
            "atmosphere_techniques": []
        }

        # 全体的なムード弧
        for scene_id in sorted(scene_designs.keys()):
            design = scene_designs[scene_id]
            atmosphere_design["overall_mood_arc"].append({
                "scene": scene_id,
                "atmosphere": design["atmosphere_type"],
                "intensity": self._calculate_atmosphere_intensity(design)
            })

        # 雰囲気遷移
        mood_arc = atmosphere_design["overall_mood_arc"]
        for i in range(len(mood_arc) - 1):
            current = mood_arc[i]
            next_mood = mood_arc[i + 1]

            transition = {
                "from_scene": current["scene"],
                "to_scene": next_mood["scene"],
                "transition_type": self._classify_atmosphere_transition(
                    current["atmosphere"],
                    next_mood["atmosphere"]
                ),
                "smoothness": self._assess_transition_smoothness(current, next_mood)
            }
            atmosphere_design["atmosphere_transitions"].append(transition)

        # ムード一貫性
        atmosphere_design["mood_consistency"] = self._analyze_mood_consistency(
            atmosphere_design["overall_mood_arc"]
        )

        # 感情的サポート
        atmosphere_design["emotional_support"] = self._analyze_emotional_support(
            scene_designs, emotion_curve
        )

        # 雰囲気技法
        atmosphere_design["atmosphere_techniques"] = self._compile_atmosphere_techniques(
            scene_designs
        )

        return atmosphere_design

    def _construct_visual_elements(self, scene_designs: dict[str, Any]) -> dict[str, Any]:
        """視覚的要素を構築"""

        visual_construction = {
            "visual_themes": [],
            "color_palette": {},
            "composition_elements": [],
            "visual_flow": [],
            "imagery_catalog": {}
        }

        # 視覚的テーマ
        themes = set()
        for design in scene_designs.values():
            location_type = design["location"]["location_type"]
            atmosphere = design["atmosphere_type"]
            theme = f"{location_type}_{atmosphere}"
            themes.add(theme)

        visual_construction["visual_themes"] = list(themes)

        # カラーパレット
        for scene_id, design in scene_designs.items():
            colors = self._extract_scene_colors(design)
            visual_construction["color_palette"][scene_id] = colors

        # 構成要素
        for design in scene_designs.values():
            elements = self._extract_composition_elements(design)
            visual_construction["composition_elements"].extend(elements)

        # 視覚的フロー
        visual_construction["visual_flow"] = self._create_visual_flow(scene_designs)

        # イメージカタログ
        visual_construction["imagery_catalog"] = self._create_imagery_catalog(scene_designs)

        return visual_construction

    def _calculate_atmosphere_intensity(self, design: dict[str, Any]) -> int:
        """雰囲気強度計算"""

        intensity_map = {
            "peaceful": 3,
            "curious": 4,
            "anticipatory": 5,
            "dynamic": 6,
            "engaging": 7,
            "progressive": 7,
            "tense": 8,
            "dramatic": 9,
            "intense": 10,
            "resolution": 4,
            "satisfying": 6,
            "conclusive": 5
        }

        return intensity_map.get(design["atmosphere_type"], 5)

    def _classify_atmosphere_transition(self, from_atmosphere: str, to_atmosphere: str) -> str:
        """雰囲気遷移分類"""

        intensity_from = self._calculate_atmosphere_intensity({"atmosphere_type": from_atmosphere})
        intensity_to = self._calculate_atmosphere_intensity({"atmosphere_type": to_atmosphere})

        diff = intensity_to - intensity_from

        if diff > 3:
            return "dramatic_escalation"
        if diff > 0:
            return "gradual_intensification"
        if diff < -3:
            return "dramatic_deescalation"
        if diff < 0:
            return "gradual_calming"
        return "stable_continuation"

    def _assess_transition_smoothness(self, current: dict[str, Any], next_scene: dict[str, Any]) -> str:
        """遷移スムーズさ評価"""

        intensity_diff = abs(next_scene["intensity"] - current["intensity"])

        if intensity_diff <= 1:
            return "very_smooth"
        if intensity_diff <= 3:
            return "smooth"
        if intensity_diff <= 5:
            return "noticeable"
        return "abrupt"

    def _analyze_mood_consistency(self, mood_arc: list[dict[str, Any]]) -> dict[str, Any]:
        """ムード一貫性分析"""

        return {
            "consistency_score": self._calculate_consistency_score(mood_arc),
            "problematic_transitions": self._identify_problematic_transitions(mood_arc),
            "consistency_recommendations": self._generate_consistency_recommendations(mood_arc)
        }

    def _analyze_emotional_support(self, scene_designs: dict[str, Any], emotion_curve: dict[str, Any]) -> dict[str, Any]:
        """感情的サポート分析"""

        return {
            "emotion_scene_alignment": self._assess_emotion_scene_alignment(scene_designs, emotion_curve),
            "support_effectiveness": self._measure_support_effectiveness(scene_designs, emotion_curve),
            "improvement_opportunities": self._identify_improvement_opportunities(scene_designs, emotion_curve)
        }

    def _compile_atmosphere_techniques(self, scene_designs: dict[str, Any]) -> list[dict[str, str]]:
        """雰囲気技法編纂"""

        techniques = []

        for scene_id, design in scene_designs.items():
            scene_techniques = {
                "scene": scene_id,
                "primary_technique": self._identify_primary_technique(design),
                "supporting_techniques": self._identify_supporting_techniques(design),
                "effectiveness": self._assess_technique_effectiveness(design)
            }
            techniques.append(scene_techniques)

        return techniques

    # Helper methods for visual construction
    def _extract_scene_colors(self, design: dict[str, Any]) -> dict[str, str]:
        """シーンカラー抽出"""

        lighting_color = design["lighting"]["base_lighting"]["color"]
        weather = design["weather_conditions"]["condition"]
        atmosphere = design["atmosphere_type"]

        color_map = {
            "warm_gold": "#FFD700",
            "white": "#FFFFFF",
            "orange_red": "#FF4500",
            "varied": "#888888"
        }

        base_color = color_map.get(lighting_color, "#CCCCCC")

        # 天候による調整
        weather_adjustments = {
            "晴れ": {"saturation": "high", "brightness": "bright"},
            "曇り": {"saturation": "low", "brightness": "dim"},
            "雨": {"saturation": "muted", "brightness": "dark"},
            "霧": {"saturation": "very_low", "brightness": "soft"}
        }

        adjustment = weather_adjustments.get(weather, {"saturation": "normal", "brightness": "normal"})

        return {
            "primary_color": base_color,
            "saturation": adjustment["saturation"],
            "brightness": adjustment["brightness"],
            "mood_influence": atmosphere
        }

    def _extract_composition_elements(self, design: dict[str, Any]) -> list[str]:
        """構成要素抽出"""

        elements = []

        # ロケーション要素
        elements.extend(design["location"]["suggested_locations"])

        # ムード要素
        for mood_element in design["mood_elements"]:
            elements.append(mood_element["element"])

        # インタラクティブ要素
        for interactive in design["interactive_elements"]:
            elements.append(interactive["element"])

        return elements

    def _create_visual_flow(self, scene_designs: dict[str, Any]) -> list[dict[str, str]]:
        """視覚的フロー作成"""

        flow = []

        for scene_id in sorted(scene_designs.keys()):
            design = scene_designs[scene_id]
            flow_point = {
                "scene": scene_id,
                "visual_focus": design["sensory_focus"][0]["focus"] if design["sensory_focus"] else "general",
                "composition": design["space_description"]["spatial_layout"]["structure"],
                "lighting_effect": design["lighting"]["overall_effect"]
            }
            flow.append(flow_point)

        return flow

    def _create_imagery_catalog(self, scene_designs: dict[str, Any]) -> dict[str, list[str]]:
        """イメージカタログ作成"""

        catalog = {
            "architectural": [],
            "natural": [],
            "atmospheric": [],
            "symbolic": [],
            "interactive": []
        }

        for design in scene_designs.values():
            # 建築的要素
            catalog["architectural"].extend(design["space_description"]["key_features"])

            # 自然要素
            weather_desc = design["weather_conditions"]["description"]
            if weather_desc != "特に印象的でない天候":
                catalog["natural"].append(weather_desc)

            # 雰囲気要素
            for mood in design["mood_elements"]:
                catalog["atmospheric"].append(mood["description"])

            # 象徴的要素
            symbolic = design["space_description"]["symbolic_meaning"]["primary_symbol"]
            catalog["symbolic"].append(symbolic)

            # インタラクティブ要素
            for interactive in design["interactive_elements"]:
                catalog["interactive"].append(interactive["element"])

        # 重複除去
        for category in catalog:
            catalog[category] = list(set(catalog[category]))

        return catalog

    # Additional helper methods
    def _get_lighting_implications(self, time: str) -> list[str]:
        """照明含意取得"""
        implications_map = {
            "朝": ["柔らかい光", "希望的", "新鮮"],
            "昼": ["明るく鮮明", "活動的", "現実的"],
            "夕方〜夜": ["劇的な陰影", "情熱的", "ドラマチック"],
            "夜〜翌朝": ["人工照明", "親密", "神秘的"]
        }
        return implications_map.get(time, ["標準的な照明"])

    def _get_mood_impact(self, time: str) -> str:
        """ムード影響取得"""
        impact_map = {
            "朝": "清新で希望に満ちたムード",
            "昼": "活動的で現実的なムード",
            "夕方〜夜": "情感的で劇的なムード",
            "夜〜翌朝": "静かで内省的なムード"
        }
        return impact_map.get(time, "ニュートラルなムード")

    def _get_weather_sensory_elements(self, weather: str) -> list[str]:
        """天候感覚要素取得"""
        sensory_map = {
            "晴れ": ["温かい日差し", "爽やかな風", "明るい光"],
            "曇り": ["重い空気", "抑えられた光", "風の音"],
            "雨": ["雨音", "湿った空気", "水滴の感触"],
            "霧": ["視界不良", "湿気", "静寂"]
        }
        return sensory_map.get(weather, ["通常の天候感覚"])

    def _assess_lighting_mood(self, base: dict[str, str], adjustment: dict[str, str]) -> str:
        """照明ムード評価"""
        base_quality = base["quality"]
        intensity = adjustment["intensity"]

        combinations = {
            ("soft", "gentle"): "温かく安らかなムード",
            ("bright", "normal"): "明るく健全なムード",
            ("dramatic", "contrasted"): "劇的で印象的なムード",
            ("artificial", "dim"): "神秘的で内密なムード"
        }

        return combinations.get((base_quality, intensity), "標準的な照明ムード")

    # Consistency and effectiveness methods
    def _calculate_consistency_score(self, mood_arc: list[dict[str, Any]]) -> float:
        """一貫性スコア計算"""
        if len(mood_arc) < 2:
            return 1.0

        total_transitions = len(mood_arc) - 1
        smooth_transitions = 0

        for i in range(total_transitions):
            current_intensity = mood_arc[i]["intensity"]
            next_intensity = mood_arc[i + 1]["intensity"]

            if abs(next_intensity - current_intensity) <= 3:
                smooth_transitions += 1

        return smooth_transitions / total_transitions

    def _identify_problematic_transitions(self, mood_arc: list[dict[str, Any]]) -> list[str]:
        """問題のある遷移特定"""
        problems = []

        for i in range(len(mood_arc) - 1):
            current = mood_arc[i]
            next_mood = mood_arc[i + 1]

            intensity_jump = abs(next_mood["intensity"] - current["intensity"])

            if intensity_jump > 5:
                problems.append(f"{current['scene']}から{next_mood['scene']}への急激な変化")

        return problems

    def _generate_consistency_recommendations(self, mood_arc: list[dict[str, Any]]) -> list[str]:
        """一貫性推奨事項生成"""
        recommendations = []

        # 全体的なパターン分析
        intensities = [point["intensity"] for point in mood_arc]

        if max(intensities) - min(intensities) > 7:
            recommendations.append("感情の起伏が激しすぎる可能性があります")

        if len(set(intensities)) < len(intensities) * 0.5:
            recommendations.append("感情変化にもう少し多様性を加えることを推奨")

        return recommendations

    def _assess_emotion_scene_alignment(self, scene_designs: dict[str, Any], emotion_curve: dict[str, Any]) -> dict[str, Any]:
        """感情シーン一致度評価"""
        alignment = {"aligned_scenes": 0, "total_scenes": len(scene_designs), "alignment_score": 0.0}

        peaks = emotion_curve.get("peak_moments", [])
        if not peaks:
            alignment["alignment_score"] = 0.5  # デフォルト
            return alignment

        aligned_count = 0
        for design in scene_designs.values():
            scene_atmosphere = design["atmosphere_type"]

            # 雰囲気と感情ピークの一致をチェック
            for peak in peaks:
                if self._atmosphere_matches_emotion(scene_atmosphere, peak.get("type", "")):
                    aligned_count += 1
                    break

        alignment["aligned_scenes"] = aligned_count
        alignment["alignment_score"] = aligned_count / len(scene_designs) if scene_designs else 0.0

        return alignment

    def _atmosphere_matches_emotion(self, atmosphere: str, emotion_type: str) -> bool:
        """雰囲気と感情の一致判定"""
        matches = {
            "tense": ["tension", "conflict", "anxiety"],
            "dramatic": ["excitement", "climax", "intensity"],
            "peaceful": ["resolution", "calm", "satisfaction"],
            "mysterious": ["curiosity", "uncertainty", "intrigue"]
        }

        matching_emotions = matches.get(atmosphere, [])
        return emotion_type in matching_emotions

    def _measure_support_effectiveness(self, scene_designs: dict[str, Any], emotion_curve: dict[str, Any]) -> float:
        """サポート効果測定"""
        # 簡単な効果測定（実際はより複雑な分析が必要）
        alignment = self._assess_emotion_scene_alignment(scene_designs, emotion_curve)
        return alignment["alignment_score"]

    def _identify_improvement_opportunities(self, scene_designs: dict[str, Any], emotion_curve: dict[str, Any]) -> list[str]:
        """改善機会特定"""
        opportunities = []

        alignment = self._assess_emotion_scene_alignment(scene_designs, emotion_curve)

        if alignment["alignment_score"] < 0.7:
            opportunities.append("情景設計と感情曲線の一致度向上")

        # 雰囲気の多様性チェック
        atmospheres = [design["atmosphere_type"] for design in scene_designs.values()]
        if len(set(atmospheres)) < len(atmospheres) * 0.6:
            opportunities.append("雰囲気の多様性向上")

        return opportunities

    # Technique identification methods
    def _identify_primary_technique(self, design: dict[str, Any]) -> str:
        """主要技法特定"""
        atmosphere = design["atmosphere_type"]

        technique_map = {
            "peaceful": "穏やかな描写技法",
            "tense": "緊張感創出技法",
            "dramatic": "劇的演出技法",
            "mysterious": "神秘的雰囲気技法"
        }

        return technique_map.get(atmosphere, "標準的描写技法")

    def _identify_supporting_techniques(self, design: dict[str, Any]) -> list[str]:
        """サポート技法特定"""
        techniques = []

        # 照明技法
        lighting_effect = design["lighting"]["overall_effect"]
        techniques.append(f"照明効果: {lighting_effect}")

        # 感覚技法
        if design["sensory_focus"]:
            primary_sense = design["sensory_focus"][0]["sense"]
            techniques.append(f"感覚強調: {primary_sense}")

        # 空間技法
        scale_impression = design["space_description"]["scale_impression"]
        techniques.append(f"空間演出: {scale_impression}")

        return techniques

    def _assess_technique_effectiveness(self, design: dict[str, Any]) -> str:
        """技法効果評価"""
        # 複数要素の組み合わせ効果を評価
        elements_count = len(design["mood_elements"])
        sensory_diversity = len(design["sensory_focus"])
        interactive_elements = len(design["interactive_elements"])

        total_score = elements_count + sensory_diversity + interactive_elements

        if total_score >= 8:
            return "very_effective"
        if total_score >= 5:
            return "effective"
        if total_score >= 3:
            return "moderately_effective"
        return "needs_improvement"
