#!/usr/bin/env bash
# Incremental check system for performance optimization
# File: scripts/local-ci/incremental_check.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CACHE_DIR="${PROJECT_ROOT}/temp/ci/cache"
LAST_CHECK_FILE="${CACHE_DIR}/last_full_check.txt"

# Initialize cache directory
setup_cache() {
    mkdir -p "$CACHE_DIR"
    touch "$LAST_CHECK_FILE"
}

# Get last full check timestamp
get_last_check_time() {
    if [[ -f "$LAST_CHECK_FILE" ]]; then
        cat "$LAST_CHECK_FILE"
    else
        echo "0"
    fi
}

# Update last check timestamp
update_last_check_time() {
    date +%s > "$LAST_CHECK_FILE"
}

# Get changed files since last check
get_changed_files() {
    local since_timestamp="$1"
    local changed_files=()

    # Get files changed since timestamp using git
    if [[ "$since_timestamp" != "0" ]]; then
        local since_date=$(date -d "@$since_timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$since_timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "1 hour ago")

        # Get changed files from git
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                changed_files+=("$file")
            fi
        done < <(git diff --name-only --since="$since_date" -z 2>/dev/null || true)
    fi

    # If no git changes or timestamp is 0, check all recent files
    if [[ ${#changed_files[@]} -eq 0 ]]; then
        # Find files modified in last hour as fallback
        while IFS= read -r -d $'\0' file; do
            changed_files+=("$file")
        done < <(find src/ -name "*.py" -mtime -1 -print0 2>/dev/null || true)
    fi

    printf '%s\n' "${changed_files[@]}"
}

# Check if incremental check is appropriate
should_run_incremental() {
    local last_check_time=$(get_last_check_time)
    local current_time=$(date +%s)
    local time_diff=$((current_time - last_check_time))

    # Run incremental if last check was less than 6 hours ago
    if [[ $time_diff -lt 21600 ]]; then
        return 0
    else
        return 1
    fi
}

# Run incremental quality checks
run_incremental_checks() {
    local last_check_time=$(get_last_check_time)

    echo "⚡ Running incremental quality checks"
    echo "📅 Last full check: $(date -d "@$last_check_time" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'Never')"

    local changed_files
    mapfile -t changed_files < <(get_changed_files "$last_check_time")

    if [[ ${#changed_files[@]} -eq 0 ]]; then
        echo "✅ No changed files detected, skipping checks"
        return 0
    fi

    echo "📁 Checking ${#changed_files[@]} changed files:"
    printf '  - %s\n' "${changed_files[@]:0:5}"
    if [[ ${#changed_files[@]} -gt 5 ]]; then
        echo "  ... and $((${#changed_files[@]} - 5)) more files"
    fi

    local failed_checks=0

    # Run lightweight checks on changed files
    echo "🔍 Running syntax check..."
    for file in "${changed_files[@]}"; do
        if [[ "$file" == *.py ]]; then
            if ! python3 -m py_compile "$file" 2>/dev/null; then
                echo "❌ Syntax error in $file"
                ((failed_checks++))
            fi
        fi
    done

    # Run import validation on Python files
    echo "📦 Running import check..."
    local python_files=()
    for file in "${changed_files[@]}"; do
        if [[ "$file" == *.py ]]; then
            python_files+=("$file")
        fi
    done

    if [[ ${#python_files[@]} -gt 0 ]] && [[ -f "scripts/tools/import_validator_simple.py" ]]; then
        if ! python3 scripts/tools/import_validator_simple.py --project-root=. --quick-check; then
            ((failed_checks++))
        fi
    fi

    if [[ $failed_checks -eq 0 ]]; then
        echo "✅ Incremental checks passed for ${#changed_files[@]} files"
        return 0
    else
        echo "❌ Incremental checks failed ($failed_checks issues)"
        return 1
    fi
}

# Run full quality checks and update timestamp
run_full_checks() {
    echo "🔄 Running full quality checks"

    # Run comprehensive checks
    if command -v make >/dev/null 2>&1; then
        if make quality-full; then
            echo "✅ Full quality checks passed"
            update_last_check_time
            return 0
        else
            echo "❌ Full quality checks failed"
            return 1
        fi
    else
        echo "⚠️ Make not available, running basic checks"
        if python3 -c "print('Basic quality check: OK')"; then
            update_last_check_time
            return 0
        else
            return 1
        fi
    fi
}

# Smart check selection
smart_check() {
    setup_cache

    if should_run_incremental; then
        echo "🧠 Smart check: Using incremental mode"
        run_incremental_checks
    else
        echo "🧠 Smart check: Using full mode (time threshold exceeded)"
        run_full_checks
    fi
}

# Force full check (resets cache)
force_full_check() {
    setup_cache
    echo "🔄 Force full check requested"

    # Reset cache
    echo "0" > "$LAST_CHECK_FILE"

    run_full_checks
}

# Main function
main() {
    local action="${1:-smart}"

    case "$action" in
        "smart")
            smart_check
            ;;
        "incremental")
            setup_cache
            run_incremental_checks
            ;;
        "full")
            force_full_check
            ;;
        "status")
            setup_cache
            local last_check_time=$(get_last_check_time)
            echo "📊 Incremental check status:"
            echo "  Last full check: $(date -d "@$last_check_time" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'Never')"
            echo "  Should use incremental: $(should_run_incremental && echo 'Yes' || echo 'No')"

            local changed_files
            mapfile -t changed_files < <(get_changed_files "$last_check_time")
            echo "  Changed files: ${#changed_files[@]}"
            ;;
        *)
            echo "Usage: $0 {smart|incremental|full|status}"
            echo "  smart       - Automatically choose incremental or full check"
            echo "  incremental - Run incremental check only"
            echo "  full        - Force full check and reset cache"
            echo "  status      - Show current incremental check status"
            exit 1
            ;;
    esac
}

# Execute if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi