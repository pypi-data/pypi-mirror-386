---
spec_id: SPEC-WORKFLOW-003
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: WORKFLOW
sources: [E2E]
tags: [workflow]
---
# SPEC-WORKFLOW-003: 拡張コーディング規約自動化システム

## 仕様書情報

- **仕様書ID**: SPEC-WORKFLOW-003
- **タイトル**: 拡張コーディング規約自動化システム
- **作成日**: 2024-07-26
- **最終更新**: 2024-07-26
- **ステータス**: 設計中
- **優先度**: 高

## 1. 概要

> 注記: 本仕様に登場する `scripts/tools/...` は旧構成の例です。現行は `src/noveler/tools/` 配下（例: `unified_syntax_fixer.py`, `check_import_style.py` 等）を中心に運用します。コマンド例は概念説明として読み替えてください。

### 1.1 目的
既存のコーディング規約チェックツール（`check_tdd_ddd_compliance.py`）を拡張し、より実用的で学習支援機能を持った統合自動化システムを構築する。

### 1.2 背景
- 既存ツールは基本的なDDD層分離チェックを実装済み
- Ruff自動修正では対応できない高度なプロジェクト固有チェックが必要
- 開発者の学習支援とチーム全体の品質向上が求められる

### 1.3 スコープ
- 既存機能と重複しない新機能の開発
- 学習支援・ガイダンス機能の実装
- 統合レポート・ダッシュボード機能
- 段階的適用システムの構築

## 2. 要件定義

### 2.1 機能要件

#### 2.1.1 既存機能の拡張（非重複）

**A. ビジネスロジック純粋性の詳細チェック**
- 既存: 技術的インポートの検出
- 新規: ビジネスロジック内の技術的操作検出

```python
# 検出対象例
# ドメインエンティティ内での技術的操作
class Episode:
    def save_to_file(self):  # ❌ 技術的関心事の混入
        with open("episode.json", "w") as f:
            json.dump(self.to_dict(), f)

    def fetch_from_api(self):  # ❌ 外部システム依存
        response = requests.get("/api/episodes")
        return response.json()
```

**B. TDDサイクル遵守チェック**
- 既存: テストファイル存在チェック
- 新規: Red-Green-Refactorサイクルの検証

**C. アーキテクチャ整合性チェック**
- 既存: 基本的な層間依存チェック
- 新規: 依存関係の詳細分析と可視化

#### 2.1.2 学習支援機能

**A. 段階的学習パス**
```python
@dataclass
class LearningLevel:
    name: str
    required_skills: list[str]
    recommended_duration: str
    success_criteria: list[str]

LEARNING_LEVELS = [
    LearningLevel(
        name="初心者",
        required_skills=["基本命名規則", "型ヒント基礎", "インポート規則"],
        recommended_duration="1週間",
        success_criteria=["ruff check通過", "基本テスト作成"]
    ),
    LearningLevel(
        name="中級者",
        required_skills=["Any型除去", "DDD層分離", "例外処理"],
        recommended_duration="1ヶ月",
        success_criteria=["Domain層純粋性確保", "ユースケース実装"]
    ),
    LearningLevel(
        name="上級者",
        required_skills=["アーキテクチャ設計", "リファクタリング戦略"],
        recommended_duration="3ヶ月",
        success_criteria=["チーム指導", "設計判断"]
    )
]
```

**B. 対話式学習ツール**
```python
class InteractiveLearningSystem:
    def start_quiz(self, level: str) -> Quiz:
        """レベル別クイズ開始"""

    def provide_immediate_feedback(self, answer: str) -> Feedback:
        """即座のフィードバック提供"""

    def suggest_next_steps(self, progress: LearningProgress) -> list[str]:
        """次のステップ提案"""
```

#### 2.1.3 統合レポート・ダッシュボード

**A. 包括的品質レポート**
```python
@dataclass
class ComprehensiveQualityReport:
    tdd_compliance: float
    ddd_compliance: float
    type_safety_score: float
    architecture_health: float
    team_learning_progress: dict[str, LearningProgress]
    improvement_suggestions: list[ImprovementSuggestion]
    roi_metrics: ROIMetrics
```

**B. 品質メトリクスダッシュボード**
- 品質トレンドの可視化
- チーム別/個人別進捗
- 改善効果の定量測定

#### 2.1.4 段階的適用システム

**A. レベル別規約適用**
```python
class GradualAdoptionSystem:
    def get_applicable_rules(self, team_level: str) -> list[Rule]:
        """チームレベルに応じた適用規則"""

    def create_migration_plan(self, current_state: CodebaseState) -> MigrationPlan:
        """段階的移行計画作成"""

    def track_adoption_progress(self) -> AdoptionProgress:
        """導入進捗の追跡"""
```

### 2.2 非機能要件

#### 2.2.1 性能要件
- 大規模コードベース（1000+ファイル）での実行時間: 5分以内
- リアルタイムフィードバック: 1秒以内
- メモリ使用量: 512MB以内

#### 2.2.2 拡張性要件
- 新規チェックルールの動的追加
- プラグインシステムによる機能拡張
- 多言語対応（現在はPythonのみ）

#### 2.2.3 保守性要件
- 既存ツールとの互換性維持
- 設定ファイルによるカスタマイズ
- ログ・デバッグ機能

## 3. システム設計

### 3.1 アーキテクチャ概要

```
Enhanced Coding Standards Automation System
├── Core Engine
│   ├── ExistingToolsIntegrator     # 既存ツール統合
│   ├── AdvancedChecker            # 高度チェック機能
│   └── ReportAggregator           # レポート統合
├── Learning Support
│   ├── InteractiveLearningSystem  # 対話式学習
│   ├── ProgressTracker           # 進捗追跡
│   └── FeedbackEngine            # フィードバック提供
├── Dashboard & Reporting
│   ├── QualityDashboard          # 品質ダッシュボード
│   ├── MetricsCalculator         # メトリクス計算
│   └── VisualizationEngine       # 可視化エンジン
└── Configuration & Extension
    ├── GradualAdoptionManager    # 段階的適用管理
    ├── PluginSystem             # プラグインシステム
    └── ConfigurationManager     # 設定管理
```

### 3.2 主要コンポーネント設計

#### 3.2.1 EnhancedComplianceChecker

```python
class EnhancedComplianceChecker:
    """拡張コンプライアンスチェッカー（メインクラス）"""

    def __init__(self, config: CheckerConfig):
        # 既存ツール統合
        self.tdd_ddd_checker = TDDDDDComplianceChecker()
        self.import_checker = ImportStyleChecker()
        self.ruff_runner = RuffRunner()

        # 新規機能
        self.business_logic_checker = BusinessLogicPurityChecker()
        self.tdd_cycle_checker = TDDCycleChecker()
        self.learning_system = InteractiveLearningSystem()

    def comprehensive_check(self) -> ComprehensiveReport:
        """包括的チェック実行"""

        # Phase 1: 既存ツール実行
        existing_results = self._run_existing_tools()

        # Phase 2: 新規高度チェック
        advanced_results = self._run_advanced_checks()

        # Phase 3: 学習支援・ガイダンス
        learning_guidance = self._provide_learning_guidance()

        # Phase 4: 統合レポート生成
        return self._generate_comprehensive_report(
            existing_results, advanced_results, learning_guidance
        )
```

#### 3.2.2 BusinessLogicPurityChecker

```python
class BusinessLogicPurityChecker:
    """ビジネスロジック純粋性チェッカー"""

    def check_entity_purity(self, entity_files: list[Path]) -> list[Violation]:
        """エンティティの純粋性チェック"""
        violations = []

        for entity_file in entity_files:
            content = entity_file.read_text()

            # 技術的操作パターンの検出
            technical_patterns = [
                r"requests\.(get|post|put|delete)",  # HTTP通信
                r"sqlite3\.connect",                 # DB接続
                r"open\s*\(",                       # ファイルI/O
                r"json\.(loads|dumps)",             # JSON操作
                r"yaml\.(load|dump)",               # YAML操作
                r"logging\.(info|error|debug)",     # ログ出力
            ]

            for pattern in technical_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    violations.append(Violation(
                        file=entity_file,
                        line=self._get_line_number(content, match.start()),
                        type="TECHNICAL_CONCERN_IN_ENTITY",
                        message=f"エンティティに技術的関心事が混入: {match.group()}",
                        suggestion=self._suggest_fix(pattern)
                    ))

        return violations

    def _suggest_fix(self, pattern: str) -> str:
        """修正提案"""
        suggestions = {
            r"requests\.": "Infrastructure層でHTTPクライアントを実装し、Repositoryパターンで注入",
            r"sqlite3\.": "Infrastructure層でDBアクセス層を作成",
            r"open\s*\(": "Infrastructure層でFileRepositoryを実装",
            r"json\.": "Infrastructure層でSerializationServiceを作成",
            r"yaml\.": "Infrastructure層でConfigurationRepositoryを実装",
            r"logging\.": "Infrastructure層でLoggingServiceを注入"
        }

        for key, suggestion in suggestions.items():
            if re.search(key, pattern):
                return suggestion

        return "Infrastructure層への分離を検討してください"
```

#### 3.2.3 TDDCycleChecker

```python
class TDDCycleChecker:
    """TDDサイクル遵守チェッカー"""

    def check_test_first_compliance(self, git_repo: Path) -> TDDComplianceReport:
        """テストファースト遵守チェック"""

        # Gitログ分析
        commits = self._analyze_git_commits(git_repo)

        violations = []
        for commit in commits:
            # テストファイルと実装ファイルのコミット順序確認
            test_files = [f for f in commit.files if f.startswith("test_")]
            impl_files = [f for f in commit.files if not f.startswith("test_") and f.endswith(".py")]

            if impl_files and not test_files:
                violations.append(TDDViolation(
                    commit=commit.hash,
                    type="IMPLEMENTATION_WITHOUT_TEST",
                    message="テストなしで実装をコミット",
                    files=impl_files
                ))

        return TDDComplianceReport(
            total_commits=len(commits),
            compliant_commits=len(commits) - len(violations),
            violations=violations,
            compliance_rate=1.0 - (len(violations) / len(commits))
        )
```

#### 3.2.4 InteractiveLearningSystem

```python
class InteractiveLearningSystem:
    """対話式学習システム"""

    def start_personalized_learning(self, user_level: str, focus_areas: list[str]) -> LearningSession:
        """個人化学習セッション開始"""

        session = LearningSession(
            user_level=user_level,
            focus_areas=focus_areas,
            start_time=datetime.now()
        )

        # レベル別カリキュラム作成
        curriculum = self._create_curriculum(user_level, focus_areas)
        session.curriculum = curriculum

        return session

    def provide_contextual_feedback(self, code_violation: Violation) -> LearningFeedback:
        """文脈に応じたフィードバック提供"""

        feedback = LearningFeedback()

        # 違反の種類に応じた教育コンテンツ
        if violation.type == "TECHNICAL_CONCERN_IN_ENTITY":
            feedback.explanation = "ドメインエンティティは純粋なビジネスロジックのみを持つべきです"
            feedback.example_before = violation.code_snippet
            feedback.example_after = self._generate_refactored_example(violation)
            feedback.learning_resources = [
                "DDD基礎ガイド（2.1節）",
                "エンティティ設計パターン動画",
                "実践演習: エンティティ分離"
            ]
            feedback.next_steps = [
                "Repository パターンの学習",
                "Infrastructure層の実装練習",
                "類似違反の修正作業"
            ]

        return feedback
```

### 3.3 データモデル

#### 3.3.1 主要エンティティ

```python
@dataclass
class ComprehensiveReport:
    """統合品質レポート"""
    timestamp: datetime
    project_info: ProjectInfo
    existing_tool_results: ExistingToolResults
    advanced_check_results: AdvancedCheckResults
    learning_guidance: LearningGuidance
    improvement_plan: ImprovementPlan
    roi_metrics: ROIMetrics

@dataclass
class Violation:
    """品質違反"""
    file: Path
    line: int
    type: str
    severity: ViolationSeverity
    message: str
    suggestion: str
    learning_resources: list[str]

@dataclass
class LearningProgress:
    """学習進捗"""
    user_id: str
    current_level: str
    completed_modules: list[str]
    skill_scores: dict[str, float]
    next_recommendations: list[str]

@dataclass
class ROIMetrics:
    """投資対効果メトリクス"""
    bug_reduction_rate: float
    development_speed_improvement: float
    code_review_efficiency: float
    team_onboarding_time_reduction: float
    total_time_saved_hours: float
    cost_benefit_ratio: float
```

## 4. 実装計画

### 4.1 開発フェーズ

#### Phase 1: 基盤整備（1週間）
- [ ] 既存ツール統合フレームワーク
- [ ] 基本的な設定管理システム
- [ ] 簡単な統合レポート機能

#### Phase 2: 高度チェック機能（2週間）
- [ ] BusinessLogicPurityChecker実装
- [ ] TDDCycleChecker実装
- [ ] アーキテクチャ整合性チェック

#### Phase 3: 学習支援システム（2週間）
- [ ] InteractiveLearningSystem実装
- [ ] 段階的学習パス
- [ ] フィードバックエンジン

#### Phase 4: ダッシュボード・可視化（1週間）
- [ ] QualityDashboard実装
- [ ] メトリクス計算・可視化
- [ ] ROI測定システム

#### Phase 5: 統合・テスト（1週間）
- [ ] 全機能統合テスト
- [ ] パフォーマンス最適化
- [ ] ドキュメント整備

### 4.2 技術仕様

#### 4.2.1 開発環境
- Python 3.11+
- 依存関係: `ruff`, `mypy`, `git`, `pyyaml`, `matplotlib`（可視化用）
- テストフレームワーク: `pytest`

#### 4.2.2 ファイル構成
```
scripts/tools/enhanced_coding_standards/
├── __init__.py
├── core/
│   ├── enhanced_compliance_checker.py
│   ├── business_logic_checker.py
│   ├── tdd_cycle_checker.py
│   └── integration_manager.py
├── learning/
│   ├── interactive_learning_system.py
│   ├── progress_tracker.py
│   └── feedback_engine.py
├── dashboard/
│   ├── quality_dashboard.py
│   ├── metrics_calculator.py
│   └── visualization_engine.py
├── config/
│   ├── checker_config.py
│   ├── learning_config.py
│   └── dashboard_config.py
└── utils/
    ├── git_analyzer.py
    ├── ast_analyzer.py
    └── report_generator.py
```

### 4.3 設定ファイル例

```yaml
# enhanced_coding_standards_config.yaml
checker:
  existing_tools:
    tdd_ddd_compliance: true
    import_style: true
    ruff_check: true

  advanced_checks:
    business_logic_purity: true
    tdd_cycle_compliance: true
    architecture_consistency: true

  severity_levels:
    TECHNICAL_CONCERN_IN_ENTITY: error
    IMPLEMENTATION_WITHOUT_TEST: warning
    LAYER_DEPENDENCY_VIOLATION: error

learning:
  personalization: true
  interactive_mode: true
  progress_tracking: true

  levels:
    beginner:
      duration_weeks: 1
      required_skills: ["naming", "type_hints", "imports"]
      success_threshold: 0.8

    intermediate:
      duration_weeks: 4
      required_skills: ["any_removal", "ddd_layers", "exceptions"]
      success_threshold: 0.85

    advanced:
      duration_weeks: 12
      required_skills: ["architecture", "refactoring", "mentoring"]
      success_threshold: 0.9

dashboard:
  metrics:
    - error_reduction_rate
    - type_safety_score
    - architecture_health
    - team_learning_progress

  visualization:
    trend_charts: true
    team_comparison: true
    individual_progress: true

  export_formats: ["html", "pdf", "json"]
```

## 5. 使用例

### 5.1 基本的な使用方法

```bash
# 包括的チェック実行
python scripts/tools/enhanced_coding_standards/main.py check --comprehensive

# 学習モード開始
python scripts/tools/enhanced_coding_standards/main.py learn --level beginner --interactive

# ダッシュボード起動（Web UI）
python scripts/tools/enhanced_coding_standards/main.py dashboard --port 8080

# レポート生成
python scripts/tools/enhanced_coding_standards/main.py report --format html --output quality_report.html
```

### 5.2 統合ワークフロー例

```bash
# 開発者の日常ワークフロー
1. コード修正
2. enhanced_coding_standards check --quick  # クイックチェック
3. 学習ガイダンスに従って修正
4. enhanced_coding_standards check --comprehensive  # 包括チェック
5. コミット前最終確認
6. コミット・プッシュ

# チームリーダーの週次レビュー
1. enhanced_coding_standards dashboard  # ダッシュボードで全体把握
2. enhanced_coding_standards report --team-summary  # チーム要約レポート
3. 個別メンバーの学習進捗確認
4. 次週の改善計画策定
```

## 6. 成功指標

### 6.1 定量的指標
- コードベース品質スコア: 85%以上
- チーム学習完了率: 90%以上
- 開発効率向上: 20%以上
- バグ削減率: 30%以上

### 6.2 定性的指標
- 開発者満足度の向上
- コードレビュー品質の向上
- 新人の学習速度向上
- チーム全体のスキル底上げ

## 7. リスク・課題

### 7.1 技術的リスク
- 既存ツールとの統合複雑性
- 大規模コードベースでの性能問題
- Git解析の精度・信頼性

### 7.2 運用リスク
- 学習システムの継続的メンテナンス
- チームの受け入れ・定着
- 設定・カスタマイズの複雑性

### 7.3 対策
- 段階的導入による影響最小化
- 十分なテスト・ドキュメント整備
- ユーザーフィードバックの継続的収集

## 8. 今後の拡張計画

### 8.1 短期（3ヶ月以内）
- 他言語対応（TypeScript, Go等）
- CI/CD統合
- Slack/Teams通知連携

### 8.2 中期（6ヶ月以内）
- 機械学習による改善提案
- チーム間ベンチマーク機能
- 品質予測システム

### 8.3 長期（1年以内）
- 業界標準メトリクスとの比較
- 外部ツール・サービス連携
- エンタープライズ機能拡充

## 関連資料

- [CODING_STANDARDS.md] - 基本コーディング規約
- [scripts/tools/check_tdd_ddd_compliance.py] - 既存チェックツール
- [TDD+DDD準拠チェックリスト] - 開発プロセス
- [品質管理システムガイド] - 品質管理方針
