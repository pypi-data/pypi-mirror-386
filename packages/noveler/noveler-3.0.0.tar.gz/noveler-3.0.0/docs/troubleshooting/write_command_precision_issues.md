# Write Command Precision Issues - トラブルシューティングガイド

## 概要

このガイドは、`/noveler-write` スラッシュコマンドまたはMCP経由の `write` コマンド実行時に、生成される原稿の精度が期待値より低い場合の診断手順と対処法を説明します。

## 問題の症状

以下のような症状が確認された場合、このガイドが役立ちます:

- ✗ 生成される原稿の文字数が少ない（期待: 4,000文字程度、実際: 1,000文字以下）
- ✗ プロットやキャラクター設定を無視した内容が生成される
- ✗ 文章の質が低い（単調、展開が雑、描写が不足）
- ✗ A28プロンプトシステムの5段階構造（Stage 1-5）が使用されていない

## 根本原因

**修正済み（2025-10-11）**: `IntegratedWritingUseCase` へのリポジトリ依存注入欠如により、A28詳細プロンプトシステムが使用されず、簡易YAMLフォールバックが発動していた問題。

**影響範囲**:
- スラッシュコマンド `/noveler-write` 経由の実行
- MCP経由の `noveler_write` ツール実行
- CLI直接実行 (`python -m noveler.presentation.cli.main write 1`) は影響なし

## 診断手順

### Step 1: バージョン確認

最新版を使用しているか確認してください:

```bash
# バージョン確認
python -m noveler.presentation.cli.main --version

# 期待される出力: v3.2.0以降（2025-10-11修正を含む）
```

**対処法**: 古いバージョンの場合は最新版にアップデート:
```bash
git pull origin master
pip install -e .[dev]
```

---

### Step 2: A30ガイドテンプレートの存在確認

A28プロンプトシステムは `docs/A30_執筆ガイド.yaml` に依存します。

```bash
# プロジェクトルートで実行
ls -la docs/A30_執筆ガイド.yaml
```

**期待される出力**:
```
-rw-r--r-- 1 user user 12345 Oct 11 22:00 docs/A30_執筆ガイド.yaml
```

**エラーメッセージ例**:
```
❌ A30ガイドテンプレート未発見
   検索パス1: /path/to/project/docs/A30_執筆ガイド.yaml
   検索パス2: /fallback/path/docs/A30_執筆ガイド.yaml
📝 A28プロンプトシステム使用不可 - 精度が低下します
💡 セットアップ: docs/A30_執筆ガイド.yaml を配置してください
```

**対処法**:
1. A30ガイドテンプレートをプロジェクトルートの `docs/` ディレクトリに配置
2. テンプレートが存在しない場合は、リポジトリから取得:
   ```bash
   cp /path/to/noveler/repo/docs/A30_執筆ガイド.yaml docs/
   ```

---

### Step 3: YamlPromptRepository初期化の確認

write実行時のログを確認し、YamlPromptRepositoryが正しく初期化されているかチェック:

```bash
# デバッグモードで実行
NOVELER_DEBUG=1 python -m noveler.presentation.cli.main write 1 --project-root /your/project
```

**正常な出力例**:
```
📄 A30ガイド使用: /your/project/docs/A30_執筆ガイド.yaml
```

**問題のある出力例**:
```
⚠️ YamlPromptRepository初期化失敗: FileNotFoundError: ...
📝 簡易YAMLフォールバックモードで実行します（精度低下）
```

**対処法**:
- A30ガイドテンプレートのパスを確認
- ファイルの読み取り権限を確認: `chmod 644 docs/A30_執筆ガイド.yaml`
- YAMLファイルの構文エラーを確認: `python -c "import yaml; yaml.safe_load(open('docs/A30_執筆ガイド.yaml'))"`

---

### Step 4: direct_claude_execution フラグの確認

`IntegratedWritingRequest` で `direct_claude_execution=True` が設定されているか確認:

```python
# デバッグコードを一時的に追加（server_runtime.py:1236付近）
print(f"DEBUG: direct_claude_execution = {req.direct_claude_execution}")
```

**期待される出力**:
```
DEBUG: direct_claude_execution = True
```

**問題のある出力**:
```
DEBUG: direct_claude_execution = False
```

**対処法**: 最新版にアップデート（2025-10-11修正で自動設定）

---

### Step 5: 生成されたYAMLプロンプトの確認

write実行後、生成されたYAMLプロンプトを確認:

```bash
# プロンプトファイルの確認
cat temp/json_output/episode_001_prompt.yaml
```

**正常な出力の特徴**:
- ✓ ファイルサイズ: 5KB以上（8,000文字レベル）
- ✓ `stage1:` から `stage5:` までの5段階構造
- ✓ 各ステージに詳細な `requirements:` セクション
- ✓ `prompt_templates:` セクションに変数定義

**問題のある出力の特徴**:
- ✗ ファイルサイズ: 1KB以下（数百文字レベル）
- ✗ 単純な `task_definition:` のみ
- ✗ 詳細な要件が欠落

**対処法**: Step 2-3を再確認

---

## よくある問題と対処法

### 問題1: "簡易YAMLフォールバックモード"の警告が出る

**原因**: A30ガイドテンプレートが見つからない、またはYAMLパースエラー

**対処法**:
1. A30ガイドテンプレートの配置確認（Step 2）
2. YAMLファイルの構文チェック:
   ```bash
   python -c "import yaml; print(yaml.safe_load(open('docs/A30_執筆ガイド.yaml')))"
   ```
3. エラーがある場合は、リポジトリから最新版を取得

---

### 問題2: プロンプトは詳細だが、原稿品質が低い

**原因**: Claude Code統合が無効、またはClaude APIの問題

**診断**:
```bash
# Claude Code統合の確認
echo $ANTHROPIC_API_KEY  # APIキーが設定されているか
```

**対処法**:
1. Claude APIキーを設定: `export ANTHROPIC_API_KEY=your_api_key`
2. Claude Code設定ファイルを確認: `.mcp/config.json` または `codex.mcp.json`
3. ネットワーク接続を確認

---

### 問題3: CLI直接実行では正常、スラッシュコマンドでは精度低下

**原因**: MCP経由の実行でリポジトリ注入が不足（2025-10-11修正で解決）

**対処法**:
1. 最新版にアップデート
2. `server_runtime.py` の修正確認:
   ```bash
   grep -n "yaml_prompt_repository" src/noveler/presentation/mcp/server_runtime.py
   ```
   期待される出力: `yaml_prompt_repository=yaml_repo` が存在

---

### 問題4: テスト環境でのみ精度低下

**原因**: テスト用のモックがA28プロンプトシステムをバイパス

**対処法**:
1. テストコードで `YamlPromptRepository` を正しくモック:
   ```python
   mock_yaml_repo = Mock()
   mock_yaml_repo.generate_stepwise_prompt = AsyncMock(
       return_value=Mock(
           yaml_content="... 詳細なYAML ...",
           validation_passed=True,
       )
   )
   ```
2. E2Eテストを参照: `tests/integration/test_slash_command_write_a28.py`

---

## 詳細ログの取得方法

問題の原因特定のため、詳細ログを取得する方法:

```bash
# デバッグログ有効化
export NOVELER_DEBUG=1
export NOVELER_LOG_LEVEL=DEBUG

# ログファイルへの出力
python -m noveler.presentation.cli.main write 1 --project-root /your/project 2>&1 | tee write_debug.log

# ログの確認
grep -i "yaml\|prompt\|repository" write_debug.log
```

**確認すべきログエントリ**:
- `YamlPromptRepository初期化`
- `A30ガイド使用`
- `generate_stepwise_prompt`
- `direct_claude_execution`

---

## 修正内容（2025-10-11）

### Before（バグ状態）
```python
# server_runtime.py:1151 (旧実装)
uc = IntegratedWritingUseCase()  # 依存注入なし
req = IntegratedWritingRequest(
    episode_number=ep,
    project_root=Path(...),
    # direct_claude_execution=True 未設定
)
```

### After（修正後）
```python
# server_runtime.py:1221-1240 (新実装)
# リポジトリ初期化
yaml_repo = _create_yaml_prompt_repository(project_path)
episode_repo = _create_episode_repository(project_path)
plot_repo = _create_plot_repository(project_path)

# UseCase初期化（依存注入）
uc = IntegratedWritingUseCase(
    yaml_prompt_repository=yaml_repo,
    episode_repository=episode_repo,
    plot_repository=plot_repo,
)

# Claude統合有効化
req = IntegratedWritingRequest(
    episode_number=ep,
    project_root=project_path,
    direct_claude_execution=True,  # ✅ 追加
)
```

---

## 関連ドキュメント

- **ADR-001**: Write Command Repository Injection (`docs/adr/ADR-001-write-command-repository-injection.md`)
- **A28プロンプトシステム**: `docs/A28_話別プロットプロンプト.md`
- **A30執筆ガイド**: `docs/A30_執筆ガイド.yaml`
- **E2Eテスト**: `tests/integration/test_slash_command_write_a28.py`
- **SPEC-CLI-050**: Slash Command Management (`specs/tools/cli/SPEC-CLI-050_slash_command_management.md`)

---

## サポート

問題が解決しない場合は、以下の情報を添えて報告してください:

1. バージョン情報: `python -m noveler.presentation.cli.main --version`
2. 環境情報: OS、Python版、依存パッケージ
3. 実行コマンド: 実行したスラッシュコマンドまたはMCP呼び出し
4. エラーメッセージ: 完全なログ出力
5. デバッグログ: `NOVELER_DEBUG=1` での実行結果

**報告先**: GitHub Issues または開発チャネル
