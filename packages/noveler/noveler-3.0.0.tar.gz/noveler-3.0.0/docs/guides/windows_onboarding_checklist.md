# Windows Onboarding Checklist

## 1. Prerequisites
- Windows 11 with PowerShell 5.1+ or PowerShell 7 (optional but recommended).
- Git for Windows 2.45+.
- Python 3.10+ available on PATH (`py -3 --version`).
- Optional: Windows Subsystem for Linux (WSL) if you prefer Remote-WSL workflows.

## 2. Clone & Repository Setup
1. `cd C:\Users\<you>\OneDrive\Documents`
2. `git clone <REPO_URL> "9_小説\00_ガイド"`
3. `cd 9_小説\00_ガイド`
4. (Optional) Pause OneDrive sync for the project directory during heavy Git operations.

## 3. Python Environment
- Windows PowerShell:
  - `py -3 -m venv .venv`
  - `.\\.venv\\Scripts\\Activate.ps1`
  - `pip install -e ".[dev]"` (uv が導入済みなら `uv pip install -e ".[dev]"` でも可)
- WSL bash:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -e ".[dev]"` (uv が導入済みなら `uv pip install -e ".[dev]"` でも可)

## 4. Baseline Diagnostics
- Windows: `bin\\invoke.ps1 diagnose --allow-failures`
- WSL: `bin/invoke diagnose --allow-failures`
- Windows: `bin\\invoke.ps1 test-smoke`
- WSL: `bin/invoke test-smoke`
  - Verify JSON/TXT files appear in `reports\\smoke\\`.
- Optional coverage (Windows): `bin\\invoke.ps1 test -- --cov=src/noveler --cov-report=json:b20-outputs/phase4-testing/coverage.json`
- Optional coverage (WSL): `bin/invoke test -- --cov=src/noveler --cov-report=json:b20-outputs/phase4-testing/coverage.json`

## 5. Git Verification
- `git status`
- `bin\git-noveler.ps1 status --short`
  - Confirms `core.worktree` and `GIT_DIR` align with Windows paths.

## 6. Daily Commands

**推奨**: Wrapper優先、`python -m` 直叩き禁止、`NOVELER_STRICT_PATHS=1` 推奨

- Windows: `bin\\invoke.ps1 test -- --k smoke`
- WSL: `bin/invoke test -- --k smoke`
- Windows/WSL: `bin\\invoke.ps1 lint`, `bin\\invoke.ps1 ci` (WSL: `bin/invoke lint`, `bin/invoke ci`) (replace `{sep}` with `\\` on Windows, `/` on WSL)

**Wrapper推奨理由**:
- Path Service 統一: `bin/noveler` 経由で環境変数・Path Service が確実に動作
- 直接実行リスク: `python -m noveler.presentation.cli.main` は Path Service の初期化が不完全になる可能性
- Strict Mode推奨: `NOVELER_STRICT_PATHS=1` で fallback 検出時に即座にエラー

**使用例**:
```bash
# 推奨（Windows）
bin\noveler mcp call run_quality_checks "{\"episode_number\": 1}"

# 推奨（WSL）
bin/noveler mcp call run_quality_checks '{"episode_number": 1}'

# 非推奨（Path Service初期化不完全リスク）
python -m noveler.presentation.cli.main mcp call ...
```


## 7. Troubleshooting
- If Git reports `UNC host access is not allowed`, confirm `.git` points to a local path (README instructions).
- If smoke tests fail due to missing optional packages, install extras: `pip install aiofiles uv`.
- For OneDrive lock issues, add `.git`, `reports/`, and `temp/` to OneDrive exclusions.

## 8. Feedback & Support
- Create GitHub issue with label `Release-Windows` (template provided).
- Share diagnostics bundle: attach latest `reports/smoke/*.json` and `diagnostics.log` from `bin\invoke diagnose`.
- Join Discord #updates channel for announcements.

