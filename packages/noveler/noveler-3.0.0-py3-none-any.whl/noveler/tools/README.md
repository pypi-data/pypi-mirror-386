# scripts/tools ディレクトリ

DDD準拠システム移行に伴う、ツール整理・統合後のディレクトリ構成

## 🏗️ DDD準拠メインシステム

### ファイル保存時品質チェック
```bash
# DDD準拠リアルタイム監視システム
python scripts/main/file_save_watcher_main.py
```
**場所**: `scripts/main/file_save_watcher_main.py`
**特徴**: エンティティ・ドメインサービス・ユースケース・アダプターによる堅牢な設計

## 🔧 ツール（手動実行・CI/CD用）

### 個別ファイル品質チェック
```bash
# 詳細品質チェック（DDD準拠）
python scripts/tools/file_quality_check.py <ファイル> --fix

# 軽量構文チェック
python scripts/tools/simple_file_check.py <ファイル>
```

### 用途
- **手動デバッグ**: 個別ファイルの詳細分析
- **CI/CD統合**: バッチ処理での品質チェック
- **Git hook**: コミット時の最終確認

## 📁 レガシーツール

### legacy/ フォルダ
移行前の非DDD準拠ツールを保管。互換性確保とリファレンス用。

```
legacy/
├── file_save_watcher.py          # 旧ファイル監視システム
├── background_file_watcher.py    # 旧バックグラウンド監視
└── start_file_watcher.sh         # 旧起動スクリプト
```

## 🎯 推奨使用方法

### 開発時
1. **DDD準拠システム**: `python scripts/main/file_save_watcher_main.py`
2. **個別確認**: `python scripts/tools/file_quality_check.py target.py --fix`

### CI/CD
1. **バッチチェック**: `python scripts/tools/file_quality_check.py *.py --quiet`
2. **Git hook**: `.git/hooks/pre-commit-file-check`（既存）

### デバッグ
1. **詳細分析**: `python scripts/tools/file_quality_check.py problem_file.py`
2. **構文のみ**: `python scripts/tools/simple_file_check.py problem_file.py`

## 🔄 移行完了項目

- ✅ DDD準拠メインシステム実装完了
- ✅ 既存ツールのlegacy移動完了
- ✅ 新旧システムの使い分け明確化
- ✅ ドキュメント整備完了

## 🚀 今後の方針

- **メインシステム**: DDD準拠システムを標準使用
- **ツール**: 特定用途での補完的使用
- **レガシー**: 段階的廃止予定（互換性維持期間あり）
