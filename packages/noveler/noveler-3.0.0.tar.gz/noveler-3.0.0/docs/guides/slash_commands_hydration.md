# Slash Commands Hydration Guide

**目的**: テンプレートベースのスラッシュコマンド管理ワークフロー完全ガイド

**契約**: SPEC-CLI-050 準拠（Slash Command Management System v1.1）

**最終更新**: 2025-10-08

---

## 概要

スラッシュコマンドは `config/slash_commands.yaml` を**唯一の真実の情報源（SSOT）**として管理されます。テンプレート編集から生成、検証までの一連のワークフローを以下に示します。

---

## ワークフロー全体像

```
1. テンプレート編集
   ↓
2. Hydrate（テンプレート→YAML マージ）
   ↓
3. Build（YAML→生成物 出力）
   ↓
4. Verify（一致検証）
   ↓
5. Commit（git追加）
```

---

## Step 1: テンプレート編集

### 対象ファイル

- **`templates/slash_commands/root_commands.yaml`** - `/test*` 系ルートコマンドの雛形
- **`templates/slash_commands/noveler_commands.yaml`** - `/noveler_*` 系コマンドの雛形（将来追加予定）

### 編集例

```yaml
# templates/slash_commands/root_commands.yaml
commands:
  - name: /test
    script: bin/test
    args: ["$@"]
    description: "pytest実行（LLM要約対応）"
    permissions:
      windows:
        - "Bash(./bin/test:*)"
      wsl:
        - "Bash(bin/test:*)"
    category: testing
    tags: ["testing", "pytest"]
```

---

## Step 2: Hydrate（テンプレート→YAML マージ）

### 実行コマンド

```bash
# 基本実行（dry-run）
python scripts/setup/hydrate_slash_commands.py

# 実際にマージ実行
python scripts/setup/hydrate_slash_commands.py --apply

# buildも同時実行
python scripts/setup/hydrate_slash_commands.py --run-build
```

### 動作

1. `templates/slash_commands/*.yaml` を読み込み
2. `config/slash_commands.yaml` の既存内容とマージ
3. 重複はYAML側を優先（テンプレートは補完のみ）

### 確認

```bash
git diff config/slash_commands.yaml
```

---

## Step 3: Build（YAML→生成物 出力）

### 実行コマンド

```bash
# 基本実行（dry-run）
python scripts/setup/build_slash_commands.py --dry-run

# 実際に生成
python scripts/setup/build_slash_commands.py

# 強制上書き
python scripts/setup/build_slash_commands.py --force
```

### 生成物

1. **`.claude/settings.local.json`** - slashCommands + permissions統合
2. **`docs/slash_commands/README.md`** - 自動生成コマンド一覧

### 確認

```bash
git diff .claude/settings.local.json docs/slash_commands/README.md
```

---

## Step 4: Verify（一致検証）

### 実行コマンド

```bash
python scripts/checks/verify_slash_commands.py
```

### 検証内容

1. YAMLからdry-run生成
2. リポジトリ内の生成ファイルとdiff
3. 相違があればCIを失敗

### 成功例

```
✅ .claude/settings.local.json: 一致
✅ docs/slash_commands/README.md: 一致
検証成功: 全生成物がYAMLと一致しています
```

### 失敗例と対処

```
❌ .claude/settings.local.json: 差分あり
--- リポジトリ
+++ YAML生成
@@ -5,7 +5,7 @@
-    "/test": "bin/test"
+    "/test": "bin/test $@"

対処: config/slash_commands.yaml を修正して再生成
```

---

## Step 5: Commit（git追加）

### 推奨コミット範囲

```bash
git add config/slash_commands.yaml
git add .claude/settings.local.json
git add docs/slash_commands/README.md
git add templates/slash_commands/*.yaml  # テンプレート編集時のみ

git commit -m "feat(slash): Update slash commands (SPEC-CLI-050)"
```

---

## よくあるシナリオ

### シナリオ1: 新規コマンド追加

1. `config/slash_commands.yaml` に直接追加
2. `python scripts/setup/build_slash_commands.py`
3. `python scripts/checks/verify_slash_commands.py`
4. git commit

### シナリオ2: テンプレートから一括追加

1. `templates/slash_commands/new_category.yaml` 作成
2. `python scripts/setup/hydrate_slash_commands.py --run-build`
3. `python scripts/checks/verify_slash_commands.py`
4. git commit

### シナリオ3: 既存コマンド修正

1. `config/slash_commands.yaml` を直接編集
2. `python scripts/setup/build_slash_commands.py`
3. `python scripts/checks/verify_slash_commands.py`
4. git commit

### シナリオ4: 手動編集してしまった場合

```bash
# 1. 現在の.claude/settings.local.jsonからYAMLへ逆変換（手動）
# 2. YAMLを正として再生成
python scripts/setup/build_slash_commands.py --force

# 3. 検証
python scripts/checks/verify_slash_commands.py
```

---

## トラブルシューティング

### Q: hydrate実行時に「既存のキーが上書きされる」警告が出る

**A**: テンプレートとYAMLで同じコマンド名が存在する場合、YAML側が優先されます。意図的な上書きでない場合はテンプレート側を削除してください。

### Q: verify失敗時の確認方法

**A**: dry-run出力と現行ファイルのdiffを確認:
```bash
python scripts/setup/build_slash_commands.py --dry-run > /tmp/new_settings.json
diff /tmp/new_settings.json .claude/settings.local.json
```

### Q: CIでverify失敗する

**A**: ローカルでbuild→verifyを実行し、差分をコミット忘れていないか確認:
```bash
python scripts/setup/build_slash_commands.py
git status
```

### Q: permissions.allowの順序が変わる

**A**: 順序の違いは許容されます（set型で管理）。機能に影響はありません。

---

## CI統合

### pre-push hook例

```bash
#!/bin/bash
# .git/hooks/pre-push

python scripts/checks/verify_slash_commands.py || {
  echo "❌ Slash commands verification failed"
  echo "Run: python scripts/setup/build_slash_commands.py"
  exit 1
}
```

### GitHub Actions例

```yaml
# .github/workflows/ci.yml
jobs:
  verify-slash-commands:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify slash commands
        run: python scripts/checks/verify_slash_commands.py
```

---

## Makefileターゲット（追加予定）

```makefile
.PHONY: slash-commands-sync slash-commands-verify

slash-commands-sync:
	python scripts/setup/hydrate_slash_commands.py --run-build

slash-commands-verify:
	python scripts/checks/verify_slash_commands.py
```

---

## 参考資料

- **SPEC-CLI-050**: [specs/tools/cli/SPEC-CLI-050_slash_command_management.md](../../specs/tools/cli/SPEC-CLI-050_slash_command_management.md)
- **CLAUDE.md**: Slash Commands セクション
- **A32_執筆コマンドガイド.md**: 現行スラッシュコマンド運用サマリ

---

## 変更履歴

| 日付 | 変更内容 |
|------|---------|
| 2025-10-08 | 初版作成（SPEC-CLI-050 v1.1準拠） |
