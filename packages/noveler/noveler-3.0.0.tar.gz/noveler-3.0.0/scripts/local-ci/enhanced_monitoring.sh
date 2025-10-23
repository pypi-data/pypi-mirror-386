#!/usr/bin/env bash
# Enhanced monitoring and error handling for local CI
# File: scripts/local-ci/enhanced_monitoring.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/temp/ci/logs"
ERROR_LOG="${LOG_DIR}/errors.log"
PERFORMANCE_LOG="${LOG_DIR}/performance.log"

# Initialize logging infrastructure
setup_logging() {
    mkdir -p "$LOG_DIR"

    # Create log files if they don't exist
    touch "$ERROR_LOG"
    touch "$PERFORMANCE_LOG"

    # Rotate logs if they get too large (>1MB)
    if [[ -f "$ERROR_LOG" && $(stat -f%z "$ERROR_LOG" 2>/dev/null || stat -c%s "$ERROR_LOG" 2>/dev/null || echo 0) -gt 1048576 ]]; then
        mv "$ERROR_LOG" "${ERROR_LOG}.old"
        touch "$ERROR_LOG"
    fi

    if [[ -f "$PERFORMANCE_LOG" && $(stat -f%z "$PERFORMANCE_LOG" 2>/dev/null || stat -c%s "$PERFORMANCE_LOG" 2>/dev/null || echo 0) -gt 1048576 ]]; then
        mv "$PERFORMANCE_LOG" "${PERFORMANCE_LOG}.old"
        touch "$PERFORMANCE_LOG"
    fi
}

# Log error with context
log_error() {
    local error_msg="$1"
    local context="${2:-unknown}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] ERROR [$context]: $error_msg" >> "$ERROR_LOG"
    echo "❌ [$context]: $error_msg" >&2
}

# Log performance metrics
log_performance() {
    local operation="$1"
    local duration="$2"
    local status="${3:-success}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] PERF [$operation]: ${duration}s ($status)" >> "$PERFORMANCE_LOG"
}

# Enhanced error handling wrapper
run_with_monitoring() {
    local operation="$1"
    local command="$2"
    local start_time=$(date +%s)

    echo "🔍 Running: $operation"

    if eval "$command"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_performance "$operation" "$duration" "success"
        echo "✅ $operation completed in ${duration}s"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_performance "$operation" "$duration" "failed"
        log_error "$operation failed after ${duration}s" "$operation"
        return 1
    fi
}

# Check system health
check_system_health() {
    echo "🏥 System health check"

    # Check disk space (warn if less than 1GB free)
    local free_space_kb=$(df . | tail -1 | awk '{print $4}')
    local free_space_gb=$((free_space_kb / 1024 / 1024))

    if [[ $free_space_gb -lt 1 ]]; then
        log_error "Low disk space: ${free_space_gb}GB free" "system_health"
        echo "⚠️ Warning: Low disk space (${free_space_gb}GB free)"
        return 1
    else
        echo "✅ Disk space: ${free_space_gb}GB free"
    fi

    # Check Python availability
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 not available" "system_health"
        echo "❌ Python3 not found"
        return 1
    else
        local python_version=$(python3 --version 2>&1)
        echo "✅ Python: $python_version"
    fi

    # Check Git repository health
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a git repository" "system_health"
        echo "❌ Not in git repository"
        return 1
    else
        echo "✅ Git repository: OK"
    fi

    return 0
}

# Generate health report
generate_health_report() {
    local report_file="${LOG_DIR}/health_report.md"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$report_file" << EOF
# Local CI Health Report

Generated: $timestamp

## Error Summary (Last 24 hours)
\`\`\`
$(tail -n 50 "$ERROR_LOG" | grep "$(date '+%Y-%m-%d')" || echo "No errors today")
\`\`\`

## Performance Summary (Last 10 operations)
\`\`\`
$(tail -n 10 "$PERFORMANCE_LOG" || echo "No performance data")
\`\`\`

## System Status
$(check_system_health 2>&1)

## Recent Git Activity
\`\`\`
$(git log --oneline -5 2>/dev/null || echo "No recent commits")
\`\`\`
EOF

    echo "📊 Health report generated: $report_file"
}

# Monitor specific git hook execution
monitor_git_hook() {
    local hook_name="$1"
    local hook_script="$2"
    shift 2
    local hook_args=("$@")

    setup_logging

    echo "🪝 Monitoring git hook: $hook_name"

    if run_with_monitoring "$hook_name" "bash '$hook_script' '${hook_args[*]}'"; then
        echo "✅ Git hook $hook_name completed successfully"
        return 0
    else
        log_error "Git hook $hook_name failed" "git_hook"
        echo "❌ Git hook $hook_name failed"
        return 1
    fi
}

# Main monitoring function
main() {
    local action="${1:-health_check}"

    setup_logging

    case "$action" in
        "health_check")
            check_system_health
            ;;
        "report")
            generate_health_report
            ;;
        "monitor_hook")
            monitor_git_hook "${@:2}"
            ;;
        "run_monitored")
            run_with_monitoring "${@:2}"
            ;;
        *)
            echo "Usage: $0 {health_check|report|monitor_hook|run_monitored}"
            echo "Examples:"
            echo "  $0 health_check                    # Check system health"
            echo "  $0 report                          # Generate health report"
            echo "  $0 monitor_hook pre-commit script.sh # Monitor git hook"
            echo "  $0 run_monitored 'test' 'make test'  # Monitor command"
            exit 1
            ;;
    esac
}

# Execute if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi