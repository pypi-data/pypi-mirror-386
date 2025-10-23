"""生成エピソードプロットエンティティ

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.project_time import project_now


@dataclass
class GeneratedEpisodePlot:
    """生成エピソードプロットエンティティ

    Claude Codeによって生成されたエピソード固有のプロット情報を管理する。
    章別プロット情報を基に、より詳細なエピソード単位のプロット要素を含む。
    """

    episode_number: int
    title: str
    summary: str
    scenes: list[dict[str, Any]]
    key_events: list[str]
    viewpoint: str
    tone: str
    conflict: str
    resolution: str
    generation_timestamp: datetime
    source_chapter_number: int
    quality_score: float = 0.0
    preview_context: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)

        if not self.title.strip():
            msg = "タイトルは空であってはいけません"
            raise ValueError(msg)

        if not self.summary.strip():
            msg = "概要は空であってはいけません"
            raise ValueError(msg)

        if self.source_chapter_number < 1:
            msg = "ソース章番号は1以上である必要があります"
            raise ValueError(msg)

    @classmethod
    def from_claude_response(
        cls,
        episode_number: int,
        source_chapter_number: int,
        claude_response: dict[str, Any],
    ) -> "GeneratedEpisodePlot":
        """Claude Codeレスポンスから生成エピソードプロットを作成

        Args:
            episode_number: エピソード番号
            source_chapter_number: ソース章番号
            claude_response: Claude Codeからのレスポンス

        Returns:
            GeneratedEpisodePlot: 生成エピソードプロット

        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        required_fields = ["title", "summary", "scenes", "key_events", "viewpoint", "tone", "conflict", "resolution"]

        for field in required_fields:
            if field not in claude_response:
                msg = f"必須フィールドが不足しています: {field}"
                raise ValueError(msg)

        return cls(
            episode_number=episode_number,
            title=claude_response["title"],
            summary=claude_response["summary"],
            scenes=claude_response["scenes"],
            key_events=claude_response["key_events"],
            viewpoint=claude_response["viewpoint"],
            tone=claude_response["tone"],
            conflict=claude_response["conflict"],
            resolution=claude_response["resolution"],
            generation_timestamp=project_now().datetime,
            source_chapter_number=source_chapter_number,
        )

    def _build_key_events_list(self) -> list[dict[str, str]]:
        """キーイベントリストを構築"""
        # 基本のキーイベント（最大3つまで）
        events_to_use = self.key_events[:3] if len(self.key_events) > 3 else self.key_events
        key_events_list = [
            {
                "event": event,
                "description": f"{event}の詳細な描写。キャラクターの行動、心情の変化、技術的要素など具体的に記述。",
            }
            for event in events_to_use
        ]

        # キーイベントが2未満の場合は追加イベントを加える
        if len(self.key_events) < 2:
            key_events_list.append({
                "event": "追加イベント",
                "description": "続くイベントの詳細。前のイベントからの流れや関連性も含めて記述。",
            })

        return key_events_list

    def to_yaml_dict(self) -> dict[str, Any]:
        """テンプレート完全準拠のYAML保存用辞書形式に変換

        話別プロットテンプレート.yamlの342行構造に完全対応

        Returns:
            dict[str, Any]: テンプレート準拠のYAML保存用辞書
        """
        payload = {
            # Header Metadata - ヘッダー情報 (テンプレート準拠)
            "metadata": {
                "version": "1.0.0",
                "last_updated": self.generation_timestamp.strftime("%Y-%m-%d"),
                "source": "Claude Code Generated",
                "purpose": "AI生成エピソードプロット",
                "compatibility": ["claude-3", "claude-4", "claude-code"],
                "target_audience": "執筆者・編集者",
                "quality_score": float(self.quality_score),
                "previous_episode_preview": self.preview_context or {},
            },
            # Basic Episode Information - 基本情報 (テンプレート完全対応)
            "episode_info": {
                "episode_number": self.episode_number,
                "title": self.title,
                "chapter_number": self.source_chapter_number,
                "theme": f"[Claude生成] {self.title}の主要テーマ",
                "purpose": f"第{self.episode_number}話の物語上の役割と目的",
                "emotional_core": f"読者に{self.tone}の感情を与える",
            },
            # Viewpoint Information - 視点情報 (テンプレート準拠)
            "viewpoint_info": {
                "viewpoint": self.viewpoint if self.viewpoint else "三人称単元視点",
                "character": "[視点キャラクター名]",
            },
            # Episode Synopsis - 概要 (テンプレート準拠)
            "synopsis": self.summary,
            # Key Events - 主要イベント (テンプレート準拠)
            "key_events": self._build_key_events_list(),
            # Story Structure - 物語構造（三幕構成）(テンプレート完全準拠)
            "story_structure": {
                "setup": {
                    "duration": "冒頭～問題発生まで",
                    "purpose": "状況設定・キャラクター提示",
                    "scene_001": {
                        "title": "導入シーン",
                        "location": f"[Claude生成] {self.scenes[0].get('setting', '未指定場所') if self.scenes else '場所の詳細'}",
                        "time": "[時間設定]",
                        "weather": "[天候・雰囲気]",
                        "opening_description": f"[Claude生成] {self.scenes[0].get('description', 'シーン説明') if self.scenes else 'シーンの開始描写'}",
                        "character_focus": {
                            "main_character": "[主人公の状態・心境]",
                            "supporting_characters": "[その他キャラクターの状況]",
                            "relationships": "[キャラクター間の関係性]",
                        },
                    },
                },
                "confrontation": {
                    "duration": "問題発生～クライマックス手前まで",
                    "purpose": "困難・対立・成長プロセス",
                    "scene_002": {
                        "title": "展開シーン",
                        "conflict_type": self.conflict if self.conflict else "技術的困難 / 人間関係 / 内面的葛藤",
                        "stakes": "[失敗した場合の結果]",
                        "technical_elements": {
                            "programming_concepts": "[使用するプログラミング概念]",
                            "magic_system": "[魔法システムの詳細]",
                            "world_building": "[世界観の拡張要素]",
                        },
                        "character_development": {
                            "growth_moments": "[キャラクターの成長機会]",
                            "relationship_changes": "[関係性の変化]",
                            "internal_conflicts": "[内面的な葛藤]",
                        },
                    },
                },
                "resolution": {
                    "duration": "クライマックス～エピソード終了",
                    "purpose": "問題解決・成長の確認・次話への布石",
                    "turning_point": {
                        "title": "[転換点のタイトル]",
                        "timing": "第二幕終盤〜第三幕開始",
                        "duration": "短期集中型",
                        "turning_point_type": {
                            "category": "internal_transformation",
                            "trigger_event": "[転換を引き起こす具体的出来事]",
                            "catalyst": "[変化のきっかけとなる要因]",
                        },
                        "character_transformation": {
                            "protagonist": {
                                "before_state": "[転換前の主人公の状態]",
                                "transformation_moment": "[変化の瞬間の詳細描写]",
                                "after_state": "[転換後の新しい状態]",
                                "internal_dialogue": "[転換時の主人公の内面描写]",
                                "external_manifestation": "[変化が外部に現れる方法]",
                            },
                            "supporting_characters": {
                                "reactions": "[他キャラクターの反応・驚き・理解]",
                                "relationship_shifts": "[関係性の変化・再定義]",
                                "influence_received": "[転換点が他キャラに与える影響]",
                            },
                        },
                        "technical_breakthrough": {
                            "programming_concept": "[関連するプログラミング概念]",
                            "magic_system_evolution": "[魔法システムの発展・理解深化]",
                            "debug_moment": "[問題解決・バグ発見の瞬間]",
                            "code_metaphor": "[プログラミングと転換点の比喩表現]",
                            "educational_value": "[読者が学べる技術的洞察]",
                        },
                        "emotional_core": {
                            "primary_emotion": self.tone if self.tone else "[転換点で表現する主要感情]",
                            "emotional_journey": [
                                {
                                    "phase": "感情変化の段階1",
                                    "emotion": "fear / anxiety / confusion",
                                    "description": "[転換前の感情状態]",
                                },
                                {
                                    "phase": "感情変化の段階2",
                                    "emotion": "determination / resolve / understanding",
                                    "description": "[転換中の感情変化]",
                                },
                                {
                                    "phase": "感情変化の段階3",
                                    "emotion": "hope / confidence / growth",
                                    "description": "[転換後の新しい感情状態]",
                                },
                            ],
                            "reader_impact": "[読者に与えるべき感情的効果]",
                            "catharsis_moment": "[感情的カタルシスの描写方法]",
                        },
                        "structural_function": {
                            "setup_payoff": "[第一幕で仕込んだ要素の回収]",
                            "conflict_resolution": self.resolution
                            if self.resolution
                            else "[第二幕の対立・困難の解決方法]",
                            "theme_expression": "[エピソードテーマの集約表現]",
                            "foreshadowing_planted": "[次話以降への伏線設置]",
                        },
                        "writing_direction": {
                            "pacing": "[緊張感のあるテンポ]",
                            "viewpoint_focus": "[誰の視点から転換点を描くか]",
                            "sensory_details": "[五感を使った臨場感の演出]",
                            "dialogue_importance": "[重要な台詞・決定的な言葉]",
                            "scene_atmosphere": "[シーンの雰囲気・環境描写]",
                            "technical_writing_notes": [
                                "[プログラミング概念の自然な組み込み方]",
                                "[専門用語の読者理解への配慮]",
                                "[技術的正確性と物語性のバランス]",
                            ],
                        },
                        "quality_validation": {
                            "logical_consistency": "[転換の論理的妥当性チェック]",
                            "character_believability": "[キャラクターの行動・変化の自然さ]",
                            "emotional_authenticity": "[感情表現の真実性・説得力]",
                            "technical_accuracy": "[プログラミング要素の正確性]",
                            "reader_engagement": "[読者の感情移入・興味維持]",
                        },
                    },
                    "climax_scene": {
                        "title": "クライマックス",
                        "resolution_method": self.resolution if self.resolution else "[問題解決の方法]",
                        "character_achievements": "[キャラクターの達成・成長]",
                        "emotional_payoff": "[感情的なカタルシス]",
                    },
                    "ending_scene": {
                        "title": "結末・次話への布石",
                        "loose_ends": "[残された謎・課題]",
                        "foreshadowing": "[将来への伏線]",
                        "character_state": "[エピソード終了時のキャラクター状態]",
                    },
                },
            },
            # Character Details - キャラクター詳細 (テンプレート準拠)
            "characters": {
                "main_character": {
                    "name": "[主人公名]",
                    "starting_state": "[エピソード開始時の状態]",
                    "arc": "[このエピソードでの変化・成長]",
                    "ending_state": "[エピソード終了時の状態]",
                    "key_moments": ["[重要な行動・決断のシーン]", "[成長を示すシーン]"],
                    "dialogue_highlights": ["[印象的なセリフ1]", "[印象的なセリフ2]"],
                },
                "supporting_character": {
                    "name": "[サポートキャラクター名]",
                    "role": "[このエピソードでの役割]",
                    "interactions": "[主人公との関わり方]",
                    "development": "[キャラクターの変化・貢献]",
                },
            },
            # Technical Elements - 技術的要素 (テンプレート準拠)
            "technical_elements": {
                "programming_concepts": [
                    {
                        "concept": "[使用するプログラミング概念1]",
                        "explanation": "[どのように物語に組み込むか]",
                        "educational_value": "[読者が学べる内容]",
                    }
                ],
                "magic_system": {
                    "spell_types": "[使用される魔法の種類]",
                    "mechanics": "[魔法の仕組み・制限]",
                    "innovations": "[新しい技術・アプローチ]",
                },
                "world_building": {
                    "locations": "[新しく登場する場所]",
                    "society_aspects": "[社会システムの描写]",
                    "cultural_elements": "[文化的背景・慣習]",
                },
            },
            # Emotional Elements - 感情的要素 (テンプレート準拠)
            "emotional_elements": {
                "primary_emotion": self.tone if self.tone else "[読者に与える主要な感情]",
                "emotional_journey": [
                    {"stage": "感情の変遷1", "description": "[どのような感情をどう描くか]"},
                    {"stage": "感情の変遷2", "description": "[感情の発展・変化]"},
                ],
                "relationship_dynamics": [
                    {
                        "relationship": "[キャラクター間の関係]",
                        "development": "[関係性の変化・深化]",
                        "key_scenes": "[関係性が分かるシーン]",
                    }
                ],
            },
            # Plot Elements - 伏線・テーマ要素 (テンプレート準拠)
            "plot_elements": {
                "foreshadowing": [
                    {
                        "element": "[将来への伏線1]",
                        "placement": "[どのシーンで提示するか]",
                        "significance": "[物語全体での意味]",
                    }
                ],
                "themes": [
                    {
                        "theme": f"[Claude生成] {self.title}のテーマ",
                        "expression": "[どのように表現するか]",
                        "character_connection": "[キャラクターとの関連]",
                    }
                ],
                "mysteries": [
                    {"mystery": "[提示される謎]", "clues": "[与えられる手がかり]", "development": "[謎の発展・深化]"}
                ],
            },
            # Writing Notes - 執筆メモ (テンプレート準拠)
            "writing_notes": {
                "viewpoint": self.viewpoint if self.viewpoint else "[視点人物・語り方]",
                "tone": self.tone if self.tone else "[エピソード全体のトーン・雰囲気]",
                "pacing": "[テンポ・リズムの注意点]",
                "technical_accuracy": ["[プログラミング概念の正確性チェック]", "[魔法システムの一貫性確認]"],
                "character_consistency": ["[キャラクターの言動の一貫性]", "[前話からの成長の自然さ]"],
                "reader_engagement": ["[読者の興味を引く要素]", "[感情移入しやすい描写]"],
            },
            # Quality Check Points - 品質チェック項目 (テンプレート準拠)
            "quality_checkpoints": {
                "story_structure": ["[三幕構成の適切なバランス]", "[各シーンの目的明確化]", "[シーン間の自然な流れ]"],
                "character_development": {
                    "main_characters": {
                        "hero": {
                            "growth_indicators": ["[主人公の成長が感じられる]", "[内面描写の深度適切]"],
                            "relationship_changes": ["[ヒロインとの関係性発展]", "[仲間との信頼関係構築]"],
                        },
                        "heroine": {
                            "growth_indicators": ["[ヒロインの成長が感じられる]", "[自立性・積極性の向上]"],
                            "relationship_changes": ["[主人公との相互理解深化]", "[自信獲得と表現力向上]"],
                        },
                    }
                },
                "technical_integration": [
                    "[プログラミング要素の自然な組み込み]",
                    "[教育的価値の提供]",
                    "[専門用語の適切な説明]",
                ],
            },
            # Reader Considerations - 想定読者層への配慮 (テンプレート準拠)
            "reader_considerations": {
                "accessibility": ["[プログラミング初心者への配慮]", "[専門用語の適切な解説]", "[技術以外の魅力要素]"],
                "engagement": ["[キャラクターへの共感しやすさ]", "[ストーリーの分かりやすさ]", "[次話への期待感醸成]"],
            },
            # Next Episode Connection - 次話への連携 (テンプレート準拠)
            "next_episode_connection": {
                "unresolved_elements": "[次話に持ち越す要素]",
                "character_growth_trajectory": "[キャラクター成長の方向性]",
                "plot_advancement": "[物語進行の次のステップ]",
                "reader_expectations": "[読者に与える期待・疑問]",
                "preview_hook": (self.preview_context or {}).get("preview", {}).get("hook"),
                "preview_quality": (self.preview_context or {}).get("quality"),
                "preview_source": (self.preview_context or {}).get("source"),
            },
            # Production Information - 制作情報 (テンプレート準拠)
            "production_info": {
                "creation_date": self.generation_timestamp.strftime("%Y-%m-%d"),
                "last_updated": self.generation_timestamp.strftime("%Y-%m-%d"),
                "status": "Claude Code生成",
                "word_count_target": 6000,
                "estimated_reading_time": "20分",
            },
            # Usage Notes - 使用方法・注意事項 (テンプレート準拠)
            "usage_notes": f"""このプロットファイルはClaude Codeによって生成されました。

使用時の注意点：
1. 基本情報（episode_info）を確認・調整してください
2. 物語構造（story_structure）を三幕構成で整理してください
3. キャラクター中心の展開を心がけてください
4. 技術要素は物語に自然に組み込んでください
5. 読者の感情に訴える要素を重視してください

生成情報：
- 生成日時: {self.generation_timestamp.isoformat()}
- 元となる章: 第{self.source_chapter_number}章
- エピソード: 第{self.episode_number}話「{self.title}」

注意：
- プログラミング知識がない読者も楽しめるように配慮
- キャラクター間の関係性を丁寧に描写
- 次話への興味を持続させる終わり方を意識
- 世界観の一貫性を保持
""",
        }

        payload.update({
            "episode_number": self.episode_number,
            "title": self.title,
            "summary": self.summary,
            "source_chapter": self.source_chapter_number,
        })
        payload["generated_plot"] = {
            "scenes": self.scenes,
            "key_events": self.key_events,
            "viewpoint": self.viewpoint,
            "tone": self.tone,
            "conflict": self.conflict,
            "resolution": self.resolution,
        }
        payload["generation_metadata"] = {
            "generated_by": "Claude Code",
            "generated_at": self.generation_timestamp.isoformat(),
            "source_chapter_number": self.source_chapter_number,
        }
        return payload


    def get_scene_count(self) -> int:
        """シーン数を取得

        Returns:
            int: シーン数
        """
        return len(self.scenes)

    def get_key_event_count(self) -> int:
        """キーイベント数を取得

        Returns:
            int: キーイベント数
        """
        return len(self.key_events)

    def has_conflict_resolution(self) -> bool:
        """コンフリクトと解決策が設定されているかチェック

        Returns:
            bool: 両方設定されている場合True
        """
        return bool(self.conflict.strip() and self.resolution.strip())

    def get_plot_structure_summary(self) -> dict[str, Any]:
        """プロット構造の要約を取得

        Returns:
            dict[str, Any]: プロット構造の要約
        """
        return {
            "episode_number": self.episode_number,
            "title": self.title,
            "scene_count": self.get_scene_count(),
            "key_event_count": self.get_key_event_count(),
            "viewpoint": self.viewpoint,
            "tone": self.tone,
            "has_conflict_resolution": self.has_conflict_resolution(),
            "generation_source": f"chapter{self.source_chapter_number:02d}",
        }
