# SPEC-REF-002: 標準プロジェクト構造移行仕様

## 1. 概要

### 1.1 目的
現在の非標準的な`scripts/`ディレクトリ構造から、Pythonコミュニティ標準の`src/`構造への移行を実施する。

### 1.2 背景
- 現状: `scripts/`直下に開発コードが配置（非標準的）
- 問題点:
  - 開発版と本番版の分離が不明確
  - MCP サーバー統合時の安全性懸念
  - CI/CD パイプライン構築の複雑化
  - 他のPythonプロジェクトとの非互換性

### 1.3 スコープ
- 影響範囲: 全モジュール（約947ファイル）
- 対象レイヤー: domain, application, infrastructure, presentation
- 除外: テストコード（tests/）は現状維持

## 2. 技術仕様

### 2.1 新ディレクトリ構造
```
00_ガイド/
├── src/                     # 開発ソースコード（新規）
│   ├── novel/               # メインパッケージ
│   │   ├── __init__.py
│   │   ├── domain/          # ドメイン層
│   │   ├── application/     # アプリケーション層
│   │   ├── infrastructure/  # インフラストラクチャ層
│   │   ├── presentation/    # プレゼンテーション層
│   │   └── main.py          # エントリーポイント
│   └── mcp_servers/         # MCPサーバー
│       └── noveler/
├── dist/                    # ビルド成果物（新規）
├── build/                   # ビルド一時ファイル（新規）
├── bin/                     # 実行スクリプト（更新）
│   ├── novel                # 本番用（デフォルト）
│   └── novel-dev            # 開発用
├── tests/                   # テスト（現状維持）
└── pyproject.toml           # プロジェクト設定（更新）
```

### 2.2 インポートパス変更
```python
# 変更前
from scripts.domain.entities.episode import Episode
from scripts.application.use_cases.create_episode import CreateEpisodeUseCase

# 変更後
from novel.domain.entities.episode import Episode
from novel.application.use_cases.create_episode import CreateEpisodeUseCase
```

### 2.3 ビルドプロセス
1. テスト実行（pytest）
2. ソースコード検証
3. `src/` → `dist/` へのコピー
4. バイトコードコンパイル（オプション）
5. ビルド情報の記録（BUILD_INFO.json）

## 3. 実装計画

### 3.1 フェーズ分割
- **Phase 1**: 基盤構築（ディレクトリ、ビルドスクリプト）
- **Phase 2**: コード移行（scripts → src）
- **Phase 3**: インポート更新（一括置換）
- **Phase 4**: 統合テスト・品質確認

### 3.2 リスク管理
| リスク | 影響度 | 対策 |
|--------|--------|------|
| インポートエラー | 高 | 段階的移行、自動テスト |
| 既存機能の破損 | 高 | scripts/をバックアップ保持 |
| MCP統合の破損 | 中 | 別途テスト環境で検証 |
| CI/CD への影響 | 低 | GitHub Actions 更新準備 |

## 4. テスト戦略

### 4.1 単体テスト
```bash
# 新構造でのテスト実行
PYTHONPATH=src pytest tests/ -v
```

### 4.2 統合テスト
- エントリーポイント動作確認（bin/novel, bin/novel-dev）
- ビルドプロセス検証（build.py）
- MCP サーバー統合確認

### 4.3 品質ゲート
- B30品質基準準拠（STRICT レベル）
- テストカバレッジ 80% 以上
- インポートエラー 0件

## 5. 成功基準

### 5.1 必須要件
- [ ] 全テスト通過（100% pass）
- [ ] ビルド成功（dist/ 生成）
- [ ] 本番用エントリーポイント動作
- [ ] 開発用エントリーポイント動作
- [ ] MCP サーバー統合維持

### 5.2 品質要件
- [ ] コード品質: STRICT レベル通過
- [ ] パフォーマンス: 現行同等以上
- [ ] 保守性: 標準構造による向上

## 6. ロールバック計画

万が一の失敗時:
1. `git checkout master` でブランチ切り替え
2. `scripts/` ディレクトリは保持されているため即座に復旧可能
3. MCP 設定の復元（必要に応じて）

## 7. 承認

- 作成者: Claude Code Assistant
- 作成日: 2025-08-28
- バージョン: 1.0.0
- ステータス: レビュー待ち

---
*この仕様書はB20 Claude Code開発作業指示書に準拠して作成されました。*
