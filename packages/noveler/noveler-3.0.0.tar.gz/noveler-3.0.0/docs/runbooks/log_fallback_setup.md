# 運用ログフォールバック設定手順

**目的**: OneDrive や共有ディスク上での `rename()` 失敗に備え、`SafeRotatingFileHandler` のフォールバック先と保持方針を運用環境に適用する。

---

## 1. 事前確認
- サービス実行ユーザー（例: `noveler`）がフォールバック先ディレクトリを書き込み可能かを確認。
- 既存ログローテーション（logrotate / systemd-journal 等）との衝突がないかをチェック。

## 2. ディレクトリ準備
```bash
sudo mkdir -p /var/log/noveler/fallback
sudo chown noveler:noveler /var/log/noveler/fallback
sudo chmod 750 /var/log/noveler/fallback
```

## 3. 環境変数設定
- サービスユニット（例: systemd）または `.env` に以下を追加：
```
NOVEL_LOG_DIR=/var/log/noveler
NOVEL_LOG_FALLBACK_DIR=/var/log/noveler/fallback
NOVEL_LOG_FALLBACK_RETENTION_DAYS=14
```
- CI やテストランナーには `NOVEL_LOG_FALLBACK_RETENTION_DAYS=7` 程度を推奨。

## 4. デプロイ後の確認
1. サービス再起動後に `/var/log/noveler` と `/var/log/noveler/fallback` の新規ファイルが生成されるかを確認。
2. 権限エラーが出ていないか `journalctl` やアプリケーションログを確認。
3. `SafeRotatingFileHandler` メッセージが発生していない場合でも、フォールバックディレクトリが存在することを確認（予備運用）。

## 5. 定期メンテナンス
- 週次でフォールバック先のディスク使用量を確認。保持日数は `NOVEL_LOG_FALLBACK_RETENTION_DAYS` で調整可能。
- 退避ログが運用監視対象の場合は、logrotate など既存仕組みに取り込む。

## 6. トラブルシューティング
| 症状 | 対応 |
| --- | --- |
| `SafeRotatingFileHandler: PermissionError during rotation` が繰り返し表示 | フォールバック先の権限を再確認。OneDrive 側の同期排他も発生していないか確認。 |
| フォールバック先に書き込めない | SELinux / AppArmor ポリシー、マウントオプションを確認。 |
| フォールバックが不要 | `NOVEL_LOG_FALLBACK_DIR` を未設定にすると OS のテンポラリに退避。完全に無効化したい場合は共有ディスクではなくローカルストレージへ `NOVEL_LOG_DIR` を移動。 |

---

**Last Updated**: 2025-10-13  
**Maintainer**: Operations Team

