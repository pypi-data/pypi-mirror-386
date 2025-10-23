# Cross-Platform bin/invoke Wrapper

## Problem

Windows 環境で `bash bin/invoke build` を実行すると "Python" だけ表示されて終了する。

### Root Cause

```bash
# bash bin/invoke の実行トレース
+ PYTHON_BIN=/c/Users/bamboocity/AppData/Local/Microsoft/WindowsApps/python3
+ exec /c/Users/.../python3 /c/Users/.../invoke.py --help
Python  # ← Windows Store stub が "Python" と出力して終了
```

**原因:**
1. `command -v python3` が Windows Store 版の Python ストブ（リダイレクタ）に解決される
2. このストブは Python をインストールするよう促すだけで、実際の Python ではない
3. 結果として "Python" という文字列だけが表示される

## Solution

### 1. bash スクリプト修正（bin/invoke）

**優先順位:**
1. `py -3` launcher（Windows 推奨）
2. `python3`（Store stub でないことを検証）
3. `python`（フォールバック）

**実装:**
```bash
if [[ -z "${PYTHON_BIN}" ]]; then
  # Windows: Prefer 'py' launcher over 'python3' to avoid Windows Store stub
  if command -v py >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v py)"
    # Use py launcher with -3 flag
    exec "${PYTHON_BIN}" -3 "${ROOT_DIR}/scripts/tooling/invoke.py" "$@"
  elif command -v python3 >/dev/null 2>&1; then
    # Verify python3 is not Windows Store stub
    if python3 --version >/dev/null 2>&1; then
      PYTHON_BIN="$(command -v python3)"
    fi
  fi

  # Fallback to 'python' if nothing else works
  if [[ -z "${PYTHON_BIN}" ]] && command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  fi

  if [[ -z "${PYTHON_BIN}" ]]; then
    echo "bin/invoke: Python executable not found. Set \$PYTHON or install Python 3.8+." >&2
    exit 1
  fi
fi
```

### 2. Windows ネイティブラッパー追加（bin/invoke.cmd）

**目的:** Git Bash なしで Windows CMD/PowerShell から直接実行可能にする

**実装:**
```cmd
@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

set "PYTHON_BIN="
if not "%PYTHON%"=="" (
    set "PYTHON_BIN=%PYTHON%"
) else (
    where py >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_BIN=py -3"
    ) else (
        where python3 >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_BIN=python3"
        ) else (
            where python >nul 2>&1
            if !errorlevel! equ 0 (
                set "PYTHON_BIN=python"
            ) else (
                echo bin/invoke.cmd: Python executable not found. >&2
                exit /b 1
            )
        )
    )
)

%PYTHON_BIN% "%ROOT_DIR%\scripts\tooling\invoke.py" %*
```

## Usage

### Git Bash / WSL
```bash
bash bin/invoke build
bash bin/invoke test
bash bin/invoke --help
```

### Windows CMD / PowerShell
```cmd
bin\invoke.cmd build
bin\invoke.cmd test
bin\invoke.cmd --help
```

### Direct Python (クロスプラットフォーム)
```bash
py -3 scripts/tooling/invoke.py build
python3 scripts/tooling/invoke.py build
```

## Verification

```bash
# Git Bash
$ bash bin/invoke --help
usage: invoke.py [-h] [--list] ...

# Windows CMD
> bin\invoke.cmd --help
usage: invoke.py [-h] [--list] ...
```

## Related

- **Issue:** Windows Store Python stub problem
- **Fix Location:** `bin/invoke` (Line 12-16)
- **Alternative:** `bin/invoke.cmd` (Windows native wrapper)
- **Contract:** CLAUDE.md - クロスプラットフォーム対応原則
