---
spec_id: SPEC-CLAUDE-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: CLAUDE
sources: [E2E, REQ]
tags: [claude]
---
# SPEC-CLAUDE-001: Claude Code連携システム仕様書

> ステータス: Deprecated（MCP移行により後継仕様へ集約）
> 後継: SPEC-CLAUDE-CODE-001 / SPEC-CLAUDE-CODE-002 / SPEC-MCP-001
> 備考: 本仕様のCLI操作例は歴史的記述。現行はMCPツール経由の実行に置き換え。

## 📋 基本情報

- **仕様ID**: SPEC-CLAUDE-001
- **作成日**: 2025-01-27
- **更新日**: 2025-01-27
- **対象**: Claude Code連携システム
- **実装優先度**: 高
- **ブランチ**: feature/SPEC-CLAUDE-001-claude-code-integration

## 🎯 概要

リアルタイム監視システムで検出されたコードエラーをClaude Codeで効率的に修正できるようにする統合システム。

### ビジネス価値
- **開発効率向上**: エラー修正時間の50%短縮
- **学習促進**: エラーパターンからの自動学習
- **品質向上**: 一貫性のある修正基準

## 🏗️ DDD設計

### ドメイン層

#### エンティティ
```python
# ClaudeIntegrationSession
class ClaudeIntegrationSession:
    """Claude Code連携セッション"""
    - session_id: ClaudeSessionId
    - error_collection: ErrorCollection
    - integration_status: IntegrationStatus
    - export_timestamp: datetime
    - suggestion_metadata: SuggestionMetadata
```

#### 値オブジェクト
```python
# ClaudeSessionId
class ClaudeSessionId:
    """Claude連携セッション識別子"""

# ErrorExportFormat
class ErrorExportFormat:
    """エラー出力フォーマット"""
    - format_type: Literal["json", "markdown", "plain"]
    - structure_version: str

# IntegrationStatus
class IntegrationStatus:
    """連携状態"""
    - is_active: bool
    - last_export: datetime
    - error_count: int
```

#### ドメインサービス
```python
# ClaudeCodeFormatService
class ClaudeCodeFormatService:
    """Claude Code向けフォーマット変換サービス"""
    - format_errors_for_claude()
    - generate_fix_suggestions()
    - create_priority_ranking()
```

### アプリケーション層

#### ユースケース
```python
# ExportErrorsForClaudeUseCase
class ExportErrorsForClaudeUseCase:
    """Claude向けエラー出力ユースケース"""
    - execute_export(session_id, format_type)
    - create_suggestion_document()
    - update_integration_status()
```

### インフラ層

#### リポジトリ実装
```python
# JsonClaudeExportRepository
class JsonClaudeExportRepository:
    """JSON形式でのエラー出力"""

# MarkdownSuggestionRepository
class MarkdownSuggestionRepository:
    """マークダウン形式での提案書出力"""
```

## 🔧 機能要件

### F001: エラー情報構造化出力
- **目的**: Claude Codeが読み取り可能な構造化データ提供
- **入力**: 品質チェックセッション群
- **出力**: JSON形式エラー情報（`temp/claude_code_errors.json`）
- **形式**:
```json
{
  "session_id": "uuid",
  "timestamp": "2025-01-27T12:00:00Z",
  "project_root": "/path/to/project",
  "errors": [
    {
      "file_path": "src/noveler/domain/entities/episode.py",
      "line_number": 45,
      "error_type": "syntax|type|style",
      "error_code": "E999",
      "message": "構文エラー詳細",
      "claude_suggestion": "修正提案",
      "priority": "high|medium|low"
    }
  ],
  "summary": {
    "total_errors": 5,
    "by_type": {"syntax": 1, "type": 3, "style": 1},
    "by_priority": {"high": 2, "medium": 2, "low": 1}
  }
}
```

### F002: Claude向け修正提案書生成
- **目的**: 人間が読みやすい修正ガイド提供
- **出力**: Markdown形式提案書（`temp/claude_code_suggestions.md`）
- **内容**:
  - 優先度別エラー一覧
  - 具体的修正手順
  - Claude Code活用例
  - 学習ポイント

### F003: 双方向連携インターフェース
- **目的**: Claude Codeからの修正結果フィードバック
- **機能**:
  - 修正前後の品質比較
  - 修正パターンの学習
  - 効果測定

### F004: 統合CLI操作
- **目的**: 既存のnovelコマンドからの操作
- **コマンド**:
```bash
# Claude向けエラー出力
novel claude-export

# 連携状態確認
novel claude-status

# 修正結果の検証
novel claude-verify
```

## 📊 非機能要件

### N001: パフォーマンス
- エラー出力時間: 1秒以内（100エラー以下）
- ファイルサイズ: JSON 100KB以下、Markdown 50KB以下

### N002: 可用性
- 既存監視システムへの影響なし
- Claude Code未使用時でも動作継続

### N003: 拡張性
- 新しいエラータイプ対応
- 出力フォーマット追加対応

## 🧪 テストケース

### テストシナリオ1: 基本エラー出力
```gherkin
Given リアルタイム監視システムが構文エラーを検出した
When Claude向けエラー出力を実行する
Then JSON形式でエラー情報が出力される
And Markdown形式で修正提案書が生成される
```

### テストシナリオ2: 大量エラー処理
```gherkin
Given 100個以上のエラーが検出されている
When Claude向けエラー出力を実行する
Then 1秒以内に処理が完了する
And 優先度順でエラーが並べられる
```

### テストシナリオ3: エラーなし状態
```gherkin
Given 現在エラーが検出されていない
When Claude向けエラー出力を実行する
Then 「エラーなし」状態が出力される
And 品質良好メッセージが表示される
```

## 🔄 実装計画

### ✅ Phase 1: ドメイン層実装（完了）
1. ✅ エンティティ・値オブジェクト作成
   - ClaudeIntegrationSession エンティティ
   - ClaudeSessionId, ErrorExportFormat, IntegrationStatus 値オブジェクト
2. ✅ ドメインサービス設計
3. ✅ ユニットテスト作成（TDD）- 全19テスト通過

### Phase 2: アプリケーション層実装
1. ユースケース実装
2. 統合テスト作成
3. エラーハンドリング

### Phase 3: インフラ層実装
1. リポジトリ実装
2. ファイル出力機能
3. CLI統合

### Phase 4: 検証・最適化
1. E2Eテスト実行
2. パフォーマンステスト
3. 実際のClaude Code連携テスト

## 📊 TDD実装結果

### ✅ テスト結果（2025-01-27）
- **テスト総数**: 19テスト
- **成功率**: 100% (19/19)
- **カバレッジ**: ドメイン層 93.62%
- **テスト種別**:
  - ClaudeIntegrationSession: 14テスト
  - ErrorCollection: 4テスト
  - SuggestionMetadata: 1テスト

### ✅ 実装済み機能
- Claude連携セッション管理
- エラー情報の構造化
- 優先度別フィルタリング
- JSON/Markdown形式出力
- 修正時間推定
- 統計情報生成

## 📈 成功指標

- **エラー修正時間**: 50%短縮
- **修正品質**: 一発修正率80%以上
- **Claude Code活用率**: 週3回以上使用
- **学習効果**: 同種エラー再発率20%削減

## 🔗 関連仕様

- SPEC-FILE-001: ファイル保存時品質チェック（アーカイブ済み。復旧時は specs/archive/ を参照）
- SPEC-STARTUP-001: 自動起動システム（アーカイブ済み。復旧待ち）

## 📝 実装注意事項

1. **既存システムとの整合性**: リアルタイム監視システムのインターフェースを変更しない
2. **ファイル競合回避**: 複数プロセスからの同時出力制御
3. **セキュリティ**: 機密情報の出力除外
4. **Claude Code非依存**: Claude Code使用しない場合でも正常動作

## 🏷️ テストマーカー

すべてのテストには以下のマーカーを付与：
```python
@pytest.mark.spec("SPEC-CLAUDE-001")
```
