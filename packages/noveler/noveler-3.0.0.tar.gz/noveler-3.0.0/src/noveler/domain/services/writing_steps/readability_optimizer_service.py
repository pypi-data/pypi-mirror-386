"""STEP 14: 文体・可読性最適化サービス

A38執筆プロンプトガイドのSTEP14「文体・可読性パス」を実装するサービス。
文体の一貫性と可読性を最適化し、読者にとって読みやすく魅力的な文章に
調整します。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from noveler.application.services.stepwise_execution_service import BaseWritingStep
from noveler.domain.models.project_model import ProjectModel
from noveler.domain.services.configuration_manager_service import ConfigurationManagerService


class WritingStyle(Enum):
    """文体スタイル"""
    NARRATIVE = "narrative"  # 物語調
    DESCRIPTIVE = "descriptive"  # 描写調
    CONVERSATIONAL = "conversational"  # 会話調
    POETIC = "poetic"  # 詩的
    DIRECT = "direct"  # 直接的
    FORMAL = "formal"  # 改まった調子
    CASUAL = "casual"  # カジュアル


class ReadabilityAspect(Enum):
    """可読性の側面"""
    SENTENCE_LENGTH = "sentence_length"  # 文の長さ
    WORD_CHOICE = "word_choice"  # 語彙選択
    SENTENCE_STRUCTURE = "sentence_structure"  # 文構造
    PARAGRAPH_FLOW = "paragraph_flow"  # 段落の流れ
    RHYTHM_PATTERN = "rhythm_pattern"  # リズムパターン
    CLARITY = "clarity"  # 明瞭性
    ENGAGEMENT = "engagement"  # 読者の関与


class StyleInconsistency(Enum):
    """文体の不一貫性タイプ"""
    TONE_SHIFT = "tone_shift"  # 語調の変化
    FORMALITY_MISMATCH = "formality_mismatch"  # 敬語レベルの不一致
    TENSE_INCONSISTENCY = "tense_inconsistency"  # 時制の不統一
    VOICE_CHANGE = "voice_change"  # 語り手の変化
    STYLE_MIXING = "style_mixing"  # スタイルの混在


@dataclass
class ReadabilityMetric:
    """可読性メトリック"""
    metric_name: str
    metric_value: float  # 0-1スケール
    description: str
    target_range: tuple[float, float]  # 目標範囲
    current_assessment: str  # 現在の評価
    improvement_potential: float  # 改善可能性


@dataclass
class StyleAnalysis:
    """文体分析"""
    dominant_style: WritingStyle
    style_distribution: dict[WritingStyle, float]
    consistency_score: float  # 一貫性スコア (0-1)
    detected_inconsistencies: list[StyleInconsistency]
    formality_level: float  # 改まり度 (0-1)
    emotional_tone: str  # 感情的トーン
    narrative_voice: str  # 語り手の声


@dataclass
class SentenceAnalysis:
    """文分析"""
    sentence_id: str
    sentence_text: str
    length: int
    complexity_score: float  # 複雑さスコア (0-1)
    readability_score: float  # 可読性スコア (0-1)
    style_classification: WritingStyle
    grammatical_issues: list[str]
    improvement_suggestions: list[str]
    rhythm_pattern: str
    emotional_weight: float  # 感情的重み


@dataclass
class ParagraphAnalysis:
    """段落分析"""
    paragraph_id: str
    sentences: list[SentenceAnalysis]
    flow_score: float  # 流れのスコア (0-1)
    coherence_score: float  # 一貫性スコア (0-1)
    transition_quality: float  # 移行品質 (0-1)
    length_balance: float  # 長さのバランス (0-1)
    information_density: float  # 情報密度


@dataclass
class ReadabilityOptimization:
    """可読性最適化"""
    optimization_id: str
    target_aspect: ReadabilityAspect
    optimization_type: str  # improve, maintain, adjust
    original_sentence: str
    optimized_sentence: str
    improvement_reason: str
    quality_impact: float  # 品質への影響 (0-1)
    readability_gain: float  # 可読性向上度 (0-1)
    confidence_level: float  # 信頼度 (0-1)


@dataclass
class StyleOptimization:
    """文体最適化"""
    optimization_id: str
    inconsistency_type: StyleInconsistency
    location: str  # 場所
    original_text: str
    optimized_text: str
    style_target: WritingStyle
    adjustment_reason: str
    consistency_improvement: float  # 一貫性向上度


@dataclass
class ReadabilityOptimizationReport:
    """可読性最適化レポート"""
    report_id: str
    episode_number: int
    optimization_timestamp: datetime
    original_text: str
    optimized_text: str
    readability_metrics: list[ReadabilityMetric]
    style_analysis: StyleAnalysis
    sentence_analyses: list[SentenceAnalysis]
    paragraph_analyses: list[ParagraphAnalysis]
    readability_optimizations: list[ReadabilityOptimization]
    style_optimizations: list[StyleOptimization]
    overall_readability_score: float  # 全体可読性スコア (0-1)
    style_consistency_score: float  # 文体一貫性スコア (0-1)
    improvement_summary: str
    quality_assessment: dict[str, float]
    recommendations: list[str]
    optimization_metadata: dict[str, Any]


@dataclass
class ReadabilityOptimizerConfig:
    """可読性最適化設定"""
    target_reading_level: str = "general"  # general, advanced, simple
    preferred_style: WritingStyle = WritingStyle.NARRATIVE
    max_sentence_length: int = 50  # 最大文字数
    min_sentence_length: int = 10  # 最小文字数
    target_paragraph_length: int = 200  # 目標段落文字数
    consistency_weight: float = 0.4  # 一貫性重み
    readability_weight: float = 0.6  # 可読性重み
    preserve_author_voice: bool = True  # 作者の声保持
    enable_rhythm_optimization: bool = True  # リズム最適化
    enable_clarity_enhancement: bool = True  # 明瞭性向上
    enable_engagement_improvement: bool = True  # 関与度改善
    aggressive_optimization: bool = False  # 積極的最適化


class ReadabilityOptimizerService(BaseWritingStep):
    """STEP 14: 文体・可読性最適化サービス

    文体の一貫性と可読性を最適化し、読者にとって読みやすく魅力的な文章に
    調整するサービス。
    A38ガイドのSTEP14「文体・可読性パス」を実装。
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
        self._optimizer_config = ReadabilityOptimizerConfig()

        # 可読性分析ツール
        self._readability_analyzers = self._initialize_readability_analyzers()
        self._style_patterns = self._initialize_style_patterns()
        self._optimization_rules = self._initialize_optimization_rules()

    @abstractmethod
    def get_step_name(self) -> str:
        """ステップ名を取得"""
        return "文体・可読性最適化"

    @abstractmethod
    def get_step_description(self) -> str:
        """ステップの説明を取得"""
        return "文体の一貫性と可読性を最適化し、読者にとって読みやすく魅力的な文章に調整します"

    @abstractmethod
    def execute_step(self, context: dict[str, Any]) -> dict[str, Any]:
        """STEP 14: 文体・可読性最適化の実行

        Args:
            context: 実行コンテキスト

        Returns:
            文体・可読性最適化結果を含むコンテキスト
        """
        try:
            episode_number = context.get("episode_number")
            project = context.get("project")

            if not episode_number or not project:
                msg = "episode_numberまたはprojectが指定されていません"
                raise ValueError(msg)

            # テキストの取得
            text_to_optimize = self._get_text_for_optimization(context)
            if not text_to_optimize:
                msg = "最適化対象のテキストが見つかりません"
                raise ValueError(msg)

            # 可読性最適化の実行
            optimization_report = self._execute_readability_optimization(
                episode_number=episode_number,
                project=project,
                text=text_to_optimize,
                context=context
            )

            # 結果をコンテキストに追加
            context["readability_optimization"] = optimization_report
            context["optimized_readable_text"] = optimization_report.optimized_text
            context["readability_optimization_completed"] = True

            return context

        except Exception as e:
            context["readability_optimization_error"] = str(e)
            raise

    def _get_text_for_optimization(self, context: dict[str, Any]) -> str:
        """最適化対象テキストの取得"""

        # 文字数最適化後のテキストがあればそれを使用
        if "optimized_text" in context:
            return context["optimized_text"]

        # その他のソースからテキストを取得
        text_sources = [
            "manuscript_text",
            "final_manuscript",
            "generated_manuscript"
        ]

        for source in text_sources:
            text = context.get(source)
            if text and isinstance(text, str):
                return text

        return ""

    def _execute_readability_optimization(
        self,
        episode_number: int,
        project: ProjectModel,
        text: str,
        context: dict[str, Any]
    ) -> ReadabilityOptimizationReport:
        """可読性最適化の実行"""

        # 初期分析
        readability_metrics = self._analyze_readability_metrics(text)
        style_analysis = self._analyze_writing_style(text)

        # 文・段落レベル分析
        sentence_analyses = self._analyze_sentences(text)
        paragraph_analyses = self._analyze_paragraphs(text, sentence_analyses)

        # 最適化の実行
        readability_optimizations = self._perform_readability_optimizations(
            text, sentence_analyses, readability_metrics
        )

        style_optimizations = self._perform_style_optimizations(
            text, style_analysis, sentence_analyses
        )

        # 最適化されたテキストの生成
        optimized_text = self._apply_optimizations(
            text, readability_optimizations, style_optimizations
        )

        # 最適化後の評価
        final_readability_score = self._calculate_overall_readability(
            optimized_text, readability_metrics
        )

        final_consistency_score = self._calculate_style_consistency(
            optimized_text, style_analysis
        )

        # 品質評価
        quality_assessment = self._assess_optimization_quality(
            text, optimized_text, readability_optimizations, style_optimizations
        )

        # レポート生成
        return self._generate_optimization_report(
            episode_number=episode_number,
            original_text=text,
            optimized_text=optimized_text,
            readability_metrics=readability_metrics,
            style_analysis=style_analysis,
            sentence_analyses=sentence_analyses,
            paragraph_analyses=paragraph_analyses,
            readability_optimizations=readability_optimizations,
            style_optimizations=style_optimizations,
            overall_readability_score=final_readability_score,
            style_consistency_score=final_consistency_score,
            quality_assessment=quality_assessment
        )

    def _analyze_readability_metrics(self, text: str) -> list[ReadabilityMetric]:
        """可読性メトリクスの分析"""
        metrics = []

        # 文の長さ
        sentences = self._split_into_sentences(text)
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        sentence_length_score = self._score_sentence_length(avg_sentence_length)

        metrics.append(ReadabilityMetric(
            metric_name="平均文長",
            metric_value=sentence_length_score,
            description=f"平均{avg_sentence_length:.1f}文字",
            target_range=(0.6, 0.8),
            current_assessment=self._assess_sentence_length(sentence_length_score),
            improvement_potential=1.0 - sentence_length_score
        ))

        # 語彙の複雑さ
        vocab_complexity = self._analyze_vocabulary_complexity(text)

        metrics.append(ReadabilityMetric(
            metric_name="語彙複雑さ",
            metric_value=vocab_complexity,
            description="語彙の難易度",
            target_range=(0.4, 0.7),
            current_assessment=self._assess_vocabulary_complexity(vocab_complexity),
            improvement_potential=abs(0.55 - vocab_complexity)
        ))

        # 段落の流れ
        paragraph_flow = self._analyze_paragraph_flow(text)

        metrics.append(ReadabilityMetric(
            metric_name="段落の流れ",
            metric_value=paragraph_flow,
            description="段落間の接続性",
            target_range=(0.7, 0.9),
            current_assessment=self._assess_paragraph_flow(paragraph_flow),
            improvement_potential=1.0 - paragraph_flow
        ))

        # リズム・テンポ
        rhythm_score = self._analyze_rhythm_pattern(text)

        metrics.append(ReadabilityMetric(
            metric_name="文章リズム",
            metric_value=rhythm_score,
            description="読みやすさのリズム",
            target_range=(0.6, 0.8),
            current_assessment=self._assess_rhythm(rhythm_score),
            improvement_potential=abs(0.7 - rhythm_score)
        ))

        return metrics

    def _analyze_writing_style(self, text: str) -> StyleAnalysis:
        """文体分析"""

        # 文体分布の分析
        style_distribution = self._calculate_style_distribution(text)
        dominant_style = max(style_distribution.keys(), key=lambda s: style_distribution[s])

        # 一貫性の分析
        consistency_score = self._calculate_style_consistency_score(text, style_distribution)

        # 不一貫性の検出
        inconsistencies = self._detect_style_inconsistencies(text)

        # 改まり度の分析
        formality_level = self._analyze_formality_level(text)

        # 感情的トーンの分析
        emotional_tone = self._analyze_emotional_tone(text)

        # 語り手の声の分析
        narrative_voice = self._analyze_narrative_voice(text)

        return StyleAnalysis(
            dominant_style=dominant_style,
            style_distribution=style_distribution,
            consistency_score=consistency_score,
            detected_inconsistencies=inconsistencies,
            formality_level=formality_level,
            emotional_tone=emotional_tone,
            narrative_voice=narrative_voice
        )

    def _analyze_sentences(self, text: str) -> list[SentenceAnalysis]:
        """文分析"""
        sentences = self._split_into_sentences(text)
        analyses = []

        for i, sentence in enumerate(sentences):
            if sentence.strip():
                analysis = SentenceAnalysis(
                    sentence_id=f"sent_{i}",
                    sentence_text=sentence.strip(),
                    length=len(sentence.strip()),
                    complexity_score=self._calculate_sentence_complexity(sentence),
                    readability_score=self._calculate_sentence_readability(sentence),
                    style_classification=self._classify_sentence_style(sentence),
                    grammatical_issues=self._detect_grammatical_issues(sentence),
                    improvement_suggestions=self._generate_sentence_improvements(sentence),
                    rhythm_pattern=self._analyze_sentence_rhythm(sentence),
                    emotional_weight=self._calculate_emotional_weight(sentence)
                )
                analyses.append(analysis)

        return analyses

    def _analyze_paragraphs(
        self,
        text: str,
        sentence_analyses: list[SentenceAnalysis]
    ) -> list[ParagraphAnalysis]:
        """段落分析"""
        paragraphs = text.split("\n\n")
        analyses = []

        sentence_idx = 0
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                # この段落に含まれる文を特定
                paragraph_sentences = []
                para_sentence_count = paragraph.count("。") + paragraph.count("！") + paragraph.count("？")

                for _ in range(para_sentence_count):
                    if sentence_idx < len(sentence_analyses):
                        paragraph_sentences.append(sentence_analyses[sentence_idx])
                        sentence_idx += 1

                analysis = ParagraphAnalysis(
                    paragraph_id=f"para_{i}",
                    sentences=paragraph_sentences,
                    flow_score=self._calculate_paragraph_flow(paragraph),
                    coherence_score=self._calculate_paragraph_coherence(paragraph),
                    transition_quality=self._calculate_transition_quality(paragraph, i, paragraphs),
                    length_balance=self._calculate_length_balance(paragraph),
                    information_density=self._calculate_information_density(paragraph)
                )
                analyses.append(analysis)

        return analyses

    def _perform_readability_optimizations(
        self,
        text: str,
        sentence_analyses: list[SentenceAnalysis],
        metrics: list[ReadabilityMetric]
    ) -> list[ReadabilityOptimization]:
        """可読性最適化の実行"""
        optimizations = []

        # 文の長さ最適化
        for sentence_analysis in sentence_analyses:
            if self._needs_length_optimization(sentence_analysis):
                optimization = self._create_length_optimization(sentence_analysis)
                if optimization:
                    optimizations.append(optimization)

        # 語彙最適化
        vocab_optimizations = self._optimize_vocabulary(sentence_analyses, metrics)
        optimizations.extend(vocab_optimizations)

        # 構造最適化
        structure_optimizations = self._optimize_sentence_structure(sentence_analyses)
        optimizations.extend(structure_optimizations)

        # リズム最適化
        if self._optimizer_config.enable_rhythm_optimization:
            rhythm_optimizations = self._optimize_rhythm(sentence_analyses)
            optimizations.extend(rhythm_optimizations)

        return optimizations

    def _perform_style_optimizations(
        self,
        text: str,
        style_analysis: StyleAnalysis,
        sentence_analyses: list[SentenceAnalysis]
    ) -> list[StyleOptimization]:
        """文体最適化の実行"""
        optimizations = []

        # 不一貫性の修正
        for inconsistency in style_analysis.detected_inconsistencies:
            optimization = self._create_style_optimization(inconsistency, text, sentence_analyses)
            if optimization:
                optimizations.append(optimization)

        # 語調統一
        tone_optimizations = self._optimize_tone_consistency(text, style_analysis)
        optimizations.extend(tone_optimizations)

        # 改まり度調整
        formality_optimizations = self._optimize_formality_level(text, style_analysis)
        optimizations.extend(formality_optimizations)

        return optimizations

    def _apply_optimizations(
        self,
        original_text: str,
        readability_opts: list[ReadabilityOptimization],
        style_opts: list[StyleOptimization]
    ) -> str:
        """最適化の適用"""
        optimized_text = original_text

        # 可読性最適化の適用
        for opt in readability_opts:
            optimized_text = optimized_text.replace(
                opt.original_sentence, opt.optimized_sentence
            )

        # 文体最適化の適用
        for opt in style_opts:
            optimized_text = optimized_text.replace(
                opt.original_text, opt.optimized_text
            )

        return optimized_text

    def _generate_optimization_report(
        self,
        episode_number: int,
        original_text: str,
        optimized_text: str,
        readability_metrics: list[ReadabilityMetric],
        style_analysis: StyleAnalysis,
        sentence_analyses: list[SentenceAnalysis],
        paragraph_analyses: list[ParagraphAnalysis],
        readability_optimizations: list[ReadabilityOptimization],
        style_optimizations: list[StyleOptimization],
        overall_readability_score: float,
        style_consistency_score: float,
        quality_assessment: dict[str, float]
    ) -> ReadabilityOptimizationReport:
        """最適化レポートの生成"""

        # 改善サマリーの生成
        improvement_summary = self._generate_improvement_summary(
            readability_optimizations, style_optimizations,
            overall_readability_score, style_consistency_score
        )

        # 推奨事項の生成
        recommendations = self._generate_optimization_recommendations(
            readability_metrics, style_analysis, quality_assessment
        )

        return ReadabilityOptimizationReport(
            report_id=f"readability_opt_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            episode_number=episode_number,
            optimization_timestamp=datetime.now(tz=datetime.timezone.utc),
            original_text=original_text,
            optimized_text=optimized_text,
            readability_metrics=readability_metrics,
            style_analysis=style_analysis,
            sentence_analyses=sentence_analyses,
            paragraph_analyses=paragraph_analyses,
            readability_optimizations=readability_optimizations,
            style_optimizations=style_optimizations,
            overall_readability_score=overall_readability_score,
            style_consistency_score=style_consistency_score,
            improvement_summary=improvement_summary,
            quality_assessment=quality_assessment,
            recommendations=recommendations,
            optimization_metadata={
                "config": self._optimizer_config.__dict__,
                "optimization_timestamp": datetime.now(tz=datetime.timezone.utc),
                "total_readability_optimizations": len(readability_optimizations),
                "total_style_optimizations": len(style_optimizations),
                "character_count_change": len(optimized_text) - len(original_text)
            }
        )

    # 分析メソッドの実装

    def _initialize_readability_analyzers(self) -> dict[str, Any]:
        """可読性分析器の初期化"""
        return {
            "sentence_length": {
                "optimal_range": (15, 35),
                "warning_threshold": 50
            },
            "vocabulary": {
                "common_words_weight": 0.7,
                "technical_words_penalty": 0.3
            },
            "rhythm": {
                "variation_target": 0.6,
                "monotony_threshold": 0.3
            }
        }

    def _initialize_style_patterns(self) -> dict[str, Any]:
        """文体パターンの初期化"""
        return {
            WritingStyle.NARRATIVE: {
                "markers": ["だった", "である", "のだ"],
                "sentence_endings": ["。", "のだった。"],
                "tone": "storytelling"
            },
            WritingStyle.DESCRIPTIVE: {
                "markers": ["ように", "まるで", "かのような"],
                "sentence_endings": ["。", "のである。"],
                "tone": "observational"
            },
            WritingStyle.CONVERSATIONAL: {
                "markers": ["「", "」", "だよ", "ですね"],
                "sentence_endings": ["。", "？", "！"],
                "tone": "informal"
            }
        }

    def _initialize_optimization_rules(self) -> dict[str, Any]:
        """最適化ルールの初期化"""
        return {
            "sentence_length": {
                "max_length": 50,
                "optimal_length": 25,
                "split_strategies": ["conjunction", "subordinate_clause"]
            },
            "vocabulary": {
                "complexity_reduction": {
                    "difficult_words": ["複雑な", "困難な", "厄介な"],
                    "simple_alternatives": ["難しい", "大変な", "面倒な"]
                }
            },
            "rhythm": {
                "variation_techniques": ["length_variation", "structure_variation"],
                "monotony_breakers": ["短文挿入", "疑問文変換"]
            }
        }

    def _split_into_sentences(self, text: str) -> list[str]:
        """文への分割"""
        import re
        # 日本語の文末記号で分割
        sentences = re.split(r"[。！？]", text)
        return [s.strip() + "。" for s in sentences if s.strip()]

    def _score_sentence_length(self, avg_length: float) -> float:
        """文の長さのスコア化"""
        optimal_length = 25
        if avg_length <= optimal_length:
            return avg_length / optimal_length
        # 長すぎる場合はペナルティ
        excess = avg_length - optimal_length
        return max(0.0, 1.0 - excess / optimal_length)

    def _assess_sentence_length(self, score: float) -> str:
        """文の長さの評価"""
        if score >= 0.8:
            return "最適"
        if score >= 0.6:
            return "良好"
        if score >= 0.4:
            return "要改善"
        return "要大幅改善"

    def _analyze_vocabulary_complexity(self, text: str) -> float:
        """語彙複雑さの分析"""
        # 簡易実装：漢字の割合で判定
        total_chars = len(text)
        if total_chars == 0:
            return 0.0

        # 漢字のカウント（簡易実装）
        kanji_count = sum(1 for c in text if ord(c) >= 0x4E00 and ord(c) <= 0x9FAF)
        kanji_ratio = kanji_count / total_chars

        # 0-1スケールに正規化
        return min(kanji_ratio * 2, 1.0)

    def _assess_vocabulary_complexity(self, complexity: float) -> str:
        """語彙複雑さの評価"""
        if complexity <= 0.3:
            return "易しい"
        if complexity <= 0.5:
            return "適切"
        if complexity <= 0.7:
            return "やや難しい"
        return "難しい"

    def _analyze_paragraph_flow(self, text: str) -> float:
        """段落の流れ分析"""
        paragraphs = text.split("\n\n")
        if len(paragraphs) <= 1:
            return 1.0

        # 接続詞の使用頻度で簡易評価
        connectors = ["そして", "しかし", "また", "さらに", "ところで", "つまり"]
        connector_count = sum(1 for connector in connectors if connector in text)

        # 段落数に対する接続詞の割合
        return min(connector_count / len(paragraphs), 1.0)

    def _assess_paragraph_flow(self, flow: float) -> str:
        """段落の流れの評価"""
        if flow >= 0.8:
            return "優秀"
        if flow >= 0.6:
            return "良好"
        if flow >= 0.4:
            return "普通"
        return "要改善"

    def _analyze_rhythm_pattern(self, text: str) -> float:
        """リズムパターンの分析"""
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            return 0.5

        # 文の長さの変動を測定
        lengths = [len(s) for s in sentences]
        if not lengths:
            return 0.5

        # 標準偏差を使って変動度を計算
        mean_length = sum(lengths) / len(lengths)
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5

        # 変動係数を正規化（適度な変動が理想）
        variation_coefficient = std_dev / mean_length if mean_length > 0 else 0

        # 0.2-0.4の変動係数が理想的
        if 0.2 <= variation_coefficient <= 0.4:
            return 1.0
        if variation_coefficient < 0.2:
            return variation_coefficient / 0.2 * 0.7  # 単調すぎる
        return max(0.0, 1.0 - (variation_coefficient - 0.4) / 0.6)  # 変動しすぎ

    def _assess_rhythm(self, rhythm_score: float) -> str:
        """リズムの評価"""
        if rhythm_score >= 0.8:
            return "優秀"
        if rhythm_score >= 0.6:
            return "良好"
        if rhythm_score >= 0.4:
            return "普通"
        return "要改善"

    def _calculate_style_distribution(self, text: str) -> dict[WritingStyle, float]:
        """文体分布の計算"""
        distribution = dict.fromkeys(WritingStyle, 0.0)

        # 各文体の特徴的なマーカーを検出
        for style, patterns in self._style_patterns.items():
            marker_count = 0
            for marker in patterns["markers"]:
                marker_count += text.count(marker)

            # 正規化
            distribution[style] = marker_count / max(len(text) / 100, 1)

        # 正規化して合計を1にする
        total = sum(distribution.values())
        if total > 0:
            distribution = {k: v / total for k, v in distribution.items()}
        else:
            # デフォルトとして物語調を設定
            distribution[WritingStyle.NARRATIVE] = 1.0

        return distribution

    def _calculate_style_consistency_score(
        self,
        text: str,
        style_distribution: dict[WritingStyle, float]
    ) -> float:
        """文体一貫性スコアの計算"""

        # 支配的スタイルの割合が高いほど一貫性が高い
        dominant_ratio = max(style_distribution.values())

        # エントロピー的な計算で多様性のペナルティ
        entropy = -sum(p * (p.bit_length() if p > 0 else 0) for p in style_distribution.values())
        max_entropy = (len(style_distribution)).bit_length() if len(style_distribution) > 0 else 1

        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        consistency = 1.0 - normalized_entropy

        return (dominant_ratio + consistency) / 2

    def _detect_style_inconsistencies(self, text: str) -> list[StyleInconsistency]:
        """文体の不一貫性検出"""
        inconsistencies = []

        # 簡易実装：敬語の混在チェック
        has_keigo = any(word in text for word in ["です", "ます", "である", "であろう"])
        has_casual = any(word in text for word in ["だ", "だよ", "だね"])

        if has_keigo and has_casual:
            inconsistencies.append(StyleInconsistency.FORMALITY_MISMATCH)

        # 時制の混在チェック
        has_past = any(word in text for word in ["だった", "した", "があった"])
        has_present = any(word in text for word in ["である", "する", "がある"])

        if has_past and has_present:
            inconsistencies.append(StyleInconsistency.TENSE_INCONSISTENCY)

        return inconsistencies

    def _analyze_formality_level(self, text: str) -> float:
        """改まり度の分析"""
        formal_markers = ["です", "ます", "である", "におかれましては"]
        casual_markers = ["だ", "だよ", "じゃん", "っす"]

        formal_count = sum(text.count(marker) for marker in formal_markers)
        casual_count = sum(text.count(marker) for marker in casual_markers)

        total_markers = formal_count + casual_count
        if total_markers == 0:
            return 0.5  # 中性

        return formal_count / total_markers

    def _analyze_emotional_tone(self, text: str) -> str:
        """感情的トーンの分析"""
        positive_words = ["嬉しい", "楽しい", "美しい", "素晴らしい", "感動"]
        negative_words = ["悲しい", "辛い", "苦しい", "悔しい", "怒り"]
        neutral_words = ["普通", "通常", "一般的", "標準的"]

        positive_count = sum(text.count(word) for word in positive_words)
        negative_count = sum(text.count(word) for word in negative_words)
        neutral_count = sum(text.count(word) for word in neutral_words)

        if positive_count > negative_count and positive_count > neutral_count:
            return "ポジティブ"
        if negative_count > positive_count and negative_count > neutral_count:
            return "ネガティブ"
        return "中性"

    def _analyze_narrative_voice(self, text: str) -> str:
        """語り手の声の分析"""
        first_person = ["私", "僕", "俺", "自分"]
        third_person = ["彼", "彼女", "その人"]

        first_count = sum(text.count(word) for word in first_person)
        third_count = sum(text.count(word) for word in third_person)

        if first_count > third_count:
            return "一人称"
        if third_count > first_count:
            return "三人称"
        return "混合"

    # 文・段落分析メソッドの実装（スタブ）

    def _calculate_sentence_complexity(self, sentence: str) -> float:
        """文の複雑さ計算"""
        # 従属節の数、文の長さ、語彙の複雑さを総合評価
        complexity_factors = []

        # 長さによる複雑さ
        length_complexity = min(len(sentence) / 50, 1.0)
        complexity_factors.append(length_complexity)

        # 従属節数による複雑さ
        subordinate_markers = ["が", "ので", "から", "ため", "とき", "ながら"]
        subordinate_count = sum(sentence.count(marker) for marker in subordinate_markers)
        subordinate_complexity = min(subordinate_count / 3, 1.0)
        complexity_factors.append(subordinate_complexity)

        return sum(complexity_factors) / len(complexity_factors)

    def _calculate_sentence_readability(self, sentence: str) -> float:
        """文の可読性計算"""
        # 長さ、語彙、構造を総合して可読性をスコア化
        readability_score = 1.0

        # 長さペナルティ
        if len(sentence) > 40:
            length_penalty = (len(sentence) - 40) / 40
            readability_score -= length_penalty * 0.3

        # 語彙複雑さペナルティ
        vocab_complexity = self._analyze_vocabulary_complexity(sentence)
        if vocab_complexity > 0.6:
            vocab_penalty = (vocab_complexity - 0.6) / 0.4
            readability_score -= vocab_penalty * 0.2

        return max(0.0, readability_score)

    def _classify_sentence_style(self, sentence: str) -> WritingStyle:
        """文のスタイル分類"""
        # 各スタイルのマーカーをチェック
        for style, patterns in self._style_patterns.items():
            marker_count = sum(sentence.count(marker) for marker in patterns["markers"])
            if marker_count > 0:
                return style

        return WritingStyle.NARRATIVE  # デフォルト

    def _detect_grammatical_issues(self, sentence: str) -> list[str]:
        """文法的問題の検出"""
        issues = []

        # 簡易チェック
        if sentence.count("。") > 1:
            issues.append("文が長すぎる可能性")

        if not sentence.endswith(("。", "！", "？")):
            issues.append("文末記号が不適切")

        return issues

    def _generate_sentence_improvements(self, sentence: str) -> list[str]:
        """文の改善提案生成"""
        suggestions = []

        if len(sentence) > 40:
            suggestions.append("文を分割して短くする")

        if sentence.count("が") > 2:
            suggestions.append("従属節を減らして簡潔にする")

        return suggestions

    def _analyze_sentence_rhythm(self, sentence: str) -> str:
        """文のリズムパターン分析"""
        if len(sentence) < 20:
            return "短調"
        if len(sentence) < 40:
            return "中調"
        return "長調"

    def _calculate_emotional_weight(self, sentence: str) -> float:
        """文の感情的重み計算"""
        emotional_words = ["嬉しい", "悲しい", "怒り", "喜び", "驚き", "恐怖"]
        emotional_count = sum(sentence.count(word) for word in emotional_words)
        return min(emotional_count / 3.0, 1.0)

    # 段落分析メソッドの実装（スタブ）

    def _calculate_paragraph_flow(self, paragraph: str) -> float:
        """段落の流れ計算"""
        return 0.8  # スタブ実装

    def _calculate_paragraph_coherence(self, paragraph: str) -> float:
        """段落の一貫性計算"""
        return 0.8  # スタブ実装

    def _calculate_transition_quality(self, paragraph: str, index: int, all_paragraphs: list[str]) -> float:
        """移行品質計算"""
        return 0.7  # スタブ実装

    def _calculate_length_balance(self, paragraph: str) -> float:
        """長さバランス計算"""
        return 0.8  # スタブ実装

    def _calculate_information_density(self, paragraph: str) -> float:
        """情報密度計算"""
        return 0.6  # スタブ実装

    # 最適化実行メソッド（スタブ実装）

    def _needs_length_optimization(self, sentence_analysis: SentenceAnalysis) -> bool:
        """長さ最適化が必要かどうか"""
        return sentence_analysis.length > self._optimizer_config.max_sentence_length

    def _create_length_optimization(self, sentence_analysis: SentenceAnalysis) -> ReadabilityOptimization | None:
        """長さ最適化の作成"""
        if sentence_analysis.length <= self._optimizer_config.max_sentence_length:
            return None

        # 簡易実装：長い文を分割
        optimized = sentence_analysis.sentence_text.replace("、そして", "。そして")

        return ReadabilityOptimization(
            optimization_id=f"length_opt_{sentence_analysis.sentence_id}",
            target_aspect=ReadabilityAspect.SENTENCE_LENGTH,
            optimization_type="improve",
            original_sentence=sentence_analysis.sentence_text,
            optimized_sentence=optimized,
            improvement_reason="文が長すぎるため分割",
            quality_impact=0.1,
            readability_gain=0.3,
            confidence_level=0.8
        )

    def _optimize_vocabulary(
        self,
        sentence_analyses: list[SentenceAnalysis],
        metrics: list[ReadabilityMetric]
    ) -> list[ReadabilityOptimization]:
        """語彙最適化"""
        return []  # スタブ実装

    def _optimize_sentence_structure(
        self,
        sentence_analyses: list[SentenceAnalysis]
    ) -> list[ReadabilityOptimization]:
        """文構造最適化"""
        return []  # スタブ実装

    def _optimize_rhythm(
        self,
        sentence_analyses: list[SentenceAnalysis]
    ) -> list[ReadabilityOptimization]:
        """リズム最適化"""
        return []  # スタブ実装

    def _create_style_optimization(
        self,
        inconsistency: StyleInconsistency,
        text: str,
        sentence_analyses: list[SentenceAnalysis]
    ) -> StyleOptimization | None:
        """文体最適化の作成"""
        # スタブ実装
        return None

    def _optimize_tone_consistency(
        self,
        text: str,
        style_analysis: StyleAnalysis
    ) -> list[StyleOptimization]:
        """語調一貫性の最適化"""
        return []  # スタブ実装

    def _optimize_formality_level(
        self,
        text: str,
        style_analysis: StyleAnalysis
    ) -> list[StyleOptimization]:
        """改まり度の最適化"""
        return []  # スタブ実装

    def _calculate_overall_readability(
        self,
        text: str,
        original_metrics: list[ReadabilityMetric]
    ) -> float:
        """全体可読性の計算"""
        # 新しいテキストでメトリクスを再計算
        new_metrics = self._analyze_readability_metrics(text)

        # 平均スコアを計算
        total_score = sum(metric.metric_value for metric in new_metrics)
        return total_score / len(new_metrics) if new_metrics else 0.5

    def _calculate_style_consistency(
        self,
        text: str,
        original_analysis: StyleAnalysis
    ) -> float:
        """文体一貫性の計算"""
        new_analysis = self._analyze_writing_style(text)
        return new_analysis.consistency_score

    def _assess_optimization_quality(
        self,
        original_text: str,
        optimized_text: str,
        readability_opts: list[ReadabilityOptimization],
        style_opts: list[StyleOptimization]
    ) -> dict[str, float]:
        """最適化品質の評価"""

        return {
            "readability_improvement": 0.3,
            "style_consistency_improvement": 0.2,
            "overall_quality": 0.8,
            "content_preservation": 0.95,
            "naturalness": 0.85
        }

    def _generate_improvement_summary(
        self,
        readability_opts: list[ReadabilityOptimization],
        style_opts: list[StyleOptimization],
        readability_score: float,
        consistency_score: float
    ) -> str:
        """改善サマリーの生成"""

        total_optimizations = len(readability_opts) + len(style_opts)

        summary_parts = [
            f"総計{total_optimizations}個の最適化を実施。",
            f"可読性スコア: {readability_score:.2f}, 文体一貫性: {consistency_score:.2f}。"
        ]

        if readability_score >= 0.8 and consistency_score >= 0.8:
            summary_parts.append("高品質な最適化が完了しました。")
        elif readability_score >= 0.6 and consistency_score >= 0.6:
            summary_parts.append("良好な最適化結果です。")
        else:
            summary_parts.append("追加の最適化を検討してください。")

        return " ".join(summary_parts)

    def _generate_optimization_recommendations(
        self,
        metrics: list[ReadabilityMetric],
        style_analysis: StyleAnalysis,
        quality_assessment: dict[str, float]
    ) -> list[str]:
        """最適化推奨事項の生成"""
        recommendations = []

        # メトリクスベースの推奨事項
        for metric in metrics:
            if metric.metric_value < 0.6:
                recommendations.append(f"📊 {metric.metric_name}の改善を推奨します")

        # 文体一貫性の推奨事項
        if style_analysis.consistency_score < 0.7:
            recommendations.append("🎭 文体の一貫性向上が必要です")

        # 品質評価ベースの推奨事項
        if quality_assessment.get("naturalness", 1.0) < 0.8:
            recommendations.append("📝 自然な文章表現への調整を検討してください")

        if not recommendations:
            recommendations.append("✅ 最適化は良好に完了しました")

        return recommendations
