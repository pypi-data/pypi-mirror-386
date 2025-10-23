# Claude Code品質作業指示書

**最終更新**: 2025年8月30日
**対象**: リファクタリング・不具合修正・新機能実装時の品質保証指示

```yaml
# B30品質作業指示書メタデータ
metadata:
  document_name: "B30_Claude_Code品質作業指示書"
  version: "2.0.0"
  purpose: "Claude Code品質保証・リファクタリング作業の構造化管理"
  last_updated: "2025年8月30日"
  target_scope: "リファクタリング・不具合修正・新機能実装"
  claude_code_optimized: true
```

```yaml
# 基本方針（必須遵守）
mandatory_policies:
  unified_import_management:
    rule: "必ずnovelerプレフィックスを使用"
    priority: "critical"
    correct_examples:
      - "from noveler.domain.entities.episode import Episode"
      - "from noveler.domain.value_objects.episode_number import EpisodeNumber"
    forbidden_patterns:
      - pattern: "from .domain.entities.episode import Episode"
        reason: "相対インポート"
        severity: "critical"
      - pattern: "from domain.entities.episode import Episode"
        reason: "noveler なし"
        severity: "critical"

  shared_component_enforcement:
    rule: "shared_utilities から統一使用"
    priority: "critical"
    correct_usage:
      import: "from noveler.presentation.cli.shared_utilities import console"
      description: "Console統一インスタンス使用"
    forbidden_usage:
      import: "from rich.console import Console"
      instantiation: "console = Console()"
      reason: "重複作成禁止"
      severity: "critical"

  tdd_ddd_process:
    rules:
      - requirement: "新機能は必ず仕様書作成から開始"
        priority: "critical"
        format: "SPEC-XXX-YYY形式"
      - requirement: "テストに @pytest.mark.spec(\"SPEC-XXX-YYY\") を付与"
        priority: "critical"
        purpose: "仕様書との連携"
      - requirement: "ドメイン → アプリケーション → インフラの依存方向を厳守"
        priority: "critical"
        purpose: "DDD アーキテクチャ準拠"
```

---

```yaml
# 禁止パターンと修正指示
prohibited_patterns:
  console_duplication:
    description: "Console重複作成の禁止"
    priority: "critical"
    category: "shared_component_violation"

    correct_pattern:
      import: "from noveler.presentation.cli.shared_utilities import console"
      usage: "console.print(\"メッセージ\")"
      reason: "統一インスタンス使用"

    prohibited_pattern:
      import: "from rich.console import Console"
      instantiation: "console = Console()"
      usage: "console.print(\"メッセージ\")"
      reason: "重複作成禁止"
      severity: "critical"

  error_handling_violation:
    description: "エラーハンドリング統一違反"
    priority: "high"
    category: "error_management"

    correct_pattern:
      import: "from noveler.presentation.cli.shared_utilities import handle_error"
      structure: |
        try:
            process()
        except Exception as e:
            handle_error(e, "process_name")
      reason: "統一エラーハンドリング使用"

    prohibited_pattern:
      structure: |
        try:
            process()
        except Exception as e:
            print(f"Error: {e}")
      reason: "個別エラー処理禁止"
      severity: "high"

  path_hardcoding:
    description: "パス操作ハードコーディング"
    priority: "critical"
    category: "path_management"

    correct_pattern:
      import: "from noveler.presentation.cli.shared_utilities import get_common_path_service"
      usage: |
        path_service = get_common_path_service(project_root)
        manuscript_dir = path_service.get_manuscript_dir()
      reason: "CommonPathService統一使用"

    prohibited_pattern:
      usage: "manuscript_dir = project_root / \"40_原稿\""
      reason: "ハードコーディング禁止"
      severity: "critical"

  implementation_comments:
    description: "実装コメントの使用"
    priority: "medium"
    category: "code_quality"

    correct_pattern:
      type: "docstring"
      example: |
        def calculate_total():
            """値の合計を計算"""
            return sum(values)
      reason: "自己文書化コード推奨"

    prohibited_pattern:
      type: "implementation_comment"
      example: |
        def calculate_total():
            # 合計を計算  ← このようなコメントは禁止
            return sum(values)
      reason: "実装コメント禁止"
      severity: "medium"
```

---

```yaml
# 作業チェックリスト - 6段階ワークフロー
workflow_checklist:
  metadata:
    total_stages: 6
    total_items: 59
    critical_items: 54
    completion_tracking: true

  stage_1_pre_implementation:
    stage_name: "実装前準備"
    stage_priority: 1
    total_items: 8
    critical_items: 6
    stage_purpose: "既存システム調査・重複回避・仕様書準備"

    items:
      - id: "B30-PRE-001"
        description: "既存コンポーネント利用可能性確認"
        status: false
        required: true
        priority: "critical"
        category: "duplication_prevention"
        automation_level: "semi_automated"
        commands:
          - "project-tools component search --keyword \"機能名\""
          - "project-tools component list"
        validation_criteria:
          - "既存コンポーネント調査完了"
          - "重複実装回避確認"

      - id: "B30-PRE-002"
        description: "共通コンポーネント検索実行"
        status: false
        required: true
        priority: "high"
        category: "preparation"
        automation_level: "fully_automated"
        commands:
          - "project-tools component search --keyword \"機能名\""
        validation_criteria:
          - "検索結果確認完了"

      - id: "B30-PRE-003"
        description: "仕様書作成（SPEC-XXX-YYY形式）"
        status: false
        required: true
        priority: "critical"
        category: "tdd_preparation"
        automation_level: "manual_only"
        format: "SPEC-XXX-YYY"
        output_files:
          - "$PROJECT_ROOT/specs/functional/SPEC-XXX-YYY.md"
        validation_criteria:
          - "仕様書作成完了"
          - "SPEC形式準拠確認"

  stage_2_implementation_phase:
    stage_name: "実装中品質管理"
    stage_priority: 2
    total_items: 12
    critical_items: 10
    stage_purpose: "統合パターン適用・継続品質チェック"

    items:
      - id: "B30-IMP-001"
        description: "スクリプトプレフィックス統一（from noveler.）"
        status: false
        required: true
        priority: "critical"
        category: "unified_import_management"
        automation_level: "semi_automated"
        reference_guides:
          - "$GUIDE_ROOT/CLAUDE.md"
        commands:
          - "python src/noveler/infrastructure/quality_gates/architecture_linter.py --project-root . --fail-on-error"
        validation_criteria:
          - "インポート統一完了"
          - "novelerプレフィックス100%適用"

      - id: "B30-IMP-002"
        description: "共通コンポーネント強制利用パターン遵守"
        status: false
        required: true
        priority: "critical"
        category: "shared_utilities"
        automation_level: "semi_automated"
        commands:
          - "python src/noveler/infrastructure/quality_gates/hardcoding_detector.py --project-root . --fail-on-critical"
        validation_criteria:
          - "共通コンポーネント使用率95%以上"
          - "Console重複作成0件"

      - id: "B30-IMP-003"
        description: "テスト作成（@pytest.mark.spec付与）"
        status: false
        required: true
        priority: "critical"
        category: "tdd_implementation"
        automation_level: "manual_verification"
        test_marker: "@pytest.mark.spec(\"SPEC-XXX-YYY\")"
        validation_criteria:
          - "仕様書連携テスト作成完了"
          - "テストマーカー付与確認"

      - id: "B30-IMP-004"
        description: "英語命名規則遵守（関数名・メソッド名）"
        status: false
        required: true
        priority: "high"
        category: "naming_convention"
        automation_level: "semi_automated"
        naming_rules:
          functions: "snake_case (english)"
          methods: "snake_case (english)"
          classes: "PascalCase (english)"
        validation_criteria:
          - "英語命名規則100%適用"
          - "日本語変数名・関数名0件"

  stage_3_post_implementation:
    stage_name: "実装後検証"
    stage_priority: 3
    total_items: 10
    critical_items: 8
    stage_purpose: "品質ゲート通過・テスト確認"

    items:
      - id: "B30-POST-001"
        description: "品質ゲート通過確認"
        status: false
        required: true
        priority: "critical"
        category: "quality_gate"
        automation_level: "fully_automated"
        commands:
          - "python scripts/tools/quality_gate_check.py"
          - "project-tools quality verify"
        validation_criteria:
          - "全品質ゲート通過確認"
          - "品質スコア基準クリア"

      - id: "B30-POST-002"
        description: "単体テスト実行・パス確認"
        status: false
        required: true
        priority: "critical"
        category: "testing"
        automation_level: "fully_automated"
        commands:
          - "noveler test run --unit --fast"
          - "./test_commands.sh test-fast"
        validation_criteria:
          - "全単体テストパス確認"
          - "カバレッジ基準達成"

      - id: "B30-POST-003"
        description: "重複パターン検知実行・解決"
        status: false
        required: true
        priority: "high"
        category: "refactoring"
        automation_level: "semi_automated"
        commands:
          - "project-tools refactor detect-duplicates"
          - "project-tools refactor auto-fix --dry-run"
        validation_criteria:
          - "重複パターン検知完了"
          - "重複解決確認"

      - id: "B30-POST-004"
        description: "リファクタリング完了確認"
        status: false
        required: true
        priority: "high"
        category: "refactoring_completion"
        automation_level: "manual_verification"
        validation_criteria:
          - "コード品質基準達成"
          - "保守性向上確認"

# 進捗集計情報
validation_summary:
  total_items: 59
  completed_items: 0
  required_items: 54
  required_completed: 0
  completion_rate: 0.0
  required_completion_rate: 0.0

  stage_summary:
    - stage_name: "実装前準備"
      total: 8
      completed: 0
      critical: 6
      stage_completion_rate: 0.0
    - stage_name: "実装中品質管理"
      total: 12
      completed: 0
      critical: 10
      stage_completion_rate: 0.0
    - stage_name: "実装後検証"
      total: 10
      completed: 0
      critical: 8
      stage_completion_rate: 0.0
```

---

```yaml
# 必須実行コマンド統合管理
automation_commands:
  stage_commands:
    pre_implementation:
      stage_name: "実装前準備"
      purpose: "品質状態確認・既存コンポーネント調査"
      commands:
        - command: "project-tools quality check --include-common-components"
          purpose: "現在の品質状態確認"
          automation_level: "fully_automated"
          expected_output: "品質状態レポート"

        - command: "project-tools component list"
          purpose: "既存コンポーネント一覧取得"
          automation_level: "fully_automated"
          expected_output: "コンポーネント一覧"

        - command: "project-tools component search --keyword \"対象機能\""
          purpose: "対象機能関連コンポーネント検索"
          automation_level: "parametric"
          parameters:
            keyword: "対象機能名を指定"
          expected_output: "関連コンポーネント検索結果"

    implementation_verification:
      stage_name: "実装中検証"
      purpose: "継続的品質チェック・重複検知"
      commands:
        - command: "project-tools quality check --include-common-components"
          purpose: "継続的品質チェック"
          automation_level: "fully_automated"
          frequency: "実装中随時"
          expected_output: "品質状態更新レポート"

        - command: "pre-commit run --all-files"
          purpose: "統合品質チェック＆自動修正実行"
          automation_level: "fully_automated"
          trigger: "コミット前"
          expected_output: "品質ゲート結果 + 自動修正レポート"
          components:
            - "unified-auto-syntax-fix: 統合構文エラー自動修正"
            - "b30-quality-auto-fix: B30統合品質チェック＆自動修正"
          auto_fix_enabled: true

        - command: "project-tools refactor detect-duplicates"
          purpose: "重複パターン検知"
          automation_level: "fully_automated"
          expected_output: "重複パターン検知結果"

        - command: "project-tools refactor auto-fix --dry-run"
          purpose: "修正プレビュー実行"
          automation_level: "semi_automated"
          expected_output: "修正プレビュー結果"

    post_implementation:
      stage_name: "実装後確認"
      purpose: "最終品質確認・テスト実行"
      commands:
        - command: "noveler test run --unit --fast"
          purpose: "高速単体テスト実行"
          automation_level: "fully_automated"
          timeout: "5分以内"
          expected_output: "テスト結果レポート"

        - command: "./test_commands.sh test-fast"
          purpose: "統合高速テスト実行"
          automation_level: "fully_automated"
          timeout: "10分以内"
          expected_output: "統合テスト結果"

        - command: "python scripts/tools/quality_gate_check.py --level MODERATE"
          purpose: "段階的品質ゲート最終確認"
          automation_level: "fully_automated"
          expected_output: "品質ゲート通過結果（MODERATE準拠）"
          quality_levels:
            - "BASIC: 基本要件のみ"
            - "MODERATE: B30基本準拠（推奨）"
            - "STRICT: B30完全準拠"

        - command: "project-tools quality verify"
          purpose: "品質検証最終実行"
          automation_level: "fully_automated"
          expected_output: "最終品質検証結果"

  command_integration:
    batch_execution: true
    error_handling: "handle_error統一使用"
    logging: "共通ログ出力"
    progress_tracking: "段階的進捗管理"
```

---

## 8. MCP統合とトークン最適化

### 🌟 MCPサーバー統合の品質基準

2025年8月30日より、Claude Code MCP統合により品質チェック工程が大幅に効率化されました。

#### MCP統合による品質チェック高速化
```yaml
quality_optimization:
  token_reduction:
    before: "800-1200トークン（冗長な品質レポート）"
    after: "40-60トークン（JSON構造化データ）"
    improvement: "95%削減"

  response_speed:
    before: "3-5秒（テキスト解析）"
    after: "0.5-1秒（JSON処理）"
    improvement: "80%向上"

  accuracy:
    before: "70%（テキストベース判定）"
    after: "90%+（構造化データ判定）"
    improvement: "+20%精度向上"
```

### 🛠️ MCP対応品質チェック実装パターン

#### JSON出力対応品質ツール
```python
# 品質チェックツールのMCP対応例
class QualityChecker:
    def run_quality_check(self, args: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """MCP/CLI両対応の品質チェック"""
        result = self._execute_quality_analysis(args)

        # MCP統合時はJSON出力
        if args.get('format') == 'json' or self._is_mcp_context():
            return {
                "quality_status": {
                    "overall_score": result.overall_score,
                    "test_coverage": {"value": result.coverage, "status": result.coverage_status},
                    "code_quality": {"value": result.quality_score, "status": result.quality_status},
                    "architecture_compliance": {"value": result.arch_score, "status": result.arch_status}
                },
                "violations": [
                    {"type": "import_violation", "count": result.import_violations, "severity": "critical"},
                    {"type": "console_duplication", "count": result.console_duplicates, "severity": "critical"},
                    {"type": "hardcoding", "count": result.hardcode_issues, "severity": "high"}
                ],
                "recommendations": result.recommendations
            }

        # 従来CLI時は人間可読出力
        return self._format_human_readable(result)
```

#### MCP統合品質ゲート
```bash
# MCP統合品質チェック（Claude Code実行）
/noveler quality check --format json
/noveler test coverage --format json
/noveler codemap verify --format json

# 従来CLI（開発時詳細確認）
noveler quality check --detailed
noveler test coverage --html
noveler codemap verify --verbose
```

### 🎯 MCP対応品質メトリクス

#### JSON構造化品質レポート
```json
{
  "quality_gate": {
    "status": "passed",
    "score": 87.5,
    "thresholds": {
      "test_coverage": {"required": 80, "actual": 85, "status": "pass"},
      "shared_components": {"required": 95, "actual": 98, "status": "pass"},
      "console_duplication": {"max": 0, "actual": 0, "status": "pass"},
      "architecture_compliance": {"required": 90, "actual": 92, "status": "pass"}
    }
  },
  "violations": {
    "critical": [],
    "high": [],
    "medium": [
      {"type": "naming_convention", "file": "src/test.py", "line": 42}
    ]
  },
  "recommendations": [
    "Consider adding more integration tests for user workflows"
  ]
}
```

### 🚀 Claude Code統合ワークフロー

#### Phase 1: MCP統合品質チェック
```bash
# Claude Code内でスラッシュコマンド実行
/noveler quality check --format json
/noveler test run --unit --format json
/noveler codemap overview --format json
```

#### Phase 2: 問題特定と修正指示
```bash
# 具体的修正指示（Claude Code経由）
/noveler fix import-violations --auto
/noveler fix console-duplication --replace-with-shared
/noveler fix hardcoding --use-path-service
```

#### Phase 3: 修正検証
```bash
# 修正後再検証（即座に結果確認）
/noveler quality verify --format json
/noveler test run --all --format json
```

### 📊 MCP統合効果測定

| 品質プロセス | Before（CLI） | After（MCP） | 改善率 |
|-------------|---------------|--------------|--------|
| 品質チェック実行 | 3-5分 | 30秒-1分 | **80%短縮** |
| 問題特定精度 | 70% | 95% | **+25%** |
| 修正適用速度 | 10-15分 | 2-3分 | **85%短縮** |
| Claude Code応答 | 8-12秒 | 1-2秒 | **90%高速化** |
| トークン使用量 | 1200-1800 | 60-120 | **95%削減** |

### 🔧 MCP対応開発ガイドライン

#### 1. 全品質ツールのMCP対応必須
```python
# 必須実装パターン
def execute_command(args: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
    """全品質コマンドは以下パターン必須"""
    result = perform_quality_check(args)

    if args.get('format') == 'json' or is_mcp_context():
        return structure_as_json(result)  # 95%トークン削減

    return format_human_readable(result)  # 従来出力
```

#### 2. エラーハンドリングのMCP対応
```python
# MCP対応エラー出力
try:
    result = execute_quality_check()
except QualityGateError as e:
    if is_mcp_context():
        return {
            "error": {
                "type": "quality_gate_failure",
                "details": e.violations,
                "fix_suggestions": e.recommendations
            }
        }

    console.print(f"[red]品質ゲートエラー: {e}[/red]")
```

#### 3. 進捗表示のMCP統合
```python
# 長時間処理のMCP対応
async def long_running_quality_check():
    """MCP統合進捗表示"""
    if is_mcp_context():
        # Claude Code向け進捗JSON
        yield {"progress": {"stage": "importing", "percent": 20}}
        yield {"progress": {"stage": "analyzing", "percent": 60}}
        yield {"progress": {"stage": "reporting", "percent": 100}}
    else:
        # 従来CLI進捗バー
        with Progress() as progress:
            task = progress.add_task("Quality Check", total=100)
            # ... 処理継続
```

### 🎪 実装時の注意点

1. **双方向互換性確保**
   - MCP統合環境と従来CLI環境の両対応必須
   - JSON出力時も人間可読性を考慮
   - エラーメッセージの構造化

2. **パフォーマンス最適化**
   - JSON変換処理の軽量化
   - 不要データの除去
   - キャッシュ活用

3. **品質基準維持**
   - MCP統合により品質基準を下げない
   - 自動修正機能の精度向上
   - 誤修正防止機構

### 📚 関連ドキュメント

- **B33**: JSON変換・MCPツール統合ガイド（技術仕様）
- **B34**: Claude Code MCP統合ガイド（セットアップ）
- **B36**: スラッシュコマンド統合ガイド（実装予定）

---

## ⚡ 実装パターン例（模範コードリポジトリ参照）

### 🎯 模範実装リポジトリ
```yaml
# 参照すべき模範実装リポジトリ
reference_repositories:
  code_master:
    path: "../___code-master"
    patterns:
      - "Unit of Work パターン"
      - "Event-driven Architecture"
      - "Repository Pattern"
    key_files:
      - "src/infrastructure/uow.py"
      - "src/domain/repositories.py"

  python_ddd_main:
    path: "../___python-ddd-main"
    patterns:
      - "AggregateRoot パターン"
      - "Domain Rules"
      - "Value Objects"
    key_files:
      - "src/modules/bidding/domain/entities.py"
      - "src/seedwork/domain/entities.py"

  pytest_archon_main:
    path: "../___pytest-archon-main"
    patterns:
      - "Architecture Boundary Testing"
      - "Import Rules Testing"
    key_files:
      - "README.md"
      - "tests/test_architecture.py"

  import_linter_main:
    path: "../___import-linter-main"
    patterns:
      - "Import Contract Management"
      - "Dependency Flow Control"
    key_files:
      - ".importlinter"
      - "README.rst"
```

### 新機能実装の基本フロー
```python
# 1. 仕様書作成
"""
SPEC-CLI-001: 新機能実装
- 目的: XXX機能の実装
- 入力: YYYパラメータ
- 出力: ZZZ結果
"""

# 2. テスト作成
@pytest.mark.spec("SPEC-CLI-001")
def test_new_feature_success_case():
    """新機能の正常動作テスト"""
    # Arrange
    service = NewFeatureService()

    # Act
    result = service.execute(valid_input)

    # Assert
    assert result.is_success
    assert result.output == expected_output

# 3. 最小実装
class NewFeatureService:
    def execute(self, input_data: InputData) -> Result:
        """新機能の実装"""
        # ドメインロジック実装
        return Result.success(processed_data)

# 4. 統合・リファクタリング
from noveler.application.use_cases.new_feature_use_case import NewFeatureUseCase
```

### ドメイン層実装パターン（___python-ddd-main 参照）
```python
# ✅ 推奨: AggregateRoot パターン（___python-ddd-main/src/seedwork/domain/entities.py 参照）
from dataclasses import dataclass, field
from noveler.seedwork.domain.entities import AggregateRoot
from noveler.seedwork.domain.events import DomainEvent
from noveler.seedwork.domain.exceptions import DomainException

@dataclass(kw_only=True)
class Episode(AggregateRoot[EpisodeId]):
    """エピソード集約ルート"""
    number: EpisodeNumber
    title: EpisodeTitle
    content: EpisodeContent
    quality_score: Optional[QualityScore] = None

    # ドメインルール適用（___python-ddd-main パターン）
    def check_publication_rules(self):
        """公開前ルールチェック"""
        self.check_rule(
            MinimumWordCountRule(
                word_count=self.content.word_count,
                minimum=1000
            )
        )
        self.check_rule(
            QualityThresholdRule(
                quality_score=self.quality_score,
                threshold=0.7
            )
        )

    # イベント駆動（___code-master パターン）
    def publish(self):
        """エピソード公開"""
        self.check_publication_rules()
        self.register_event(
            EpisodePublished(
                episode_id=self.id,
                published_at=datetime.utcnow()
            )
        )

# ✅ 推奨: Domain Rules パターン（___python-ddd-main 参照）
class MinimumWordCountRule:
    """最小文字数ルール"""
    def __init__(self, word_count: int, minimum: int):
        self.word_count = word_count
        self.minimum = minimum

    def is_satisfied(self) -> bool:
        return self.word_count >= self.minimum

# ✅ 推奨: 純粋ドメインサービス
class EpisodeQualityService:
    """エピソード品質評価サービス"""

    def evaluate_quality(self, episode: Episode) -> QualityScore:
        """品質評価を実行"""
        # 外部依存なしの純粋ロジック
        score = self._calculate_base_score(episode)
        return QualityScore(score)

    def _calculate_base_score(self, episode: Episode) -> float:
        """基本スコア計算"""
        return episode.word_count.value * 0.1
```

### アプリケーション層実装パターン（___code-master 参照）
```python
# ✅ 推奨: Unit of Work パターン（___code-master/src/infrastructure/uow.py 参照）
from noveler.infrastructure.unit_of_work import AbstractUnitOfWork

class EpisodeCreationUseCase:
    """エピソード作成ユースケース（Unit of Work適用）"""

    def __init__(self, uow: AbstractUnitOfWork):
        self._uow = uow

    def execute(self, request: CreateEpisodeRequest) -> CreateEpisodeResponse:
        """エピソード作成の実行"""
        with self._uow:
            # トランザクション開始
            # ドメインオブジェクト生成
            episode = Episode.create(
                number=EpisodeNumber(request.episode_number),
                title=EpisodeTitle(request.title)
            )

            # ビジネスルールチェック
            episode.check_publication_rules()

            # リポジトリ経由で永続化
            self._uow.episodes.add(episode)

            # イベント処理
            for event in episode.events:
                self._handle_domain_event(event)

            # コミット（Unit of Work自動処理）
            self._uow.commit()

            return CreateEpisodeResponse.success(episode)

    def _handle_domain_event(self, event: DomainEvent):
        """ドメインイベント処理"""
        # イベントハンドラーへディスパッチ
        pass

# ✅ 推奨: Repository パターン（___code-master 参照）
class AbstractEpisodeRepository:
    """エピソードリポジトリ抽象基底クラス"""

    def add(self, episode: Episode) -> None:
        raise NotImplementedError

    def get(self, episode_id: EpisodeId) -> Episode:
        raise NotImplementedError

    def list(self, criteria: SearchCriteria) -> List[Episode]:
        raise NotImplementedError
```

---

## 🧪 テスト品質基準

### 必須テストパターン（___pytest-archon-main 参照）
```python
# Domain層テスト: 不変条件・ビジネスルール
@pytest.mark.unit
@pytest.mark.spec("SPEC-DOM-EPI-001")
class TestEpisode:
    def test_create_with_valid_data_success(self):
        """有効データでの作成成功"""
        episode = Episode.create(
            number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード")
        )
        assert episode.is_valid()

    def test_create_with_invalid_number_fails(self):
        """無効な話数での作成失敗"""
        with pytest.raises(InvalidEpisodeNumberError):
            EpisodeNumber(0)  # 0は無効

# ✅ 推奨: Architecture Boundary Test（___pytest-archon-main 参照）
from pytest_archon import archrule

def test_domain_layer_independence():
    """ドメイン層の独立性テスト"""
    (
        archrule("domain_independence", comment="ドメイン層は他層に依存しない")
        .match("noveler.domain*")
        .should_not_import("noveler.application*")
        .should_not_import("noveler.infrastructure*")
        .should_not_import("noveler.presentation*")
        .may_import("noveler.domain.*")
        .check("scripts")
    )

def test_application_layer_dependencies():
    """アプリケーション層の依存関係テスト"""
    (
        archrule("application_dependencies", comment="アプリケーション層はドメイン層のみ依存")
        .match("noveler.application.use_cases*")
        .should_import("noveler.domain*")
        .should_not_import("noveler.infrastructure.adapters*")
        .should_not_import("noveler.presentation*")
        .check("scripts")
    )

def test_shared_utilities_usage():
    """共通ユーティリティ使用率テスト"""
    def at_least_95_percent_usage(module, direct_imports, all_imports):
        # Console重複作成チェック
        console_imports = [
            k for k, v in all_imports.items()
            if "rich.console.Console" in v
        ]
        shared_imports = [
            k for k, v in all_imports.items()
            if "noveler.presentation.cli.shared_utilities" in v
        ]
        # 95%以上が共通ユーティリティ使用
        return len(shared_imports) / max(len(console_imports), 1) >= 0.95

    archrule("shared_utilities_enforcement")\
        .match("noveler.presentation.cli*")\
        .should(at_least_95_percent_usage)\
        .check("scripts")
```

### テスト命名規則（厳守）
- クラス名: `TestDomainEntityName` (英語パスカルケース)
- メソッド名: `test_business_action_condition` (英語スネークケース)
- 仕様書マーク: `@pytest.mark.spec("SPEC-XXX-YYY")` (必須)

---

```yaml
# 品質ゲート基準・メトリクス管理
quality_metrics:
  gate_thresholds:
    overall_coverage:
      metric: "全体カバレッジ"
      minimum_threshold: 80
      unit: "percentage"
      priority: "critical"
      measurement_command: "pytest --cov=src/noveler --cov-report=term"

    domain_layer_coverage:
      metric: "Domain層カバレッジ"
      minimum_threshold: 90
      unit: "percentage"
      priority: "critical"
      scope: "src/noveler/domain"
      measurement_command: "pytest --cov=src/noveler/domain --cov-report=term"

    shared_component_usage:
      metric: "共通コンポーネント使用率"
      minimum_threshold: 95
      unit: "percentage"
      priority: "critical"
      measurement_command: "python scripts/infrastructure/quality_gates/hardcoding_detector.py --project-root . --report-usage"

    console_duplication:
      metric: "Console重複作成"
      maximum_threshold: 0
      unit: "count"
      priority: "critical"
      measurement_command: "python scripts/infrastructure/quality_gates/hardcoding_detector.py --project-root . --check-console"

    error_handling_unification:
      metric: "統一エラーハンドリング率"
      minimum_threshold: 90
      unit: "percentage"
      priority: "high"
      measurement_command: "python scripts/infrastructure/quality_gates/architecture_linter.py --project-root . --check-error-handling"

  measurement_commands:
    coverage_generation:
      - command: "noveler test run --coverage --durations=20"
        purpose: "カバレッジレポート生成（novel統合）"
        output_format: "html_report"
        timeout: "15分"

      - command: "pytest --cov=src/noveler --cov-report=html"
        purpose: "詳細カバレッジレポート生成"
        output_location: "htmlcov/"
        timeout: "10分"

    quality_kpi_verification:
      - command: "python scripts/tools/quality_gate_check.py --detailed"
        purpose: "品質KPI詳細確認"
        output_format: "detailed_report"
        automation_level: "fully_automated"

      - command: "pytest --cache-clear tests/unit/domain/test_domain_dependency_guards.py"
        purpose: "Domain層外部依存ガードの再検証（キャッシュ無効化込み）"
        output_format: "pytest_report"
        automation_level: "semi_automated"

      - command: "bin/test -n=2 -m '(not e2e) and (not integration_skip)' --maxfail=1 --durations=10"
        purpose: "並列実行時の品質ゲート確認（推奨マーカー設定付き）"
        output_format: "pytest_report"
        automation_level: "semi_automated"

      - command: "project-tools quality report --scope all"
        purpose: "全スコープ品質レポート"
        output_format: "comprehensive_report"
        automation_level: "fully_automated"

  pass_criteria:
    all_metrics_pass: true
    critical_metrics_mandatory: true
    high_priority_recommended: true
    failure_action: "実装停止・修正必須"
```

### インポート管理パターン（___import-linter-main 参照）
```ini
# .importlinter 設定例（___import-linter-main 参照）
[importlinter]
root_package = noveler

[importlinter:contract:1]
name = ドメイン層独立性
type = forbidden
source_modules =
    noveler.domain
forbidden_modules =
    noveler.application
    noveler.infrastructure
    noveler.presentation

[importlinter:contract:2]
name = アプリケーション層依存制約
type = forbidden
source_modules =
    noveler.application
forbidden_modules =
    noveler.infrastructure.adapters
    noveler.presentation

[importlinter:contract:3]
name = 共通ユーティリティ強制使用
type = required
source_modules =
    noveler.presentation.cli
required_modules =
    noveler.presentation.cli.shared_utilities
ignore_imports =
    noveler.presentation.cli.shared_utilities
```

---

## 🔄 リファクタリング専用指示

### 段階的リファクタリング手順
1. **現状分析**: コードの問題点特定
2. **テスト確保**: 既存機能のテスト充実
3. **段階的修正**: 小さな単位での修正実施
4. **検証**: 各段階でのテスト実行・確認
5. **最終確認**: 品質ゲート通過確認

### 自動修正ツール活用
```bash
# 自動修正のプレビュー
project-tools refactor auto-fix --dry-run

# 修正適用
project-tools refactor auto-fix --apply

# 修正後検証
project-tools quality verify

# 自動統合パターン適用
project-tools refactor auto-integrate --scope all
project-tools refactor replace-with-common --pattern console_creation
```

### リファクタリング前の必須確認
```bash
# 品質状態確認
project-tools quality check --include-common-components

# 既存テスト実行
noveler test run --unit --fast
```

### レガシーコード更新パターン
```python
# 段階的移行パターン
if USE_NEW_ARCHITECTURE:
    # 新アーキテクチャ使用
    orchestrator = ErrorHandlingOrchestratorFactory.create_default_orchestrator()
    result = orchestrator.execute_with_error_handling(...)
else:
    # レガシー使用（廃止予定警告付き）
    warnings.warn("Legacy architecture is deprecated", DeprecationWarning)
```

### リファクタリング完了チェックリスト

#### コード品質
- [ ] 統合インポート管理（scriptsプレフィックス）統一完了
- [ ] 共通コンポーネント強制利用パターン適用完了
- [ ] 命名規則（英語スネークケース）統一完了
- [ ] 実装コメント削除・docstring適切付与完了

#### 動作品質
- [ ] 全テストパス確認完了
- [ ] 品質ゲート通過確認完了
- [ ] パフォーマンス基準クリア確認完了
- [ ] エラーハンドリング統一適用完了

#### 保守品質
- [ ] 重複コード排除完了
- [ ] DDD依存方向違反解消完了
- [ ] テストカバレッジ目標達成完了
- [ ] ドキュメント更新完了

### 問題発生時の対応
1. **エラー発生**: まずテストを実行して現状把握
2. **品質ゲート失敗**: 具体的なエラーメッセージを確認して対処
3. **テスト失敗**: 修正内容を見直し、適切なテスト更新を実施
4. **不明点**: 本品質作業指示書を参照

---

## 🎯 成功のチェックポイント

### 実装品質
- [ ] CLAUDE.mdの規約100%遵守
- [ ] 共通コンポーネント強制利用パターン適用
- [ ] DDD依存方向違反なし
- [ ] テスト網羅率目標達成

### コード品質
- [ ] 命名規則統一 (英語スネークケース)
- [ ] インポート統一 (scriptsプレフィックス)
- [ ] 実装コメント排除
- [ ] docstring適切付与

### 動作品質
- [ ] 全テストパス
- [ ] 品質ゲート通過
- [ ] パフォーマンス基準クリア
- [ ] エラーハンドリング統一

---

---

## 📚 関連資料

### 必須参照ドキュメント
- **[B20_Claude_Code開発作業指示書.md](B20_Claude_Code開発作業指示書.md)** - 新機能実装・開発プロセス
- **[CLAUDE.md](../CLAUDE.md)** - プロジェクト基本方針
- **backup/B11_システムアーキテクチャ基礎.md** - 理論詳細が必要な場合のみ参照

### 模範実装リポジトリ（必須参照）
- **___code-master** - Unit of Work、Event-driven Architecture
- **___python-ddd-main** - AggregateRoot、Domain Rules、Value Objects
- **___pytest-archon-main** - Architecture Boundary Testing
- **___import-linter-main** - Import Contract Management

---

**💎 重要**: この品質作業指示書は、Claude Codeでの実装作業において**必ず参照すべき中核ドキュメント**です。B31/B32/B33およびリファクタリング専用テンプレートの詳細は本書に統合済みのため、新機能実装・リファクタリング・不具合修正時は本書のみを参照してください。


### Import契約（importlinter）
- pre-commit で importlinter が導入済みの場合に自動検査。未導入なら自動スキップ。
- ローカル検査: `make lint-imports`。CIでも `.importlinter` 契約で検査。
