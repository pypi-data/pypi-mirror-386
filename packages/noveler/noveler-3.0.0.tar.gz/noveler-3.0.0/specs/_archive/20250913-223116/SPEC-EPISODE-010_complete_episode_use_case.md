# SPEC-EPISODE-010: 執筆完了ユースケース仕様書

## SPEC-EPISODE-013: エピソード完成ユースケース


## 概要
`CompleteEpisodeUseCase`は、エピソード執筆完了時の統合的な管理ファイル更新を行うユースケースです。トランザクション制御により、複数の管理ファイルを一貫性を保って更新し、執筆プロセスの完了を記録します。

## クラス設計

### CompleteEpisodeUseCase

**責務**
- 執筆完了イベントの処理
- 複数管理ファイルの統合的更新
- トランザクション制御による一貫性保証
- サマリー情報の生成

## データ構造

### CompleteEpisodeRequest (DataClass)
```python
@dataclass(frozen=True)
class CompleteEpisodeRequest:
    project_name: str                    # プロジェクト名
    project_path: Path                   # プロジェクトパス
    episode_number: int                  # エピソード番号
    quality_score: Decimal               # 品質スコア
    plot_data: dict[str, Any] | None = None  # プロットデータ
```

**バリデーション**
- `project_name`: 空文字列不可
- `episode_number`: 正の整数必須

### CompleteEpisodeResponse (DataClass)
```python
@dataclass
class CompleteEpisodeResponse:
    success: bool                        # 処理成功フラグ
    error_message: str | None = None     # エラーメッセージ
    updated_files: list[str] = []        # 更新されたファイル一覧
    summary: dict[str, Any] = {}         # サマリー情報
    warnings: list[str] = []             # 警告一覧
```

**ファクトリメソッド**
- `success()`: 成功レスポンス作成
- `failure()`: 失敗レスポンス作成

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: CompleteEpisodeRequest) -> CompleteEpisodeResponse:
```

**目的**
エピソード執筆完了処理を統合的に実行し、関連する全ての管理ファイルを更新する。

**引数**
- `request`: 執筆完了リクエスト

**戻り値**
- `CompleteEpisodeResponse`: 処理結果

**処理フロー**
1. 完了イベントの作成
2. ドメインエンティティ（`CompletedEpisode`）の作成
3. プロットデータからの情報抽出
4. トランザクション内での全記録更新
5. サマリー情報の生成
6. 警告情報の収集
7. レスポンス構築

**更新対象ファイル**
- `話数管理.yaml`: エピソードステータス更新
- `伏線管理.yaml`: 伏線の配置・解決記録
- `キャラ成長.yaml`: キャラクター成長イベント記録
- `重要シーン.yaml`: 重要シーン情報記録
- `改訂履歴.yaml`: 改訂履歴追加
- `章別プロット/{章}.yaml`: 章別プロット更新

**例外処理**
- トランザクション失敗時：自動ロールバック
- ファイルアクセスエラー：`EpisodeCompletionError`
- バリデーションエラー：`ValueError`

## プライベートメソッド

### _create_completion_event()

**目的**
リクエスト情報から完了イベント（`EpisodeCompletionEvent`）を作成する。

**処理内容**
- 文字数の自動計算
- 完了時刻の設定
- 品質スコアの設定

### _calculate_word_count()

**目的**
指定されたエピソードの原稿ファイルから文字数を計算する。

**処理内容**
- `40_原稿/第XXX話_*.md`ファイルを検索
- フロントマターを除外して本文文字数を計算
- ファイル不存在時は0を返却

### _update_all_records_transactionally()

**目的**
トランザクション制御により複数の管理ファイルを一貫して更新する。

**処理内容**
1. トランザクション開始
2. 各リポジトリでの更新実行
   - エピソードステータス更新
   - 伏線配置・解決記録
   - キャラクター成長記録
   - 重要シーン記録
   - 改訂履歴追加
   - 章別プロット更新
3. 全て成功時にコミット
4. エラー時にロールバック

**戻り値**
- `list[str]`: 更新されたファイル名一覧（重複除去済み）

### _generate_summary()

**目的**
執筆完了処理のサマリー情報を生成する。

**生成内容**
```python
{
    "episode_number": int,              # エピソード番号
    "quality_score": float,             # 品質スコア
    "word_count": int,                  # 文字数
    "character_growth_count": int,      # キャラ成長記録数
    "important_scenes_count": int,      # 重要シーン数
    "foreshadowing_planted": int,       # 配置された伏線数
    "foreshadowing_resolved": int,      # 解決された伏線数
    "completed_at": str,                # 完了時刻（ISO形式）
}
```

### _determine_chapter()

**目的**
エピソード番号から対応する章を判定する。

**アルゴリズム**
- 10話ごとに章を分ける
- `((episode_number - 1) // 10) + 1`で計算

### _create_plot_updates()

**目的**
章別プロット更新用のデータを作成する。

**生成内容**
```python
{
    "status": "執筆済み",
    "actual_implementation": {...},     # 実際の実装内容
    "next_episode_impact": {...},       # 次回エピソードへの影響
    "improvements": {...},              # 改善点・警告
}
```

## 依存関係

### ドメイン層
- `CompletedEpisode`: 完了エピソードエンティティ
- `EpisodeCompletionEvent`: 完了イベント値オブジェクト
- `CharacterGrowthEvent`: キャラ成長イベント値オブジェクト
- `ImportantScene`: 重要シーン値オブジェクト
- `EpisodeCompletionError`: ドメイン例外

### リポジトリ
- `EpisodeManagementRepository`: 話数管理リポジトリ
- `ForeshadowingRepository`: 伏線管理リポジトリ
- `CharacterGrowthRepository`: キャラ成長リポジトリ
- `ImportantSceneRepository`: 重要シーンリポジトリ
- `RevisionHistoryRepository`: 改訂履歴リポジトリ
- `ChapterPlotRepository`: 章別プロットリポジトリ
- `CompletionTransactionManager`: トランザクションマネージャー

## 設計原則遵守

### DDD準拠
- ✅ ドメインロジックは`CompletedEpisode`エンティティに委譲
- ✅ 値オブジェクト（イベント、シーン等）の適切な使用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ トランザクションパターンによる一貫性保証

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的な例外処理
- ✅ 型安全な実装
- ✅ 不変オブジェクトの使用

## 使用例

```python
# リポジトリ群の準備
episode_repo = YamlEpisodeManagementRepository()
foreshadowing_repo = YamlForeshadowingRepository()
growth_repo = YamlCharacterGrowthRepository()
scene_repo = YamlImportantSceneRepository()
history_repo = YamlRevisionHistoryRepository()
plot_repo = YamlChapterPlotRepository()
transaction_manager = YamlCompletionTransactionManager()

# ユースケース作成
use_case = CompleteEpisodeUseCase(
    episode_repo, foreshadowing_repo, growth_repo,
    scene_repo, history_repo, plot_repo, transaction_manager
)

# 執筆完了処理実行
request = CompleteEpisodeRequest(
    project_name="sample_novel",
    project_path=Path("/path/to/project"),
    episode_number=5,
    quality_score=Decimal("85.5"),
    plot_data={"theme": "character_growth", "climax": True}
)

response = use_case.execute(request)

if response.success:
    print(f"更新されたファイル: {response.updated_files}")
    print(f"品質スコア: {response.summary['quality_score']}")
    print(f"文字数: {response.summary['word_count']}")
    for warning in response.warnings:
        print(f"警告: {warning}")
else:
    print(f"処理失敗: {response.error_message}")
```

## トランザクション設計

### ACID特性
- **Atomicity**: 全ての更新が成功するか、全てロールバック
- **Consistency**: 管理ファイル間の整合性保証
- **Isolation**: 並行実行時の分離保証
- **Durability**: 更新内容の永続化保証

### エラー時の動作
1. 任意の更新でエラーが発生
2. 自動的にロールバック実行
3. 更新前の状態に復元
4. エラー情報を含むレスポンス返却

## テスト観点

### 単体テスト
- 正常な執筆完了フロー
- 各種エラー条件での動作
- トランザクションのロールバック動作
- サマリー生成の正確性
- 文字数計算の正確性

### 統合テスト
- 実際のプロジェクトファイルでの統合処理
- 複数リポジトリとの協調動作
- トランザクションマネージャーとの連携

## 品質基準

- **一貫性**: ACID特性を満たすトランザクション処理
- **信頼性**: エラー時の安全なロールバック
- **追跡可能性**: 詳細な更新履歴とサマリー
- **保守性**: 明確な責務分離と型安全性
- **拡張性**: 新しい管理ファイルタイプへの対応
