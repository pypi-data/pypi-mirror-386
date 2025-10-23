"""Smart Auto-Enhancement Infrastructure Adapter

SPEC-SAE-004: Smart Auto-Enhancement インフラストラクチャアダプター仕様
- 既存のA31評価、Claude分析サービスをSmart Auto-Enhancementで利用するためのアダプター
- ドメインプロトコルを既存実装にマッピング
- 必須要件チェックを最優先で実行
- Dependency Inversion Principle準拠
"""

# Guarded imports to avoid PLC0415 (function-scope imports) and allow optional DI wiring
try:
    from noveler.application.use_cases.smart_auto_enhancement_use_case import (
        SmartAutoEnhancementUseCase as _SmartAutoEnhancementUseCase,
    )
except Exception:  # pragma: no cover - optional at runtime
    _SmartAutoEnhancementUseCase = None
try:
    from noveler.infrastructure.di.repository_factory import (
        RepositoryFactory as _RepositoryFactory,
    )
except Exception:  # pragma: no cover - optional at runtime
    _RepositoryFactory = None
from noveler.domain.services.quality_requirements_auto_fixer import AutoFixerStatus, QualityRequirementsAutoFixer
from noveler.domain.services.quality_requirements_checker import QualityRequirementsChecker
from noveler.domain.services.smart_auto_enhancement_service import (
    A31Evaluator,
    BasicQualityChecker,
    ClaudeAnalyzer,
    SmartAutoEnhancementService,
)
from noveler.domain.value_objects.quality_score import QualityScore


class BasicQualityCheckerAdapter(BasicQualityChecker):
    """基本品質チェッカーアダプター

    必須要件（Must Pass）を最優先でチェックし、
    不合格の場合は即座に修正指示を返す
    """

    def __init__(self, project_name: str = "default", auto_fix_enabled: bool = True) -> None:
        self.requirements_checker = QualityRequirementsChecker(project_name)
        self.auto_fixer = QualityRequirementsAutoFixer(project_name) if auto_fix_enabled else None
        self.project_name = project_name

    def check_quality(self, episode_content: str) -> tuple[QualityScore, list[str]]:
        """基本品質チェックを実行

        必須要件優先アプローチ:
        1. 必須要件チェック（文字数、リズム）
        2. 不合格の場合は自動修正を試行（有効時）
        3. 合格の場合のみ構造的品質チェックを実行
        """
        # 1. 必須要件チェック
        requirements_result = self.requirements_checker.check_must_pass_requirements(episode_content)
        final_content = episode_content

        # 必須要件が不合格で自動修正が有効な場合は修正を試行
        if not requirements_result.all_passed and self.auto_fixer:
            return self._check_quality_with_auto_fix(episode_content)

        # 必須要件が不合格で自動修正が無効な場合は従来通り失敗を返す
        if not requirements_result.all_passed:
            failure_messages = []
            for issue in requirements_result.issues:
                failure_messages.append(f"【{issue.title}】")
                failure_messages.append(issue.description)
                failure_messages.append(issue.fix_instruction)
                failure_messages.append("")  # 空行

            return QualityScore(0), failure_messages

        # 2. 必須要件が合格の場合のみ構造的品質チェックを実行
        additional_score = self._calculate_structural_quality_bonus(final_content)
        additional_issues = self._detect_minor_structural_issues(final_content)

        # 基本合格スコア70 + 構造的品質ボーナス
        final_score = min(100, 70 + additional_score)

        return QualityScore(int(final_score)), additional_issues

    def _check_quality_with_auto_fix(self, episode_content: str) -> tuple[QualityScore, list[str]]:
        """自動修正機能付き品質チェック

        Args:
            episode_content: チェック対象コンテンツ

        Returns:
            tuple[QualityScore, list[str]]: スコアとメッセージリスト
        """
        # 自動修正実行
        fix_result = self.auto_fixer.auto_fix_requirements(episode_content)

        # 修正結果サマリを生成
        fix_summary = self.auto_fixer.get_fix_summary(fix_result)

        messages = [
            "🔧 自動修正実行結果:",
            "",
            fix_summary,
            "",
        ]

        # 修正成功の場合
        if fix_result.status == AutoFixerStatus.COMPLETED_SUCCESS:
            # 修正後コンテンツで構造的品質チェックを実行
            additional_score = self._calculate_structural_quality_bonus(fix_result.final_content)
            additional_issues = self._detect_minor_structural_issues(fix_result.final_content)

            messages.extend([
                "✅ 必須要件修正成功",
                f"📝 修正後文字数: {len(fix_result.final_content)}文字",
                f"🎯 最終スコア: {70 + additional_score}点",
            ])

            if additional_issues:
                messages.extend(["", "追加チェック項目:", *additional_issues])

            final_score = min(100, 70 + additional_score)
            return QualityScore(int(final_score)), messages

        # 修正失敗の場合
        messages.extend([
            "❌ 自動修正失敗",
            "",
            "手動修正が必要な項目:",
        ])

        # 最終チェック結果の問題を追加
        for issue in fix_result.final_check_result.issues:
            messages.extend([
                f"【{issue.title}】",
                issue.description,
                issue.fix_instruction,
                "",
            ])

        return QualityScore(0), messages

    def _calculate_structural_quality_bonus(self, content: str) -> int:
        """構造的品質ボーナススコア計算

        必須要件合格後の追加品質評価:
        - 基本的な文章構造
        - 明らかなエラーの有無
        - 段落構造の適切性
        """
        bonus_score = 0

        # 1. 基本的な文章構造チェック
        if self._has_basic_structure(content):
            bonus_score += 10

        # 2. 明らかな文章エラーのチェック
        if not self._has_obvious_errors(content):
            bonus_score += 10

        # 3. 段落構造の基本チェック
        if self._has_proper_paragraphs(content):
            bonus_score += 10

        return min(30, bonus_score)  # 最大30点のボーナス

    def _detect_minor_structural_issues(self, content: str) -> list[str]:
        """軽微な構造的問題の検出

        必須要件合格後の追加チェック項目
        """
        issues = []

        # 明らかな文章エラー（軽微）
        if "。。" in content:
            issues.append("句点の重複があります")

        if "、、" in content:
            issues.append("読点の重複があります")

        if "？？" in content:
            issues.append("疑問符の重複があります")

        if "！！" in content:
            issues.append("感嘆符の重複があります")

        # 明らかに不自然な改行
        if content.count("\n\n\n") > 2:
            issues.append("過度な空行があります")

        return issues

    def _has_basic_structure(self, content: str) -> bool:
        """基本的な文章構造の有無"""
        # 文の開始と終了の基本パターン
        sentences = content.split("。")
        if len(sentences) < 3:
            return False

        # 基本的な文字種の存在
        has_hiragana = any("あ" <= char <= "ん" for char in content)
        has_punctuation = "。" in content and "、" in content

        return has_hiragana and has_punctuation

    def _has_obvious_errors(self, content: str) -> bool:
        """明らかな文章エラーの有無"""
        # 重複記号パターン
        error_patterns = ["。。", "、、", "？？", "！！", "（（", "））"]
        return any(pattern in content for pattern in error_patterns)

    def _has_proper_paragraphs(self, content: str) -> bool:
        """適切な段落構造の有無"""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        # 最低限の段落数
        if len(paragraphs) < 2:
            return False

        # 各段落の最小文字数
        return all(len(paragraph) >= 50 for paragraph in paragraphs)


class A31EvaluatorAdapter(A31Evaluator):
    """A31評価器アダプター

    既存のA31Complete評価システムをSmart Auto-Enhancement用にアダプト
    """

    def __init__(self) -> None:
        self._use_case = None  # 実際の実装では依存注入

    async def evaluate(
        self, _project_name: str, _episode_number: int, _episode_content: str
    ) -> tuple[QualityScore, dict]:
        """A31評価を実行"""
        try:
            # 既存のA31CompleteCheckUseCaseを呼び出し（実装時に依存注入）
            # 現在はモック結果を返す
            mock_score = 75.0
            mock_results = {
                "total_items": 68,
                "passed_items": 51,
                "failed_items": 17,
                "auto_fixes_applied": 5,
                "evaluation_details": {},
            }
            return QualityScore(int(mock_score)), mock_results
        except Exception as e:
            msg = f"A31評価エラー: {e!s}"
            raise RuntimeError(msg) from e


class ClaudeAnalyzerAdapter(ClaudeAnalyzer):
    """Claude分析器アダプター

    既存のClaude分析システムをSmart Auto-Enhancement用にアダプト
    """

    def __init__(self) -> None:
        self._analyzer = None  # 実際の実装では依存注入

    async def analyze(
        self, _project_name: str, _episode_number: int, _a31_results: dict
    ) -> tuple[QualityScore, dict]:
        """Claude分析を実行"""
        try:
            # 実装時にはInSessionClaudeAnalyzer等を注入
            # 現在は詳細なモック結果を返す
            mock_score = 82.0
            mock_results = {
                "claude_analysis_applied": True,
                "improvements_count": 12,
                "enhanced_items": [
                    {
                        "category": "文章構造",
                        "original": "彼は学校に行った。そして友達に会った。",
                        "enhanced": "彼は学校に向かい、校門で待っていた友達と再会を果たした。",
                        "improvement_type": "表現豊富化",
                        "score_impact": "+3",
                    },
                    {
                        "category": "キャラクター描写",
                        "original": "彼女は怒っていた。",
                        "enhanced": "彼女の眉間には深い皺が刻まれ、拳を固く握りしめていた。",
                        "improvement_type": "感情表現強化",
                        "score_impact": "+5",
                    },
                    {
                        "category": "場面転換",
                        "original": "次の日になった。",
                        "enhanced": "翌朝、陽光が窓から差し込む中で—",
                        "improvement_type": "シーン遷移改善",
                        "score_impact": "+2",
                    },
                ],
                "execution_time_ms": 2500.0,
                "analysis_details": {
                    "narrative_flow": {
                        "score": 85,
                        "feedback": "物語の流れは良好。ただし場面転換でより自然な繋がりを意識すると効果的",
                    },
                    "character_development": {
                        "score": 78,
                        "feedback": "キャラクターの内面描写に改善余地あり。感情の変化をより詳細に描写することを推奨",
                    },
                    "dialogue_quality": {
                        "score": 83,
                        "feedback": "対話は自然で読みやすい。キャラクターごとの話し方の違いがよく表現されている",
                    },
                    "world_building": {
                        "score": 80,
                        "feedback": "世界観の設定は一貫している。背景の詳細描写を増やすとより没入感が向上",
                    },
                },
                "suggestions": [
                    "感情表現により具体的な身体的反応を加える",
                    "場面転換時の時間経過をより自然に表現する",
                    "キャラクターの内面の葛藤をもう少し深く掘り下げる",
                    "環境描写で五感を活用した表現を増やす",
                ],
            }
            return QualityScore(int(mock_score)), mock_results
        except Exception as e:
            msg = f"Claude分析エラー: {e!s}"
            raise RuntimeError(msg) from e


class SmartAutoEnhancementServiceFactory:
    """Smart Auto-Enhancement サービスファクトリー

    依存関係を適切に注入してSmartAutoEnhancementServiceを構築
    """

    @staticmethod
    def create_service(project_name: str = "default", auto_fix_enabled: bool = True) -> "SmartAutoEnhancementService":
        """Smart Auto-Enhancement サービスを作成

        Args:
            project_name: プロジェクト名（設定読み込み用）
            auto_fix_enabled: 自動修正機能有効化フラグ
        """
        # アダプターを作成（プロジェクト名と自動修正フラグを渡す）
        basic_checker = BasicQualityCheckerAdapter(project_name, auto_fix_enabled)
        a31_evaluator = A31EvaluatorAdapter()
        claude_analyzer = ClaudeAnalyzerAdapter()

        # サービスを構築
        return SmartAutoEnhancementService(
            basic_checker=basic_checker, a31_evaluator=a31_evaluator, claude_analyzer=claude_analyzer
        )

    @staticmethod
    def create_use_case() -> object:
        """Smart Auto-Enhancement ユースケースを作成"""
        if _SmartAutoEnhancementUseCase is None or _RepositoryFactory is None:
            msg = (
                "SmartAutoEnhancementUseCase/RepositoryFactory is unavailable. "
                "Ensure application.use_cases and infrastructure.di are importable."
            )
            raise ImportError(msg)

        # RepositoryFactoryを初期化してlogger_serviceとunit_of_workを取得
        repository_factory = _RepositoryFactory()
        logger_service = repository_factory.get_logger_service()
        unit_of_work = repository_factory.get_unit_of_work()

        # SmartAutoEnhancementServiceを適切に作成
        enhancement_service = SmartAutoEnhancementServiceFactory.create_service()

        # ユースケースを構築
        return _SmartAutoEnhancementUseCase(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
            enhancement_service=enhancement_service,
        )
