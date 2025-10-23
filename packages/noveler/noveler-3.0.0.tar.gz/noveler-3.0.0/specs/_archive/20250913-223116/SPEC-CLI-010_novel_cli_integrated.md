# 統合CLIコマンド 仕様書

## 1. 目的
小説執筆支援システムのすべての機能を単一のコマンド`novel`から利用可能にする統合CLIインターフェースを提供する。ユーザーフレンドリーで一貫性のあるコマンド体系を実現する。

## 2. 前提条件
- Python 3.11以上
- YAMLベースのプロジェクト構造
- Git環境（一部機能）
- テキストエディタ（設定可能）

## 3. コマンド体系

### 3.1 基本構文
```bash
novel <コマンド> [サブコマンド] [引数] [オプション]
```

### 3.2 グローバルオプション
```bash
--help, -h          # ヘルプ表示
--version, -v       # バージョン表示
--verbose           # 詳細出力
--quiet, -q         # 静音モード
--config <ファイル>  # 設定ファイル指定
```

## 4. コマンド仕様

### 4.1 プロジェクト管理コマンド

#### `novel new` - 新規プロジェクト作成
**目的**: 新しい小説プロジェクトを作成

**構文**:
```bash
novel new <プロジェクト名> [--genre <ジャンル>] [--author <作者名>] [--template <テンプレート>]
```

**処理フロー**:
1. プロジェクト番号の自動採番（既存の最大番号+1）
2. プロジェクトフォルダ作成（形式: `NN_プロジェクト名`）
3. 標準ディレクトリ構造の生成
4. テンプレートファイルのコピー
5. プロジェクト設定.yamlの初期化

**標準ディレクトリ構造**:
```
NN_プロジェクト名/
├── プロジェクト設定.yaml
├── 10_企画/
├── 20_プロット/
├── 30_設定集/
├── 40_原稿/
├── 50_管理資料/
└── backup/
```

#### `novel init` - 対話的プロジェクト初期化
**目的**: 詳細な設定を対話的に行いながらプロジェクトを初期化

**構文**:
```bash
novel init [--interactive] [--from-template <名前>]
```

**対話項目**:
- プロジェクト名
- ジャンル選択
- 作者情報
- 執筆スタイル
- 目標設定

#### `novel status` - プロジェクト状態確認
**目的**: 現在のプロジェクトの進捗と設定を表示

**構文**:
```bash
novel status [--detailed] [--json]
```

**表示内容**:
- プロジェクト基本情報
- 執筆進捗（話数、総文字数）
- 最新エピソード情報
- 品質スコア統計
- 次のアクション提案

#### `novel doctor` - システム診断
**目的**: システムの問題を検出し、修復提案を行う

**構文**:
```bash
novel doctor [--repair] [--check-only]
```

**診断項目**:
- 必須ファイルの存在確認
- YAMLファイルの整合性
- 権限設定
- 依存関係
- ディレクトリ構造

### 4.2 執筆作業コマンド

#### `novel write` - 執筆作業
**目的**: エピソードの新規作成・編集を行う

**サブコマンド**:
```bash
novel write new [話数] [--title <タイトル>] [--auto] [--no-quality]
novel write edit <話数> [--editor <エディタ>]
```

**処理フロー（new）**:
1. エピソード番号の決定（指定または自動採番）
2. プロット確認（存在する場合）
3. 原稿ファイル作成
4. エディタ起動
5. 品質チェック実行（--no-quality以外）
6. 品質記録保存
7. 話数管理更新

**自動モード（--auto）**:
- プロットからの自動生成
- AI支援執筆
- テンプレート適用

#### `novel plot` - プロット管理
**目的**: マスタープロット・章別プロットの作成と管理

**サブコマンド**:
```bash
novel plot master [--edit] [--show]
novel plot chapter <章番号> [--create] [--integrate]
novel plot status [--detailed]
```

**統合機能**:
- 章別プロットの集約
- 整合性チェック
- 進捗トラッキング

#### `novel scene` - 重要シーン管理
**目的**: 感情的に重要なシーンの設計と管理

**サブコマンド**:
```bash
novel scene add <話数> --category <カテゴリ> --description <説明>
novel scene list [--category <カテゴリ>]
novel scene show <話数>
novel scene validate
```

**カテゴリ**:
- `emotional_peak`: 感情的頂点
- `turning_point`: 転換点
- `revelation`: 真実の開示
- `character_growth`: キャラ成長
- `relationship_change`: 関係性変化

#### `novel complete-episode` - エピソード完成処理
**目的**: エピソードの完成ステータス更新と関連ファイル更新

**構文**:
```bash
novel complete-episode <プロジェクト名> <話数> [--status <ステータス>] [--enhanced]
```

**更新対象**:
- 話数管理.yaml
- 伏線管理.yaml
- キャラ成長.yaml
- 重要シーン.yaml
- 品質記録.yaml

### 4.3 品質管理コマンド

#### `novel quality` / `novel check` - 品質チェック
**目的**: 原稿の品質を多角的にチェック

**構文**:
```bash
novel quality <原稿ファイル> [--auto-fix] [--level <レベル>] [--save]
novel quality --bulk [--parallel] [--report]
```

**チェック項目**:
1. **基本文章スタイル** (30%)
   - 誤字脱字
   - 重複表現
   - 不適切な言い回し

2. **物語構造** (25%)
   - 起承転結
   - テンポ
   - 場面転換

3. **キャラクター描写** (20%)
   - 一貫性
   - 魅力度
   - 成長描写

4. **世界観の一貫性** (15%)
   - 設定矛盾
   - 時系列整合性

5. **読者エンゲージメント** (10%)
   - 引き込み要素
   - ページターナー要素

**自動修正（--auto-fix）**:
- 誤字脱字の修正
- 不適切な表現の置換
- 文体の統一

#### `novel analyze` - アクセス分析
**目的**: 読者の反応とアクセスデータを分析

**構文**:
```bash
novel analyze [--update] [--report] [--period <期間>]
```

**分析内容**:
- PV/UU推移
- 離脱率分析
- 読者コメント分析
- 改善提案生成

### 4.4 公開・管理コマンド

#### `novel publish` - 公開準備
**目的**: エピソードの公開前処理

**構文**:
```bash
novel publish --episode <話数> [--platform <プラットフォーム>] [--schedule <日時>]
```

**処理内容**:
- 最終品質チェック
- フォーマット変換
- メタデータ設定
- 公開チェックリスト確認

#### `novel config` - 設定管理
**目的**: システムとプロジェクトの設定管理

**サブコマンド**:
```bash
novel config show [--all]
novel config set <キー> <値>
novel config edit [--editor <エディタ>]
```

**設定階層**:
1. システム設定（~/.novel/config.yaml）
2. プロジェクト設定（プロジェクト設定.yaml）
3. 環境変数（NOVEL_*）

### 4.5 特殊コマンド

#### `novel ai` - AI連携
**目的**: AI執筆支援機能の利用

**構文**:
```bash
novel ai suggest --context <文脈>
novel ai expand --text <テキスト>
novel ai review --episode <話数>
```

#### `novel backup` - バックアップ管理
**目的**: プロジェクトのバックアップと復元

**構文**:
```bash
novel backup create [--compress]
novel backup restore <バックアップ名>
novel backup list
```

## 5. エラーハンドリング

### 5.1 エラーレベル
1. **INFO**: 情報メッセージ（緑色）
2. **WARNING**: 警告（黄色）
3. **ERROR**: エラー（赤色）
4. **FATAL**: 致命的エラー（赤色太字）

### 5.2 エラーメッセージ形式
```
❌ [エラーレベル] エラー概要
  詳細: 具体的な問題の説明
  対処法: 推奨される解決方法
  参考: 関連ドキュメントへのリンク
```

### 5.3 共通エラー
- プロジェクト外での実行
- 必須ファイルの不在
- 権限不足
- 無効な引数

## 6. 設定ファイル

### 6.1 グローバル設定（~/.novel/config.yaml）
```yaml
editor: vscode  # デフォルトエディタ
theme: dark     # UI テーマ
language: ja    # 言語設定
logging:
  level: INFO
  file: ~/.novel/logs/novel.log
```

### 6.2 プロジェクト設定（プロジェクト設定.yaml）
```yaml
project:
  name: "小説タイトル"
  author: "作者名"
  genre: "ファンタジー"
writing:
  target_words_per_episode: 3000
  style: "ライトノベル"
quality:
  auto_check: true
  min_score: 70
```

## 7. プラグイン機構

### 7.1 プラグイン配置
```
~/.novel/plugins/
├── custom_command.py
├── quality_checker_extension.py
└── export_formatter.py
```

### 7.2 プラグインインターフェース
```python
class NovelPlugin:
    def __init__(self, cli: NovelCLI):
        self.cli = cli

    def register_commands(self, parser: ArgumentParser):
        """コマンドの登録"""
        pass

    def execute(self, args: Namespace):
        """コマンドの実行"""
        pass
```

## 8. パフォーマンス考慮事項

### 8.1 遅延インポート
- 使用されるモジュールのみインポート
- 起動時間の最小化

### 8.2 キャッシュ戦略
- YAMLファイルのメモリキャッシュ
- 品質チェック結果のキャッシュ

### 8.3 並列処理
- 一括品質チェック時の並列実行
- 大量ファイル処理の最適化

## 9. セキュリティ

### 9.1 ファイルアクセス
- プロジェクトディレクトリ外へのアクセス制限
- シンボリックリンクの適切な処理

### 9.2 外部コマンド実行
- サニタイゼーション
- インジェクション対策

## 10. 実装メモ
- メインエントリポイント: `bin/noveler`（MCPサーバー連携）
- シェルラッパー: `bin/novel`
- テスト: `tests/e2e/test_novel_cli.py`
- 作成日: 2025-07-21

## 11. 未決定事項
- [ ] Web UI連携
- [ ] リモートバックアップ
- [ ] 共同執筆機能
- [ ] 多言語対応の詳細
