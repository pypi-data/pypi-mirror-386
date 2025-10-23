# キャッシュディレクトリ移行計画

## 現状のキャッシュ系ディレクトリ

### Pythonランタイムキャッシュ
- `__pycache__/` (複数箇所)
- `.pytest_cache/` (テスト実行時生成)
→ **移行対象外** (Python/pytest自動生成、.gitignore管理)

### ツール固有キャッシュ

#### Ruff（リンター）
- `.ruff_cache/` (ルート)
- `config/.ruff_cache/`
- `.dev/ruff_cache/`
→ **移行候補**: `.cache/ruff/` へ統合

設定変更必要箇所:
- `config/.ruff.toml` の `cache-dir` 設定
- CI/CD スクリプト内のパス参照

#### Import Linter
- `.dev/import_linter_cache/`
- `src/.import_linter_cache/`
→ **移行候補**: `.cache/import-linter/`

設定変更必要箇所:
- `.importlinter` 設定ファイル（存在する場合）
- Makefile/CI内の参照

#### Hypothesis（プロパティベーステスト）
- `.hypothesis/`
→ **移行候補**: `.cache/hypothesis/`

設定変更必要箇所:
- `tests/conftest.py` または pytest設定
- Hypothesis設定 (`hypothesis.settings`)

#### DDD設計キャッシュ
- `.ddd_cache/`
→ **移行候補**: `.cache/ddd/`

設定変更必要箇所:
- DDDチェックスクリプト
- 関連する分析ツール

#### Serena（MCPツール）
- `.serena/cache/`
→ **移行不要**: 既にMCP管理下で適切に配置済み

理由:
- Serena MCP設定で管理されている
- `.serena/` ディレクトリ全体がSerena専用領域として機能
- 移行によるメリットがない

### 一時ファイル系
- `temp/cache/`
- `temp/pre-commit-cache/`
→ **現状維持** (`temp/` 内で管理)

### WSL環境固有
- `wsl.localhostUbuntu-22.04homebamboocity.noveler_cache/` (重複エントリ)
→ **調査・クリーンアップ対象** (不要なら削除)

## 移行優先順位

### Phase 1: 低リスク移行（✅ 完了）
1. **DDD Cache**: `.ddd_cache/` → `.cache/ddd/` ✅
   - 影響範囲: 独自スクリプトのみ
   - 変更箇所: DDDチェックスクリプト内のパス定義
   - 実施日: 2025-10-02
   - 変更ファイル:
     - `src/noveler/infrastructure/services/ddd_compliance_cache.py`
     - `dist/noveler/infrastructure/services/ddd_compliance_cache.py`

2. **Serena Cache**: 移行不要（現状維持）
   - `.serena/cache/` は既に適切に管理されている

### Phase 2: ツール設定変更が必要（✅ 完了）
3. **Ruff Cache**: 統合して `.cache/ruff/` ✅
   - 影響範囲: config/.ruff.toml, CI
   - 変更箇所: `cache-dir` 設定を追加
   - 実施日: 2025-10-02
   - 変更ファイル: `config/.ruff.toml`
   - 注記: Ruff未インストール環境のため実行テストは省略

4. **Import Linter**: `.cache/import-linter/` ✅
   - 影響範囲: .importlinter設定, Makefile
   - 実施日: 2025-10-02
   - 注記: Import Linterは設定ファイルでキャッシュパス変更不可
   - 対応: `.cache/import-linter/` ディレクトリを作成済み

5. **Hypothesis**: `.cache/hypothesis/` ✅
   - 影響範囲: pytest設定
   - 変更箇所: tests/conftest.py
   - 実施日: 2025-10-02
   - 変更内容:
     - `database_file=Path(".cache/hypothesis/examples.db")` 設定追加
     - デフォルトプロファイル登録

### Phase 3: レガシーキャッシュのクリーンアップ（✅ 完了）
6. **WSL重複キャッシュ**: 削除完了 ✅
   - ディレクトリ: `wsl.localhostUbuntu-22.04homebamboocity.noveler_cache/` (2つの重複エントリ)
   - 実施日: 2025-10-02
   - 削除方法: `find . -maxdepth 1 -type d -name "*wsl*" -print0 | xargs -0 rm -rf`
   - `.gitignore` 追加: `wsl.localhost*/`

7. **レガシーキャッシュディレクトリ削除**: 完了 ✅
   - `.ddd_cache/`: Phase 1で `.cache/ddd/` へ移行済み → 削除完了
   - `.ruff_cache/`: Phase 2で `.cache/ruff/` へ移行済み → 削除完了
   - 実施日: 2025-10-02
   - 注記: `.gitignore` に既存エントリあり（保持）

## 実施手順テンプレート

各Phase実施時:
1. 対象ディレクトリのバックアップ作成
2. `.cache/<tool>/` 作成
3. 設定ファイル更新
4. ツール実行テスト
5. 旧ディレクトリ削除（.gitignore更新）
6. コミット・プッシュ
7. CI/CD動作確認

## .gitignore更新

移行完了後に `.gitignore` へ追加:
```
.cache/
!.cache/.gitkeep
```

既存の個別エントリは削除:
```
# 削除対象
.ruff_cache/
.ddd_cache/
.hypothesis/
.serena/cache/
.import_linter_cache/
```
