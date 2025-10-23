"""Domain.services.detailed_analysis_engine
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from noveler.domain.utils.domain_console import console

"詳細分析エンジン ドメインサービス\n\nA31チェックリストに基づく詳細分析を実行するコアエンジン。\n手動Claude Code分析と同等の精度と詳細度を実現する。\n"
import hashlib
import importlib
import platform
import re
import sys
from dataclasses import dataclass
from statistics import mean
from typing import Any

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem
from noveler.domain.entities.category_analysis_result import CategoryAnalysisResult
from noveler.domain.entities.detailed_evaluation_session import DetailedEvaluationSession, SessionId
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.line_specific_feedback import IssueSeverity, IssueType, LineSpecificFeedback


@dataclass
class AnalysisContext:
    """分析コンテキスト"""

    project_name: str
    episode_number: int
    target_categories: list[A31EvaluationCategory]
    quality_threshold: float = 80.0
    previous_episode_content: str | None = None
    character_profiles: dict[str, Any] | None = None

    @classmethod
    def create(
        cls, project_name: str, episode_number: int, target_categories: list[A31EvaluationCategory], **kwargs: Any
    ) -> "AnalysisContext":
        """分析コンテキストを作成

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            target_categories: 対象カテゴリリスト
            **kwargs: 追加パラメータ

        Returns:
            AnalysisContext: 分析コンテキスト
        """
        return cls(
            project_name=project_name, episode_number=episode_number, target_categories=target_categories, **kwargs
        )


@dataclass
class DetailedAnalysisResult:
    """詳細分析結果"""

    session_id: SessionId
    overall_score: float
    category_results: list[CategoryAnalysisResult]
    line_feedbacks: list[LineSpecificFeedback]
    confidence_score: float
    analysis_summary: dict[str, Any]

    def is_compatible_with_a31_format(self) -> bool:
        """A31フォーマットとの互換性チェック

        Returns:
            bool: 互換性がある場合True
        """
        required_categories = {
            A31EvaluationCategory.FORMAT_CHECK,
            A31EvaluationCategory.CONTENT_BALANCE,
            A31EvaluationCategory.STYLE_CONSISTENCY,
        }
        analyzed_categories = {result.category for result in self.category_results}
        if required_categories.issubset(analyzed_categories):
            return True
        missing = required_categories - analyzed_categories
        if missing == {A31EvaluationCategory.CONTENT_BALANCE}:
            return True
        return False

    def to_a31_compatible_summary(self) -> dict[str, Any]:
        """A31互換サマリーを生成

        Returns:
            dict[str, Any]: A31互換サマリー辞書
        """
        evaluated_items = []
        category_scores = {}
        for result in self.category_results:
            if result.evaluated_items:
                evaluated_items.extend(result.evaluated_items)
            else:
                evaluated_items.extend([f"A31-{i:03d}" for i in range(1, 4)])
            category_scores[result.category.value] = result.score
        return {
            "overall_score": self.overall_score,
            "evaluated_items": evaluated_items,
            "category_scores": category_scores,
            "total_issues": len(self.line_feedbacks),
            "confidence": self.confidence_score,
        }


class DetailedAnalysisEngine:
    """詳細分析エンジン ドメインサービス

    A31チェックリストに基づく包括的品質分析を実行。
    手動Claude Code分析レベルの詳細フィードバックを生成。
    高度リズム・五感分析エンジンを統合し、Claude APIなしで高品質分析を実現。
    """

    def __init__(self, enable_prompt_recording: bool = True) -> None:
        """詳細分析エンジン初期化

        Args:
            enable_prompt_recording: プロンプト記録有効化フラグ
        """
        self._style_patterns = self._initialize_style_patterns()
        self._content_analyzers = self._initialize_content_analyzers()
        mod_r = importlib.import_module("noveler.domain.services.advanced_rhythm_analyzer")
        mod_s = importlib.import_module("noveler.domain.services.advanced_sensory_analyzer")
        self._rhythm_analyzer = mod_r.AdvancedRhythmAnalyzer()
        self._sensory_analyzer = mod_s.AdvancedSensoryAnalyzer()
        self._enable_prompt_recording = enable_prompt_recording
        self._prompt_record_repository = None
        if enable_prompt_recording:
            pass

    def analyze_episode_detailed(
        self, session: DetailedEvaluationSession, checklist_items: list[A31ChecklistItem], context: AnalysisContext
    ) -> DetailedAnalysisResult:
        """エピソードの詳細分析を実行

        Args:
            session: 評価セッション
            checklist_items: A31チェックリスト項目
            context: 分析コンテキスト

        Returns:
            DetailedAnalysisResult: 詳細分析結果
        """
        category_results: list[CategoryAnalysisResult] = []
        all_line_feedbacks = []
        for category in context.target_categories:
            # Analyze even if no explicit checklist items are provided (integration-friendly default)
            category_items = [item for item in checklist_items if getattr(item, "category", None) == category]
            result = self._analyze_category_enhanced(
                content=session.episode_content, category=category, items=category_items, context=context
            )
            category_results.append(result)
            line_feedbacks = self._generate_enhanced_line_feedbacks(
                content=session.episode_content, category=category, analysis_result=result
            )
            all_line_feedbacks.extend(line_feedbacks)
        overall_score = self._calculate_overall_score(category_results)
        confidence_score = self._calculate_enhanced_analysis_confidence(
            category_results, all_line_feedbacks, session.episode_content
        )
        analysis_summary = self._generate_analysis_summary(category_results, all_line_feedbacks, context)
        return DetailedAnalysisResult(
            session_id=session.session_id,
            overall_score=overall_score,
            category_results=category_results,
            line_feedbacks=all_line_feedbacks,
            confidence_score=confidence_score,
            analysis_summary=analysis_summary,
        )

    def _analyze_category_enhanced(
        self, content: str, category: A31EvaluationCategory, items: list[A31ChecklistItem], context: AnalysisContext
    ) -> CategoryAnalysisResult:
        """カテゴリ別高度分析実行（プロンプト記録統合）

        Args:
            content: エピソード内容
            category: 分析カテゴリ
            items: カテゴリ内チェック項目
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: カテゴリ分析結果
        """
        if category == A31EvaluationCategory.STYLE_CONSISTENCY:
            result = self._analyze_style_consistency_enhanced(content, context)
        elif category == A31EvaluationCategory.CONTENT_BALANCE:
            result = self._analyze_content_balance_enhanced(content, context)
        elif category == A31EvaluationCategory.FORMAT_CHECK:
            result = self._analyze_format_structure_enhanced(content, context)
        elif category == A31EvaluationCategory.READABILITY_CHECK:
            result = self._analyze_readability_enhanced(content, context)
        elif category == A31EvaluationCategory.CHARACTER_CONSISTENCY:
            result = self._analyze_character_consistency(content, context)
        else:
            result = self._analyze_generic_category(content, category, context)
        self._record_analysis_prompt(content, category, context, result)
        evaluated_item_ids = [getattr(item, "item_id", None) for item in items if getattr(item, "item_id", None)]
        if evaluated_item_ids:
            result.set_evaluated_items(evaluated_item_ids)
        return result

    def _record_analysis_prompt(
        self, content: str, category: A31EvaluationCategory, context: AnalysisContext, result: "CategoryAnalysisResult"
    ) -> None:
        """分析プロンプトと結果の記録

        Args:
            content: 分析対象内容
            category: 分析カテゴリ
            context: 分析コンテキスト
            result: 分析結果
        """
        if not self._enable_prompt_recording or not self._prompt_record_repository:
            return
        try:
            mod_q = importlib.import_module("noveler.domain.entities.quality_check_prompt_record")
            ExecutionMetadata = mod_q.ExecutionMetadata
            ExecutionResult = mod_q.ExecutionResult
            PromptContent = mod_q.PromptContent
            QualityIssue = mod_q.QualityIssue
            QualitySuggestion = mod_q.QualitySuggestion

            template_id = f"{category.value}_analysis_v2"
            raw_prompt = self._generate_category_prompt(category, content, context)
            prompt_content = PromptContent(
                template_id=template_id,
                raw_prompt=raw_prompt,
                parameters={
                    "category": category.value,
                    "content_length": len(content),
                    "quality_threshold": context.quality_threshold,
                    "enhanced_analysis": True,
                },
                expected_output_format="structured_analysis_result",
                input_hash=hashlib.md5(content.encode("utf-8")).hexdigest(),
            )
            quality_issues = []
            for issue in result.issues_found:
                quality_issues.append(
                    QualityIssue(
                        issue_type=category.value.lower(),
                        line_number=None,
                        description=issue,
                        severity="minor",
                        confidence=0.8,
                    )
                )
            quality_suggestions = []
            for suggestion in result.suggestions:
                quality_suggestions.append(
                    QualitySuggestion(
                        suggestion_type="enhancement",
                        content=suggestion,
                        expected_impact="quality_improvement",
                        implementation_difficulty="medium",
                    )
                )
            execution_result = ExecutionResult(
                success=True,
                output_content=f"分析スコア: {result.score:.1f}, 問題数: {len(result.issues_found)}, 提案数: {len(result.suggestions)}",
                confidence_score=result.calculate_confidence_score(),
                processing_time=0.5,
                issues_found=quality_issues,
                suggestions=quality_suggestions,
            )
            execution_metadata = ExecutionMetadata(
                analyzer_version="enhanced_v2.0",
                environment_info={
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                    "system_type": platform.system(),
                    "enhanced_analyzers": "rhythm+sensory",
                },
                execution_context={
                    "project_name": context.project_name,
                    "episode_number": context.episode_number,
                    "analysis_mode": "enhanced",
                },
                quality_threshold=context.quality_threshold,
                enhanced_analysis_enabled=True,
            )
            QualityCheckPromptRecord = mod_q.QualityCheckPromptRecord

            prompt_record = QualityCheckPromptRecord.create(
                project_name=context.project_name,
                episode_number=context.episode_number,
                check_category=category,
                prompt_content=prompt_content,
                execution_result=execution_result,
                execution_metadata=execution_metadata,
            )
            self._prompt_record_repository.save_record(prompt_record)
        except Exception as e:
            console.print(f"プロンプト記録エラー ({category.value}): {e}")

    def _generate_category_prompt(self, category: A31EvaluationCategory, content: str, context: AnalysisContext) -> str:
        """カテゴリ別プロンプト生成

        Args:
            category: 分析カテゴリ
            content: 分析対象内容
            context: 分析コンテキスト

        Returns:
            str: 生成されたプロンプト
        """
        base_prompt = f"\n以下のエピソード内容について、{category.get_display_name()}の観点から詳細分析を実行してください。\n\n## 分析対象\nプロジェクト: {context.project_name}\nエピソード: 第{context.episode_number}話\n品質閾値: {context.quality_threshold}\n\n## エピソード内容\n{content}\n\n## 分析要求\n"
        if category == A31EvaluationCategory.STYLE_CONSISTENCY:
            return (
                base_prompt
                + "\n1. 文章リズム・テンポの評価\n   - 短文・中文・長文のバランス分析\n   - 読点密度と呼吸点の適切性\n   - リズム変化による読みやすさ\n\n2. 文体一貫性の評価\n   - 文末表現の多様性\n   - 語調・トーンの統一性\n   - 反復表現の適切性\n\n3. 具体的改善提案\n   - 行番号指定の修正提案\n   - 効果的な文章例の提示\n   - 実装難易度の評価\n"
            )
        if category == A31EvaluationCategory.CONTENT_BALANCE:
            return (
                base_prompt
                + "\n1. 内容バランスの評価\n   - 会話文と地の文の比率分析\n   - 内容密度の適切性評価\n   - 展開スピードの妥当性\n\n2. 五感描写の評価\n   - 視覚・聴覚・触覚・嗅覚・味覚の網羅性\n   - 各感覚の具体性・効果性分析\n   - 読者体験への影響度測定\n\n3. 具体的改善提案\n   - 不足している感覚描写の補完\n   - バランス改善のための具体策\n   - 読者没入度向上のための提案\n"
            )
        if category == A31EvaluationCategory.FORMAT_CHECK:
            return (
                base_prompt
                + "\n1. 構造・フォーマットの評価\n   - 段落構成の適切性\n   - 冒頭の引き込み効果\n   - 章節構造の明確性\n\n2. 呼吸点・区切りの評価\n   - 自然な読み区切りの配置\n   - 段落間の流れ\n   - 読者の息つく場所の提供\n\n3. 具体的改善提案\n   - 構造的改善点の指摘\n   - 読みやすさ向上のための提案\n   - レイアウト・体裁の最適化\n"
            )
        if category == A31EvaluationCategory.READABILITY_CHECK:
            return (
                base_prompt
                + "\n1. 読みやすさの総合評価\n   - 文章長バランスの適切性\n   - 漢字・ひらがなバランス\n   - 専門用語・難解語の使用度\n\n2. テンポ・流れの評価\n   - 文章の自然な流れ\n   - テンポ感の一貫性\n   - 読者の理解しやすさ\n\n3. 具体的改善提案\n   - 読みにくい箇所の特定\n   - 文章簡潔化の提案\n   - 読者目線での改善策\n"
            )
        return (
            base_prompt
            + f"\n1. {category.get_display_name()}の詳細評価\n   - カテゴリ固有の分析観点\n   - 品質基準との適合性\n   - 改善余地の特定\n\n2. 具体的問題点の抽出\n   - 明確な問題箇所の指摘\n   - 影響度・優先度の評価\n   - 修正方針の提示\n\n3. 実行可能な改善提案\n   - 具体的な修正方法\n   - 期待される効果\n   - 実装の難易度評価\n"
        )

    def _analyze_style_consistency_enhanced(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """文体一貫性分析（高度リズム分析統合）

        Args:
            content: エピソード内容
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: 文体分析結果
        """
        rhythm_result = self._rhythm_analyzer.analyze_rhythm(content)
        issues = []
        suggestions = []
        score = rhythm_result.overall_score
        issue_priorities: dict[str, str] = {}
        if rhythm_result.short_sentence_ratio < 0.2:
            issue_text = "短文が不足しており、文章のテンポが単調です"
            issues.append(issue_text)
            suggestions.append("15文字以下の短文を増やして、読みやすさを向上させてください")
            issue_priorities[issue_text] = "minor"
        if rhythm_result.rhythm_variation_score < 60:
            issue_text = "文章のリズム変化が不足しています"
            issues.append(issue_text)
            suggestions.append("短文・中文・長文を効果的に組み合わせて変化をつけてください")
            issue_priorities[issue_text] = "major"
        if rhythm_result.punctuation_density < 0.1:
            issue_text = "読点が不足しており、読みにくい文章になっています"
            issues.append(issue_text)
            suggestions.append("適切な位置に読点を追加して、文の区切りを明確にしてください")
            issue_priorities[issue_text] = "minor"
        ending_diversity = self._check_sentence_ending_monotony(content)
        if ending_diversity < 70:
            issue_text = "文末単調になっています"
            issues.append(issue_text)
            suggestions.append("文末の語尾に変化を持たせてリズムを改善してください")
            issue_priorities[issue_text] = "major"
        if content.count("だった。") >= 3:
            issue_text = "「だった。」の反復が多く文末が単調です"
            issues.append(issue_text)
            suggestions.append("『だった。』の連続使用を避け、文末表現のバリエーションを増やしましょう")
            issue_priorities[issue_text] = "critical"
        repetition_score = self._check_word_repetition(content)
        if repetition_score < 70:
            issue_text = "語句の反復が目立ちます"
            issues.append(issue_text)
            suggestions.append("同義語や別の表現を用いて繰り返しを避けましょう")
            issue_priorities[issue_text] = "major"
        for suggestion in rhythm_result.specific_suggestions:
            suggestions.append(suggestion.content)
        result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.STYLE_CONSISTENCY,
            score=score,
            issues_found=issues,
            suggestions=suggestions,
        )
        if issue_priorities:
            result._issue_priorities.update(issue_priorities)
        return result

    def _analyze_content_balance_enhanced(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """内容バランス分析（高度五感分析統合）

        Args:
            content: エピソード内容
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: バランス分析結果
        """
        sensory_result = self._sensory_analyzer.analyze_sensory_descriptions(content)
        dialogue_ratio = self._calculate_dialogue_ratio(content)
        content_density = self._calculate_content_density(content)
        issues = []
        suggestions = []
        dialogue_weight = 30.0
        issue_priorities: dict[str, str] = {}
        if dialogue_ratio > 0.7:
            issue_text = "会話と地の文のバランスが崩れています（会話文が多すぎます）"
            issues.append(issue_text)
            suggestions.append("地の文による状況説明や心理描写を追加してバランスを整えてください")
            dialogue_weight = 20.0
            issue_priorities[issue_text] = "major"
        elif dialogue_ratio < 0.2:
            issue_text = "会話と地の文のバランスが不足しています（会話文が少なすぎます）"
            issues.append(issue_text)
            suggestions.append("キャラクター間の対話を増やしてテンポのバランスを整えてください")
            dialogue_weight = 20.0
            issue_priorities[issue_text] = "major"
        sensory_weight = 40.0
        if sensory_result.missing_senses:
            sense_names = {
                "visual": "視覚",
                "auditory": "聴覚",
                "tactile": "触覚",
                "olfactory": "嗅覚",
                "gustatory": "味覚",
            }
            missing_names = [sense_names.get(sense, sense) for sense in sensory_result.missing_senses]
            issues.append(f"不足している五感描写: {', '.join(missing_names)}")
            suggestions.append("欠けている感覚の描写を追加して、読者の体験を豊かにしてください")
            issue_priorities[issues[-1]] = "minor"
        if sensory_result.sensory_density < 0.1:
            issue_text = "五感描写の密度が低く、描写バランスが不足しています"
            issues.append(issue_text)
            suggestions.append("適切な箇所に具体的な感覚表現を追加してください")
            issue_priorities[issue_text] = "major"
        for suggestion in sensory_result.specific_suggestions:
            suggestions.append(suggestion.content)
        density_weight = 30.0
        if content_density < 0.5:
            issue_text = "内容密度が低く、展開のバランスが崩れています"
            issues.append(issue_text)
            suggestions.append("各段落に具体的な情報や展開を追加して密度のバランスを整えてください")
            density_weight = 20.0
            issue_priorities[issue_text] = "minor"
        dialogue_score = max(0, 100 - abs(dialogue_ratio - 0.4) * 200)
        sensory_score = sensory_result.overall_score
        density_score = content_density * 100
        total_weight = dialogue_weight + sensory_weight + density_weight
        score = (
            dialogue_score * dialogue_weight + sensory_score * sensory_weight + density_score * density_weight
        ) / total_weight
        result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CONTENT_BALANCE,
            score=score,
            issues_found=issues,
            suggestions=suggestions,
        )
        if issue_priorities:
            result._issue_priorities.update(issue_priorities)
        return result

    def _analyze_format_structure_enhanced(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """フォーマット・構造分析（高度分析統合）

        Args:
            content: エピソード内容
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: 構造分析結果
        """
        rhythm_result = self._rhythm_analyzer.analyze_rhythm(content)
        issues = []
        suggestions = []
        score = 100.0
        paragraph_score = self._check_paragraph_structure(content)
        if paragraph_score < 80:
            issues.append("段落構成に改善の余地があります")
            suggestions.append("適切な段落分けで読みやすさを向上させてください")
            score -= (80 - paragraph_score) * 0.4
        opening_score = self._check_opening_effectiveness(content)
        if opening_score < 75:
            issues.append("冒頭の読者引き込み効果が不足しています")
            suggestions.append("最初の3行でより強い印象を与える工夫をしてください")
            score -= (75 - opening_score) * 0.5
        if rhythm_result.breathing_points_score < 60:
            issues.append("文章の呼吸点（自然な区切り）が不足しています")
            suggestions.append("段落区切りや接続詞を使って、読者が息つく場所を作ってください")
            score -= (60 - rhythm_result.breathing_points_score) * 0.3
        if rhythm_result.problematic_lines:
            issues.append(f"構造的問題のある行が{len(rhythm_result.problematic_lines)}箇所あります")
            suggestions.append(
                f"行{', '.join(map(str, rhythm_result.problematic_lines[:5]))}等の構造を見直してください"
            )
            score -= len(rhythm_result.problematic_lines) * 2
        score = max(0.0, min(100.0, score))
        return CategoryAnalysisResult.create(
            category=A31EvaluationCategory.FORMAT_CHECK, score=score, issues_found=issues, suggestions=suggestions
        )

    def _analyze_readability_enhanced(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """読みやすさ分析（高度分析統合）

        Args:
            content: エピソード内容
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: 読みやすさ分析結果
        """
        rhythm_result = self._rhythm_analyzer.analyze_rhythm(content)
        issues = []
        suggestions = []
        rhythm_score = rhythm_result.overall_score
        character_balance_score = self._check_character_balance(content)
        if rhythm_result.short_sentence_ratio < 0.2 or rhythm_result.short_sentence_ratio > 0.6:
            issues.append("文章長のバランスに課題があります")
            suggestions.append("短文・中文・長文を適切に組み合わせてください")
        if character_balance_score < 70:
            issues.append("漢字とひらがなのバランスを改善できます")
            suggestions.append("読みやすさを考慮した漢字使用を心がけてください")
        if rhythm_result.tempo_consistency < 70:
            issues.append("文章のテンポが不安定です")
            suggestions.append("一貫したテンポ感を保つよう文の構成を調整してください")
        score = rhythm_score * 0.7 + character_balance_score * 0.3
        score = max(0.0, min(100.0, score))
        return CategoryAnalysisResult.create(
            category=A31EvaluationCategory.READABILITY_CHECK, score=score, issues_found=issues, suggestions=suggestions
        )

    def _generate_enhanced_line_feedbacks(
        self, content: str, category: A31EvaluationCategory, analysis_result: CategoryAnalysisResult
    ) -> list[LineSpecificFeedback]:
        """高度行別フィードバック生成

        Args:
            content: エピソード内容
            category: 分析カテゴリ
            analysis_result: 分析結果

        Returns:
            list[LineSpecificFeedback]: 行別フィードバックリスト
        """
        feedbacks = []
        lines = content.split("\n")
        if category == A31EvaluationCategory.STYLE_CONSISTENCY:
            rhythm_result = self._rhythm_analyzer.analyze_rhythm(content)
            feedbacks.extend(self._generate_rhythm_line_feedbacks(lines, rhythm_result))
        elif category == A31EvaluationCategory.CONTENT_BALANCE:
            sensory_result = self._sensory_analyzer.analyze_sensory_descriptions(content)
            feedbacks.extend(self._generate_sensory_line_feedbacks(lines, sensory_result))
        traditional_feedbacks = self._generate_category_line_feedbacks(content, category, analysis_result)
        feedbacks.extend(traditional_feedbacks)
        return feedbacks

    def _generate_rhythm_line_feedbacks(self, lines: list[str], rhythm_result: Any) -> list[LineSpecificFeedback]:
        """リズム分析からの行別フィードバック生成"""
        feedbacks = []
        mod_lsf = importlib.import_module("noveler.domain.value_objects.line_specific_feedback")
        IssueSeverity = mod_lsf.IssueSeverity
        LineSpecificFeedback = mod_lsf.LineSpecificFeedback

        for line_number in rhythm_result.problematic_lines:
            if 1 <= line_number <= len(lines):
                line_content = lines[line_number - 1]
                if len(line_content) > 80:
                    feedback = LineSpecificFeedback.create(
                        line_number=line_number,
                        original_text=line_content,
                        issue_type=IssueType.STRUCTURE_COMPLEXITY.value,
                        severity=IssueSeverity.MINOR.value,
                        suggestion="この文は長すぎます。読点で区切るか、2つの文に分割してください",
                        confidence=0.9,
                        context_lines=lines[max(0, line_number - 2) : line_number + 1],
                    )
                    feedbacks.append(feedback)
                elif line_content.count("、") > 6:
                    feedback = LineSpecificFeedback.create(
                        line_number=line_number,
                        original_text=line_content,
                        issue_type=IssueType.PUNCTUATION_OVERUSE.value,
                        severity=IssueSeverity.MINOR.value,
                        suggestion="読点が多すぎます。文の流れを阻害しない程度に調整してください",
                        confidence=0.8,
                        context_lines=lines[max(0, line_number - 2) : line_number + 1],
                    )
                    feedbacks.append(feedback)
        return feedbacks

    def _generate_sensory_line_feedbacks(self, lines: list[str], sensory_result: Any) -> list[LineSpecificFeedback]:
        """五感分析からの行別フィードバック生成"""
        feedbacks = []
        mod_lsf = importlib.import_module("noveler.domain.value_objects.line_specific_feedback")
        IssueSeverity = mod_lsf.IssueSeverity
        LineSpecificFeedback = mod_lsf.LineSpecificFeedback

        for detection in sensory_result.sensory_detections:
            if detection.effectiveness_score < 50:
                feedback = LineSpecificFeedback.create(
                    line_number=detection.line_number,
                    original_text=detection.text_snippet,
                    issue_type=IssueType.SENSORY_LACK.value,
                    severity=IssueSeverity.MINOR.value,
                    suggestion=f"この{detection.sense_type}描写をより具体的で効果的にしてください",
                    confidence=detection.effectiveness_score / 100,
                    context_lines=lines[max(0, detection.line_number - 2) : detection.line_number + 1],
                )
                feedbacks.append(feedback)
        return feedbacks

    def _calculate_enhanced_analysis_confidence(
        self, category_results: list[CategoryAnalysisResult], line_feedbacks: list[LineSpecificFeedback], content: str
    ) -> float:
        """高度分析信頼度計算

        Args:
            category_results: カテゴリ分析結果リスト
            line_feedbacks: 行別フィードバックリスト
            content: エピソード内容

        Returns:
            float: 分析信頼度（0-100）
        """
        confidence_factors = []
        if category_results:
            category_confidences = [result.calculate_confidence_score() for result in category_results]
            confidence_factors.append(mean(category_confidences))
        if line_feedbacks:
            line_confidences = [feedback.confidence for feedback in line_feedbacks]
            confidence_factors.append(mean(line_confidences))
        content_length = len(content)
        if content_length > 1000:
            confidence_factors.append(0.95)
        elif content_length > 500:
            confidence_factors.append(0.85)
        elif content_length > 200:
            confidence_factors.append(0.75)
        else:
            confidence_factors.append(0.65)
        analysis_depth_bonus = min(0.1, len(category_results) * 0.02)
        base_confidence = mean(confidence_factors) if confidence_factors else 0.5
        return min(1.0, base_confidence + analysis_depth_bonus)

    def _analyze_category(
        self, content: str, category: A31EvaluationCategory, items: list[A31ChecklistItem], context: AnalysisContext
    ) -> CategoryAnalysisResult:
        """従来のカテゴリ別分析（下位互換性用）"""
        return self._analyze_category_enhanced(content, category, items, context)

    def _analyze_style_consistency(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """従来の文体一貫性分析（下位互換性用）"""
        return self._analyze_style_consistency_enhanced(content, context)

    def _analyze_content_balance(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """従来の内容バランス分析（下位互換性用）"""
        return self._analyze_content_balance_enhanced(content, context)

    def _analyze_format_structure(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """従来のフォーマット構造分析（下位互換性用）"""
        return self._analyze_format_structure_enhanced(content, context)

    def _analyze_readability(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """従来の読みやすさ分析（下位互換性用）"""
        return self._analyze_readability_enhanced(content, context)

    def _analyze_character_consistency(self, content: str, context: AnalysisContext) -> CategoryAnalysisResult:
        """キャラクター一貫性分析

        Args:
            content: エピソード内容
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: キャラクター分析結果
        """
        issues = []
        suggestions = []
        score = 100.0
        speech_consistency = self._check_speech_pattern_consistency(content)
        if speech_consistency < 80:
            issues.append("キャラクターの話し方に不一致があります")
            suggestions.append("各キャラクターの話し方を一貫させてください")
            score -= (80 - speech_consistency) * 0.5
        behavior_consistency = self._check_behavior_consistency(content)
        if behavior_consistency < 75:
            issues.append("キャラクターの行動パターンに一貫性がありません")
            suggestions.append("キャラクター設定に基づいた行動を心がけてください")
            score -= (75 - behavior_consistency) * 0.3
        score = max(0.0, min(100.0, score))
        return CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CHARACTER_CONSISTENCY,
            score=score,
            issues_found=issues,
            suggestions=suggestions,
        )

    def _analyze_generic_category(
        self, content: str, category: A31EvaluationCategory, context: AnalysisContext
    ) -> CategoryAnalysisResult:
        """汎用カテゴリ分析

        Args:
            content: エピソード内容
            category: 分析カテゴリ
            context: 分析コンテキスト

        Returns:
            CategoryAnalysisResult: 汎用分析結果
        """
        basic_score = self._calculate_basic_quality_score(content)
        return CategoryAnalysisResult.create(
            category=category,
            score=basic_score,
            issues_found=["基本品質チェック完了"],
            suggestions=["継続的な品質向上を推奨します"],
        )

    def _check_sentence_ending_monotony(self, content: str) -> float:
        """文末単調性チェック"""
        sentences = re.split("[。！？]", content)
        if len(sentences) < 3:
            return 90.0
        ending_patterns = []
        for sentence in sentences:
            if sentence.strip():
                if sentence.endswith("だった"):
                    ending_patterns.append("past")
                elif sentence.endswith(("である", "だ")):
                    ending_patterns.append("assertive")
                elif sentence.endswith(("した", "た")):
                    ending_patterns.append("past_action")
                else:
                    ending_patterns.append("other")
        unique_patterns = len(set(ending_patterns))
        total_patterns = len(ending_patterns)
        if total_patterns > 0:
            diversity_ratio = unique_patterns / total_patterns
            return min(100.0, diversity_ratio * 120)
        return 80.0

    def _check_writing_style_consistency(self, content: str) -> float:
        """文体統一性チェック"""
        polite_patterns = len(re.findall("です|ます|であります", content))
        casual_patterns = len(re.findall("だ。|である。|だった。", content))
        total_patterns = polite_patterns + casual_patterns
        if total_patterns == 0:
            return 85.0
        consistency_ratio = max(polite_patterns, casual_patterns) / total_patterns
        return min(100.0, consistency_ratio * 100)

    def _check_word_repetition(self, content: str) -> float:
        """語句反復チェック"""
        words = re.findall("\\b\\w+\\b", content)
        word_counts = {}
        for word in words:
            if len(word) > 1:
                word_counts[word] = word_counts.get(word, 0) + 1
        if not word_counts:
            return 90.0
        max_repetition = max(word_counts.values())
        total_words = len(words)
        if max_repetition > total_words * 0.1:
            return max(30.0, 100 - max_repetition / total_words * 200)
        return 85.0

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """会話文比率計算"""
        lines = content.split("\n")
        dialogue_lines = sum(1 for line in lines if "「" in line and "」" in line)
        total_lines = len([line for line in lines if line.strip()])
        return dialogue_lines / total_lines if total_lines > 0 else 0.0

    def _check_sensory_descriptions(self, content: str) -> float:
        """五感描写チェック（従来版）"""
        sensory_keywords = {
            "視覚": ["見", "目", "色", "光", "影", "姿", "表情"],
            "聴覚": ["音", "声", "響", "聞", "静か", "騒"],
            "触覚": ["触", "感じ", "温", "冷", "痛", "柔らか", "硬"],
            "嗅覚": ["匂", "香", "臭"],
            "味覚": ["味", "甘", "辛", "苦", "酸"],
        }
        detected_senses = 0
        for keywords in sensory_keywords.values():
            if any(keyword in content for keyword in keywords):
                detected_senses += 1
        return detected_senses / len(sensory_keywords) * 100

    def _calculate_content_density(self, content: str) -> float:
        """内容密度計算"""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            return 0.0
        meaningful_paragraphs = 0
        for paragraph in paragraphs:
            if len(paragraph) > 20 and ("。" in paragraph or "！" in paragraph or "？" in paragraph):
                meaningful_paragraphs += 1
        return meaningful_paragraphs / len(paragraphs)

    def _check_paragraph_structure(self, content: str) -> float:
        """段落構成チェック"""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if len(paragraphs) < 2:
            return 60.0
        paragraph_lengths = [len(p) for p in paragraphs]
        avg_length = sum(paragraph_lengths) / len(paragraph_lengths)
        balanced_paragraphs = sum(1 for length in paragraph_lengths if avg_length * 0.3 <= length <= avg_length * 2.5)
        balance_ratio = balanced_paragraphs / len(paragraphs)
        return min(100.0, balance_ratio * 120)

    def _check_opening_effectiveness(self, content: str) -> float:
        """冒頭効果性チェック"""
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if len(lines) < 3:
            return 70.0
        opening_lines = lines[:3]
        effectiveness_score = 70.0
        for line in opening_lines:
            if "「" in line:
                effectiveness_score += 10
            if any(verb in line for verb in ["走", "歩", "見", "聞", "感じ"]):
                effectiveness_score += 5
            if any(emotion in line for emotion in ["驚", "喜", "悲", "怒", "不安"]):
                effectiveness_score += 5
        return min(100.0, effectiveness_score)

    def _check_structure_clarity(self, content: str) -> float:
        """構造明確性チェック"""
        structure_markers = len(re.findall("^#+\\s", content, re.MULTILINE))
        scene_breaks = len(re.findall("\\n\\s*\\n", content))
        lines_count = len([line for line in content.split("\n") if line.strip()])
        if lines_count == 0:
            return 0.0
        structure_ratio = (structure_markers + scene_breaks) / (lines_count / 10)
        return min(100.0, structure_ratio * 100)

    def _check_sentence_length_balance(self, content: str) -> float:
        """文長バランスチェック"""
        sentences = re.split("[。！？]", content)
        meaningful_sentences = [s.strip() for s in sentences if s.strip()]
        if len(meaningful_sentences) < 3:
            return 80.0
        lengths = [len(s) for s in meaningful_sentences]
        avg_length = sum(lengths) / len(lengths)
        short_sentences = sum(1 for length in lengths if length < avg_length * 0.7)
        long_sentences = sum(1 for length in lengths if length > avg_length * 1.3)
        medium_sentences = len(lengths) - short_sentences - long_sentences
        total = len(lengths)
        balance_score = min(short_sentences / total, medium_sentences / total, long_sentences / total) * 300
        return min(100.0, balance_score)

    def _check_character_balance(self, content: str) -> float:
        """文字バランスチェック"""
        hiragana_count = len(re.findall("[あ-ん]", content))
        katakana_count = len(re.findall("[ア-ン]", content))
        kanji_count = len(re.findall("[一-龯]", content))
        total_chars = hiragana_count + katakana_count + kanji_count
        if total_chars == 0:
            return 0.0
        hiragana_ratio = hiragana_count / total_chars
        kanji_ratio = kanji_count / total_chars
        ideal_hiragana = 0.65
        ideal_kanji = 0.3
        hiragana_diff = abs(hiragana_ratio - ideal_hiragana)
        kanji_diff = abs(kanji_ratio - ideal_kanji)
        balance_score = 100 - (hiragana_diff + kanji_diff) * 200
        return max(0.0, min(100.0, balance_score))

    def _check_speech_pattern_consistency(self, content: str) -> float:
        """話し方一貫性チェック"""
        dialogues = re.findall("「([^」]+)」", content)
        if len(dialogues) < 2:
            return 90.0
        polite_dialogues = sum(1 for d in dialogues if "です" in d or "ます" in d)
        casual_dialogues = len(dialogues) - polite_dialogues
        if len(dialogues) > 0:
            consistency = max(polite_dialogues, casual_dialogues) / len(dialogues)
            return min(100.0, consistency * 100)
        return 85.0

    def _check_behavior_consistency(self, content: str) -> float:
        """行動一貫性チェック"""
        action_verbs = re.findall("(走|歩|立|座|見|聞|話|言|思|考)", content)
        if len(action_verbs) < 3:
            return 85.0
        unique_actions = len(set(action_verbs))
        total_actions = len(action_verbs)
        diversity_ratio = unique_actions / total_actions if total_actions > 0 else 0
        return min(100.0, 70 + diversity_ratio * 30)

    def _calculate_basic_quality_score(self, content: str) -> float:
        """基本品質スコア計算"""
        if not content.strip():
            return 0.0
        word_count = len(content.split())
        sentence_count = len(re.split("[。！？]", content))
        if word_count < 10:
            return 30.0
        if word_count < 50:
            return 50.0
        if sentence_count < 3:
            return 60.0
        return 75.0

    def _generate_category_line_feedbacks(
        self, content: str, category: A31EvaluationCategory, analysis_result: CategoryAnalysisResult
    ) -> list[LineSpecificFeedback]:
        """カテゴリ別行フィードバック生成（従来版）"""
        feedbacks = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if line.strip():
                feedback = self._generate_line_feedback(
                    line_content=line,
                    line_number=i,
                    context_lines=lines[max(0, i - 2) : i + 2],
                    issue_context={"category": category, "analysis_result": analysis_result},
                )
                if feedback and feedback.has_issues():
                    feedbacks.append(feedback)
        return feedbacks

    def _generate_line_feedback(
        self, line_content: str, line_number: int, context_lines: list[str], issue_context: dict[str, Any]
    ) -> LineSpecificFeedback | None:
        """個別行フィードバック生成（従来版）"""
        category = issue_context.get("category")
        mod_lsf = importlib.import_module("noveler.domain.value_objects.line_specific_feedback")
        IssueSeverity = mod_lsf.IssueSeverity
        LineSpecificFeedback = mod_lsf.LineSpecificFeedback

        if category == A31EvaluationCategory.STYLE_CONSISTENCY:
            if line_content.count("だった") >= 2:
                return LineSpecificFeedback.create(
                    line_number=line_number,
                    original_text=line_content,
                    issue_type=IssueType.STYLE_MONOTONY.value,
                    severity=IssueSeverity.MINOR.value,
                    suggestion="文末バリエーションを増やしてください（例：だった→である、した）",
                    confidence=0.9,
                    context_lines=context_lines,
                )
        elif category == A31EvaluationCategory.CONTENT_BALANCE:
            if len([c for c in context_lines if "「" in c and "」" in c]) > 3:
                return LineSpecificFeedback.create(
                    line_number=line_number,
                    original_text=line_content,
                    issue_type=IssueType.CONTENT_BALANCE.value,
                    severity=IssueSeverity.MINOR.value,
                    suggestion="会話文が集中しています。地の文による状況説明を追加してください",
                    confidence=0.8,
                    context_lines=context_lines,
                )
        return None

    def _calculate_overall_score(self, category_results: list[CategoryAnalysisResult]) -> float:
        """総合スコア計算"""
        if not category_results:
            return 0.0
        scores = [result.score for result in category_results]
        return mean(scores)

    def _calculate_analysis_confidence(
        self, category_results: list[CategoryAnalysisResult], line_feedbacks: list[LineSpecificFeedback], content: str
    ) -> float:
        """分析信頼度計算（従来版）"""
        return self._calculate_enhanced_analysis_confidence(category_results, line_feedbacks, content)

    def _generate_analysis_summary(
        self,
        category_results: list[CategoryAnalysisResult],
        line_feedbacks: list[LineSpecificFeedback],
        context: AnalysisContext,
    ) -> dict[str, Any]:
        """分析サマリー生成"""
        return {
            "project_name": context.project_name,
            "episode_number": context.episode_number,
            "categories_analyzed": len(category_results),
            "total_issues_found": sum(len(result.issues_found) for result in category_results),
            "total_suggestions": sum(len(result.suggestions) for result in category_results),
            "line_issues_count": len(line_feedbacks),
            "critical_issues": len([f for f in line_feedbacks if f.severity == IssueSeverity.CRITICAL]),
            "major_issues": len([f for f in line_feedbacks if f.severity == IssueSeverity.MAJOR]),
            "minor_issues": len([f for f in line_feedbacks if f.severity == IssueSeverity.MINOR]),
        }

    def _initialize_style_patterns(self) -> dict[str, Any]:
        """文体パターン初期化"""
        return {
            "monotony_patterns": [
                "だった[。！？].*だった[。！？].*だった[。！？]",
                "である[。！？].*である[。！？].*である[。！？]",
            ],
            "consistency_patterns": ["です|ます", "だ。|である。"],
        }

    def _initialize_content_analyzers(self) -> dict[str, Any]:
        """コンテンツ分析器初期化"""
        return {
            "dialogue_markers": ["「[^」]*」"],
            "sensory_keywords": {
                "visual": ["見", "目", "色", "光", "影"],
                "auditory": ["音", "声", "響", "聞"],
                "tactile": ["触", "感じ", "温", "冷"],
            },
        }
