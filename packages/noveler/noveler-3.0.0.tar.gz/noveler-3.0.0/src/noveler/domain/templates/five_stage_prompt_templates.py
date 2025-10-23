#!/usr/bin/env python3
"""5段階分割プロンプトテンプレート

仕様書: SPEC-FIVE-STAGE-001
各段階に最適化されたプロンプトテンプレート定義
"""

from noveler.domain.value_objects.five_stage_writing_execution import ExecutionStage, StagePromptTemplate


class FiveStagePromptTemplateFactory:
    """5段階プロンプトテンプレートファクトリー"""

    @staticmethod
    def create_all_templates() -> dict[ExecutionStage, StagePromptTemplate]:
        """全段階のプロンプトテンプレート作成"""
        return {
            ExecutionStage.DATA_COLLECTION: FiveStagePromptTemplateFactory._create_data_collection_template(),
            ExecutionStage.PLOT_ANALYSIS: FiveStagePromptTemplateFactory._create_plot_analysis_template(),
            ExecutionStage.EPISODE_DESIGN: FiveStagePromptTemplateFactory._create_episode_design_template(),
            ExecutionStage.MANUSCRIPT_WRITING: FiveStagePromptTemplateFactory._create_manuscript_writing_template(),
            ExecutionStage.QUALITY_FINALIZATION: FiveStagePromptTemplateFactory._create_quality_finalization_template(),
        }

    @staticmethod
    def _create_data_collection_template() -> StagePromptTemplate:
        """Stage 1: データ収集・準備テンプレート"""
        template_content = """# Stage 1: データ収集・準備

## 実行概要
- **段階**: {stage_name}
- **セッションID**: {session_id}
- **対象エピソード**: 第{episode_number:03d}話
- **予想ターン数**: {expected_turns}ターン

## 実行指示

### 主要タスク
1. **既存ファイル調査・読み込み**
   - 章別プロットファイルの確認と読み込み
   - キャラクター設定ファイルの確認と読み込み
   - 世界観設定ファイルの確認と読み込み
   - 前回エピソードまでの原稿内容確認

2. **プロジェクト構造分析**
   - ディレクトリ構造の把握
   - 利用可能なデータファイルのリスト作成
   - データファイル間の関連性分析

3. **基礎情報整理**
   - エピソード基本情報の整理
   - 執筆設定の確認（ジャンル: {genre}, 視点: {viewpoint}, 視点キャラクター: {viewpoint_character}）
   - 目標文字数: {word_count_target}文字
   - カスタム要件: {custom_requirements}

### 出力要求
以下のJSON形式で結果を出力してください：

```json
{{
    "stage": "data_collection",
    "status": "completed",
    "collected_data": {{
        "chapter_plots": {{
            "files_found": ["ファイル名リスト"],
            "content_summary": "プロット内容要約",
            "key_plot_points": ["重要プロット点リスト"]
        }},
        "character_data": {{
            "files_found": ["キャラクターファイルリスト"],
            "main_characters": ["主要キャラクター名リスト"],
            "character_relationships": "キャラクター関係性情報"
        }},
        "world_settings": {{
            "files_found": ["世界観ファイルリスト"],
            "key_settings": ["重要設定項目リスト"],
            "setting_constraints": "設定上の制約情報"
        }},
        "previous_episodes": {{
            "latest_episode": 15,
            "story_progress": "物語進行状況",
            "unresolved_plot_threads": ["未解決プロット線"]
        }},
        "project_structure": {{
            "directories_found": ["ディレクトリリスト"],
            "data_completeness": "データ完全性評価",
            "missing_files": ["不足ファイルリスト"]
        }}
    }},
    "data_quality_assessment": {{
        "completeness_score": 85,
        "consistency_score": 90,
        "issues_found": ["データ品質問題リスト"],
        "recommendations": ["改善提案リスト"]
    }},
    "next_stage_preparation": {{
        "ready_for_analysis": true,
        "critical_data_available": true,
        "notes": "次段階への引き継ぎ事項"
    }}
}}
```

### 重要な注意事項
- **効率重視**: 必要最小限のデータ読み込みに集中
- **構造化**: 後続段階で使いやすい形式でデータを整理
- **品質チェック**: データの完全性と一貫性を確認
- **ターン制限**: {expected_turns}ターン以内での完了を目標

### エラーハンドリング
データが不完全または不整合の場合は、影響度を評価し、後続段階での対処法を提案してください。

前段階結果参照:
{previous_results}"""

        return StagePromptTemplate(
            stage=ExecutionStage.DATA_COLLECTION,
            template_content=template_content,
            required_context_keys=[],
            output_format="json",
            max_turns_override=None,
        )

    @staticmethod
    def _create_plot_analysis_template() -> StagePromptTemplate:
        """Stage 2: プロット分析・設計テンプレート"""
        template_content = """# Stage 2: プロット分析・設計

## 実行概要
- **段階**: {stage_name}
- **セッションID**: {session_id}
- **対象エピソード**: 第{episode_number:03d}話
- **予想ターン数**: {expected_turns}ターン

## 実行指示

### 主要タスク
1. **章別プロット詳細分析**
   - 収集データ基づく章別プロットの解析
   - 第{episode_number:03d}話の位置付け確認
   - 全体プロット内での役割分析

2. **キャラクター分析**
   - 主要キャラクターの現在状況把握
   - キャラクター成長軌道分析
   - 関係性変化の予測

3. **世界観・設定分析**
   - 現在の世界観状況確認
   - 設定制約の把握
   - 新要素導入可能性検討

### 前段階データ活用
以下の収集データを分析に活用してください：
- 章別プロット: {chapter_plots}
- キャラクター情報: {character_data}
- キャラクター口調辞書: {character_voice_patterns}
- 世界観設定: {world_settings}
- 物語進行状況: {previous_episodes}
- 執筆品質ルール: {quality_rules_summary}

### 出力要求
以下のJSON形式で結果を出力してください：

```json
{{
    "stage": "plot_analysis",
    "status": "completed",
    "plot_analysis_results": {{
        "episode_position": {{
            "chapter_context": "章内での位置付け",
            "story_arc_position": "ストーリーアークでの位置",
            "tension_curve_position": "緊張曲線での位置"
        }},
        "key_plot_elements": {{
            "primary_conflict": "主要な対立・問題",
            "secondary_conflicts": ["副次的対立リスト"],
            "resolution_targets": ["解決すべき要素リスト"]
        }},
        "character_analysis": {{
            "viewpoint_character_state": {{
                "current_situation": "{viewpoint_character}の現状",
                "emotional_state": "感情状態",
                "goals_and_motivations": "目標と動機",
                "character_arc_position": "キャラクターアーク進行度"
            }},
            "supporting_characters": [
                {{
                    "name": "キャラクター名",
                    "role_in_episode": "エピソードでの役割",
                    "relationship_dynamics": "関係性動向"
                }}
            ]
        }},
        "world_building_elements": {{
            "active_settings": ["使用予定設定リスト"],
            "new_elements_needed": ["新規導入要素"],
            "consistency_considerations": ["設定整合性注意事項"]
        }},
        "foreshadowing_opportunities": {{
            "setup_elements": ["伏線設置要素"],
            "payoff_elements": ["回収要素"],
            "future_connections": ["将来話との接続点"]
        }}
    }},
    "design_recommendations": {{
        "plot_focus_areas": ["重点プロット領域"],
        "character_development_opportunities": ["キャラ成長機会"],
        "pacing_considerations": ["ペース配分考慮事項"],
        "tone_and_mood_targets": "目標トーン・ムード"
    }},
    "next_stage_preparation": {{
        "design_ready": true,
        "key_decisions_made": ["確定済み設計決定"],
        "open_design_questions": ["未決設計課題"]
    }}
}}
```

### 品質基準
- **A30執筆ガイド準拠**: プロット分析はA30基準に準拠
- **論理的一貫性**: 既存プロットとの論理的整合性確保
- **キャラクター真実性**: キャラクター行動の動機付け明確化

前段階結果参照:
{previous_results}"""

        return StagePromptTemplate(
            stage=ExecutionStage.PLOT_ANALYSIS,
            template_content=template_content,
            required_context_keys=["chapter_plots", "character_data", "character_voice_patterns", "world_settings", "previous_episodes", "quality_rules_summary"],
            output_format="json",
            max_turns_override=None,
        )

    @staticmethod
    def _create_episode_design_template() -> StagePromptTemplate:
        """Stage 3: エピソード設計テンプレート"""
        template_content = """# Stage 3: エピソード設計

## 実行概要
- **段階**: {stage_name}
- **セッションID**: {session_id}
- **対象エピソード**: 第{episode_number:03d}話
- **予想ターン数**: {expected_turns}ターン

## 実行指示

### 主要タスク
1. **三幕構成設計**
   - 分析結果に基づく三幕構成の具体化
   - 各幕の展開とターニングポイント設計
   - クライマックスとリゾリューション設計

2. **重要シーン設計**
   - キーシーンの詳細設計
   - シーン間の接続設計
   - 感情的インパクト設計

3. **伏線・展開計画**
   - 伏線設置計画
   - 既存伏線の回収計画
   - 将来への布石計画

### 前段階データ活用
以下の分析結果を設計に反映してください：
- プロット分析: {plot_analysis_results}
- キャラクター分析: {character_analysis}
- 設計推奨事項: {design_recommendations}

### カスタム要件対応
以下の要件を設計に組み込んでください：
{custom_requirements}

### 出力要求
以下のJSON形式で結果を出力してください：

```json
{{
    "stage": "episode_design",
    "status": "completed",
    "episode_design": {{
        "three_act_structure": {{
            "act1": {{
                "percentage": "25%",
                "key_events": ["第1幕重要事件リスト"],
                "character_state_changes": ["キャラクター状態変化"],
                "setup_elements": ["設定・導入要素"],
                "inciting_incident": "きっかけとなる事件"
            }},
            "act2": {{
                "percentage": "50%",
                "key_events": ["第2幕重要事件リスト"],
                "character_development": ["キャラクター発展"],
                "conflict_escalation": ["対立激化要素"],
                "midpoint_twist": "中間点転換"
            }},
            "act3": {{
                "percentage": "25%",
                "key_events": ["第3幕重要事件リスト"],
                "climax_design": "クライマックス設計",
                "resolution_elements": ["解決要素"],
                "story_consequences": ["物語への影響"]
            }}
        }},
        "key_scenes": [
            {{
                "scene_name": "シーン名",
                "act_position": "第X幕",
                "purpose": "シーンの目的",
                "characters_involved": ["参加キャラクター"],
                "setting_location": "舞台設定",
                "emotional_beat": "感情的要素",
                "plot_advancement": "プロット推進要素",
                "character_development": "キャラ成長要素"
            }}
        ],
        "pacing_design": {{
            "opening_pace": "導入部ペース",
            "development_pace": "展開部ペース",
            "climax_pace": "クライマックスペース",
            "conclusion_pace": "結論部ペース",
            "tension_curve": "緊張感変化曲線"
        }},
        "foreshadowing_plan": {{
            "elements_to_setup": [
                {{
                    "element": "伏線要素",
                    "placement_scene": "設置シーン",
                    "subtlety_level": "微妙さレベル",
                    "payoff_timeline": "回収予定"
                }}
            ],
            "elements_to_payoff": [
                {{
                    "element": "回収要素",
                    "setup_reference": "設置済み場所",
                    "payoff_scene": "回収シーン",
                    "impact_level": "インパクトレベル"
                }}
            ]
        }}
    }},
    "writing_guidelines": {{
        "tone_targets": ["目標トーン"],
        "style_considerations": ["文体考慮事項"],
        "viewpoint_consistency": "{viewpoint} ({viewpoint_character}) 一貫性維持",
        "word_count_distribution": {{
            "act1_words": 875,
            "act2_words": 1750,
            "act3_words": 875,
            "total_target": {word_count_target}
        }}
    }},
    "quality_checkpoints": {{
        "a30_compliance_points": ["A30準拠チェック点"],
        "character_consistency_checks": ["キャラ一貫性チェック"],
        "plot_logic_validations": ["プロット論理検証"],
        "pacing_validations": ["ペース妥当性検証"]
    }},
    "next_stage_preparation": {{
        "writing_ready": true,
        "detailed_outline_complete": true,
        "scene_by_scene_plan": "シーン別詳細計画",
        "writing_priorities": ["執筆優先事項"]
    }}
}}
```

### 設計品質基準
- **ドラマティック構造**: 明確な三幕構成と感情的アーク
- **キャラクター動機**: 全キャラクターの行動に明確な動機
- **プロット論理**: 因果関係の明確性と論理的一貫性
- **ペース配分**: 目標文字数に対する適切なペース設定

前段階結果参照:
{previous_results}"""

        return StagePromptTemplate(
            stage=ExecutionStage.EPISODE_DESIGN,
            template_content=template_content,
            required_context_keys=["plot_analysis_results", "character_analysis", "design_recommendations"],
            output_format="json",
            max_turns_override=None,
        )

    @staticmethod
    def _create_manuscript_writing_template() -> StagePromptTemplate:
        """Stage 4: 原稿執筆テンプレート"""
        template_content = """# Stage 4: 原稿執筆

## 実行概要
- **段階**: {stage_name}
- **セッションID**: {session_id}
- **対象エピソード**: 第{episode_number:03d}話
- **予想ターン数**: {expected_turns}ターン（最も重要な段階）

## 実行指示

### 主要タスク
1. **設計に基づく原稿執筆**
   - エピソード設計の忠実な実装
   - 三幕構成に沿った展開
   - キーシーンの効果的な描写

2. **文体・視点調整**
   - {viewpoint} ({viewpoint_character}) の一貫した維持
   - {genre}ジャンルに適した文体
   - 読者との適切な距離感設定

3. **ペース配分調整**
   - 目標文字数 {word_count_target}文字への適切な配分
   - 各幕のバランス調整
   - 緊張感とリズムの制御

### 前段階設計データ活用
以下の設計を実装してください：
- 三幕構成: {three_act_structure}
- キーシーン: {key_scenes}
- ペース設計: {pacing_design}
- 執筆ガイドライン: {writing_guidelines}
- キャラクター口調パターン: {character_voice_patterns}
- 執筆品質ルール適用: {quality_rules_application}

### 品質要求
- **A30執筆ガイド準拠**: 禁止表現・推奨表現の厳守
- **定量品質ルール適用**: {emotion_expression_rules}
- **会話比率管理**: {dialogue_ratio_targets}
- **キャラクター相互作用**: {character_interaction_requirements}
- **説明制限遵守**: {explanation_limits}
- **文字数精度**: 目標±10%以内での完成
- **キャラクター一貫性**: 既存設定との整合性
- **プロット論理性**: 設計された因果関係の忠実な実装

### 🚨 重要: 完全な原稿出力が必須 🚨
- **必ず実際の原稿内容を "manuscript" フィールドに含めてください**
- **メタデータのみの出力は絶対に避けてください**
- **原稿内容が空の場合は実行失敗です**
- **最低3000文字以上の実際の原稿を記述してください**

### 出力要求
以下のJSON形式で結果を出力してください：

```json
{{
    "stage": "manuscript_writing",
    "status": "completed",
    "manuscript": "### 第{episode_number:03d}話 [タイトル]\\n\\n　直人は朝の光で目を覚ました。\\n　「今日もまた、新しい一日が始まる」\\n　彼は窓から差し込む光を見つめながら、ベッドから起き上がった。\\n\\n[実際の原稿を最低3000文字以上で記述]\\n\\n---\\n\\n- 文字数: [実際の文字数]\\n- 実装シーン数: [シーン数]\\n- 三幕構成実装度: [X/3]",
    "writing_metrics": {{
        "actual_word_count": 0,
        "target_achievement_rate": 0.0,
        "act_distribution": {{
            "act1_words": 0,
            "act2_words": 0,
            "act3_words": 0
        }},
        "scene_implementation": {{
            "designed_scenes": 0,
            "implemented_scenes": 0,
            "scene_success_rate": 0.0
        }}
    }},
    "quality_self_assessment": {{
        "a30_compliance": {{
            "prohibited_expressions_avoided": true,
            "recommended_expressions_used": true,
            "compliance_score": 95
        }},
        "character_consistency": {{
            "viewpoint_maintenance": true,
            "character_voice_consistency": true,
            "relationship_consistency": true
        }},
        "plot_implementation": {{
            "design_adherence": true,
            "logical_flow": true,
            "pacing_effectiveness": true
        }},
        "writing_quality": {{
            "readability": true,
            "emotional_impact": true,
            "genre_appropriateness": true
        }}
    }},
    "implementation_notes": {{
        "design_adaptations": ["設計からの調整事項"],
        "creative_additions": ["創造的追加要素"],
        "writing_challenges": ["執筆上の課題"],
        "solutions_applied": ["適用した解決策"]
    }},
    "next_stage_preparation": {{
        "quality_check_ready": true,
        "potential_issues": ["品質チェック想定課題"],
        "improvement_areas": ["改善可能領域"],
        "confidence_level": "高"
    }}
}}
```

### 執筆重要注意事項
1. **完全性**: 不完全な文章や中断は厳禁
2. **一貫性**: 冒頭から結末まで一貫した品質維持
3. **創造性**: 設計を超える創造的要素の適切な追加
4. **効率性**: {expected_turns}ターン以内での高品質完成

### エラー回避
- 長すぎる描写による文字数オーバー回避
- キャラクター設定矛盾の回避
- プロット論理破綻の回避
- 視点ブレの回避

前段階結果参照:
{previous_results}"""

        return StagePromptTemplate(
            stage=ExecutionStage.MANUSCRIPT_WRITING,
            template_content=template_content,
            required_context_keys=["three_act_structure", "key_scenes", "pacing_design", "writing_guidelines", "character_voice_patterns", "quality_rules_application", "emotion_expression_rules", "dialogue_ratio_targets", "character_interaction_requirements", "explanation_limits"],
            output_format="json",
            max_turns_override=4,  # 最重要段階のため最大ターン数を4に設定
        )

    @staticmethod
    def _create_quality_finalization_template() -> StagePromptTemplate:
        """Stage 5: 品質チェック・仕上げテンプレート"""
        template_content = """# Stage 5: 品質チェック・仕上げ

## 実行概要
- **段階**: {stage_name}
- **セッションID**: {session_id}
- **対象エピソード**: 第{episode_number:03d}話
- **予想ターン数**: {expected_turns}ターン

## 実行指示

### 主要タスク
1. **A30執筆ガイド準拠チェック**
   - 禁止表現の検出・修正
   - 推奨表現の適用確認
   - 品質基準達成度評価

2. **品質問題の特定・修正**
   - 文章品質の向上
   - 論理的整合性の確認
   - 読みやすさの改善

3. **最終調整・仕上げ**
   - 文字数の最終調整
   - 全体バランスの微調整
   - 最終品質保証

### 前段階原稿データ
以下の原稿を品質チェック・改善してください：
原稿内容: {manuscript}
執筆メトリクス: {writing_metrics}
品質自己評価: {quality_self_assessment}
定量チェック基準: {quantitative_check_criteria}
品質採点基準: {quality_scoring_rubric}

### 品質チェック基準
1. **A30執筆ガイド準拠** (重要度: 最高)
   - 禁止表現リストとの照合
   - 推奨表現の活用度評価
   - 文体・トーン基準適合性

2. **技術的品質** (重要度: 高)
   - 誤字脱字の修正
   - 文法・語法の正確性
   - 表記統一の確認

3. **内容品質** (重要度: 高)
   - プロット論理性確認
   - キャラクター一貫性検証
   - 設定整合性チェック

4. **読者体験品質** (重要度: 中)
   - 読みやすさ向上
   - 感情的インパクト確認
   - ペース感の最適化

### 🚨 重要: 最終原稿の完全出力が必須 🚨
- **必ず修正済みの完全な最終原稿を "final_manuscript" フィールドに含めてください**
- **メタデータのみの出力は絶対に避けてください**
- **最終原稿が空または不完全な場合は実行失敗です**
- **品質チェック・修正済みの3000文字以上の完全原稿を出力してください**

### 出力要求
以下のJSON形式で結果を出力してください：

```json
{{
    "stage": "quality_finalization",
    "status": "completed",
    "final_manuscript": "### 第{episode_number:03d}話 [最終タイトル]\\n\\n　直人は朝の光で目を覚ました。\\n　「今日もまた、新しい一日が始まる」\\n　彼は窓から差し込む光を見つめながら、ベッドから起き上がった。\\n\\n[品質チェック・修正済みの完全な最終原稿を3000文字以上で記述]\\n\\n---\\n\\n- 最終文字数: [実際の文字数]\\n- 品質スコア: [実際のスコア]\\n- A30準拠度: [実際の準拠度]",
    "quality_check_results": {{
        "a30_compliance": {{
            "prohibited_found": 0,
            "prohibited_fixed": 0,
            "recommended_applied": 0,
            "compliance_score": 98,
            "compliance_grade": "A+"
        }},
        "technical_quality": {{
            "typos_fixed": 0,
            "grammar_improvements": 0,
            "consistency_adjustments": 0,
            "technical_score": 95
        }},
        "content_quality": {{
            "plot_logic_score": 90,
            "character_consistency_score": 95,
            "setting_coherence_score": 92,
            "content_score": 92
        }},
        "reader_experience": {{
            "readability_score": 88,
            "emotional_impact_score": 90,
            "pacing_score": 85,
            "experience_score": 88
        }},
        "overall_quality_score": 93
    }},
    "improvements_made": [
        {{
            "category": "修正カテゴリー",
            "issue": "特定された問題",
            "solution": "適用した解決策",
            "impact": "改善インパクト"
        }}
    ],
    "final_metrics": {{
        "final_word_count": 0,
        "target_achievement_rate": 0.0,
        "quality_improvement_rate": 0.0,
        "editing_efficiency": "高"
    }},
    "quality_report": {{
        "strengths": ["原稿の強み"],
        "areas_improved": ["改善された領域"],
        "remaining_considerations": ["今後の検討事項"],
        "reader_impact_prediction": "読者への影響予測",
        "series_continuity_assessment": "シリーズ継続性評価"
    }},
    "final_validation": {{
        "ready_for_publication": true,
        "quality_gate_passed": true,
        "confidence_level": "非常に高い",
        "recommendation": "公開推奨"
    }}
}}
```

### 品質保証プロセス
1. **自動チェック**: 基本的な品質問題の検出
2. **人的レビュー**: 内容・表現の質的評価
3. **総合評価**: 全体品質スコアの算出
4. **最終承認**: 公開可否の判定

### 品質基準値
- A30準拠度: 95%以上
- 総合品質スコア: 90%以上
- 文字数達成率: 90%-110%
- 技術的品質: エラーゼロ

前段階結果参照:
{previous_results}"""

        return StagePromptTemplate(
            stage=ExecutionStage.QUALITY_FINALIZATION,
            template_content=template_content,
            required_context_keys=["manuscript", "writing_metrics", "quality_self_assessment", "quantitative_check_criteria", "quality_scoring_rubric"],
            output_format="json",
            max_turns_override=None,
        )
