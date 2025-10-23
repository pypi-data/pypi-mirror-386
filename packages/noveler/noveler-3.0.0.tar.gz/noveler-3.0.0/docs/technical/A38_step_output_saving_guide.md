# A38ステップ出力保存機能ガイド

## 概要

A38執筆プロンプトガイドの各ステップ（全18ステップ）の LLM 出力を `.noveler` フォルダに自動保存する機能の技術ガイドです。

## 機能目的

- **トレーサビリティ向上**: 各ステップの実行結果を確実に記録
- **デバッグ支援**: ステップ間の依存関係と出力内容を明確化
- **品質分析基盤**: プロセス改善とパフォーマンス分析のデータ蓄積
- **実行精度向上**: ステップ単位でのエラー原因特定と修正支援

## アーキテクチャ

### 主要コンポーネント

#### 1. StepOutputManager
- **場所**: `src/noveler/domain/services/step_output_manager.py`
- **役割**: ステップ出力の保存・読み込み・管理
- **主要メソッド**:
  - `save_step_output()`: 基本的な出力保存
  - `save_structured_step_output()`: 構造化出力保存
  - `list_step_outputs()`: ファイル一覧取得
  - `load_step_output()`: 保存済み出力の読み込み
  - `cleanup_old_outputs()`: 古いファイルのクリーンアップ

#### 2. PathServiceAdapter拡張
- **場所**: `src/noveler/infrastructure/adapters/path_service_adapter.py`
- **追加メソッド**:
  - `get_noveler_output_dir()`: .noveler ディレクトリパス取得
  - `get_step_output_file_path()`: ステップ出力ファイルパス生成

#### 3. StepwiseWritingUseCase統合
- **場所**: `src/noveler/application/use_cases/stepwise_writing_use_case.py`
- **統合箇所**:
  - `_execute_single_step()`: 各ステップ実行後の自動保存
  - `_save_step_output()`: 出力データの抽出・保存ロジック

## ファイル構造

### 保存先ディレクトリ
```
プロジェクトルート/
├── .noveler/                    # A38ステップ出力専用フォルダ
│   ├── EP0001_step01_20250109103030.json   # エピソード1・ステップ1（4桁EP, 秒まで）
│   ├── EP0001_step02_20250109103115.json   # エピソード1・ステップ2
│   ├── ...
│   └── EP001_step18_20250109110530.json  # エピソード1・ステップ18
```

### ファイル命名規則
```
EP{episode_number:04d}_step{step_number:02d}_{timestamp}.json

例:
- EP0001_step01_20250109103030.json  # エピソード1・ステップ1・実行時刻（秒まで）
- EP0002_step15_20250110141245.json  # エピソード2・ステップ15・実行時刻（秒まで）
```

### JSON出力形式
```json
{
  "episode_number": 1,
  "step_number": 5,
  "step_name": "STEP05_EmotionCurveDesignerService",
  "timestamp": "2025-01-09T10:30:45+09:00",
  "llm_response": {
    "raw_content": "LLMからの生応答内容...",
    "content_length": 1234,
    "content_preview": "応答内容の最初の200文字..."
  },
  "structured_data": {
    "emotion_design": {...},
    "character_emotions": [...],
    "scene_transitions": [...]
  },
  "quality_metrics": {
    "overall_score": 0.85,
    "specific_metrics": {
      "coherence": 0.9,
      "creativity": 0.8
    }
  },
  "execution_metadata": {
    "execution_time_ms": 2500,
    "saved_at": "2025-01-09T10:30:46+09:00",
    "file_path": "/path/to/.noveler/EP0001_step05_20250109103030.json",
    "format_version": "1.0.0"
  }
}
```

## 使用方法

### 基本的な動作
StepwiseWritingUseCase 経由で A38 執筆を実行すると、自動的に各ステップの出力が保存されます。

```python
# 通常の A38 執筆実行
request = StepwiseWritingRequest(
    episode_number=1,
    project_root=Path("/path/to/project"),
    target_steps=[1, 2, 3, 4, 5]  # 実行したいステップ
)

# 実行時に自動的に .noveler フォルダに出力保存される
response = await stepwise_writing_use_case.execute(request)
```

### 手動での出力管理

#### 出力ファイル一覧取得
```python
# 全ファイル取得
all_files = await step_output_manager.list_step_outputs()

# エピソード1のファイルのみ
ep1_files = await step_output_manager.list_step_outputs(episode_number=1)

# ステップ5の全エピソードファイル
step5_files = await step_output_manager.list_step_outputs(step_number=5)
```

#### 保存済み出力の読み込み
```python
# ファイルパスを指定して読み込み
file_path = Path(".noveler/EP0001_step05_20250109103030.json")
output_data = await step_output_manager.load_step_output(file_path)

print(f"ステップ名: {output_data['step_name']}")
print(f"品質スコア: {output_data['quality_metrics']['overall_score']}")
```

#### 古いファイルのクリーンアップ
```python
# エピソード1の出力ファイルを最新5個まで保持
deleted_count = await step_output_manager.cleanup_old_outputs(
    episode_number=1,
    keep_latest=5
)
print(f"{deleted_count}個のファイルを削除しました")
```

#### 統計情報の取得
```python
# エピソード1の統計情報
stats = await step_output_manager.get_step_output_statistics(episode_number=1)

print(f"総ファイル数: {stats['total_files']}")
print(f"総サイズ: {stats['total_size_mb']}MB")
print(f"カバーしているステップ数: {stats['steps_coverage']}")
```

## /noveler write のI/O保存（LLMリクエスト/レスポンス）

### 概要
`/noveler write <episode>` 実行時に、LLMへのリクエスト/レスポンスを `.noveler` に保存する場合の命名規則です。

### 命名規則（step番号なし）
```
EP{episode_number:04d}_{timestamp}.json

例:
- EP0001_20250109103030.json  # エピソード1, 2025-01-09 10:30:30（秒まで）
```

### 取得API（PathServiceAdapter）
- 実装: `src/noveler/infrastructure/adapters/path_service_adapter.py`
- メソッド:
  - `get_write_command_file_path(episode_number: int, timestamp: str | None = None) -> Path`
    - 仕様に沿ったファイルパスを返却（タイムスタンプ省略時は自動生成）

LLMリクエスト発行直前・レスポンス受信直後に、本APIで得たパスへ JSON で保存してください。

## エラーハンドリング

### 保存失敗時の動作
- ステップ出力の保存に失敗しても、A38 執筆プロセス自体は継続されます
- 失敗は警告レベルでログに記録されます
- ファイルシステムの問題や権限不足が主な原因です

### 対処方法
1. `.noveler` ディレクトリの書き込み権限を確認
2. ディスク容量の確認
3. ログでの詳細エラー内容確認

## パフォーマンス考慮事項

### ファイルサイズ管理
- LLM 応答内容は200文字のプレビューとして保存
- 大量の structured_data がある場合は定期的なクリーンアップを推奨
- 1エピソード分（18ステップ）で平均 500KB〜2MB

### 非同期保存
- ステップ出力保存は非同期で実行され、メイン処理をブロックしません
- ファイル I/O は適切にエラーハンドリングされています

## トラブルシューティング

### よくある問題

#### 問題1: .noveler フォルダが作成されない
```bash
# 原因確認
ls -la プロジェクトルート/
# 権限確認
chmod 755 プロジェクトルート/
```

#### 問題2: ファイルが保存されない
```python
# PathService の設定確認
print(path_service.project_root())
print(path_service.get_noveler_output_dir())
```

#### 問題3: 古いファイルが蓄積される
```python
# 定期的なクリーンアップの実装
await step_output_manager.cleanup_old_outputs(
    episode_number=episode_num,
    keep_latest=10  # 最新10個を保持
)
```

## テスト

### ユニットテスト
- **場所**: `tests/unit/domain/services/test_step_output_manager.py`
- **カバレッジ**: 95%以上
- **実行方法**: `pytest tests/unit/domain/services/test_step_output_manager.py -v`

### テスト項目
- 基本的な保存・読み込み
- StructuredStepOutput 形式対応
- ファイル一覧・統計情報取得
- エラーハンドリング（無効パラメータ等）
- 非同期処理の正確性

## 今後の拡張予定

### Phase 2 予定機能
- **出力比較機能**: 同じステップの複数実行結果の比較
- **品質トレンド分析**: ステップごとの品質スコア推移可視化
- **自動レポート生成**: 全18ステップの実行サマリー自動作成
- **圧縮保存対応**: 大量データの効率的保存

### Phase 3 予定機能
- **クラウド同期**: チーム間での出力データ共有
- **機械学習統合**: 過去の出力データを活用した品質予測
- **リアルタイム監視**: ダッシュボードでの執筆進捗可視化

## 設定オプション

### 環境変数による設定
```bash
# 保存する最大ファイル数（デフォルト: 制限なし）
export NOVELER_MAX_STEP_OUTPUT_FILES=100

# 自動クリーンアップの有効化（デフォルト: 無効）
export NOVELER_AUTO_CLEANUP=true

# 保存を無効化（デバッグ用）
export NOVELER_DISABLE_STEP_OUTPUT_SAVING=false
```

---

## 関連ドキュメント

- [A38執筆プロンプトガイド](../A38_執筆プロンプトガイド.md)
- [StepwiseWritingUseCase仕様書](../../specs/SPEC-STEPWISE-WRITING-001.md)
- [PathServiceAdapter設計ガイド](./path_service_adapter_guide.md)

## 更新履歴

- **v1.0.0** (2025-01-09): 初回リリース - 基本的なステップ出力保存機能
- **v1.1.0** (予定): 出力比較・統計分析機能追加
- **v2.0.0** (予定): クラウド同期・ML統合
