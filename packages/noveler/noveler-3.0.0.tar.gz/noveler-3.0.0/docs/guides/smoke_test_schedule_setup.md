# スモークテスト定期実行セットアップガイド

## 目的

Windows/WSL両環境で`bin/invoke test-smoke`を定期実行し、互換性メトリクスを週次レビューで共有する。

## 前提条件

- `scripts/diagnostics/run_smoke_suite.py` 実装済み ✅
- `bin/invoke test-smoke` コマンド動作確認済み ✅
- `reports/smoke/` ディレクトリにJSON/TXTログが保存される ✅

---

## Windows環境での設定

### 1. タスクスケジューラによる定期実行

**毎日午前2:30に実行する例：**

```powershell
# タスク作成
schtasks /Create /TN "NovelerSmokeTest" `
  /TR "pwsh -NoProfile -File C:\Users\bamboocity\OneDrive\Documents\9_小説\00_ガイド\bin\invoke.ps1 test-smoke" `
  /SC DAILY /ST 02:30 /RL LIMITED /F

# 登録内容確認
schtasks /Query /TN "NovelerSmokeTest" /V /FO LIST

# タスク削除（必要時）
schtasks /Delete /TN "NovelerSmokeTest" /F
```

### 2. 手動実行での動作確認

```powershell
# PowerShell経由
bin\invoke.ps1 test-smoke

# 結果確認
Get-ChildItem reports\smoke\ | Sort-Object LastWriteTime -Descending | Select-Object -First 2
```

---

## WSL環境での設定

### 1. cronによる定期実行

**毎日午前2:30に実行する例：**

```bash
# crontab編集
crontab -e

# 以下を追加（リポジトリパスは環境に応じて調整）
30 2 * * * cd /mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド && bin/invoke test-smoke >> /tmp/noveler-smoke-cron.log 2>&1
```

### 2. 手動実行での動作確認

```bash
# Bash経由
bin/invoke test-smoke

# 結果確認
ls -lt reports/smoke/ | head -n 3
```

---

## 週次レビュー共有フロー

### ステップ1: 最新結果の収集

```powershell
# Windows PowerShell
$latest = Get-ChildItem reports\smoke\smoke_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

```bash
# WSL Bash
latest=$(ls -t reports/smoke/smoke_*.json | head -n 1)
cat "$latest" | jq '.'
```

### ステップ2: サマリー抽出

最新のJSON結果から以下を確認：

- `summary.total_tests`: 実行テスト数
- `summary.passed`: 成功数
- `summary.failed`: 失敗数
- `summary.error`: エラー数
- `summary.duration_sec`: 実行時間
- `failures[]`: 失敗詳細（存在する場合）

### ステップ3: 週次レポート作成

以下のテンプレートで週次レビューに共有：

```markdown
## スモークテスト週次サマリー（YYYY-MM-DD）

### Windows環境
- 実行日時: YYYY-MM-DD HH:MM
- 成功/失敗: XX/XX
- 実行時間: XX.X秒
- 主な問題: なし / [issue#XXX]

### WSL環境
- 実行日時: YYYY-MM-DD HH:MM
- 成功/失敗: XX/XX
- 実行時間: XX.X秒
- 主な問題: なし / [issue#XXX]

### アクション
- [ ] 失敗ケースの調査（担当: XXX）
- [ ] パフォーマンス劣化の確認（担当: XXX）
```

---

## トラブルシューティング

### Q1: タスクスケジューラでスモークテストが失敗する

**確認項目：**
- `pwsh -NoProfile -File` の絶対パスが正しいか
- 実行ユーザーに `reports/smoke/` への書き込み権限があるか
- Python仮想環境が有効化されているか（`invoke.ps1`が`.venv`をアクティベート）

**デバッグ方法：**
```powershell
# タスクスケジューラのログ確認
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | Where-Object {$_.Message -like "*NovelerSmokeTest*"} | Select-Object -First 5
```

### Q2: WSL cronでスモークテストが失敗する

**確認項目：**
- crontab内のリポジトリパスが正しいか
- `bin/invoke`に実行権限があるか (`chmod +x bin/invoke`)
- `/tmp/noveler-smoke-cron.log` にエラーログが記録されているか

**デバッグ方法：**
```bash
# cron実行ログ確認
tail -f /tmp/noveler-smoke-cron.log
```

---

## 参考資料

- [Windows Tool Alternatives](./windows_tool_alternatives.md)
- [Windows Onboarding Checklist](./windows_onboarding_checklist.md)
- [Cross-Platform Plan](../migration/windows_wsl_cross_platform_plan.md)
