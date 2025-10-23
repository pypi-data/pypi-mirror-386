---
allowed-tools: ["mcp__noveler__*"]
argument-hint: "<command> [options]"
description: "小説執筆支援（グローバル）"
model: "claude-3-5-sonnet-20241022"
---

小説執筆支援グローバルコマンドを実行します：

$ARGUMENTS

## 使用可能コマンド

### 📝 執筆コマンド
- `write <話数> [--dry-run]` - エピソード執筆
  - 例: `/noveler write 1 --dry-run` (第1話をドライランで執筆)
  - 例: `/noveler write 3` (第3話を実際に執筆)

### 🔍 品質チェック
- `check <話数> [--auto-fix]` - 品質チェック
  - 例: `/noveler check 1` (第1話の品質チェック)
  - 例: `/noveler check 5 --auto-fix` (第5話の品質チェック + 自動修正)

### 📊 プロジェクト管理
- `status` - プロジェクト状況確認
  - 執筆済み話数、品質状況、進捗を表示

### 📖 プロット生成
- `plot <話数>` - プロット生成
  - 例: `/noveler plot 7` (第7話のプロット生成)

### 🚀 プロジェクト初期化
- `init <project-name>` - 新規プロジェクト初期化
  - 例: `/noveler init my-novel` (新規プロジェクト作成)

## 🚀 クイックスタート

```bash
/noveler init my-novel          # 新規プロジェクト作成
/noveler write 1 --dry-run      # 第1話執筆（ドライラン）
/noveler check 1                # 第1話品質チェック
/noveler status                 # 現在の執筆状況確認
```

## 📋 オプション

- `--dry-run`: テスト実行（実際のファイル生成なし）
- `--auto-fix`: 品質チェック時の自動修正有効
- `--verbose`: 詳細ログ出力

## 🔗 システム連携

このコマンドは95%トークン削減を実現するJSON変換MCPサーバーと統合されており、効率的な小説執筆ワークフローを提供します。
