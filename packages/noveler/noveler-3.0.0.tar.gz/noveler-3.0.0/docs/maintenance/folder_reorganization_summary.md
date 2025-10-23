# フォルダ整理作業サマリー（レビュー用）

**作成日**: 2025-10-02
**目的**: クロスプラットフォーム対応後のフォルダ整理状況と今後の計画をレビュー

---

## 完了した作業

### 1. MCP関連ファイル整理 ✅
**実施内容**:
- `config/mcp/` ディレクトリを新規作成
- `config/mcp/codex.template.json` を配置（現行 `codex.mcp.json` のテンプレート化）
- `config/mcp/README.md` を作成（使用方法・注意事項を記載）

**現状**:
- 実運用ファイル（`codex.mcp.json`, `.claude.json`）は現在の場所で維持
- テンプレートとして参照・更新用に `config/mcp/` を活用

### 2. bin/README.md 更新 ✅
**実施内容**:
- OS別（Linux/WSL, Windows PowerShell）の実行方法を追記
- 実行ポリシー設定手順を明記
- `.ps1` 版と拡張子なし版の使い分けガイドを追加

### 3. キャッシュ類の洗い出しと移行 ✅
**成果物**: [cache_migration_plan.md](cache_migration_plan.md)

**洗い出し結果**:
- Ruff: `.ruff_cache/`, `config/.ruff_cache/`, `.dev/ruff_cache/`
- Import Linter: `.dev/import_linter_cache/`, `src/.import_linter_cache/`
- Hypothesis: `.hypothesis/`
- DDD: `.ddd_cache/`
- Serena: `.serena/cache/`
- WSL環境: `wsl.localhostUbuntu-22.04homebamboocity.noveler_cache/` (重複)

**移行状況**:
1. **Phase 1（低リスク）**: ✅ 完了
   - DDD Cache → `.cache/ddd/` へ移行
   - Serena Cache → 現状維持（適切に管理済み）
2. **Phase 2（要設定変更）**: ✅ 完了
   - Ruff → `config/.ruff.toml` に `cache-dir = ".cache/ruff"` 設定追加
   - Import Linter → `.cache/import-linter/` ディレクトリ作成
   - Hypothesis → `tests/conftest.py` に設定追加
3. **Phase 3（クリーンアップ）**: ⏸️ 保留
   - WSL重複キャッシュ削除は技術的課題のため保留
   - レガシーディレクトリ（`.ddd_cache/`, `.ruff_cache/`）は手動削除推奨

### 4. アーカイブ系フォルダ調査 ✅
**成果物**: [archive_migration_plan.md](archive_migration_plan.md)

**調査結果**:
- `b20-outputs/`: **現状維持推奨** (`.b20rc.yaml` で使用中、実運用)
- `b20-test/`: 存在確認済み、1ファイル（`requirements.md`）のみ

**推奨アクション**:
- 短期: `b20-outputs/` は現在の場所で運用継続
- 中長期: B20ワークフロー完了後に `archive/b20/` への移行を検討

---

## 保留・今後の作業

### 5. 資料ディレクトリの役割明文化 ✅

**対象ディレクトリ**:
- `docs/`: 23サブディレクトリ、各種ガイド・仕様書
- `specs/`: 仕様書・設計文書（SPEC-XXX-YYY形式）
- `models/`: メタデータモデル
- `templates/`: テンプレートファイル

**実施内容**:
1. `docs/README.md` 作成: 23サブディレクトリとA-number体系の説明
2. `models/README.md` 作成: データモデル定義の役割と使用例
3. `specs/README.md`, `templates/README.md` は既存のため確認のみ

---

## 完了した実装

段階的実施の進捗:
1. ✅ MCP設定整理（`config/mcp/` 作成、テンプレート配置）
2. ✅ bin/README.md更新（OS別実行手順追加）
3. ✅ キャッシュPhase 1移行（DDD Cache、Serena現状維持確認）
4. ✅ 資料ディレクトリREADME作成（`docs/`, `models/`）
5. ✅ キャッシュPhase 2移行（Ruff, Import Linter, Hypothesis設定）
6. ⏸️ Phase 3クリーンアップ（WSL重複キャッシュは保留）

---

## 今後の推奨事項

### 1. レガシーキャッシュの手動削除
以下のディレクトリは安全に削除可能:
- `.ddd_cache/` → `.cache/ddd/` へ移行済み
- `.ruff_cache/` → `.cache/ruff/` へ移行済み

### 2. WSL環境からのクリーンアップ
Windows環境での削除に課題があるため、WSL環境から以下を実行:
```bash
rm -rf wsl.localhostUbuntu-22.04homebamboocity.noveler_cache
```

### 3. b20-outputs の内部整理（中長期）
現状は実運用継続で問題なし。B20ワークフロー完了後に:
- 過去成果物のサブディレクトリ化
- `archive/b20/` への段階的移行を検討

---

## 関連ドキュメント

- [folder_structure_guidelines.md](folder_structure_guidelines.md) - 整理方針の大枠
- [cache_migration_plan.md](cache_migration_plan.md) - キャッシュ移行詳細（Phase 1-2完了、Phase 3保留）
- [archive_migration_plan.md](archive_migration_plan.md) - アーカイブ系移行詳細

---

## 完了報告

**作業完了日**: 2025-10-02

フォルダ整理の主要タスク（Section 1-6）を完了しました:
- ✅ MCP設定のテンプレート化
- ✅ bin/README.md のクロスプラットフォーム対応
- ✅ キャッシュディレクトリの統一（Phase 1-2）
- ✅ 資料ディレクトリのREADME整備
- ⏸️ WSL重複キャッシュ削除は技術的課題のため保留（手動削除推奨）
