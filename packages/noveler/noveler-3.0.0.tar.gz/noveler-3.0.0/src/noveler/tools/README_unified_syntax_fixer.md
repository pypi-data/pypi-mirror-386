# 統合構文エラー修正ツール

## 概要

`unified_syntax_fixer.py`は、Pythonファイルの構文エラーを自動的に検出・修正する統合ツールです。
複数の修正スクリプトの機能を統合し、使いやすいコマンドラインインターフェースを提供します。

**Phase 3統合完了**: 以下の修正機能が統合されました：
- `enhanced_unmatched_paren_fixer.py`: 高度な括弧修正機能
- `syntax_error_fixer.py`: 基本的な構文エラー修正機能
- `syntax_fixer_ddd.py`: DDD設計原則とアーキテクチャ

**2025/8/15 pre-commit統合完了**: B30品質作業指示書準拠の自動修正システムが統合されました：
- pre-commit時の自動修正実行
- B30ワークフロー統合モード
- 段階的品質レベル対応

## 特徴

- 🔍 **自動検出**: 様々な構文エラーパターンを自動的に検出
- 🔧 **安全な修正**: 構文エラーがないファイルは変更しない
- 🎯 **複数モード**: 安全/通常/積極的な修正モードを選択可能
- 📁 **一括処理**: ディレクトリ内のすべてのPythonファイルを処理
- ✅ **事前確認**: ドライランモードで修正内容を事前に確認可能

## インストール

```bash
# scriptsディレクトリ内に配置済み
cd scripts/tools/
```

## 使用方法

### 基本的な使い方

```bash
# カレントディレクトリの構文エラーをチェック
python unified_syntax_fixer.py --check

# 特定のファイルを修正
python unified_syntax_fixer.py path/to/file.py

# ディレクトリ内のすべてのファイルを修正
python unified_syntax_fixer.py scripts/

# ドライラン（実際に修正せず確認）
python unified_syntax_fixer.py --dry-run
```

### 修正モード

#### 1. **SAFE（安全）モード**
```bash
python unified_syntax_fixer.py --mode safe
```
- バックアップファイル（.bak）を作成
- 最も保守的な修正のみ実行

#### 2. **NORMAL（通常）モード**（デフォルト）
```bash
python unified_syntax_fixer.py --mode normal
```
- 標準的な修正を実行
- バックアップなし

#### 3. **AGGRESSIVE（積極的）モード**
```bash
python unified_syntax_fixer.py --mode aggressive
```
- 複数のエラーを順次修正
- 最大5回まで修正を試行

#### 4. **CHECK（チェックのみ）モード**
```bash
python unified_syntax_fixer.py --check
# または
python unified_syntax_fixer.py --mode check
```
- 構文エラーのチェックのみ
- ファイルは変更しない

#### 5. **B30_WORKFLOW（B30統合）モード** ⭐新機能
```bash
python unified_syntax_fixer.py --b30-workflow
# または
python unified_syntax_fixer.py --mode b30_workflow
```
- B30品質作業指示書準拠のワークフロー実行
- 品質ゲートチェック統合
- チェックリスト形式レポート生成
- project-toolsエイリアス対応

### pre-commit自動修正統合 ⭐新機能

#### 自動修正システム（2025/8/15統合完了）
```bash
# Git コミット時に自動実行される修正フロー
git commit -m "your changes"

# 実行される内容:
# 1. unified-auto-syntax-fix: 統合構文エラー自動修正
# 2. b30-quality-auto-fix: B30統合品質チェック＆自動修正
```

#### 手動での統合品質チェック
```bash
# 全ファイル対象の品質チェック＆自動修正
pre-commit run --all-files

# 個別フック実行
pre-commit run unified-auto-syntax-fix    # 統合構文エラー自動修正
pre-commit run b30-quality-auto-fix       # B30統合品質チェック＆自動修正
```

### オプション

| オプション | 説明 |
|-----------|------|
| `--check` | 構文エラーのチェックのみ実行 |
| `--dry-run` | 実際に修正せず、修正可能な箇所を表示 |
| `--mode {safe,normal,aggressive,check}` | 修正モードを指定 |
| `--no-recursive` | サブディレクトリを処理しない |
| `-h, --help` | ヘルプを表示 |

## 対応エラーパターン

1. **unmatched ')'** - 閉じ括弧の不一致
2. **unexpected indent** - 不正なインデント
3. **invalid syntax** - 構文エラー（if/for/while文のコロン不足など）
4. **'(' was never closed** - 開き括弧が閉じられていない
5. **perhaps you forgot a comma** - カンマ不足

## 使用例

### プロジェクト全体のチェック

```bash
# プロジェクト全体の構文エラーをチェック
python unified_syntax_fixer.py . --check

# 結果例：
# 🔍 150 ファイルを処理中...
# ❌ 5 ファイルにエラーが見つかりました:
#   • domain/services/example.py: Line 45: unmatched ')'
#   • tests/test_sample.py: Line 23: unexpected indent
#   ...
```

### 安全な修正の実行

```bash
# まずドライランで確認
python unified_syntax_fixer.py scripts/ --dry-run

# 問題なければ安全モードで修正
python unified_syntax_fixer.py scripts/ --mode safe

# 結果例：
# 🔍 50 ファイルを処理中...
# 🔧 修正済み: scripts/domain/services/example.py
# 📊 結果:
#   • チェック: 50 ファイル
#   • 修正: 3 ファイル
```

### 単一ファイルの修正

```bash
# エラーのあるファイルを修正
python unified_syntax_fixer.py broken_file.py

# 修正できない場合はエラーメッセージを表示
# ❌ broken_file.py: 修正失敗 - Line 10: invalid syntax
```

## 注意事項

- 修正前に必ずバックアップを作成することを推奨
- 修正後は必ずコードの動作を確認してください
- 複雑な構文エラーは手動での修正が必要な場合があります
- `--mode safe`を使用してバックアップを自動作成できます

## トラブルシューティング

### 修正が失敗する場合

1. `--dry-run`で修正内容を確認
2. `--mode aggressive`で積極的な修正を試行
3. それでも失敗する場合は手動で修正

### パフォーマンスの問題

大規模なプロジェクトでは`--no-recursive`オプションを使用して、
ディレクトリごとに処理することを推奨します。

## ライセンス

プロジェクトのライセンスに準拠
