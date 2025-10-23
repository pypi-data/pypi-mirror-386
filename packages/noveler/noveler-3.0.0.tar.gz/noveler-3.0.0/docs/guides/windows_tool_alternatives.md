# Windows 向け外部ツール代替ガイド

## 目的
- GNU parallel や cron といった Unix 固有ツールを利用せずに、Windows ネイティブ環境でも同程度の運用体験を再現する。
- `make` 非依存の `bin/invoke` / `bin/invoke.ps1` と組み合わせて、クロスプラットフォームの自動化フローを維持する。

## GNU parallel の代替手段

**選択肢 1: PowerShell 7 (`ForEach-Object -Parallel`)**
```powershell
# 例: JSON シナリオを並列で検証する
$jobs = Get-Content scenarios.json | ConvertFrom-Json
$jobs | ForEach-Object -Parallel {
    & bin\invoke.ps1 test -- -k $_.marker
} -ThrottleLimit 4
```
- PowerShell 7 以上で使用可能。`-ThrottleLimit` で同時実行数を制御する。
- 既存の Bash スクリプトと同じ引数を渡せるよう `bin\invoke.ps1` を経由する。

**選択肢 2: `Start-ThreadJob` + `Receive-Job`**
```powershell
$jobs = @()
foreach ($marker in @('smoke', 'unit', 'integration')) {
    $jobs += Start-ThreadJob -ScriptBlock { param($m) & bin\invoke.ps1 test -- -k $m } -ArgumentList $marker
}
Wait-Job $jobs | Out-Null
Receive-Job $jobs | Tee-Object -FilePath logs\parallel-tests.log
```
- PowerShell 5.1 でも利用できる。ログの集約やエラー確認を `Receive-Job` で行う。

## cron の代替手段

**Windows タスク スケジューラ (`schtasks`) を利用する**
```powershell
$taskName = 'NovelerNightly'
$command  = "pwsh -NoProfile -File `"$pwd\\bin\\invoke.ps1`" ci"
schtasks /Create /TN $taskName /TR $command /SC DAILY /ST 01:00 /RL LIMITED /F
```
- `/SC` で実行間隔を指定（`DAILY`, `HOURLY`, `WEEKLY` など）。
- `schtasks /Query /TN NovelerNightly /V /FO LIST` で登録内容を確認できる。
- OneDrive 配下で実行する場合は `Start in` パスを UNC (`\\wsl.localhost\\...`) に合わせるとロック競合を避けやすい。

**補足: 登録済みタスクの削除**
```powershell
schtasks /Delete /TN NovelerNightly /F
```

## 運用ガイドライン
- 並列実行や定期実行では先に `bin\invoke.ps1 --list` で利用可能タスクを確認する。
- `NOVELER_CACHE_ROOT` が UNC パスを指していることを `bin\invoke.ps1 diagnose` などで事前に確認し、OneDrive 配下にキャッシュを作らない。
- 外部ツールが未インストールの場合は `invoke lint`・`invoke impact-audit` のログに `[skip]` メッセージが出るため、必要に応じてインストール方針を決める。

## 環境診断
- `bin/invoke.ps1 diagnose`（または `bin/invoke diagnose`）で Python / キャッシュ / git / 代表コマンドの動作をまとめて検証できます。
  - スモークテストは `bin/invoke.ps1 test-smoke` あるいは `python scripts/diagnostics/run_smoke_suite.py` で実行できます。結果は `reports/smoke/` に保存されます。
  - Task Scheduler 例: `schtasks /Create /TN NovelerSmoke /TR "pwsh -NoProfile -File bin\invoke.ps1 test-smoke" /SC DAILY /ST 02:30 /F`
  - 解除は `schtasks /Delete /TN NovelerSmoke /F`
  - WSL 側から実行する場合は `crontab -e` で `0 3 * * * cd $HOME/9_小説/00_ガイド && ~/bin/invoke test-smoke >>$HOME/noveler_smoke.log 2>&1` を追加してください。
  - JSON で結果を取得したい場合は `bin/invoke.ps1 diagnose --json` を利用してください。
  - 失敗時は終了コード1になるため、タスク スケジューラや `schtasks` と組み合わせて定期的なヘルスチェックが可能です。
- 手動で確認する場合は `python scripts/diagnostics/check_env.py --allow-failures --no-commands` のように呼び出せます。

## Git ラッパーの設定
- PowerShell: `bin/git-noveler.ps1` は `NOVELER_GIT_DIR`（既定: `$HOME/.git-noveler`）と `NOVELER_WORK_TREE`（既定: プロジェクトルート）を利用して `git --git-dir=... --work-tree=...` を実行します。引数がなければ `git status --short` を表示します。
  - 例: `pwsh -NoProfile -File bin/git-noveler.ps1 pull`、`pwsh -NoProfile -File bin/git-noveler.ps1 log -5`。
  - `$PROFILE` に `Set-Alias Use-NovelerGit (Join-Path $PWD 'bin/git-noveler.ps1')` を追記すると呼び出しが簡単になります。
- WSL / Bash: `bin/git-noveler` も同様に `NOVELER_GIT_DIR` / `NOVELER_WORK_TREE` を参照します。`chmod +x bin/git-noveler` のうえ `ln -sf "$(pwd)/bin/git-noveler" ~/bin/git-noveler` で PATH に追加できます。
  - UNC 経由で OneDrive を利用する場合は `export NOVELER_WORK_TREE=\\wsl.localhost\\Ubuntu-22.04\\home\\bamboocity\\.noveler_worktree` のように設定してください。
- `scripts/diagnostics/setup_git_worktree.ps1` / `.sh` を併用すると `core.worktree` の設定と検証 (`git status`) まで自動実行できます。

## 参考資料
- Microsoft Docs: [PowerShell ForEach-Object -Parallel](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/foreach-object)
- Microsoft Docs: [Start-ThreadJob](https://learn.microsoft.com/powershell/module/threadjob/start-threadjob)
- Microsoft Docs: [schtasks](https://learn.microsoft.com/windows-server/administration/windows-commands/schtasks)

## Git リポジトリ認識の選択肢
- 最も簡単なのは VS Code の Remote - WSL で `~/9_小説/00_ガイド` を開き、WSL 側の bare リポジトリ (`~/.git-noveler`) をそのまま利用する方法です。
- Windows 側でソース管理を行いたい場合は、次の手順で bare リポジトリを複製します。
  1. WSL で `git clone --bare ~/.git-noveler /mnt/c/Users/bamboocity/.git-noveler-win` を実行。
  2. Windows 側で `.git` を `gitdir: C:/Users/bamboocity/.git-noveler-win` に書き換える。
  3. `git --git-dir C:\Users\bamboocity\.git-noveler-win config --bool core.bare false`。
  4. `git --git-dir C:\Users\bamboocity\.git-noveler-win config core.worktree "C:\Users\bamboocity\OneDrive\Documents\9_小説\00_ガイド"`。
  5. `bin\git-noveler.ps1` で `status` を確認し、VS Code を再起動する。
- UNC (`\wsl$` / `\wsl.localhost`) を Git ディレクトリに指定すると Windows Git がブロックするため、必ず上記のどちらかを選んでください。