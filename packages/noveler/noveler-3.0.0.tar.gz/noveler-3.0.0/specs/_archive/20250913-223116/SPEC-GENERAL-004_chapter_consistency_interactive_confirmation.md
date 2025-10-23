# SPEC-GENERAL-004: 章別整合性対話確認ユースケース仕様書

## 概要
`ChapterConsistencyInteractiveConfirmation`は、章別プロットの変更に伴う整合性確認を対話的に行うユースケースです。プロット変更による影響範囲の提示、話数管理・伏線管理への影響確認、ユーザーによる選択的更新の実行を段階的に行い、安全で確実な章別整合性の維持を支援します。

## クラス設計

### ChapterConsistencyInteractiveConfirmation

**責務**
- 章別プロット変更の影響分析
- 影響範囲の視覚的提示
- 話数管理への影響確認と選択的更新
- 伏線管理への影響確認と選択的更新
- 対話的な確認プロセスの管理
- 更新履歴の記録と追跡

## データ構造

### ChapterImpactType (Enum)
```python
class ChapterImpactType(Enum):
    EPISODE_STRUCTURE = "episode_structure"    # 話数構成への影響
    FORESHADOWING = "foreshadowing"           # 伏線配置への影響
    CHARACTER_ARC = "character_arc"           # キャラクターアークへの影響
    TIMELINE = "timeline"                     # タイムラインへの影響
    SCENE_FLOW = "scene_flow"                 # シーンフローへの影響
```

### ConsistencyCheckResult (DataClass)
```python
@dataclass
class ConsistencyCheckResult:
    chapter_number: int                       # 対象章番号
    impact_types: list[ChapterImpactType]     # 影響タイプ
    affected_episodes: list[int]              # 影響エピソード番号
    affected_foreshadowing: list[str]         # 影響伏線ID
    severity: str                             # 影響度（low/medium/high）
    recommendations: list[str]                # 推奨アクション
    auto_fixable: bool                        # 自動修正可能フラグ
```

### InteractiveConfirmationRequest (DataClass)
```python
@dataclass
class InteractiveConfirmationRequest:
    project_name: str                         # プロジェクト名
    changed_chapters: list[int]               # 変更された章番号
    version_info: dict[str, str]              # バージョン情報
    consistency_results: list[ConsistencyCheckResult]  # 整合性チェック結果
    interactive_mode: bool = True             # 対話モードフラグ
    auto_approve_low_impact: bool = False     # 低影響自動承認フラグ
```

### InteractiveConfirmationResponse (DataClass)
```python
@dataclass
class InteractiveConfirmationResponse:
    success: bool                             # 処理成功フラグ
    confirmed_updates: dict[str, list[str]]   # 承認された更新
    skipped_updates: dict[str, list[str]]     # スキップされた更新
    manual_review_required: list[str]         # 手動レビュー必要項目
    update_log: list[str]                     # 更新ログ
    rollback_info: dict[str, any] = {}        # ロールバック情報
```

### UpdateChoice (DataClass)
```python
@dataclass
class UpdateChoice:
    item_type: str                            # 項目タイプ（episode/foreshadowing）
    item_id: str                              # 項目ID
    current_state: dict[str, any]             # 現在の状態
    proposed_state: dict[str, any]            # 提案される状態
    user_choice: str = "pending"              # ユーザー選択（approve/skip/modify）
    modification: dict[str, any] | None = None # 修正内容
```

## パブリックメソッド

### execute_interactive_confirmation()

**シグネチャ**
```python
def execute_interactive_confirmation(
    self,
    request: InteractiveConfirmationRequest
) -> InteractiveConfirmationResponse:
```

**目的**
章別プロット変更に対する対話的な整合性確認を実行する。

**引数**
- `request`: 対話確認リクエスト

**戻り値**
- `InteractiveConfirmationResponse`: 確認結果

**処理フロー**
1. **影響分析表示**: 変更による影響範囲を表示
2. **カテゴリ別確認**: 影響タイプごとに確認
3. **個別項目選択**: 更新項目の個別選択
4. **確認と実行**: 選択内容の最終確認と実行
5. **結果記録**: 更新結果とログの記録

### preview_chapter_changes()

**シグネチャ**
```python
def preview_chapter_changes(
    self,
    project_name: str,
    chapter_numbers: list[int]
) -> str:
```

**目的**
章変更のプレビューを生成する。

### apply_selected_updates()

**シグネチャ**
```python
def apply_selected_updates(
    self,
    project_name: str,
    update_choices: list[UpdateChoice]
) -> bool:
```

**目的**
選択された更新を適用する。

### create_rollback_point()

**シグネチャ**
```python
def create_rollback_point(
    self,
    project_name: str,
    description: str
) -> str:
```

**目的**
更新前のロールバックポイントを作成する。

## プライベートメソッド

### _display_impact_summary()

**シグネチャ**
```python
def _display_impact_summary(
    self,
    consistency_results: list[ConsistencyCheckResult]
) -> None:
```

**目的**
整合性チェック結果のサマリーを表示する。

**表示例**
```
=== 章別プロット変更の影響分析 ===

📚 第3章の変更による影響:

  話数構成:
    • 影響を受けるエピソード: 第15-18話
    • 推奨: エピソードの順序調整

  伏線管理:
    • 影響を受ける伏線: F003, F007
    • 推奨: 伏線配置タイミングの見直し

  影響度: 中

📚 第4章の変更による影響:

  キャラクターアーク:
    • 影響を受けるキャラクター: 主人公、賢者
    • 推奨: 成長曲線の調整

  影響度: 低（自動修正可能）
```

### _confirm_episode_updates()

**シグネチャ**
```python
def _confirm_episode_updates(
    self,
    affected_episodes: list[dict[str, any]]
) -> list[UpdateChoice]:
```

**目的**
エピソード更新の個別確認を行う。

**確認画面例**
```
=== 話数管理の更新確認 ===

以下のエピソードに対する更新を確認してください:

[1] 第15話「試練の始まり」
    現在: 第3章前半
    変更案: 第3章中盤へ移動
    理由: プロット構成の変更により順序調整が必要

    [A] 承認  [S] スキップ  [M] 修正  [?] 詳細

[2] 第16話「師との出会い」
    現在: 第3章中盤
    変更案: 第3章後半へ移動
    理由: 新キャラクター登場タイミングの調整

    [A] 承認  [S] スキップ  [M] 修正  [?] 詳細

選択: _
```

### _confirm_foreshadowing_updates()

**シグネチャ**
```python
def _confirm_foreshadowing_updates(
    self,
    affected_foreshadowing: list[dict[str, any]]
) -> list[UpdateChoice]:
```

**目的**
伏線更新の個別確認を行う。

### _execute_updates_with_progress()

**シグネチャ**
```python
def _execute_updates_with_progress(
    self,
    project_name: str,
    confirmed_choices: list[UpdateChoice]
) -> dict[str, list[str]]:
```

**目的**
確認された更新を進捗表示付きで実行する。

### _handle_complex_impact()

**シグネチャ**
```python
def _handle_complex_impact(
    self,
    impact: ConsistencyCheckResult
) -> list[UpdateChoice]:
```

**目的**
複雑な影響を持つ項目の特別処理を行う。

### _create_update_summary()

**シグネチャ**
```python
def _create_update_summary(
    self,
    response: InteractiveConfirmationResponse
) -> str:
```

**目的**
更新結果のサマリーを作成する。

## 対話フロー例

### 1. 初期確認
```
章別プロットの変更を検出しました。
整合性確認を開始しますか？ [Y/n]: Y
```

### 2. 影響分析表示
```
分析中... 完了

📊 影響分析結果:
- 影響を受ける章: 2章
- 影響を受けるエピソード: 8話
- 影響を受ける伏線: 5件
- 推定作業時間: 約15分

詳細を表示しますか？ [Y/n]: Y
```

### 3. カテゴリ別確認
```
=== カテゴリ別更新確認 ===

[1] 話数管理の更新 (5件)
[2] 伏線管理の更新 (3件)
[3] すべて自動更新
[4] すべて手動確認
[5] キャンセル

選択してください [1-5]: 1
```

### 4. 個別確認
```
話数管理の更新 (1/5)

第15話「試練の始まり」
━━━━━━━━━━━━━━━━━━━━━━━━━━
現在の配置: 第3章前半（3-2）
推奨される配置: 第3章中盤（3-4）

変更理由:
新たに追加された「師との準備」シーンの後に
配置することで、物語の流れが自然になります。

この更新を適用しますか？
[Enter] 承認 | [s] スキップ | [m] 修正 | [d] 詳細 | [q] 中止
> _
```

### 5. 最終確認
```
=== 更新内容の最終確認 ===

承認された更新:
✅ 話数管理: 4件
  - 第15話: 配置変更（3-2 → 3-4）
  - 第16話: 配置変更（3-4 → 3-5）
  - 第17話: 配置変更（3-5 → 3-6）
  - 第18話: ステータス更新

✅ 伏線管理: 2件
  - F003: 配置エピソード調整
  - F007: 解決タイミング変更

スキップ: 2件
❌ 話数管理: 第19話（手動確認が必要）
❌ 伏線管理: F012（複雑な依存関係）

これらの更新を実行しますか？ [Y/n]: _
```

## 依存関係

### ドメインサービス
- `ChapterAnalyzer`: 章別影響分析
- `ConsistencyChecker`: 整合性チェック
- `UpdateExecutor`: 更新実行

### リポジトリ
- `ProjectRepository`: プロジェクト情報管理
- `EpisodeRepository`: エピソード情報管理
- `ForeshadowingRepository`: 伏線情報管理
- `UpdateHistoryRepository`: 更新履歴管理

### UIサービス
- `InteractiveConsole`: コンソール対話制御
- `ProgressDisplay`: 進捗表示
- `ColorFormatter`: カラー出力

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`UpdateChoice`, `ConsistencyCheckResult`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービスの適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
chapter_analyzer = ChapterAnalyzer()
consistency_checker = ConsistencyChecker()
update_executor = UpdateExecutor()
project_repo = YamlProjectRepository()
episode_repo = YamlEpisodeRepository()
foreshadowing_repo = YamlForeshadowingRepository()
update_history_repo = UpdateHistoryRepository()
interactive_console = InteractiveConsole()
progress_display = ProgressDisplay()
color_formatter = ColorFormatter()

# ユースケース作成
use_case = ChapterConsistencyInteractiveConfirmation(
    chapter_analyzer=chapter_analyzer,
    consistency_checker=consistency_checker,
    update_executor=update_executor,
    project_repository=project_repo,
    episode_repository=episode_repo,
    foreshadowing_repository=foreshadowing_repo,
    update_history_repository=update_history_repo,
    interactive_console=interactive_console,
    progress_display=progress_display,
    color_formatter=color_formatter
)

# 整合性チェック結果の準備
consistency_results = [
    ConsistencyCheckResult(
        chapter_number=3,
        impact_types=[ChapterImpactType.EPISODE_STRUCTURE, ChapterImpactType.FORESHADOWING],
        affected_episodes=[15, 16, 17, 18],
        affected_foreshadowing=["F003", "F007"],
        severity="medium",
        recommendations=[
            "エピソード順序の調整を推奨",
            "伏線配置タイミングの見直しを推奨"
        ],
        auto_fixable=False
    ),
    ConsistencyCheckResult(
        chapter_number=4,
        impact_types=[ChapterImpactType.CHARACTER_ARC],
        affected_episodes=[20, 21],
        affected_foreshadowing=[],
        severity="low",
        recommendations=["キャラクター成長曲線の微調整"],
        auto_fixable=True
    )
]

# 対話的確認の実行
request = InteractiveConfirmationRequest(
    project_name="fantasy_adventure",
    changed_chapters=[3, 4],
    version_info={
        "from": "v1.2.0",
        "to": "v1.3.0",
        "description": "第3-4章のプロット改訂"
    },
    consistency_results=consistency_results,
    interactive_mode=True,
    auto_approve_low_impact=True
)

# ロールバックポイントの作成
rollback_id = use_case.create_rollback_point(
    project_name="fantasy_adventure",
    description="章別プロット変更前の状態"
)

print(f"ロールバックポイント作成: {rollback_id}")

# 対話的確認の実行
response = use_case.execute_interactive_confirmation(request)

if response.success:
    print("\n✅ 整合性更新が完了しました")

    print("\n承認された更新:")
    for category, items in response.confirmed_updates.items():
        print(f"  {category}: {len(items)}件")
        for item in items[:3]:  # 最初の3件を表示
            print(f"    - {item}")

    if response.skipped_updates:
        print("\nスキップされた更新:")
        for category, items in response.skipped_updates.items():
            print(f"  {category}: {len(items)}件")

    if response.manual_review_required:
        print("\n⚠️ 手動レビューが必要な項目:")
        for item in response.manual_review_required:
            print(f"  - {item}")

    print(f"\n更新ログ: {len(response.update_log)}件の操作を記録")
else:
    print("\n❌ 整合性更新がキャンセルされました")
    print("ロールバックポイントから復元できます")

# プレビュー機能の使用
preview = use_case.preview_chapter_changes(
    project_name="fantasy_adventure",
    chapter_numbers=[5, 6]
)

print("\n章変更プレビュー:")
print(preview)

# 特定の更新のみ適用
specific_choices = [
    UpdateChoice(
        item_type="episode",
        item_id="15",
        current_state={"position": "3-2", "status": "draft"},
        proposed_state={"position": "3-4", "status": "draft"},
        user_choice="approve"
    )
]

success = use_case.apply_selected_updates(
    project_name="fantasy_adventure",
    update_choices=specific_choices
)
```

## エラーハンドリング

### ユーザーキャンセル
```python
try:
    user_choice = self.interactive_console.get_choice(options)
except KeyboardInterrupt:
    logger.info("ユーザーが処理をキャンセルしました")
    # ロールバック情報を保持して終了
    return InteractiveConfirmationResponse(
        success=False,
        confirmed_updates={},
        skipped_updates=self._convert_to_skipped(all_choices),
        manual_review_required=[],
        update_log=["処理がユーザーによってキャンセルされました"],
        rollback_info={"rollback_id": rollback_id, "can_restore": True}
    )
```

### 更新エラー
```python
try:
    self.update_executor.execute(update_choice)
except UpdateExecutionError as e:
    logger.error(f"更新エラー: {e}")
    # 部分的なロールバックを実行
    self._partial_rollback(completed_updates)
    raise ChapterConsistencyError(f"更新中にエラーが発生しました: {str(e)}")
```

## テスト観点

### 単体テスト
- 影響分析の正確性
- 対話フローの各ステップ
- 更新選択の処理
- ロールバック機能
- エラー条件での動作

### 統合テスト
- 実際のプロジェクトデータでの動作
- 複数章の同時更新
- 大量項目の処理性能
- UIの応答性

## 品質基準

- **透明性**: 影響範囲の明確な提示
- **制御性**: きめ細かい更新制御
- **安全性**: ロールバック機能の確実性
- **効率性**: 自動化可能な部分の識別
- **追跡可能性**: 全更新の履歴記録
