# MessageBus運用手順書

**作成日**: 2025-09-22
**対象**: SPEC-901 MessageBus 運用担当者
**前提**: noveler CLI アクセス権限

## 📋 概要

このドキュメントはMessageBusの日常運用、監視、トラブルシューティング手順を定めます。

## 🔍 日常監視

### ヘルス状況確認
```bash
# 基本ヘルス状況
noveler bus health

# 詳細統計（DLQ含む）
noveler bus health --detailed
```

**正常な出力例**:
```
MessageBus Health Status
Processed Events: 1,250
Commands: 89 total, p95: 45.2ms, failure rate: 0.00%
Events: 1,161 total, p95: 12.3ms, failure rate: 0.34%
```

### パフォーマンス指標確認
```bash
# 詳細メトリクス表示
noveler bus metrics

# メトリクスリセット（週次推奨）
noveler bus metrics --reset
```

**注意すべき指標**:
- コマンド failure rate > 5%
- イベント failure rate > 10%
- P95 > 100ms（コマンド）
- P95 > 50ms（イベント）

## 🚨 アラート対応

### DLQ監視
```bash
# DLQエントリ確認
noveler bus list --type dlq

# DLQ詳細統計
noveler bus health --detailed
```

**DLQ発生時の対応**:
1. エラー内容の確認
2. 根本原因の特定
3. 必要に応じてリプレイ実行

### エラー種別分析
DLQ統計から頻出エラーパターンを特定し、システム改善に活用します。

```json
{
  "error_types": {
    "Connection timeout...": 5,
    "File not found...": 3,
    "Permission denied...": 2
  }
}
```

## 🔧 運用操作

### 手動フラッシュ
```bash
# フラッシュ対象の確認（ドライラン）
noveler bus flush --dry-run

# 実際のフラッシュ実行
noveler bus flush --limit 50
```

### エントリ管理
```bash
# 全エントリ一覧（テーブル形式）
noveler bus list --type all

# JSON形式でエクスポート
noveler bus list --type all --format json > bus_status.json

# 特定エントリのリプレイ
noveler bus replay a1b2c3d4
```

### 緊急時の強制リプレイ
```bash
# DLQ以外からの強制リプレイ
noveler bus replay a1b2c3d4 --force
```

## 🗂️ データ管理

### ディレクトリ構造
```
<project>/temp/bus_outbox/
├── pending/          # 配信待ちイベント
├── dlq/             # 配信失敗イベント
└── [動的ファイル]
```

### クリーンアップ（テスト環境）
```bash
# 全データ削除（注意：本番環境では実行厳禁）
rm -rf temp/bus_outbox
```

### バックアップ（本番環境推奨）
```bash
# DLQデータの定期バックアップ
cp -r temp/bus_outbox/dlq/ backup/dlq_$(date +%Y%m%d_%H%M%S)

# 統計情報のエクスポート
noveler bus health --detailed > monitoring/health_$(date +%Y%m%d_%H%M%S).log
```

## ⚙️ 設定管理

### 環境変数
- `NOVELER_DISABLE_BACKGROUND_FLUSH=1`: 背景フラッシュ無効化（テスト時）

### 設定値（BusConfig）
- `dlq_max_attempts: 5` - DLQ移行しきい値
- `max_retries: 3` - リトライ回数
- `backoff_base_sec: 0.05` - 初期バックオフ時間
- `backoff_max_sec: 0.5` - 最大バックオフ時間
- `jitter_sec: 0.05` - ジッタ時間

## 📊 監視基準値

### 正常運用時の目安
| 指標 | 正常値 | 注意 | 危険 |
|------|--------|------|------|
| コマンド失敗率 | < 1% | 1-5% | > 5% |
| イベント失敗率 | < 3% | 3-10% | > 10% |
| DLQエントリ数 | 0-5件 | 6-20件 | > 20件 |
| P95処理時間（コマンド） | < 50ms | 50-100ms | > 100ms |
| P95処理時間（イベント） | < 20ms | 20-50ms | > 50ms |

### 定期確認スケジュール
- **毎日**: ヘルス状況確認（`noveler bus health`）
- **週次**: メトリクスリセット（`noveler bus metrics --reset`）
- **月次**: DLQデータバックアップとクリーンアップ検討

## 🚑 トラブルシューティング

### よくある問題と対処法

#### 1. DLQエントリが急増
```bash
# 原因分析
noveler bus health --detailed
noveler bus list --type dlq --format json

# 対処: 根本原因修正後にリプレイ
noveler bus replay <problem_entry_id>
```

#### 2. パフォーマンス劣化
```bash
# 現状確認
noveler bus metrics

# 対処: システムリソース確認、不要プロセス停止
```

#### 3. 背景フラッシュ停止
```bash
# 症状: pending エントリが蓄積し続ける
noveler bus list --type pending

# 対処: 手動フラッシュで一時的解決
noveler bus flush

# 根本対処: アプリケーション再起動
```

#### 4. ディスク容量不足
```bash
# 確認
du -sh temp/bus_outbox/

# 対処: 古いDLQエントリの整理
find temp/bus_outbox/dlq/ -name "*.json" -mtime +30 -delete
```

## 📞 エスカレーション

以下の場合は開発チームにエスカレーション:
- DLQエントリが100件を超過
- 失敗率が24時間継続して10%を超過
- システム全体のレスポンス時間が著しく劣化
- データ破損やファイルシステム異常

## 📝 記録管理

### ログファイル
- アプリケーションログ: MessageBus関連のエラー/警告
- 運用ログ: 手動操作の実行記録
- パフォーマンスログ: 定期的なメトリクス記録

### レポート作成
月次運用レポートには以下を含める:
- 処理量統計（コマンド/イベント数）
- 平均レスポンス時間推移
- 失敗率推移
- DLQ発生傾向分析
- 実施した運用作業記録
