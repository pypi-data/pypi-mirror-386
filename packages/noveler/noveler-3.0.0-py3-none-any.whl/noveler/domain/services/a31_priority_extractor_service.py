#!/usr/bin/env python3
"""A31重点項目抽出ドメインサービス

A31チェックリストから重点項目を自動抽出し、
Claude Code分析に最適化された形式で提供するドメインサービス。
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.entities.a31_priority_item import A31CheckPhase, A31PriorityItem
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


class ExtractionStrategy(Enum):
    """抽出戦略列挙型"""

    MANUAL_CURATION = "manual_curation"  # 手動キューション式（方式B）
    AUTO_SCORING = "auto_scoring"  # 自動スコアリング
    HYBRID = "hybrid"  # ハイブリッド（推奨）


@dataclass(frozen=True)
class PriorityExtractionCriteria:
    """重点項目抽出基準 バリューオブジェクト"""

    priority_threshold: float = 0.7
    target_phases: list[A31CheckPhase] = None
    focus_categories: list[A31EvaluationCategory] | None = None
    max_items: int = 25
    strategy: ExtractionStrategy = ExtractionStrategy.HYBRID

    def __post_init__(self) -> None:
        """抽出基準妥当性検証"""
        if not 0.0 < self.priority_threshold <= 1.0:
            msg = "priority_threshold は 0.0 < threshold <= 1.0 である必要があります"
            raise ValueError(msg)

        if self.max_items < 1:
            msg = "max_items は 1 以上である必要があります"
            raise ValueError(msg)

        # target_phases のデフォルト設定
        if self.target_phases is None:
            object.__setattr__(
                self,
                "target_phases",
                [A31CheckPhase.PHASE2_WRITING, A31CheckPhase.PHASE3_REVISION, A31CheckPhase.STAGE2_CONTENT],
            )

    def get_phase_priority_weight(self, phase: A31CheckPhase) -> float:
        """フェーズ別優先度重みを取得"""
        if phase in self.target_phases:
            return phase.get_priority_weight()
        return 0.3  # 対象外フェーズは低重み


@dataclass
class A31ChecklistData:
    """A31チェックリストデータ構造"""

    checklist_items: dict[str, list[dict[str, Any]]]
    metadata: dict[str, Any]
    target_episode: int | None = None
    target_title: str | None = None

    def get_all_items(self) -> list[dict[str, Any]]:
        """全チェック項目を平坦なリストで取得"""
        all_items = []
        for phase_name, items in self.checklist_items.items():
            for item in items:
                item_with_phase = {**item, "phase_name": phase_name}
                all_items.append(item_with_phase)
        return all_items


class A31PriorityExtractorService:
    """A31重点項目抽出ドメインサービス

    A31チェックリストの解析と重点項目の自動識別を担当し、
    Claude Code分析に適した項目セットを生成する。
    """

    def __init__(self) -> None:
        """抽出サービス初期化"""
        # 方式B: 手動キューション式の重点項目定義
        self._curated_priority_items = self._load_manual_curation_rules()

        # 自動スコアリング用のキーワード重み
        self._keyword_weights = {
            "high_priority": {
                "keywords": ["冒頭", "バランス", "五感", "描写", "リズム", "引き込み", "感情"],
                "weight": 0.3,
            },
            "medium_priority": {"keywords": ["確認", "チェック", "統一", "一貫性", "適切", "妥当"], "weight": 0.15},
            "claude_suitable": {"keywords": ["分析", "評価", "測定", "判定", "検証"], "weight": 0.2},
        }

    def extract_priority_items(
        self, checklist_data: A31ChecklistData, criteria: PriorityExtractionCriteria
    ) -> list[A31PriorityItem]:
        """重点項目を抽出する

        Args:
            checklist_data: A31チェックリストデータ
            criteria: 抽出基準

        Returns:
            list[A31PriorityItem]: 抽出された重点項目リスト
        """
        all_items = checklist_data.get_all_items()
        candidate_items = []

        for item_data in all_items:
            # 優先度スコア計算
            priority_score = self._calculate_priority_score(item_data, criteria)

            # 閾値チェック
            if priority_score < criteria.priority_threshold:
                continue

            # フェーズフィルタリング
            phase = self._parse_phase(item_data.get("phase_name", ""))
            if phase not in criteria.target_phases:
                continue

            # カテゴリフィルタリング
            category = self._parse_category(item_data)
            if criteria.focus_categories and category not in criteria.focus_categories:
                continue

            # A31PriorityItem エンティティ作成
            try:
                priority_item = A31PriorityItem.create(
                    item_id=item_data.get("id", "UNKNOWN"),
                    content=item_data.get("item", ""),
                    phase=phase,
                    category=category,
                    priority_score=priority_score,
                    item_type=item_data.get("type", "content_quality"),
                    reference_guides=item_data.get("reference_guides", []),
                )

                # Claude適性チェック
                if priority_item.is_claude_suitable():
                    candidate_items.append(priority_item)

            except (ValueError, KeyError):
                # 無効な項目はスキップ
                continue

        # 優先度順にソートして上位を返却
        candidate_items.sort(key=lambda x: x.calculate_adjusted_priority_score(), reverse=True)

        return candidate_items[: criteria.max_items]

    def _calculate_priority_score(self, item_data: dict[str, Any], criteria: PriorityExtractionCriteria) -> float:
        """項目の優先度スコアを計算"""

        if criteria.strategy == ExtractionStrategy.MANUAL_CURATION:
            return self._calculate_manual_curation_score(item_data)
        if criteria.strategy == ExtractionStrategy.AUTO_SCORING:
            return self._calculate_auto_scoring_score(item_data)
        # HYBRID
        manual_score = self._calculate_manual_curation_score(item_data)
        auto_score = self._calculate_auto_scoring_score(item_data)
        return (manual_score * 0.6) + (auto_score * 0.4)  # 手動重視

    def _calculate_manual_curation_score(self, item_data: dict[str, Any]) -> float:
        """手動キューション式スコア計算"""
        item_id = item_data.get("id", "")

        # 方式B: 事前定義された重点項目
        if item_id in self._curated_priority_items:
            return self._curated_priority_items[item_id]["priority_score"]

        return 0.3  # デフォルト低スコア

    def _calculate_auto_scoring_score(self, item_data: dict[str, Any]) -> float:
        """自動スコアリング計算"""
        score = 0.5  # ベース
        content = item_data.get("item", "").lower()
        item_type = item_data.get("type", "")

        # キーワードベース加点
        for config in self._keyword_weights.values():
            for keyword in config["keywords"]:
                if keyword in content:
                    score += config["weight"]

        # タイプベース加点
        high_priority_types = [
            "content_balance",
            "sensory_check",
            "style_variety",
            "readability_check",
            "hook_check",
            "emotional_expression",
        ]

        if item_type in high_priority_types:
            score += 0.4

        # フェーズベース加点
        phase_name = item_data.get("phase_name", "")
        if "Phase2" in phase_name or "Stage2" in phase_name:
            score += 0.2

        return min(score, 1.0)

    def _parse_phase(self, phase_name: str) -> A31CheckPhase:
        """フェーズ名文字列をA31CheckPhaseに変換"""
        phase_mapping = {
            "Phase0_自動執筆開始（推奨）": A31CheckPhase.PHASE0_AUTO_START,
            "Phase1_設計・下書き段階": A31CheckPhase.PHASE1_PLANNING,
            "Phase2_執筆段階": A31CheckPhase.PHASE2_WRITING,
            "Phase3_推敲段階": A31CheckPhase.PHASE3_REVISION,
            "Phase4_品質チェック段階": A31CheckPhase.PHASE4_QUALITY_CHECK,
            "Phase5_完成処理段階": A31CheckPhase.PHASE5_COMPLETION,
            "公開前最終確認": A31CheckPhase.FINAL_CONFIRMATION,
            "Stage1_技術的推敲段階": A31CheckPhase.STAGE1_TECHNICAL,
            "Stage2_内容的推敲段階": A31CheckPhase.STAGE2_CONTENT,
            "Stage3_読者体験最適化段階": A31CheckPhase.STAGE3_READER_OPTIMIZATION,
        }

        return phase_mapping.get(phase_name, A31CheckPhase.PHASE1_PLANNING)

    def _parse_category(self, item_data: dict[str, Any]) -> A31EvaluationCategory:
        """項目データからA31EvaluationCategoryを推定"""
        content = item_data.get("item", "").lower()
        item_type = item_data.get("type", "")

        # タイプベース判定
        type_mapping = {
            "content_balance": A31EvaluationCategory.CONTENT_BALANCE,
            "sensory_check": A31EvaluationCategory.SENSORY_DESCRIPTION,
            "style_variety": A31EvaluationCategory.BASIC_WRITING_STYLE,
            "character_consistency": A31EvaluationCategory.CHARACTER_CONSISTENCY,
            "readability_check": A31EvaluationCategory.BASIC_WRITING_STYLE,
        }

        if item_type in type_mapping:
            return type_mapping[item_type]

        # キーワードベース推定
        if any(word in content for word in ["バランス", "会話", "地の文"]):
            return A31EvaluationCategory.CONTENT_BALANCE
        if any(word in content for word in ["五感", "描写", "感覚"]):
            return A31EvaluationCategory.SENSORY_DESCRIPTION
        if any(word in content for word in ["キャラクター", "口調", "一貫性"]):
            return A31EvaluationCategory.CHARACTER_CONSISTENCY

        return A31EvaluationCategory.BASIC_WRITING_STYLE

    def _load_manual_curation_rules(self) -> dict[str, dict[str, Any]]:
        """方式B: 手動キューション式の重点項目定義を読み込み

        具体的改善提案テンプレート付きの高品質分析設定
        """
        return {
            # Phase2: 執筆段階の重点項目（具体的改善提案強化版）
            "A31-021": {
                "priority_score": 0.95,
                "claude_focus": "冒頭3行の具体的改善提案生成",
                "analysis_depth": "high",
                "concrete_improvement_templates": [
                    "【冒頭1行目】技術的要素を含む状況設定: 例「DEBUGログが画面に流れる中、直人は～」",
                    "【冒頭2行目】読者の疑問を誘発する要素: 例「なぜこのタイミングで？何が起きている？」",
                    "【冒頭3行目】キャラクター感情と次の展開への期待: 例「不安と期待が入り混じった表情で～」",
                ],
                "improvement_examples": {
                    "weak_opening": "朝、学園に向かった。",
                    "strong_opening": "DEBUGログが画面を埋め尽くす中、直人は眉をひそめた。昨夜のシステム更新が原因なのか、それとも新たな異常なのか——答えを求めて、彼は学園への足を速めた。",
                    "improvement_rationale": "技術的設定→疑問提起→行動動機の3段階構成で読者の関心を段階的に引き上げる",
                },
            },
            "A31-022": {
                "priority_score": 0.90,
                "claude_focus": "会話・地の文バランス具体的調整案",
                "analysis_depth": "high",
                "concrete_improvement_templates": [
                    "【会話過多の場合】「～と言った」の後に状況描写を挿入: 例「『そうなんだ』と直人は答えながら、画面のエラーログに視線を向けた」",
                    "【地の文過多の場合】内面描写を会話に変換: 例「心配だ」→「『大丈夫かな？』と小声でつぶやいた」",
                    "【理想的配置】3:7～4:6比率での自然な配分例を具体的に提示",
                ],
                "improvement_examples": {
                    "dialogue_heavy": "『こんにちは』『元気？』『うん、元気だよ』『よかった』",
                    "balanced_version": "『こんにちは』と声をかけると、あすかは振り返って微笑んだ。『元気？』『うん、元気だよ』彼女の表情には昨日の疲れが少し残っているようだった。『よかった』",
                    "improvement_rationale": "会話の間に状況・感情描写を挟み、読者の理解を深めながら自然なリズムを作る",
                },
            },
            "A31-023": {
                "priority_score": 0.88,
                "claude_focus": "五感描写の具体的配置と強化案",
                "analysis_depth": "high",
                "concrete_improvement_templates": [
                    "【視覚】技術的な光や色彩: 例「画面の青白い光が顔を照らし」「エラーコードの赤い文字が点滅して」",
                    "【聴覚】システム音や環境音: 例「キーボードの打鍵音」「アラートの電子音」「ファンの駆動音」",
                    "【触覚】緊張や温度感: 例「手のひらに汗がにじみ」「冷たいマウスを握りしめ」",
                    "【場面連動】シーンに応じた感覚の自然な組み込み方法を具体例で提示",
                ],
                "improvement_examples": {
                    "sensory_weak": "直人はコンピューターを操作した。",
                    "sensory_rich": "キーボードの打鍵音が響く中、直人は画面の青白い光に照らされながらコードを打ち込んだ。指先に伝わる微細な振動と、集中による軽い頭痛が、彼の緊張状態を物語っていた。",
                    "improvement_rationale": "聴覚→視覚→触覚→内部感覚の順で重層的に描写し、読者の没入感を段階的に高める",
                },
            },
            "A31-024": {
                "priority_score": 0.82,
                "claude_focus": "シーン転換の自然さと効果性",
                "analysis_depth": "medium",
                "concrete_improvement_templates": [
                    "【時間転換】「～した後」「しばらくして」の代わりに具体的時間や状況変化で転換",
                    "【場所転換】移動の動機と過程を簡潔に描写",
                    "【心境転換】感情の変化をきっかけとした自然な場面移行",
                ],
            },
            "A31-025": {
                "priority_score": 0.85,
                "claude_focus": "文体リズムとバリエーション分析",
                "analysis_depth": "high",
                "concrete_improvement_templates": [
                    "【文末変化】「だった」「である」「した」の連続回避と代替表現例",
                    "【文長調整】短文・中文・長文の効果的な組み合わせパターン",
                    "【倒置・体言止め】緊張感や余韻を生む効果的な配置例",
                ],
            },
            # Phase3: 推敲段階の重点項目
            "A31-032": {
                "priority_score": 0.80,
                "claude_focus": "文章リズムと読みやすさの詳細分析",
                "analysis_depth": "high",
            },
            "A31-033": {
                "priority_score": 0.75,
                "claude_focus": "キャラクター口調の一貫性検証",
                "analysis_depth": "medium",
            },
            "A31-034": {
                "priority_score": 0.78,
                "claude_focus": "伏線と描写の過不足バランス分析",
                "analysis_depth": "medium",
            },
            # A41 Stage2: 内容的推敲段階
            "A41-021": {
                "priority_score": 0.92,
                "claude_focus": "冒頭3行の読者興味度精密分析",
                "analysis_depth": "high",
            },
            "A41-023": {"priority_score": 0.87, "claude_focus": "五感バランスの詳細診断", "analysis_depth": "high"},
            "A41-024": {"priority_score": 0.85, "claude_focus": "感情描写の具体性と効果性", "analysis_depth": "high"},
            "A41-026": {"priority_score": 0.83, "claude_focus": "5層内面描写の深度分析", "analysis_depth": "high"},
        }

    def get_extraction_statistics(self, extracted_items: list[A31PriorityItem]) -> dict[str, Any]:
        """抽出統計情報を生成"""
        if not extracted_items:
            return {"total_items": 0}

        phase_distribution = {}
        category_distribution = {}
        suitability_distribution = {}

        for item in extracted_items:
            # フェーズ分布
            phase_key = item.phase.value
            phase_distribution[phase_key] = phase_distribution.get(phase_key, 0) + 1

            # カテゴリ分布
            category_key = item.category.value
            category_distribution[category_key] = category_distribution.get(category_key, 0) + 1

            # 適性分布
            suitability_key = item.claude_analysis_suitability.value
            suitability_distribution[suitability_key] = suitability_distribution.get(suitability_key, 0) + 1

        avg_priority = sum(item.priority_score for item in extracted_items) / len(extracted_items)
        high_priority_count = sum(1 for item in extracted_items if item.is_high_priority())

        return {
            "total_items": len(extracted_items),
            "high_priority_items": high_priority_count,
            "average_priority_score": round(avg_priority, 3),
            "phase_distribution": phase_distribution,
            "category_distribution": category_distribution,
            "suitability_distribution": suitability_distribution,
            "claude_suitable_count": sum(1 for item in extracted_items if item.is_claude_suitable()),
        }

    def generate_concrete_improvement_suggestions(
        self,
        priority_items: list["A31PriorityItem"],
        manuscript_content: str,
        episode_context: dict[str, Any] | None = None,
    ) -> dict[str, list[str]]:
        """具体的改善提案を生成

        Args:
            priority_items: 抽出された重点項目
            manuscript_content: 原稿内容
            episode_context: エピソード文脈情報

        Returns:
            dict[str, list[str]]: 項目ID毎の具体的改善提案リスト
        """
        suggestions = {}
        manual_rules = self._load_manual_curation_rules()

        for item in priority_items:
            item_id = item.item_id.value

            if item_id not in manual_rules:
                continue

            rule = manual_rules[item_id]
            concrete_templates = rule.get("concrete_improvement_templates", [])
            improvement_examples = rule.get("improvement_examples", {})

            # 原稿内容を分析して具体的提案を生成
            item_suggestions = self._generate_context_specific_suggestions(
                item_id=item_id,
                templates=concrete_templates,
                examples=improvement_examples,
                manuscript_content=manuscript_content,
                episode_context=episode_context or {},
            )

            suggestions[item_id] = item_suggestions

        return suggestions

    def _generate_context_specific_suggestions(
        self,
        item_id: str,
        templates: list[str],
        examples: dict[str, Any],
        manuscript_content: str,
        episode_context: dict[str, Any],
    ) -> list[str]:
        """コンテキスト対応の具体的改善提案生成

        Args:
            item_id: 項目ID
            templates: 改善提案テンプレート
            examples: 改善例
            manuscript_content: 原稿内容
            episode_context: エピソード文脈

        Returns:
            list[str]: 具体的改善提案リスト
        """
        context_suggestions = []

        # A31-021: 冒頭3行の具体的改善
        if item_id == "A31-021":
            opening_lines = self._extract_opening_lines(manuscript_content, 3)
            context_suggestions.extend(self._generate_opening_specific_suggestions(opening_lines, templates, examples))

        # A31-022: 会話バランスの具体的改善
        elif item_id == "A31-022":
            dialogue_analysis = self._analyze_dialogue_balance(manuscript_content)
            context_suggestions.extend(
                self._generate_balance_specific_suggestions(dialogue_analysis, templates, examples)
            )

        # A31-023: 五感描写の具体的改善
        elif item_id == "A31-023":
            sensory_analysis = self._analyze_sensory_descriptions(manuscript_content)
            context_suggestions.extend(
                self._generate_sensory_specific_suggestions(sensory_analysis, templates, examples)
            )

        # その他の項目: テンプレートベース提案
        else:
            context_suggestions.extend(templates)

        return context_suggestions

    def _extract_opening_lines(self, content: str, line_count: int = 3) -> list[str]:
        """冒頭行の抽出"""
        lines = content.strip().split("\n")
        # 空行や見出しを除外して実際の本文行を取得
        content_lines = []
        for line in lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith("#"):
                content_lines.append(clean_line)
                if len(content_lines) >= line_count:
                    break
        return content_lines

    def _analyze_dialogue_balance(self, content: str) -> dict[str, Any]:
        """会話と地の文のバランス分析"""

        # 会話文の検出（「」で囲まれた部分）
        dialogue_matches = re.findall(r"「[^」]*」", content)
        dialogue_chars = sum(len(match) for match in dialogue_matches)

        total_chars = len(content.replace(" ", "").replace("\n", ""))
        dialogue_ratio = (dialogue_chars / total_chars * 100) if total_chars > 0 else 0

        return {
            "dialogue_ratio": dialogue_ratio,
            "narrative_ratio": 100 - dialogue_ratio,
            "dialogue_count": len(dialogue_matches),
            "total_chars": total_chars,
            "is_dialogue_heavy": dialogue_ratio > 45,
            "is_narrative_heavy": dialogue_ratio < 25,
        }

    def _analyze_sensory_descriptions(self, content: str) -> dict[str, Any]:
        """五感描写の分析"""
        sensory_keywords = {
            "visual": ["見る", "光", "色", "明るい", "暗い", "輝く", "照らす", "青白い", "赤い"],
            "auditory": ["聞こえる", "音", "声", "響く", "静か", "騒がしい", "打鍵音", "アラート", "電子音"],
            "tactile": ["触れる", "手", "冷たい", "暖かい", "振動", "汗", "握る", "なでる"],
            "olfactory": ["香り", "匂い", "臭い", "芳香", "嗅ぐ"],
            "gustatory": ["味", "甘い", "苦い", "酸っぱい", "辛い", "美味しい"],
        }

        sensory_counts = {}
        for sense, keywords in sensory_keywords.items():
            count = sum(content.count(keyword) for keyword in keywords)
            sensory_counts[sense] = count

        total_sensory = sum(sensory_counts.values())

        return {
            "sensory_counts": sensory_counts,
            "total_sensory": total_sensory,
            "dominant_senses": [sense for sense, count in sensory_counts.items() if count > 0],
            "missing_senses": [sense for sense, count in sensory_counts.items() if count == 0],
            "sensory_density": total_sensory / len(content) * 1000 if content else 0,
        }

    def _generate_opening_specific_suggestions(
        self, opening_lines: list[str], templates: list[str], examples: dict[str, Any]
    ) -> list[str]:
        """冒頭行の具体的改善提案生成"""
        suggestions = []

        if not opening_lines:
            suggestions.append(
                "【冒頭不足】原稿に内容が検出されませんでした。技術的要素を含む魅力的な冒頭3行を執筆してください。"
            )
            return suggestions

        # 実際の冒頭内容に基づく具体的提案
        for i, line in enumerate(opening_lines, 1):
            if len(line) < 20:
                suggestions.append(
                    f"【冒頭{i}行目】「{line[:15]}...」をより詳細に描写してください。状況設定と感情を含めて30文字以上に拡張することを推奨します。"
                )

            if "DEBUG" not in line and "システム" not in line and "コード" not in line:
                suggestions.append(
                    f"【冒頭{i}行目】技術的要素を追加してください。例：「DEBUGログ」「エラーコード」「システム異常」などの単語を自然に織り込む。"
                )

        # テンプレートベースの提案も追加
        suggestions.extend(templates)

        return suggestions

    def _generate_balance_specific_suggestions(
        self, analysis: dict[str, Any], templates: list[str], examples: dict[str, Any]
    ) -> list[str]:
        """会話バランスの具体的改善提案生成"""
        suggestions = []
        dialogue_ratio = analysis["dialogue_ratio"]

        if analysis["is_dialogue_heavy"]:
            suggestions.append(
                f"【会話過多】現在の会話比率{dialogue_ratio:.1f}%。地の文を追加して35-40%程度に調整してください。"
            )
            suggestions.append("【具体的手法】「～と言った」の後に、表情・動作・状況描写を1-2文追加してください。")

            if examples.get("balanced_version"):
                suggestions.append(f"【改善例】{examples['balanced_version']}")

        elif analysis["is_narrative_heavy"]:
            suggestions.append(
                f"【地の文過多】現在の会話比率{dialogue_ratio:.1f}%。会話を増やして30-35%程度に調整してください。"
            )
            suggestions.append("【具体的手法】内面描写の一部を「つぶやき」や「短い会話」に変換してください。")

        else:
            suggestions.append(
                f"【バランス良好】会話比率{dialogue_ratio:.1f}%は適切な範囲内です。現在のバランスを維持してください。"
            )

        suggestions.extend(templates)
        return suggestions

    def _generate_sensory_specific_suggestions(
        self, analysis: dict[str, Any], templates: list[str], examples: dict[str, Any]
    ) -> list[str]:
        """五感描写の具体的改善提案生成"""
        suggestions = []
        missing_senses = analysis["missing_senses"]
        sensory_density = analysis["sensory_density"]

        if sensory_density < 2.0:
            suggestions.append(
                f"【五感描写不足】感覚描写密度{sensory_density:.2f}/1000文字。3.0以上を目標に五感描写を追加してください。"
            )

        if missing_senses:
            sense_names = {
                "visual": "視覚",
                "auditory": "聴覚",
                "tactile": "触覚",
                "olfactory": "嗅覚",
                "gustatory": "味覚",
            }
            missing_names = [sense_names.get(sense, sense) for sense in missing_senses]
            suggestions.append(f"【不足している感覚】{', '.join(missing_names)}の描写を追加してください。")

        # 技術系小説特有の五感描写提案
        if "visual" in missing_senses:
            suggestions.append(
                "【視覚描写追加】「画面の青白い光」「エラーコードの赤い点滅」「LEDの緑色の点灯」などの技術的視覚要素を追加。"
            )

        if "auditory" in missing_senses:
            suggestions.append(
                "【聴覚描写追加】「キーボードの打鍵音」「ファンの駆動音」「アラートの電子音」「システム起動音」などを追加。"
            )

        if "tactile" in missing_senses:
            suggestions.append(
                "【触覚描写追加】「マウスの冷たさ」「キーボードの手触り」「緊張による手汗」「集中による肩こり」などを追加。"
            )

        suggestions.extend(templates)
        return suggestions
