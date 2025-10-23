# SPEC-CLAUDE-003: ファイル保存監視統合システム

## 概要
watchdogライブラリを使用してファイル保存を監視し、自動的にClaude向けエラーエクスポートを実行するシステム。

## 背景と課題
Phase 1で実装したClaude向けエクスポート機能を、ファイル保存と同時に自動実行することで、リアルタイムなエラー検出・修正ワークフローを実現する。

## 要件

### 機能要件
1. **ファイル監視機能**: Pythonファイル（.py）の保存を検出
2. **自動品質チェック**: ファイル保存時に品質チェックを自動実行
3. **Claude向け自動エクスポート**: エラー検出時にClaude向け情報を自動出力
4. **監視対象フィルタリング**: scriptsディレクトリ内のファイルのみ監視
5. **重複実行防止**: 短時間の連続保存に対する防止機構

### 非機能要件
1. **DDD準拠**: ドメイン駆動設計に基づく実装
2. **パフォーマンス**: ファイル保存時の遅延最小化
3. **安定性**: 監視プロセスの長時間稼働
4. **設定可能性**: 監視対象・除外ファイルの設定

## ドメインモデル設計

### エンティティ
- `FileWatchSession`: ファイル監視セッション
- `FileChangeEvent`: ファイル変更イベント
- `AutoExportTrigger`: 自動エクスポートトリガー

### 値オブジェクト
- `WatchMode`: 監視モード（continuous/oneshot）
- `FilePattern`: 監視対象ファイルパターン
- `ExportPolicy`: エクスポートポリシー

### ドメインサービス
- `FileWatcherService`: ファイル監視サービス
- `AutoExportService`: 自動エクスポートサービス
- `EventFilterService`: イベントフィルタリングサービス

### リポジトリ
- `FileWatchSessionRepository`: 監視セッション永続化

## アプリケーション層設計

### ユースケース
- `StartFileWatchingUseCase`: ファイル監視開始
- `HandleFileChangeUseCase`: ファイル変更処理
- `AutoExportOnChangeUseCase`: 変更時自動エクスポート

### インフラ層
- `WatchdogFileWatcher`: watchdogライブラリ統合
- `BackgroundTaskRunner`: バックグラウンドタスク実行
- `EventDebouncer`: イベント重複排除

## 実装仕様

### 監視対象
```
監視ディレクトリ: scripts/
対象ファイル: *.py
除外パターン:
  - __pycache__/
  - *.pyc
  - tests/
  - temp/
```

### 実行フロー
```
1. ファイル保存検出
2. デバウンス処理（500ms待機）
3. 品質チェック実行
4. エラー検出時にClaude向けエクスポート
5. 結果通知（オプション）
```

### CLI仕様
```bash
# 監視モード開始
novel watch

# 特定ディレクトリの監視
novel watch --dir scripts/domain

# 詳細ログ付き監視
novel watch --verbose

# ワンショット監視（1回のみ実行）
novel watch --oneshot
```

## テストケース

### ユニットテスト
1. **FileWatcherService**
   - ファイル変更検出テスト
   - フィルタリングテスト
   - デバウンス処理テスト

2. **StartFileWatchingUseCase**
   - 正常系: 監視開始成功
   - 異常系: 監視ディレクトリが存在しない
   - 異常系: 既に監視中の場合

### 統合テスト
1. **ファイル保存→自動エクスポート**
   - テストファイル作成→保存→エクスポート確認
   - エラーファイル修正→保存→エクスポート更新確認

### E2E/BDDテスト
```gherkin
機能: ファイル保存時の自動Claude向けエクスポート
  シナリオ: Pythonファイルの保存でエラー情報が自動エクスポートされる
    前提 ファイル監視が有効になっている
    もし scripts/domain/test.py にエラーのあるコードを保存する
    ならば 500ms以内にClaude向けエラー情報がエクスポートされる
    かつ temp/claude_export_*.json ファイルが生成される
    かつ エラー情報が最新の状態で更新される
```

## 実装計画

### Phase 2.1: ドメイン層実装
1. エンティティ・値オブジェクトの実装
2. ドメインサービスの実装
3. リポジトリインターフェースの定義

### Phase 2.2: アプリケーション層実装
1. ユースケースの実装
2. イベントハンドラーの実装
3. 設定管理の実装

### Phase 2.3: インフラ層実装
1. watchdog統合の実装
2. バックグラウンドタスクランナー
3. CLI統合

### Phase 2.4: 統合テスト・E2E実装
1. 統合テストの実装
2. BDDシナリオの実装
3. パフォーマンステスト

## 設定例

### watch_config.yaml
```yaml
file_watcher:
  watch_directories:
    - "scripts/"
  include_patterns:
    - "*.py"
  exclude_patterns:
    - "__pycache__/"
    - "*.pyc"
    - "tests/"
    - "temp/"
  debounce_interval: 500  # ms
  auto_export:
    enabled: true
    format: "json"
    output_dir: "temp/"
    priority_filter: null  # all, high, medium, low
```

## 成功基準
1. **機能完成度**: `novel watch` コマンドが正常動作
2. **自動化**: ファイル保存から1秒以内にエクスポート完了
3. **安定性**: 24時間連続監視でエラーなし
4. **品質基準**: テストカバレッジ85%以上

## 関連仕様
- SPEC-CLAUDE-002: Claude向けエラーエクスポート機能
- SPEC-QUALITY-001: 品質チェックシステム
- SPEC-CLI-001: 統合CLIコマンド
