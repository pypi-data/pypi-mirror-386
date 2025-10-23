#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Create virtualenv (./.venv) if missing"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate || true

echo "[2/4] Upgrade pip"
python -m pip install --upgrade pip

echo "[3/4] Install requirements (best-effort)"
if [ -f requirements/base.txt ]; then pip install -r requirements/base.txt || true; fi
if [ -f requirements/dev.txt ]; then pip install -r requirements/dev.txt || true; fi

echo "[4/4] Install dev tools"
pip install ruff mypy pytest pytest-cov pre-commit || true

if [ -f .pre-commit-config.yaml ]; then
  echo "Configure pre-commit hooks"
  pre-commit install || true
fi

echo "[done] Development environment is ready."

