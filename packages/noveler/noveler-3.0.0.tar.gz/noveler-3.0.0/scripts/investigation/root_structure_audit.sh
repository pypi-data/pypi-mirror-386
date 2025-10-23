#!/bin/bash
# File: scripts/investigation/root_structure_audit.sh
# Purpose: Phase 0.5 事前調査 - ルート構造の安全性確認
# Context: docs/proposals/root-structure-policy-v2.md に基づく実装

set -euo pipefail

REPORT_DIR="reports/investigation"
REPORT_FILE="${REPORT_DIR}/root_structure_audit_$(date +%Y%m%d_%H%M%S).txt"

mkdir -p "${REPORT_DIR}"

echo "========================================" | tee "${REPORT_FILE}"
echo "Root Structure Audit Report" | tee -a "${REPORT_FILE}"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${REPORT_FILE}"
echo "========================================" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

# 1. ユーザーデータの性質確認
echo "=== 1. User Data Investigation ===" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

for dir in 20_プロット 40_原稿 50_管理資料; do
    if [ -d "$dir" ]; then
        echo "--- $dir ---" | tee -a "${REPORT_FILE}"

        # Git履歴確認（最初の5コミット）
        echo "Git history (first 5 commits):" | tee -a "${REPORT_FILE}"
        git log --oneline --all -- "$dir" 2>/dev/null | head -5 | tee -a "${REPORT_FILE}" || echo "  No git history" | tee -a "${REPORT_FILE}"

        # ファイル数とサイズ
        echo "File count:" | tee -a "${REPORT_FILE}"
        find "$dir" -type f 2>/dev/null | wc -l | tee -a "${REPORT_FILE}" || echo "  0" | tee -a "${REPORT_FILE}"

        # サンプルファイル（最初の10個）
        echo "Sample files (first 10):" | tee -a "${REPORT_FILE}"
        find "$dir" -type f 2>/dev/null | head -10 | tee -a "${REPORT_FILE}" || echo "  None" | tee -a "${REPORT_FILE}"

        echo "" | tee -a "${REPORT_FILE}"
    else
        echo "--- $dir: NOT FOUND ---" | tee -a "${REPORT_FILE}"
        echo "" | tee -a "${REPORT_FILE}"
    fi
done

# 2. レガシーモジュールの参照確認
echo "=== 2. Legacy Module Reference Check ===" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

for module in noveler domain common models; do
    if [ -d "$module" ]; then
        echo "--- $module/ ---" | tee -a "${REPORT_FILE}"

        # ripgrepでの参照検索
        echo "Direct imports in Python code:" | tee -a "${REPORT_FILE}"
        rg "^from $module" --type py 2>/dev/null | tee -a "${REPORT_FILE}" || echo "  No direct imports found" | tee -a "${REPORT_FILE}"

        # 動的インポートの可能性
        echo "Potential dynamic imports:" | tee -a "${REPORT_FILE}"
        rg "importlib.*['\"]$module" --type py 2>/dev/null | tee -a "${REPORT_FILE}" || echo "  No dynamic imports found" | tee -a "${REPORT_FILE}"

        # __init__.py の存在確認
        if [ -f "$module/__init__.py" ]; then
            echo "  Has __init__.py" | tee -a "${REPORT_FILE}"
        else
            echo "  No __init__.py (not a package)" | tee -a "${REPORT_FILE}"
        fi

        echo "" | tee -a "${REPORT_FILE}"
    else
        echo "--- $module/: NOT FOUND ---" | tee -a "${REPORT_FILE}"
        echo "" | tee -a "${REPORT_FILE}"
    fi
done

# 3. CODEMAP.yaml 自動生成確認
echo "=== 3. CODEMAP.yaml Generation Check ===" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

echo "CI/CD workflow checks:" | tee -a "${REPORT_FILE}"
if [ -d ".github/workflows" ]; then
    grep -r "CODEMAP" .github/workflows/ 2>/dev/null | tee -a "${REPORT_FILE}" || echo "  No CODEMAP generation found in workflows" | tee -a "${REPORT_FILE}"
else
    echo "  No .github/workflows directory" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

echo "Pre-commit hook checks:" | tee -a "${REPORT_FILE}"
if [ -f ".pre-commit-config.yaml" ]; then
    grep -i "codemap" .pre-commit-config.yaml 2>/dev/null | tee -a "${REPORT_FILE}" || echo "  No CODEMAP generation in pre-commit" | tee -a "${REPORT_FILE}"
else
    echo "  No .pre-commit-config.yaml" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

# 4. pre-commit 設定ファイルの差分
echo "=== 4. Pre-commit Config Files ===" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

for f in .pre-commit-config*.yaml; do
    if [ -f "$f" ]; then
        echo "--- $f ---" | tee -a "${REPORT_FILE}"
        echo "First 20 lines:" | tee -a "${REPORT_FILE}"
        head -20 "$f" | tee -a "${REPORT_FILE}"
        echo "" | tee -a "${REPORT_FILE}"

        echo "Repo count:" | tee -a "${REPORT_FILE}"
        grep -c "^  - repo:" "$f" 2>/dev/null | tee -a "${REPORT_FILE}" || echo "  0" | tee -a "${REPORT_FILE}"
        echo "" | tee -a "${REPORT_FILE}"
    fi
done

# 5. Makefile 移行状況確認
echo "=== 5. Makefile Migration Status ===" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

if [ -f "Makefile" ]; then
    echo "Makefile targets:" | tee -a "${REPORT_FILE}"
    make -qp 2>/dev/null | grep "^[a-zA-Z]" | head -20 | tee -a "${REPORT_FILE}" || echo "  Unable to parse Makefile" | tee -a "${REPORT_FILE}"
else
    echo "  No Makefile" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

if [ -f "bin/invoke" ] || [ -f "scripts/invoke.py" ]; then
    echo "Invoke tasks available:" | tee -a "${REPORT_FILE}"
    if [ -f "bin/invoke" ]; then
        ./bin/invoke --list 2>/dev/null | head -20 | tee -a "${REPORT_FILE}" || echo "  Unable to list invoke tasks" | tee -a "${REPORT_FILE}"
    else
        python scripts/invoke.py --list 2>/dev/null | head -20 | tee -a "${REPORT_FILE}" || echo "  Unable to list invoke tasks" | tee -a "${REPORT_FILE}"
    fi
else
    echo "  No invoke system found" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

# サマリー
echo "========================================" | tee -a "${REPORT_FILE}"
echo "Audit Complete" | tee -a "${REPORT_FILE}"
echo "Report saved to: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
echo "========================================" | tee -a "${REPORT_FILE}"

echo ""
echo "Next steps:"
echo "1. Review the report at: ${REPORT_FILE}"
echo "2. Make decisions based on findings:"
echo "   - User data: Sample or personal?"
echo "   - Legacy modules: Safe to delete?"
echo "   - pre-commit: Which config to keep?"
echo "3. Proceed to Phase 1 emergency response"
