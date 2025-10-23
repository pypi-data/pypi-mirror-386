# SPEC-GENERAL-101: 整合性更新オーケストレータ仕様書

## 概要
`ConsistencyUpdateOrchestrator`は、プロジェクト全体の整合性を維持するための更新処理を統合的に管理するオーケストレータです。プロット変更、設定変更、構造変更に伴う関連ファイルの自動更新、整合性チェック、更新履歴管理を一元的に処理します。

## クラス設計

### ConsistencyUpdateOrchestrator

**責務**
- 変更影響範囲の総合的な分析
- 複数サービスの協調的な更新実行
- 更新順序の最適化と依存関係管理
- トランザクション的な更新処理
- 更新履歴とロールバック情報の管理
- エラー時の部分的ロールバック

## データ構造

### UpdateType (Enum)
```python
class UpdateType(Enum):
    PLOT_CHANGE = "plot_change"              # プロット変更
    SETTING_CHANGE = "setting_change"        # 設定変更
    STRUCTURE_CHANGE = "structure_change"    # 構造変更
    CHARACTER_CHANGE = "character_change"    # キャラクター変更
    TIMELINE_CHANGE = "timeline_change"      # タイムライン変更
    METADATA_CHANGE = "metadata_change"      # メタデータ変更
```

### ConsistencyUpdateRequest (DataClass)
```python
@dataclass
class ConsistencyUpdateRequest:
    project_name: str                        # プロジェクト名
    update_type: UpdateType                  # 更新タイプ
    changed_files: list[str]                 # 変更されたファイル
    update_context: dict[str, any]           # 更新コンテキスト
    auto_update: bool = True                 # 自動更新フラグ
    dry_run: bool = False                    # ドライランフラグ
    create_backup: bool = True               # バックアップ作成フラグ
```

### ConsistencyUpdateResponse (DataClass)
```python
@dataclass
class ConsistencyUpdateResponse:
    success: bool                            # 処理成功フラグ
    updated_files: list[str]                 # 更新されたファイル
    skipped_files: list[str]                 # スキップされたファイル
    errors: list[UpdateError]                # エラー情報
    update_summary: dict[str, any]           # 更新サマリー
    rollback_info: RollbackInfo | None = None # ロールバック情報
    execution_time: float = 0.0              # 実行時間（秒）
```

### UpdatePlan (DataClass)
```python
@dataclass
class UpdatePlan:
    update_id: str                           # 更新ID
    steps: list[UpdateStep]                  # 更新ステップ
    dependencies: dict[str, list[str]]       # 依存関係マップ
    estimated_time: float                    # 推定所要時間
    risk_level: str                          # リスクレベル
    rollback_strategy: str                   # ロールバック戦略
```

### UpdateStep (DataClass)
```python
@dataclass
class UpdateStep:
    step_id: str                             # ステップID
    service_name: str                        # 実行サービス名
    operation: str                           # 操作内容
    target_files: list[str]                  # 対象ファイル
    parameters: dict[str, any]               # パラメータ
    can_parallel: bool                       # 並列実行可能フラグ
    is_critical: bool                        # クリティカルフラグ
```

## パブリックメソッド

### execute_consistency_update()

**シグネチャ**
```python
def execute_consistency_update(
    self,
    request: ConsistencyUpdateRequest
) -> ConsistencyUpdateResponse:
```

**目的**
整合性を保ちながらプロジェクト全体の更新を実行する。

**引数**
- `request`: 整合性更新リクエスト

**戻り値**
- `ConsistencyUpdateResponse`: 更新結果

**処理フロー**
1. **影響分析**: 変更による影響範囲の分析
2. **更新計画作成**: 最適な更新順序の決定
3. **バックアップ**: 必要に応じてバックアップ作成
4. **更新実行**: 計画に従った更新の実行
5. **検証**: 更新後の整合性検証
6. **結果集約**: 更新結果の統合

### create_update_plan()

**シグネチャ**
```python
def create_update_plan(
    self,
    request: ConsistencyUpdateRequest
) -> UpdatePlan:
```

**目的**
更新リクエストから実行計画を作成する。

### validate_consistency()

**シグネチャ**
```python
def validate_consistency(
    self,
    project_name: str,
    validation_scope: list[str] | None = None
) -> ConsistencyReport:
```

**目的**
プロジェクトの整合性を検証する。

### rollback_update()

**シグネチャ**
```python
def rollback_update(
    self,
    rollback_info: RollbackInfo
) -> bool:
```

**目的**
更新をロールバックする。

## プライベートメソッド

### _analyze_impact()

**シグネチャ**
```python
def _analyze_impact(
    self,
    request: ConsistencyUpdateRequest
) -> dict[str, list[str]]:
```

**目的**
変更による影響範囲を分析する。

**分析内容**
```python
impact_map = {
    "direct_impact": [],      # 直接影響を受けるファイル
    "indirect_impact": [],    # 間接的に影響を受けるファイル
    "cascade_impact": [],     # カスケード的に影響を受けるファイル
    "validation_required": [] # 検証が必要なファイル
}
```

### _create_execution_order()

**シグネチャ**
```python
def _create_execution_order(
    self,
    update_steps: list[UpdateStep],
    dependencies: dict[str, list[str]]
) -> list[list[UpdateStep]]:
```

**目的**
依存関係を考慮した実行順序を作成する。

**アルゴリズム**
```python
# トポロジカルソートによる依存関係解決
# 並列実行可能なステップのグループ化
# クリティカルパスの特定
```

### _execute_update_step()

**シグネチャ**
```python
def _execute_update_step(
    self,
    step: UpdateStep,
    context: UpdateContext
) -> StepResult:
```

**目的**
個別の更新ステップを実行する。

### _coordinate_services()

**シグネチャ**
```python
def _coordinate_services(
    self,
    update_type: UpdateType,
    context: dict[str, any]
) -> list[UpdateStep]:
```

**目的**
更新タイプに応じて適切なサービスを協調させる。

**サービス協調パターン**
```python
service_coordination = {
    UpdateType.PLOT_CHANGE: [
        "plot_analyzer",
        "episode_updater",
        "foreshadowing_updater",
        "timeline_adjuster"
    ],
    UpdateType.CHARACTER_CHANGE: [
        "character_analyzer",
        "dialogue_updater",
        "relationship_updater"
    ],
    # 他の更新タイプ...
}
```

### _handle_partial_failure()

**シグネチャ**
```python
def _handle_partial_failure(
    self,
    completed_steps: list[UpdateStep],
    failed_step: UpdateStep,
    error: Exception
) -> PartialRollbackResult:
```

**目的**
部分的な失敗時の処理を行う。

### _create_rollback_checkpoint()

**シグネチャ**
```python
def _create_rollback_checkpoint(
    self,
    project_name: str,
    update_id: str
) -> RollbackInfo:
```

**目的**
ロールバック用のチェックポイントを作成する。

## 更新フロー例

### プロット変更時の更新フロー
```python
# 1. マスタープロット変更を検出
changed_files = ["20_プロット/全体構成.yaml"]

# 2. 影響分析
impacts = {
    "direct": [
        "20_プロット/章別プロット/第3章.yaml",
        "20_プロット/章別プロット/第4章.yaml"
    ],
    "indirect": [
        "50_管理資料/話数管理.yaml",
        "50_管理資料/伏線管理.yaml"
    ],
    "cascade": [
        "40_原稿/第015話_*.md",
        "40_原稿/第016話_*.md"
    ]
}

# 3. 更新計画
plan = UpdatePlan(
    steps=[
        UpdateStep("update_chapter_plots", "plot_service", ...),
        UpdateStep("update_episode_management", "episode_service", ...),
        UpdateStep("update_foreshadowing", "foreshadowing_service", ...),
        UpdateStep("validate_consistency", "validation_service", ...)
    ]
)

# 4. 実行
results = execute_parallel_steps(plan.steps)
```

## 依存関係

### ドメインサービス
- `ImpactAnalyzer`: 影響範囲分析
- `DependencyResolver`: 依存関係解決
- `ConsistencyValidator`: 整合性検証

### アプリケーションサービス
- `PlotUpdateService`: プロット更新
- `EpisodeUpdateService`: エピソード更新
- `ForeshadowingUpdateService`: 伏線更新
- `CharacterUpdateService`: キャラクター更新
- `TimelineUpdateService`: タイムライン更新

### インフラストラクチャ
- `BackupService`: バックアップ管理
- `TransactionManager`: トランザクション管理
- `FileSystemService`: ファイルシステム操作

## 設計原則遵守

### DDD準拠
- ✅ オーケストレータパターンによる複数サービスの協調
- ✅ 明確な責務分離（調整のみ、ビジネスロジックは各サービス）
- ✅ トランザクション境界の適切な管理
- ✅ イベント駆動による疎結合

### TDD準拠
- ✅ 明確な入出力定義
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ テスト可能な設計

## 使用例

```python
# 依存関係の準備
impact_analyzer = ImpactAnalyzer()
dependency_resolver = DependencyResolver()
consistency_validator = ConsistencyValidator()
plot_update_service = PlotUpdateService()
episode_update_service = EpisodeUpdateService()
foreshadowing_update_service = ForeshadowingUpdateService()
character_update_service = CharacterUpdateService()
timeline_update_service = TimelineUpdateService()
backup_service = BackupService()
transaction_manager = TransactionManager()
file_system_service = FileSystemService()

# オーケストレータ作成
orchestrator = ConsistencyUpdateOrchestrator(
    impact_analyzer=impact_analyzer,
    dependency_resolver=dependency_resolver,
    consistency_validator=consistency_validator,
    plot_update_service=plot_update_service,
    episode_update_service=episode_update_service,
    foreshadowing_update_service=foreshadowing_update_service,
    character_update_service=character_update_service,
    timeline_update_service=timeline_update_service,
    backup_service=backup_service,
    transaction_manager=transaction_manager,
    file_system_service=file_system_service
)

# プロット変更による整合性更新
plot_change_request = ConsistencyUpdateRequest(
    project_name="fantasy_adventure",
    update_type=UpdateType.PLOT_CHANGE,
    changed_files=["20_プロット/全体構成.yaml"],
    update_context={
        "change_description": "第3章のクライマックスを変更",
        "affected_chapters": [3, 4],
        "version": "v1.3.0"
    },
    auto_update=True,
    dry_run=False,
    create_backup=True
)

# ドライラン実行
dry_run_request = ConsistencyUpdateRequest(
    **plot_change_request.__dict__,
    dry_run=True
)

dry_run_response = orchestrator.execute_consistency_update(dry_run_request)

print("=== ドライラン結果 ===")
print(f"影響ファイル数: {len(dry_run_response.updated_files)}")
for file in dry_run_response.updated_files:
    print(f"  - {file}")

if input("\n実際に更新を実行しますか？ [y/N]: ").lower() == 'y':
    # 実際の更新実行
    response = orchestrator.execute_consistency_update(plot_change_request)

    if response.success:
        print(f"\n✅ 整合性更新完了")
        print(f"更新ファイル数: {len(response.updated_files)}")
        print(f"実行時間: {response.execution_time:.2f}秒")

        print("\n更新サマリー:")
        for category, count in response.update_summary.items():
            print(f"  {category}: {count}件")

        if response.rollback_info:
            print(f"\nロールバック情報: {response.rollback_info.checkpoint_id}")
    else:
        print(f"\n❌ 更新失敗")
        for error in response.errors:
            print(f"  - {error.message}")

        if response.rollback_info:
            print("\nロールバックを実行しますか？")

# キャラクター変更による整合性更新
character_change_request = ConsistencyUpdateRequest(
    project_name="fantasy_adventure",
    update_type=UpdateType.CHARACTER_CHANGE,
    changed_files=["30_設定集/キャラクター.yaml"],
    update_context={
        "changed_characters": ["主人公", "師匠"],
        "change_type": "relationship",
        "description": "師弟関係の深化"
    }
)

# 更新計画の作成のみ
update_plan = orchestrator.create_update_plan(character_change_request)

print(f"\n更新計画:")
print(f"推定時間: {update_plan.estimated_time}秒")
print(f"リスクレベル: {update_plan.risk_level}")
print(f"ステップ数: {len(update_plan.steps)}")

for i, step in enumerate(update_plan.steps, 1):
    print(f"\n{i}. {step.operation}")
    print(f"   サービス: {step.service_name}")
    print(f"   対象: {', '.join(step.target_files[:3])}...")
    print(f"   並列実行: {'可' if step.can_parallel else '不可'}")

# 整合性検証のみ実行
validation_report = orchestrator.validate_consistency(
    project_name="fantasy_adventure",
    validation_scope=["plot", "episodes", "foreshadowing"]
)

print(f"\n整合性検証結果:")
print(f"状態: {'✅ 正常' if validation_report.is_consistent else '⚠️ 不整合あり'}")
if not validation_report.is_consistent:
    for issue in validation_report.issues:
        print(f"  - {issue.category}: {issue.description}")
```

## エラーハンドリング戦略

### トランザクション管理
```python
with self.transaction_manager.begin() as transaction:
    try:
        # 更新処理
        for step in execution_order:
            result = self._execute_update_step(step, context)
            transaction.add_completed(step, result)
    except Exception as e:
        # 自動ロールバック
        transaction.rollback()
        raise ConsistencyUpdateError(f"更新中にエラーが発生: {str(e)}")
```

### 部分的失敗の処理
```python
def _handle_partial_failure(self, completed_steps, failed_step, error):
    # 1. クリティカルステップの失敗 → 全体ロールバック
    if failed_step.is_critical:
        return self._full_rollback(completed_steps)

    # 2. 非クリティカル → 部分的継続
    return self._partial_continue(completed_steps, failed_step)
```

### リトライ戦略
```python
@retry(max_attempts=3, backoff_factor=2)
def _execute_with_retry(self, step: UpdateStep) -> StepResult:
    return self._execute_update_step(step)
```

## パフォーマンス最適化

### 並列実行
```python
# 依存関係のないステップを並列実行
parallel_groups = self._create_parallel_groups(update_steps)
for group in parallel_groups:
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(self._execute_step, step) for step in group]
        results = [f.result() for f in futures]
```

### キャッシュ活用
```python
# 影響分析結果のキャッシュ
@lru_cache(maxsize=100)
def _get_impact_cache(self, file_path: str, change_type: str) -> list[str]:
    return self.impact_analyzer.analyze(file_path, change_type)
```

## テスト観点

### 単体テスト
- 影響分析の正確性
- 依存関係解決アルゴリズム
- 実行順序の最適性
- エラーハンドリング
- ロールバック機能

### 統合テスト
- 複数サービスの協調動作
- 大規模プロジェクトでの性能
- 並列実行の正確性
- トランザクション管理

## 品質基準

- **信頼性**: 部分的失敗時の安全な処理
- **一貫性**: 整合性の確実な維持
- **効率性**: 並列実行による高速化
- **透明性**: 詳細な実行ログと結果レポート
- **回復性**: 確実なロールバック機能
