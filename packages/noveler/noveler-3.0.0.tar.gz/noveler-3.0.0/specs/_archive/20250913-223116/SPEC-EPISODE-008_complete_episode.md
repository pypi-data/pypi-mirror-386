# SPEC-EPISODE-008: 執筆完了処理 仕様書

## SPEC-EPISODE-012: エピソード完成


## 1. 目的
執筆完了時に必要な管理ファイルの更新を自動化し、執筆者の負担を軽減しつつ、物語の構造管理を強化する。

## 2. 前提条件
- 原稿ファイル（Markdown）が完成済み
- 品質チェックが実行済み（品質スコア取得可能）
- 章別プロットファイルが存在する（キャラ成長・重要シーン情報）
- 各種管理YAMLファイルが所定の場所に存在

## 3. 主要な振る舞い

### 3.1 執筆完了イベントの処理
**入力**:
- エピソード番号
- 品質スコア（品質チェック結果から）
- プロットデータ（章別プロットから）

**処理**:
1. 話数管理.yamlの更新
   - ステータス: `draft` → `completed`
   - 完了日: 現在日付
   - 品質スコア: 入力値
   - 文字数: 原稿から自動計算

2. 伏線管理.yamlの更新
   - 仕込んだ伏線: ステータスを `planted` に
   - 回収した伏線: ステータスを `resolved` に
   - 話数リストへの追加

3. キャラ成長.yamlの更新
   - プロットデータから成長イベントを転記
   - 原稿から検出した成長イベントを追加（オプション）

4. 重要シーン.yamlの更新
   - プロットデータから重要シーンを転記
   - 感情的高まりを検出して追加（オプション）

5. 改訂履歴.yamlへの記録
   - 執筆完了イベントの記録
   - タイムスタンプと関連メタデータ

6. 章別プロットテンプレート.yamlの更新
   - ステータス: `planning` → `執筆済み`/`推敲済み`/`公開済み`
   - 実際の実装内容の記録（計画との差分）
   - 次話への影響の記録
   - 改善点・学習点の記録
   - 伏線管理の詳細更新（仕込み済み確認、予期しない追加、回収記録）

**出力**:
- 更新されたファイルのリスト
- 更新内容のサマリー

### 3.2 トランザクション管理
- 全ファイルの更新は原子的に実行
- 失敗時は全てロールバック
- バックアップファイルの自動作成

### 3.3 検証とエラーハンドリング
- 必須ファイルの存在確認
- YAMLスキーマ検証
- 重複エントリの防止
- 具体的なエラーメッセージ

## 4. ドメインモデル

### 4.1 エンティティ
- `CompletedEpisode`: 完了したエピソードの集約ルート
- `CharacterGrowthRecord`: キャラクター成長記録
- `ImportantSceneRecord`: 重要シーン記録
- `ForeshadowingRecord`: 伏線管理記録

### 4.2 値オブジェクト
- `EpisodeCompletionEvent`: 執筆完了イベント
- `CharacterGrowthEvent`: キャラ成長イベント
- `ImportantScene`: 重要シーン
- `ForeshadowingStatus`: 伏線ステータス（planted/resolved）

### 4.3 ドメインサービス
- `EpisodeCompletionService`: 執筆完了処理の調整
- `PlotDataExtractor`: プロットデータからの情報抽出
- `ManuscriptAnalyzer`: 原稿からの自動検出（将来拡張）

## 5. 技術仕様

### 5.1 リポジトリインターフェース
```python
class EpisodeManagementRepository:
    def update_episode_status(self, episode_number: int, status: str, metadata: dict) -> None

class ForeshadowingRepository:
    def update_foreshadowing_status(self, foreshadowing_id: str, status: str, episode: int) -> None

class CharacterGrowthRepository:
    def add_growth_event(self, character: str, episode: int, event: CharacterGrowthEvent) -> None

class ImportantSceneRepository:
    def add_important_scene(self, episode: int, scene: ImportantScene) -> None

class ChapterPlotRepository:
    def update_chapter_plot_status(self, chapter: str, episode: int, updates: dict) -> None
```

### 5.2 ユースケース
```python
class CompleteEpisodeUseCase:
    def execute(self, request: CompleteEpisodeRequest) -> CompleteEpisodeResponse
```

### 5.3 統合ポイント
- novel.py CLIコマンド: `novel complete EPISODE_NUMBER [--auto-commit]`
- 品質チェックシステムとの連携
- プロット管理システムとの連携

## 6. 非機能要件

### 6.1 パフォーマンス
- 全ファイル更新を5秒以内に完了
- メモリ使用量を最小限に抑制

### 6.2 信頼性
- トランザクション保証
- 自動バックアップ
- ロールバック機能

### 6.3 保守性
- 明確なエラーメッセージ
- ログ出力
- 拡張可能な設計

## 7. 将来の拡張性
- AI/MLベースの自動検出機能
- 読者反応データとの連携
- 統計分析機能の追加

## 8. 実装完了状況（2025年7月22日更新）

### 8.1 基本実装
- **ファイル**: `scripts/main/complete_episode.py`, `scripts/management/complete_episode.py`
- **完成度**: 完全実装済み
- **機能**:
  - エピソード執筆完了処理
  - ステータス管理（執筆済み、推敲済み、公開済み）
  - 品質チェック実行（オプション）
  - WritingPhaseの自動進行
  - 執筆記録の保存

### 8.2 拡張実装（品質記録活用システム統合版）
- **ファイル**: `scripts/main/complete_episode_enhanced.py`
- **完成度**: 完全実装済み
- **追加機能**:
  - 品質記録活用システムとの統合
  - 学習データの自動記録
  - 改善提案の生成・表示
  - 品質トレンド分析
  - 話数管理.yamlの自動同期

**拡張オプション**:
- `--writing-time`: 執筆時間の記録
- `--revision-count`: 修正回数
- `--feedback`: ユーザーフィードバック
- `--environment`: 執筆環境
- `--audience`: ターゲット読者層
- `--goal`: 執筆目標
- `--show-suggestions`: 改善提案を表示
- `--show-trend`: 品質トレンドを表示

### 8.3 DDD準拠実装
- **ファイル**: `scripts/application/use_cases/complete_episode_use_case.py`
- **完成度**: 完全実装済み
- **特徴**:
  - トランザクション管理による一貫性保証
  - 6つの管理ファイルの統合的更新
  - エラー時の安全なロールバック
  - リポジトリパターンによる実装

**更新対象ファイル**:
1. 話数管理.yaml - ステータス、品質スコア、文字数
2. 伏線管理.yaml - 伏線の設置・回収記録
3. キャラ成長.yaml - キャラクター成長イベント
4. 重要シーン.yaml - 重要シーンの記録
5. 改訂履歴.yaml - 完了イベントの履歴
6. 章別プロット.yaml - 実装結果の反映

### 8.4 統合サービス
- `QualityTrendAnalysisService`: 品質トレンド分析
- `ImprovementSuggestionService`: 改善提案生成
- `LearningDataIntegrationService`: 学習データ統合
- `EpisodeManagementSyncService`: 話数管理同期
- `CompletionTransactionManager`: トランザクション管理

### 8.5 CLIコマンド
```bash
# 基本コマンド
novel complete EPISODE_NUMBER [--status STATUS]

# 拡張コマンド（推奨）
novel complete-episode-enhanced PROJECT_NAME EPISODE_NUMBER [OPTIONS]
```
