# SPEC-QUALITY-008: 全話品質チェック機能 仕様書

## SPEC-QUALITY-012: 一括品質チェック


## 1. 目的
プロジェクトの全エピソードを一括で品質チェックし、各話の品質スコアを記録・分析することで、執筆者の品質向上を支援する機能を提供します。

## 2. 前提条件
- プロジェクトが存在し、複数のエピソードが含まれている
- 品質チェック機能が実装済みである
- 品質記録ファイル（品質記録_AI学習用.yaml）の仕様が定義済み
- 統合CLIコマンドが実装済みである

## 3. 主要な振る舞い
### 3.1 全話品質チェック実行
- 入力: プロジェクト名、オプション（範囲指定、並列実行など）
- 処理:
  - 指定プロジェクトの全エピソードを取得
  - 各エピソードに対して品質チェックを実行
  - 品質スコアを計算し、品質記録に保存
  - 品質向上トレンドを分析
  - 問題のある話を特定
- 出力: 品質チェック結果レポート、品質記録更新

### 3.2 品質記録管理
- 入力: エピソード情報、品質スコア
- 処理:
  - 品質記録ファイルを読み込み
  - 新しい品質データを追加
  - 品質履歴を更新
  - 品質トレンドを計算
- 出力: 更新された品質記録

### 3.3 品質レポート生成
- 入力: 品質チェック結果
- 処理:
  - 全話の品質スコアを集計
  - 品質向上トレンドを分析
  - 問題のある話を特定
  - 改善提案を生成
- 出力: 品質レポート

## 4. 入出力仕様
### 4.1 入力
```python
@dataclass
class BulkQualityCheckRequest:
    project_name: str
    episode_range: Optional[Tuple[int, int]] = None  # (start, end)
    parallel: bool = False
    include_archived: bool = False
    force_recheck: bool = False
```

### 4.2 出力
```python
@dataclass
class BulkQualityCheckResult:
    project_name: str
    total_episodes: int
    checked_episodes: int
    average_quality_score: float
    quality_trend: QualityTrend
    problematic_episodes: List[int]
    improvement_suggestions: List[str]
    execution_time: float
    success: bool
    errors: List[str]
```

## 5. エラーハンドリング
- **プロジェクト存在しない**: `ProjectNotFoundError`
- **エピソードが存在しない**: `NoEpisodesFoundError`
- **品質チェック実行失敗**: `QualityCheckFailedError`
- **品質記録保存失敗**: `QualityRecordSaveError`
- **ファイルアクセス権限なし**: `FilePermissionError`

## 6. パフォーマンス要件
- レスポンスタイム: 10話あたり1秒以内
- 並列実行: 最大4並列で実行可能
- メモリ使用量: 1GB以内（大規模プロジェクトでも）
- 中断・再開: 長時間実行時の中断・再開機能

## 7. セキュリティ考慮事項
- ファイルアクセス権限の適切な確認
- 品質記録データの整合性保証
- 並列実行時のデータ競合回避
- 一時ファイルの適切な削除

## 8. CLIインターフェース
```bash
# 基本的な全話品質チェック
novel quality bulk <project_name>

# 範囲指定での品質チェック
novel quality bulk <project_name> --range 1-10

# 並列実行での品質チェック
novel quality bulk <project_name> --parallel

# 強制再チェック
novel quality bulk <project_name> --force

# 詳細レポート生成
novel quality bulk <project_name> --report detailed

# アーカイブ済みエピソード含む
novel quality bulk <project_name> --include-archived
```

## 9. 実装チェックリスト
- [ ] BulkQualityCheckService の実装
- [ ] QualityHistoryService の実装
- [ ] 品質記録管理機能の実装
- [ ] 品質レポート生成機能の実装
- [ ] エラーハンドリングの実装
- [ ] 並列実行機能の実装
- [ ] CLIオプションの実装
- [ ] パフォーマンス要件の確認
- [ ] セキュリティ考慮事項の実装
- [ ] 型定義の完全性確認
- [ ] テストケース作成
- [ ] ドキュメント更新
- [ ] コードレビュー

## 10. 実装完了状況（2025年7月22日更新）

### 10.1 エンティティ実装
- **BulkQualityCheck** (`domain/entities/bulk_quality_check.py`)
  - ✅ 全話品質チェックエンティティ（完全実装済み）
  - ✅ プロジェクト名、範囲指定、並列実行フラグ
  - ✅ アーカイブ含む、強制再チェックオプション

- **QualityRecord** (`domain/entities/bulk_quality_check.py`)
  - ✅ 品質記録エンティティ（完全実装済み）
  - ✅ エピソード番号、品質スコア、カテゴリスコア
  - ✅ タイムスタンプ管理

- **QualityHistory** (`domain/entities/bulk_quality_check.py`)
  - ✅ 品質記録履歴エンティティ（完全実装済み）
  - ✅ 品質記録の追加・管理
  - ✅ 品質トレンド計算（線形回帰）
  - ✅ 問題エピソード特定機能

### 10.2 値オブジェクト実装
- **QualityTrend** (`domain/entities/bulk_quality_check.py`)
  - ✅ 品質トレンド値オブジェクト（完全実装済み）
  - ✅ トレンド方向（改善/安定/低下）
  - ✅ 傾き値、信頼度レベル

### 10.3 ドメインサービス実装
- **BulkQualityCheckService** (`domain/services/bulk_quality_check_service.py`)
  - ✅ 全話品質チェックサービス（完全実装済み）
  - ✅ 逐次実行機能
  - ✅ 並列実行機能（ThreadPoolExecutor使用、最大4並列）
  - ✅ 品質履歴管理統合
  - ✅ 改善提案生成ロジック

### 10.4 リクエスト/レスポンス実装
- **BulkQualityCheckRequest** (`domain/services/bulk_quality_check_service.py`)
  - ✅ 全話品質チェックリクエスト（完全実装済み）
  - ✅ プロジェクト名、エピソード範囲
  - ✅ 並列実行、アーカイブ含む、強制再チェックフラグ

- **BulkQualityCheckResult** (`domain/services/bulk_quality_check_service.py`)
  - ✅ 全話品質チェック結果（完全実装済み）
  - ✅ チェック統計（総数、完了数、平均スコア）
  - ✅ 品質トレンド、問題エピソードリスト
  - ✅ 改善提案、実行時間、エラー情報

### 10.5 CLI統合
- **novel quality --bulk** (`main/novel.py`)
  - ✅ 全話品質チェックコマンド（実装済み）
  - ✅ 範囲指定オプション（--range）
  - ✅ 並列実行オプション（--parallel）
  - ✅ 強制再チェックオプション（--force）
  - ✅ レポート形式指定（--report）

- **実装状況**:
  - ✅ プロジェクト検証
  - ✅ 範囲パース処理
  - ✅ エピソードファイル検索
  - ✅ 品質チェック実行（モック実装）
  - ✅ 結果レポート表示
  - ⚠️ 実際のBulkQualityCheckService統合は未完了

### 10.6 エラーハンドリング
- ✅ NoEpisodesFoundError（実装済み）
- ✅ プロジェクト検証エラー（実装済み）
- ✅ 範囲指定エラー（実装済み）
- ✅ 実行時エラーキャッチ（実装済み）

### 10.7 テスト実装
- ✅ ユニットテスト（`tests/unit/domain/test_bulk_quality_check.py`）
- ✅ 統合テスト（`tests/integration/test_bulk_quality_check_integration.py`）

### 10.8 パフォーマンス達成状況
- ✅ 並列実行: 最大4並列（目標達成）
- ✅ 実行時間計測機能（実装済み）
- ⚠️ 10話あたり1秒以内の目標は環境依存

### 10.9 今後の改善点
- CLIコマンドとBulkQualityCheckServiceの実統合
- 品質記録の永続化（YAMLファイルへの保存）
- より高度な改善提案生成アルゴリズム
- 中断・再開機能の実装
- 詳細レポート生成機能の充実

---

**最終更新**: 2025年7月22日
**作成者**: 品質管理システム開発チーム
**バージョン**: 1.1
**承認**: 実装完了・仕様更新済み
