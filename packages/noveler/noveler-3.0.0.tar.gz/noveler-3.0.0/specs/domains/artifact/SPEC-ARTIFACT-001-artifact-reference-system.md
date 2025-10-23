---
spec_id: SPEC-ARTIFACT-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-15
category: ARTIFACT
sources: [REQ]
tags: [artifact, reference, mcp, prompt_optimization]
---
# SPEC-ARTIFACT-001: アーティファクト参照システム実装仕様

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-ARTIFACT-001 |
| 仕様名 | アーティファクト参照システム実装仕様 |
| バージョン | 1.0.0 |
| 作成日 | 2025-01-09 |
| 最終更新 | 2025-09-15 |
| 作成者 | Claude Code |
| レビュー担当 | システム設計者 |
| 承認者 | プロジェクト責任者 |

## 概要

### 目的

`/noveler write`コマンド実行時にエピソードプロットが原稿生成プロンプトに含まれない問題を解決し、プロンプトサイズの大幅削減を実現するPass-by-Reference（参照渡し）システムを実装する。

### 背景

#### 問題の詳細
1. 原稿生成プロンプトにプロットが含まれない問題（整合性低下）
2. プロンプトサイズとトークン消費の問題（制限抵触）
3. スケーラビリティの問題（詳細度・話数の増加に伴う膨張）

### 解決策

SHA256ベースのコンテンツアドレス管理による参照渡しシステムを実装し、以下を実現する：

- プロンプトには短い参照ID（`artifact:abc123`形式）のみを含める
- LLMは必要に応じて`fetch_artifact`ツールでコンテンツをオンデマンド取得
- 80%以上（実測87.4%以上）のプロンプト削減を達成

## 機能要件

### FR-001: アーティファクトストレージ機能

#### FR-001-001: コンテンツアドレス管理
- 要件: SHA256ハッシュベースのコンテンツ識別
- 形式: `artifact:{12文字のハッシュ}`（例: `artifact:abc123def456`）
- 一意性: 同一コンテンツは同じアーティファクトIDを生成

#### FR-001-002: ハイブリッドストレージ
- メモリキャッシュ + `.noveler/artifacts/` へのJSON永続化
- メモリにない場合は永続化ストレージから読み込み
- ディレクトリ例:
  ```
  .noveler/
  └── artifacts/
      ├── abc123def456.json
      └── ...
  ```

#### FR-001-003: メタデータ管理
- 必須: `artifact_id`, `content_type`, `created_at`, `size_bytes`
- 任意: `source_file`, `description`, `tags`

### FR-002: MCPツール機能

#### FR-002-001: fetch_artifact ツール
- 機能: 参照IDからコンテンツを取得
- 引数: `artifact_id` 必須、`section?`, `format?`, `project_root?`
- 戻り値例:
```json
{
  "success": true,
  "artifact_id": "artifact:abc123def456",
  "content": "...",
  "section": null,
  "format": "text",
  "metadata": {"size_bytes": 1024, "content_type": "text", "source_file": "/path/to/file.md"},
  "instructions": "アーティファクト 'artifact:abc123def456' の全コンテンツを取得しました"
}
```

#### FR-002-002: list_artifacts ツール
- 機能: 利用可能なアーティファクト一覧を表示
- 引数: `project_root?`
- 戻り値: `total_artifacts`, `artifacts[]` を含む

### FR-003: プロンプト統合機能

#### FR-003-001: prepare_plot_data 修正
- プロットをアーティファクト化し、参照IDと取得手順を含むプロンプトを生成
- セッションデータに `plot_artifact_id` を保存

#### FR-003-002: write_manuscript_draft 修正
- アーティファクト参照を前提とした執筆プロンプトを生成
- セッションデータに `plot_artifact_id` を保存

### FR-004: セクション指定部分取得
- JSON/YAML/Markdownのセクション抽出をサポート
- 例: `fetch_artifact artifact:abc123 --section="characters"`

## 非機能要件

### NFR-001: パフォーマンス
- 削減率: 80%以上（実測87.4%）
- 応答時間: 取得2秒以内（1MB以下）/ 一覧1秒以内（100個以下）

### NFR-002: 可用性
- 破損ファイル時はnull返却とログ記録
- 既存セッション互換・段階的移行

### NFR-003: セキュリティ
- プロジェクト境界のアクセス制御・パス検証
- 保存の原子性、ハッシュ検証、I/Oリトライ

## 設計仕様（抜粋）

### アーキテクチャ
```
Application: JSONConversionServer (MCP Tools)
  ├─ fetch_artifact / list_artifacts
  ├─ prepare_plot_data (modified)
  └─ write_manuscript_draft (modified)
Domain: ArtifactStoreService (store/fetch/list)
Infra: Memory Cache + .noveler/artifacts/*.json
```

### データモデル
```python
@dataclass
class ArtifactMetadata:
    artifact_id: str
    content_type: str
    created_at: str
    size_bytes: int
    source_file: str | None = None
    description: str | None = None
    tags: dict[str, str] | None = None
```

## テスト

### 統合テスト
- JSONConversionServer 統合（ツール登録、非同期実行、エラー時レスポンス）

### E2Eテスト
- `tests/e2e/test_artifact_reference_workflow.py`
  - prepare_plot_data → write_manuscript_draft 完全ワークフロー
  - fetch_artifact/list_artifacts 検証
  - 削減率80%以上を確認

## 受入基準（要約）
- 削減率80%以上、参照プロンプト生成、fetch/list動作、整合性担保

## 更新履歴

| バージョン | 日付 | 変更内容 | 担当者 |
|-----------|------|----------|--------|
| 1.0.0 | 2025-01-09 | 初版作成 | Claude Code |
| 1.0.1 | 2025-09-15 | 現用に復帰（フロントマター付与、E2E対応記述更新） | bamboocity |

