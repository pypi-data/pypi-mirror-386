# SPEC-CLAUDE-002: Claude Codeエクスポートユースケース仕様書

## 📋 基本情報

- **仕様ID**: SPEC-CLAUDE-002
- **作成日**: 2025-07-28
- **対象**: Claude Codeエクスポートユースケース
- **実装優先度**: 高
- **ブランチ**: feature/SPEC-CLAUDE-002-claude-export-use-case

## 🎯 概要

ファイル保存時品質チェックシステムで検出されたエラー情報をClaude Code向けに出力するユースケース。

### ビジネス価値
- **即座のエラー修正**: ファイル保存時に自動でClaude向け情報生成
- **開発効率向上**: エラー修正時間の短縮
- **一貫性**: 統一的なエラー情報提供

## 🏗️ DDD設計

### ドメイン層

#### エンティティ
- `ClaudeIntegrationSession`（既存）
- `FileQualityCheckSession`（既存）

#### 値オブジェクト
- `ClaudeSessionId`（既存）
- `ErrorExportFormat`（既存）

#### ドメインサービス
```python
# ClaudeCodeFormatService
class ClaudeCodeFormatService:
    """Claude Code向けフォーマット変換サービス"""
    - format_errors_for_claude(sessions: list[FileQualityCheckSession])
    - generate_fix_suggestions(sessions: list[FileQualityCheckSession])
    - create_priority_ranking(sessions: list[FileQualityCheckSession])
```

### アプリケーション層

#### ユースケース
```python
# ExportErrorsForClaudeUseCase
class ExportErrorsForClaudeUseCase:
    """Claude向けエラー出力ユースケース"""
    - execute_export() -> ClaudeIntegrationSession
    - export_recent_errors() -> ClaudeIntegrationSession
    - export_file_errors(file_path: FilePath) -> ClaudeIntegrationSession
```

### インフラ層

#### リポジトリ実装
- `ClaudeCodeAdapter`（既存）
- `FileQualityCheckSessionRepository`（既存）

## 🔧 機能要件

### F001: 自動エラー出力
- **目的**: ファイル保存時の自動エラー出力
- **トリガー**: ファイル保存イベント
- **出力**: JSON + Markdown形式

### F002: 手動エラー出力
- **目的**: オンデマンドでのエラー出力
- **コマンド**: `novel claude-export`
- **フィルタ**: ファイル別、優先度別

### F003: 増分エラー出力
- **目的**: 新しいエラーのみ出力
- **対象**: 前回出力以降のエラー
- **効率**: 重複排除

## 🧪 テストケース

### テストシナリオ1: 基本エラー出力
```gherkin
Given ファイル保存時品質チェックでエラーが検出された
When Claude向けエラー出力を実行する
Then temp/claude_code_errors.jsonが生成される
And temp/claude_code_suggestions.mdが生成される
```

### テストシナリオ2: エラーなし状態
```gherkin
Given 現在エラーが検出されていない
When Claude向けエラー出力を実行する
Then 「エラーなし」状態のファイルが生成される
```

### テストシナリオ3: 増分出力
```gherkin
Given 前回出力後に新しいエラーが発生した
When 増分エラー出力を実行する
Then 新しいエラーのみが出力される
```

## 🔄 実装計画

### Phase 1: ドメインサービス実装（TDD）
1. ClaudeCodeFormatService作成
2. ユニットテスト作成（失敗）
3. 最小実装
4. リファクタリング

### Phase 2: ユースケース実装（TDD）
1. ExportErrorsForClaudeUseCase作成
2. 統合テスト作成
3. 実装
4. エラーハンドリング

### Phase 3: CLI統合
1. novel claude-exportコマンド実装
2. E2Eテスト作成
3. 動作確認

## 📊 TDD実装要件

### テスト優先事項
1. **RED**: 失敗するテストを先に作成
2. **GREEN**: 最小実装でテスト通過
3. **REFACTOR**: コード品質向上

### テストマーカー
```python
@pytest.mark.spec("SPEC-CLAUDE-002")
```

## 🎯 成功指標

- **ファイル生成**: JSON/Markdownファイルの確実な生成
- **パフォーマンス**: 1秒以内のエクスポート完了
- **Claude Code検出**: 生成ファイルをClaude Codeが読み取り可能

## 🔗 関連仕様

- [SPEC-CLAUDE-001: Claude Code連携システム](./SPEC-CLAUDE-001_claude_code_integration_system.md)
- [SPEC-FILE-001: ファイル保存時品質チェック](./SPEC-FILE-001_file_save_quality_check.md)

## 📝 実装注意事項

1. **既存システム**: ファイル保存監視システムとの統合
2. **エラーハンドリング**: Claude Code連携失敗時の適切な処理
3. **パフォーマンス**: 大量エラー時の処理効率
4. **セキュリティ**: 機密情報の出力除外
