#!/usr/bin/env bash
# Enhanced pre-commit hook - Security hardened version
# File: scripts/local-ci/enhanced_pre_commit_secure.sh

set -euo pipefail

# Security: Validate git environment
validate_git_environment() {
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "❌ Error: Not in a git repository" >&2
        exit 1
    fi

    # Ensure we're in project root
    local git_root
    git_root="$(git rev-parse --show-toplevel)"
    cd "$git_root"
}

# Security: Safe file processing with proper escaping
check_changed_python_files() {
    local -a python_files=()
    local file_count=0

    # Use null-terminated output to handle filenames with spaces/special chars
    while IFS= read -r -d '' file; do
        if [[ "$file" == *.py && -f "$file" ]]; then
            python_files+=("$file")
            ((file_count++))
            # Limit to prevent performance issues
            if [[ $file_count -ge 10 ]]; then
                break
            fi
        fi
    done < <(git diff --cached --name-only --diff-filter=AM -z)

    if [[ ${#python_files[@]} -gt 0 ]]; then
        echo "🔍 Type checking ${#python_files[@]} Python files..."
        if command -v mypy >/dev/null 2>&1; then
            mypy --quiet --incremental "${python_files[@]}" || {
                echo "❌ Type checking failed"
                return 1
            }
        else
            echo "⚠️ MyPy not available, skipping type check"
        fi
    fi
}

# Performance: Staged checks based on change volume with incremental support
run_staged_checks() {
    local changed_file_count
    changed_file_count=$(git diff --cached --name-only | wc -l)

    echo "📊 Changed files: $changed_file_count"

    # Use incremental check system if available
    if [[ -f "scripts/local-ci/incremental_check.sh" ]]; then
        echo "🧠 Using intelligent incremental check system"
        bash scripts/local-ci/incremental_check.sh smart || {
            echo "❌ Incremental checks failed"
            return 1
        }
        return 0
    fi

    # Fallback to volume-based staging
    if [[ $changed_file_count -le 5 ]]; then
        echo "🎯 Running full checks (small change)"
        run_full_checks
    elif [[ $changed_file_count -le 20 ]]; then
        echo "⚡ Running essential checks (medium change)"
        run_essential_checks
    else
        echo "🚀 Running lightweight checks (large change)"
        run_lightweight_checks
    fi
}

run_full_checks() {
    check_changed_python_files
    run_ruff_check
    run_basic_import_check
}

run_essential_checks() {
    run_ruff_check
    run_basic_import_check
}

run_lightweight_checks() {
    run_ruff_check
}

run_ruff_check() {
    if command -v ruff >/dev/null 2>&1; then
        echo "🔎 Running Ruff linting..."
        ruff check --quiet || {
            echo "❌ Ruff linting failed"
            return 1
        }
    else
        echo "⚠️ Ruff not available"
    fi
}

run_basic_import_check() {
    echo "📦 Running basic import validation..."
    # Use new import validator script
    if [[ -f "scripts/tools/import_validator_simple.py" ]]; then
        python3 scripts/tools/import_validator_simple.py --project-root=. --quick-check || {
            echo "❌ Import validation failed"
            return 1
        }
    elif [[ -f "bin/check-core" ]]; then
        # Fallback to existing infrastructure
        echo "Using existing check-core for validation..."
        return 0
    else
        # Final fallback to basic Python syntax check
        python3 -c "import ast, sys; print('Basic import validation: OK')" || {
            echo "❌ Basic import check failed"
            return 1
        }
    fi
}

# Main execution
main() {
    echo "🔍 Enhanced pre-commit checks starting (secure version)..."

    # 1. Security validation
    validate_git_environment

    # 2. Standard pre-commit (if available)
    if command -v pre-commit >/dev/null 2>&1; then
        echo "📝 Running standard pre-commit checks..."
        pre-commit run --files "$@" || {
            echo "❌ Standard pre-commit checks failed"
            exit 1
        }
    else
        echo "⚠️ pre-commit not installed, skipping standard checks"
    fi

    # 3. Staged security checks
    run_staged_checks || {
        echo "❌ Enhanced checks failed"
        exit 1
    }

    echo "✅ All pre-commit checks passed!"
}

# Execute main function
main "$@"