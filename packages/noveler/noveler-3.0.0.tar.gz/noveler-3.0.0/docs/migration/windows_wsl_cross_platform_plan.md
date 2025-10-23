# Windows / WSL 両対応移行計画書

## 1. 背景
- 現行プロジェクトは WSL 上の Bash / GNU ツール前提で環境構築・テストを行っている。
- Windows ネイティブ環境でも同一フローを再現したいが、スクリプトやパス検出に WSL 固有前提が残っている。
- 既存ユーザーの多くは WSL ワークフローを継続利用しているため、後方互換性を確保した段階的リリースが求められる。

## 2. 目的
- Windows と WSL の双方で主要コマンド (`noveler`, `bin/test`, `make` 相当) を同じ手順で実行できる状態を整える。
- 環境差異に起因する不具合を最小化し、構築・検証・運用ドキュメントを一本化する。
- Bash / PowerShell の二重メンテナンスを避け、共通 Python 実装を軸に保守コストを抑える。

## 3. 適用範囲
- CLI ラッパーおよび補助スクリプト (`bin/*`, `scripts/*`, `Makefile` 関連)。
- Claude Code 環境検出・パス解決など OS 依存ロジックを含む `src/noveler/infrastructure`。
- README や `docs/guides`, `docs/migration` など開発ドキュメント。

## 4. 成功指標 (Definition of Done)
1. Windows 11 PowerShell / WSL Ubuntu 双方で次を実行し成功する：
   - `noveler --help`
   - `python scripts/run_pytest.py -k smoke`
   - `python scripts/install_global_command.py --dry-run`
2. 主要スクリプトが `sys.executable` 明示で Python を起動していることを `git grep` と診断スクリプトで確認できる。
3. README / クイックスタートに Windows と WSL の手順差異およびワークツリー設定手順が明記されている。
4. 診断スクリプト (`scripts/diagnostics/check_env.py`) で環境判定・`core.worktree` 状況・代表コマンドの実行結果・キャッシュ配置が確認できる。

## 5. リスクと対応
- **スクリプト二重化による保守負荷** → Python 実装を共通化し、必要最小限のシェルラッパーに留める。
- **環境差異によるテスト失敗** → スモークテストを両環境で必ず実行し、CI への組み込みを検討。
- **外部ツール依存 (GNU parallel, cron 等)** → Windows では代替手段をドキュメント化し、利用可否を選択可能にする。
- **OneDrive との競合** → テスト・ビルドキャッシュは WSL 側 (`~/.noveler_cache`) に退避し、同期対象から切り離す。

## 6. 対応戦略

### 6.1 プラットフォーム判定ユーティリティの共通化
- `src/noveler/infrastructure/utils/platform.py` を新設し、`platform.system()` と環境変数から Windows / WSL / Linux / macOS を判定。
- `claude_code_session_integration.py` など WSL 固有パスを参照しているモジュールを新ユーティリティ経由に差し替える。
- `GlobalCommandInstaller` 等の Windows 固有パスを扱うコンポーネントでも共通ユーティリティを利用し、安全なパス変換を行う。

### 6.2 スクリプトの Python 一本化とラッパー最小化
- `bin/test`, `bin/install.sh`, `bin/create-project` など Bash スクリプトを Python 実装へ段階的に置き換え、WSL/Windows 共通コードを提供。
- 外部エントリポイントとして PowerShell (.ps1) / Bash ラッパーが必要な場合のみ薄いラッパーを提供し、内部では共通 Python モジュールを呼び出す。
- すべての Python スクリプトで `sys.executable` を使用し、`python3`, `pip3` など OS 依存呼び出しを排除。
- `scripts/tooling/` 配下にクロスプラットフォーム向けユーティリティ（例: `test_runner.py`）を集約し、`bin/test`・`bin/test.ps1` などの薄いラッパーから共通コードを呼び出す。

### 6.3 `make` 代替のハブスクリプト整備
- `scripts/tooling/invoke.py`（仮称）を用意し、`make test` / `make lint` 等の代表ターゲットを Python から実行できるハブを提供。
- Windows で `make` が見つからない場合の案内を README に追記し、利用者が迷わないようにする。
- Makefile は WSL / Linux 向けに維持するが、内部処理は共通 Python 関数へ委譲する。

### 6.4 外部ツール依存の棚卸しと代替案
- `pyproject.toml` やドキュメントで推奨している GNU parallel / cron などを洗い出し、Windows では PowerShell Scheduled Task や `ForEach-Object -Parallel` などの代替を提示。
- ツールが存在しない場合はスキップまたはフォールバックできる実装を追加する。

### 6.5 ドキュメント整備
- README、`docs/guides/quick_start.md` 等に Windows ネイティブ環境構築手順（Python 仮想環境、PATH 設定、PowerShell プロファイル編集）を追記。
- 本計画書と TODO.md を連携させ、進捗管理を一元化する。

### 6.6 検証とモニタリング
- `scripts/diagnostics/check_env.py` を整備し、Python バージョン・キャッシュ配置・git `core.worktree`・代表コマンド（`bin/invoke --list` / `bin/noveler --help` など）の動作ログを収集できるようにした。`--json` 出力で CI 監視にも利用可能。
- `bin/invoke diagnose` / `bin/invoke.ps1 diagnose` から診断スクリプトをワンコマンドで呼び出せるようにし、Slash コマンドや Codex CLI での実行も統一。
- `scripts/diagnostics/run_smoke_suite.py` を新設し、`bin/invoke test-smoke` で `pytest -k smoke` を共通のロギング形式（JSON/TXT）で実行できるようにした。Task Scheduler / cron からの定期実行を想定し、README で `schtasks` / `cron` サンプルを提示。
- Windows Git との連携パターンを整理し、VS Code は Remote - WSL で開く方法と、`git clone --bare ~/.git-noveler /mnt/c/Users/<name>/.git-noveler-win` → `.git` の `gitdir` 書き換え → `core.bare=false` / `core.worktree=<Windows path>` 設定という Windows 側複製案を README に記載。
- `scripts/tooling/cache_root.ensure_cache_root` を再利用して Hypothesis / pytest / mypy / ruff / pip / uv / import-linter のキャッシュを `NOVELER_CACHE_ROOT` 配下へ自動収束させ、OneDrive 直下に生成されないようにした。
- Git bare リポジトリ向けに `bin/git-noveler`（Bash）/`bin/git-noveler.ps1`（PowerShell）を追加し、`--git-dir` / `--work-tree` を固定して `git status` を既定動作にした。PATH（WSL `~/bin` / PowerShell `$PROFILE`）へ追加する手順はガイドに記載。
- 併せて `scripts/diagnostics/setup_git_worktree.ps1` / `.sh` を更新し、UNC/WSL パスを指定して `core.worktree` を設定した後に `git status` を実行するフォローアップ手順を明文化した。

### 6.7 ロールアウト計画
- **Phase 0**: プラットフォーム判定ユーティリティ導入と主要モジュール差し替え。
- **Phase 1**: `bin/test` / `bin/install` の Python 化と README 更新。
- **Phase 2**: `make` 代替ハブ導入、外部ツール代替案の実装、キャッシュ移行スクリプトの整備。
- **Phase 3**: 診断スクリプト整備と両環境スモークテスト構築、Git ラッパー提供。
- 各フェーズ完了時に WSL / Windows のスモークテストを実施し、問題なければ次フェーズへ進む。

## 7. 実行ロードマップ
| フェーズ | 主要タスク | 成果物 |
| --- | --- | --- |
| Phase 0 | プラットフォーム判定ユーティリティ実装、`claude_code_session_integration` 差し替え | `utils/platform.py`、コードレビュー |
| Phase 1 | Python ベースの共通ランナー整備、`sys.executable` 置換、README 更新 | 新 CLI モジュール、更新済み README |
| Phase 2 | `make` 代替ハブ、外部ツール代替案、キャッシュ集約スクリプト整備 | `scripts/tooling/invoke.py`、キャッシュガイド、タスクスケジューラ手順書 |
| Phase 3 | 診断スクリプト・Git ラッパー整備、スモークテスト自動化、ドキュメント最終整備 | `scripts/diagnostics/check_env.py`、`setup_git_worktree.ps1/.sh`、検証レポート |

## 8. マイルストーン
- M1: Phase 0 完了（週次レビューで承認）。
- M2: Phase 1 完了後、Windows ユーザー初期フィードバックを収集。
- M3: Phase 2 完了後、クロスプラットフォーム運用手順を公開。
- M4: Phase 3 完了で DoD 達成、TODO.md の該当項目をクローズ。

## 9. 進捗管理
- TODO.md の「Cross-Platform Compatibility」セクションでタスク単位の進捗を追跡。
- 週次で WSL / Windows のスモークテスト結果と未解決の環境差異をレビュー。

## 10. 付録
- 関連ドキュメント:
  - `README.md`
  - `docs/guides/quick_start.md`
  - `docs/migration/novel_to_noveler.md`
  - `config/novel_config.yaml`
  - `docs/migration/windows_release_prep_summary.md`
- 想定される追加タスク:
  - PowerShell プロファイル (`$PROFILE`) への PATH/alias 設定スクリプト化
  - OneDrive 同期によるロック・遅延問題の調査
  - Git Bash / MSYS2 利用者向け補足ガイド

## 11. 残作業と TODO 連携
- **Phase 0-1**: 判定ユーティリティ・共通ランナー・Windows ドキュメント整備は完了済み（TODO.md 参照）。
- **Phase 2**: `invoke` ハブ / 外部ツール代替 / キャッシュ集約スクリプトは 2025-10-02 に完了。残タスクは Phase 3 以降に移行する。
- **Phase 3（進行中）**:
  - `bin/invoke diagnose` を基点にした診断スモークの定期実行サイクル（Windows / WSL）を構築する。
  - Git ラッパー・診断ドキュメントを活用し、初回実行手順とフィードバックループを週次レビューに取り込む。
- **リリース準備**: 段階的ロールアウト方針と既存ユーザーへの影響評価を仕上げ、`TODO.md` の「Cross-Platform Compatibility」で残タスクを追跡する。