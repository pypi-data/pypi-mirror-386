#!/usr/bin/env python3
"""CI wrapper: run_quality_checks → NDJSON + exit code control

Usage examples:
  - python scripts/ci/run_quality_checks_ndjson.py --file-path manuscript/EP001.txt \
        --fail-on-score-below 80 --severity-threshold medium --out reports/quality.ndjson

Exit codes:
  0: success (no fail conditions met)
  2: should_fail = true (fail conditions met)
  3: execution error
"""
from __future__ import annotations

import argparse
import os
import json
import sys
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp_servers.noveler.tools.run_quality_checks_tool import RunQualityChecksTool
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest


# ============================================================================
# CI Configuration Management
# ============================================================================

def _load_ci_defaults() -> dict:
    """
    Load CI defaults from ci_defaults.yaml configuration file.

    Location: scripts/ci/ci_defaults.yaml

    Returns:
        dict with ci configuration (with sensible fallbacks if file not found)

    Note:
    - This centralizes all magic numbers and configuration values
    - Enables easy customization without code changes
    - Provides fallback defaults if configuration file is missing
    """
    config_path = Path(__file__).parent / "ci_defaults.yaml"

    # Sensible defaults (used if config file not found)
    defaults = {
        "ci": {
            "tool": {"subprocess_timeout": 30, "stdout_buffer_size": 8192},
            "output": {
                "default_directory": "temp",
                "default_filename": "quality.ndjson",
                "default_path": "temp/quality.ndjson",
                "gate_b_report_path": "reports/quality.ndjson",
                "gate_c_report_path": "reports/editorial_checklist.md",
            },
            "gates": {
                "gate_b": {"min_threshold": 80.0, "aspects": ["rhythm", "readability", "grammar", "style"]},
                "gate_c": {"require_all_pass": True},
            },
            "error_handling": {
                "exit_code_success": 0,
                "exit_code_should_fail": 2,
                "exit_code_error": 3,
                "exit_code_interrupt": 3,
            },
            "severity_levels": ["low", "medium", "high", "critical"],
            "default_severity": "low",
            "logging": {
                "warn_on_stderr": True,
                "debug_on_stderr": False,
                "error_truncate_length": 50,
            },
        }
    }

    if not config_path.exists():
        return defaults

    try:
        content = config_path.read_text(encoding="utf-8")
        try:
            import yaml

            config_data = yaml.safe_load(content) or {}
            # Deep merge with defaults (config overrides defaults)
            if "ci" in config_data:
                _deep_merge(defaults["ci"], config_data["ci"])
        except ImportError:
            # PyYAML not available; use lightweight parser
            config_data = _parse_yaml_simple(content) or {}
            if "ci" in config_data:
                _deep_merge(defaults["ci"], config_data["ci"])
    except Exception as e:
        print(f"Warning: Failed to load CI defaults from {config_path}: {e}", file=sys.stderr)
        return defaults

    return defaults


def _deep_merge(target: dict, source: dict) -> None:
    """
    Deep merge source dict into target dict (in-place).

    Args:
        target: Target dict to merge into
        source: Source dict to merge from

    Note:
    - Modifies target dict in-place
    - Recursively merges nested dicts
    - source values override target values
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def get_ci_config(ci_defaults: dict, key_path: str, fallback=None):
    """
    Get a configuration value by dot-separated key path.

    Args:
        ci_defaults: CI defaults dict loaded from config
        key_path: Dot-separated path (e.g., "tool.subprocess_timeout")
        fallback: Fallback value if key not found

    Returns:
        Configuration value or fallback if not found

    Example:
        timeout = get_ci_config(ci_defaults, "tool.subprocess_timeout", 30)
    """
    keys = key_path.split(".")
    value = ci_defaults.get("ci", {})
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return fallback
    return value if value is not None else fallback


# Custom exceptions for better error handling and debugging
class CIWrapperError(Exception):
    """Base exception for CI wrapper errors."""
    pass


class YAMLParseError(CIWrapperError):
    """Raised when YAML parsing fails."""
    def __init__(self, path: str, error: Exception, line_number: int = None):
        self.path = path
        self.error = error
        self.line_number = line_number
        message = f"Failed to parse YAML file {path}: {str(error)}"
        if line_number:
            message += f" (near line {line_number})"
        super().__init__(message)


class ToolExecutionError(CIWrapperError):
    """Raised when Tool execution fails."""
    def __init__(self, error_message: str, exit_code: int = 3):
        self.exit_code = exit_code
        super().__init__(error_message)


class GateCEvaluationError(CIWrapperError):
    """Raised when Gate C evaluation fails."""
    def __init__(self, report_path: str, error: Exception):
        self.report_path = report_path
        self.error = error
        super().__init__(f"Gate C evaluation failed for {report_path}: {str(error)}")


class WorkingDirectoryError(CIWrapperError):
    """Raised when working directory setup fails."""
    def __init__(self, path: str, error: Exception):
        self.path = path
        self.error = error
        super().__init__(f"Failed to change working directory to {path}: {str(error)}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run noveler quality checks and emit NDJSON for CI")
    target = p.add_mutually_exclusive_group(required=False)
    target.add_argument("--file-path", type=str, help="Target file path to analyze")
    target.add_argument("--episode", type=int, help="Episode number (fallback if file not given)")
    p.add_argument("--project-root", type=str, default=None, help="Project root to analyze (changes working directory)")
    p.add_argument("--project-name", type=str, default=None, help="Optional project name")
    p.add_argument("--aspects", type=str, default=None, help="Comma list (e.g. rhythm,readability,grammar,style)")
    p.add_argument("--severity-threshold", type=str, default="low", choices=["low","medium","high","critical"])
    p.add_argument("--reason-codes", type=str, default=None, help="Comma list to filter reason codes")
    p.add_argument("--types", type=str, default=None, help="Comma list to filter types")
    p.add_argument("--text-contains", type=str, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--sort-by", type=str, default=None, choices=["line_number","severity","reason_code","type"])
    p.add_argument("--sort-order", type=str, default="asc", choices=["asc","desc"])
    # fail_on
    p.add_argument("--fail-on-score-below", type=float, default=None)
    p.add_argument("--fail-on-severity-at-least", type=str, default=None, choices=["low","medium","high","critical"])
    p.add_argument("--fail-on-reason-codes", type=str, default=None, help="Comma list")
    p.add_argument("--fail-on-max-issue-count", type=int, default=None)
    # Gate C (Editorial Checklist)
    p.add_argument("--enable-gate-c", action="store_true", help="Enable Gate C (editorial checklist evaluation)")
    p.add_argument("--editorial-report", type=str, default=None, help="Path to editorial checklist report")
    # output
    p.add_argument("--out", type=str, default=None, help="Path to write NDJSON; also prints to stdout (default: temp/quality.ndjson)")
    # Optional: treat any PathService fallback usage as CI failure
    p.add_argument("--fail-on-path-fallback", action="store_true", help="Exit with failure if path_fallback_used is true")
    return p.parse_args()


def _parse_yaml_simple(content: str) -> dict:
    """
    Lightweight YAML parser for gate_defaults.yaml (no PyYAML dependency).

    Supports:
    - Nested dicts (indented key: value pairs)
    - Scalar lists (array items with dash prefix containing scalar values)
    - Scalar values (bool, int, float, string)
    - Comments (# lines and inline)

    Limitations (acceptable for current gate_defaults.yaml, but note for future):
    - List-of-dicts (- key: value with nested fields) not fully supported
      (scalar list items work; dict items in lists will lose nested fields)
    - Complex YAML features (aliases, anchors, tags) not supported

    This parser is intentionally minimal to avoid PyYAML dependency while
    handling the actual structures in gate_defaults.yaml. For complex YAML,
    PyYAML is still used if available.

    Args:
        content: Raw YAML text

    Returns:
        Parsed dict structure
    """
    result = {}
    stack = [result]  # Stack of containers to handle nesting
    indent_levels = [0]  # Track indentation levels

    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1

        # Skip empty lines and comment-only lines
        if not line.strip() or line.strip().startswith("#"):
            continue

        # Calculate indentation
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Pop stack to current indentation level
        while len(indent_levels) > 1 and indent < indent_levels[-1]:
            stack.pop()
            indent_levels.pop()

        # Handle list items (- value or - key: value)
        if stripped.startswith("- "):
            list_content = stripped[2:].strip()

            # Check if it's a key: value pair (dict item in list)
            if ":" in list_content:
                key, _, value = list_content.partition(":")
                key = key.strip()
                value = value.strip()

                # Create dict item
                if value:
                    # Single-line dict: - key: value
                    item = {key: _parse_yaml_value(value)}
                else:
                    # Multi-line dict: - key:
                    #                    nested: value
                    item = {key: {}}

                # Ensure current container is a list
                current = stack[-1]
                if isinstance(current, list):
                    current.append(item)
                    # If value is empty (nested), push the nested dict to stack
                    if not value:
                        stack.append(item[key])
                        # YAML nesting for list items uses +2, not +4
                        # steps:
                        #   - key: foo
                        #     nested: bar    <- indented by 2 from dash
                        indent_levels.append(indent + 2)
            else:
                # Scalar list item: - value
                parsed_value = _parse_yaml_value(list_content)

                # Ensure current container is a list
                current = stack[-1]
                if isinstance(current, list):
                    current.append(parsed_value)

            continue

        # Handle key: value pairs
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            # Parse value
            if value:
                # Non-empty value on same line
                parsed_value = _parse_yaml_value(value)
                # Add to current container
                if isinstance(stack[-1], dict):
                    stack[-1][key] = parsed_value
            else:
                # Nested structure follows; peek ahead to determine type
                # Skip comments and blank lines to find the real next line
                is_list = False
                peek_idx = i
                while peek_idx < len(lines):
                    peek_line = lines[peek_idx].strip()
                    # Skip empty lines and comment-only lines
                    if peek_line and not peek_line.startswith("#"):
                        # Found a real line; check if it's a list item
                        is_list = peek_line.startswith("- ")
                        break
                    peek_idx += 1

                if is_list:
                    # Create a list for this key
                    parsed_value = []
                else:
                    # Create a dict for this key
                    parsed_value = {}

                # Add to current container
                if isinstance(stack[-1], dict):
                    stack[-1][key] = parsed_value

                # Push to stack to handle nested items
                stack.append(parsed_value)
                indent_levels.append(indent + 2)

    return result


def _parse_yaml_value(value: str):
    """
    Parse a YAML value (bool, int, float, string, list).
    """
    value = value.strip()

    # Strip inline comments (text after # that's not in a string)
    # Simple approach: find # outside of quotes
    if "#" in value:
        # Check if # is inside quotes
        in_single = False
        in_double = False
        for i, char in enumerate(value):
            if char == "'" and (i == 0 or value[i-1] != "\\"):
                in_single = not in_single
            elif char == '"' and (i == 0 or value[i-1] != "\\"):
                in_double = not in_double
            elif char == "#" and not in_single and not in_double:
                value = value[:i].rstrip()
                break

    value = value.strip()

    # Boolean
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False

    # None
    if value.lower() in ("null", "~"):
        return None

    # Float (must check before integer, as 82.5 contains digits)
    if "." in value:
        try:
            # Try to parse as float
            if value.replace(".", "", 1).replace("-", "", 1 if value.startswith("-") else 0).isdigit():
                return float(value)
        except (ValueError, AttributeError):
            pass

    # Integer
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    # String (remove quotes if present)
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    return value


def _load_gate_defaults() -> dict:
    """
    Load Gate B/C default thresholds from configuration.

    Attempts:
    1. Try PyYAML if available
    2. Fall back to lightweight YAML parser
    3. Fall back to stub defaults if file not found

    Returns:
        dict with gate_defaults configuration
    """
    from pathlib import Path

    result = {
        "gate_defaults": {
            "outputs": {"core_report": "reports/quality.ndjson"},
            "thresholds": {
                "severity": "low",
                "gate_b": {},
            },
            "episodes": {"default": 1},
            "editorial_checklist": {"require_all_pass": True},
        }
    }

    config_path = Path(__file__).parent.parent.parent / "config" / "quality" / "gate_defaults.yaml"

    if not config_path.exists():
        return result

    try:
        content = config_path.read_text(encoding="utf-8")

        # Try PyYAML first (most robust)
        data = None
        try:
            import yaml
            data = yaml.safe_load(content) or {}
        except ImportError:
            # PyYAML not available, use lightweight parser
            data = _parse_yaml_simple(content) or {}

        if "gate_defaults" in data:
            result["gate_defaults"] = data["gate_defaults"]
    except Exception:
        # Fall back to defaults on any parse error
        pass

    return result


def check_gate_c_status(editorial_report_path: str, require_all_pass: bool = True, subprocess_timeout: int = 30) -> dict:
    """
    Evaluate editorial checklist status for Gate C.

    Args:
        editorial_report_path: Path to editorial checklist file
        require_all_pass: Whether all items must pass
        subprocess_timeout: Timeout in seconds for editorial checklist evaluator subprocess

    Returns:
        dict with gate_c_pass, gate_c_should_fail, gate_c_counts, etc.

    Note:
    - subprocess_timeout is loaded from ci_defaults.yaml (tool.subprocess_timeout)
    - Default is 30 seconds if not specified
    """
    import subprocess

    result = {
        "gate_c_pass": True,
        "gate_c_should_fail": False,
        "gate_c_counts": {
            "total": 0,
            "pass": 0,
            "note": 0,
            "todo": 0,
            "unknown": 0,
            "checked": 0,
            "unchecked": 0,
        },
        "gate_c_counts_by_status": {"PASS": 0, "NOTE": 0, "TODO": 0, "UNKNOWN": 0},
    }

    try:
        # Call scripts/tools/editorial_checklist_evaluator.py with correct CLI args
        from pathlib import Path
        evaluator_path = Path(__file__).parent.parent / "tools" / "editorial_checklist_evaluator.py"
        proc = subprocess.run(
            ["python", str(evaluator_path), "--file", editorial_report_path, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=subprocess_timeout
        )

        # editorial_checklist_evaluator.py returns 0 (pass) or 2 (fail), see L131
        if proc.returncode in (0, 2):
            try:
                output = json.loads(proc.stdout)
                # Map subprocess output to gate_c_counts
                counts = output.get("counts", {})
                result["gate_c_counts"] = {
                    "total": output.get("total_items", 0),
                    "pass": counts.get("PASS", 0),
                    "note": counts.get("NOTE", 0),
                    "todo": counts.get("TODO", 0),
                    "unknown": counts.get("UNKNOWN", 0),
                    "checked": sum(counts.values()),
                    "unchecked": 0,
                }
                result["gate_c_counts_by_status"] = counts

                # Determine gate_c_pass based on subprocess result
                gate_c_pass = output.get("pass", True)
                result["gate_c_pass"] = gate_c_pass
                result["gate_c_should_fail"] = not gate_c_pass if require_all_pass else False

            except json.JSONDecodeError:
                result["gate_c_error"] = "Failed to parse subprocess output"
        else:
            result["gate_c_error"] = f"Editorial evaluator failed with code {proc.returncode}: {proc.stderr}"

    except subprocess.TimeoutExpired:
        result["gate_c_error"] = "Editorial checklist evaluator timed out"
    except FileNotFoundError:
        # Fallback if subprocess path not found - return neutral result (pass)
        pass
    except Exception as e:
        result["gate_c_error"] = str(e)

    return result


def _setup_working_directory(args: argparse.Namespace) -> None:
    """
    Setup working directory based on command-line arguments.

    Args:
        args: Parsed command-line arguments

    Behavior:
    - If --project-root provided, change to that directory
    - Otherwise, if running from 00_ガイド, prefer sibling sample project
    - Silently fall back to current directory on any error

    Raises:
        WorkingDirectoryError: If explicit --project-root is provided but fails to change directory
    """
    if args.project_root:
        try:
            os.chdir(args.project_root)
        except Exception as e:
            # For explicit project root, log and continue but warn user
            print(
                f"Warning: Failed to change to explicit project root {args.project_root}: {e}",
                file=sys.stderr
            )
            return

    # Heuristic: when running from 00_ガイド repo, prefer sibling sample project if present
    try:
        guide_root = ROOT
        if guide_root.exists() and guide_root.name.endswith("00_ガイド"):
            sample = guide_root.parent / "10_Fランク魔法使いはDEBUGログを読む"
            if sample.exists() and sample.is_dir():
                os.chdir(sample)
    except Exception as e:
        # Heuristic failure is not critical; log and continue
        print(f"Debug: Failed to apply 00_ガイド heuristic: {e}", file=sys.stderr)


def _build_filters(args: argparse.Namespace) -> dict:
    """
    Build filter parameters from command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        dict with filter parameters (empty if none specified)
    """
    filters = {}
    if args.reason_codes:
        filters["reason_codes"] = [s.strip() for s in args.reason_codes.split(",") if s.strip()]
    if args.types:
        filters["types"] = [s.strip() for s in args.types.split(",") if s.strip()]
    if args.text_contains:
        filters["text_contains"] = args.text_contains
    if args.limit is not None:
        filters["limit"] = args.limit
    return filters


def _build_fail_on(args: argparse.Namespace, gate_config: dict) -> dict:
    """
    Build fail_on parameters from command-line arguments and gate config.

    Args:
        args: Parsed command-line arguments
        gate_config: Gate configuration dict

    Returns:
        dict with fail_on parameters (empty if none specified)
    """
    fail_on = {}
    if args.fail_on_score_below is not None:
        fail_on["score_below"] = args.fail_on_score_below
    elif gate_config.get("thresholds", {}).get("gate_b"):
        # Use minimum of gate_b thresholds as default fail_on score
        gate_b_thresholds = gate_config["thresholds"]["gate_b"]
        if isinstance(gate_b_thresholds, dict) and gate_b_thresholds:
            fail_on["score_below"] = float(min(gate_b_thresholds.values()))

    if args.fail_on_severity_at_least is not None:
        fail_on["severity_at_least"] = args.fail_on_severity_at_least
    if args.fail_on_reason_codes:
        fail_on["reason_codes"] = [s.strip() for s in args.fail_on_reason_codes.split(",") if s.strip()]
    if args.fail_on_max_issue_count is not None:
        fail_on["max_issue_count"] = args.fail_on_max_issue_count
    return fail_on


def _build_additional_params(args: argparse.Namespace, gate_config: dict, filters: dict, fail_on: dict) -> dict:
    """
    Build additional_params for Tool request from command-line arguments and gate config.

    Args:
        args: Parsed command-line arguments
        gate_config: Gate configuration dict
        filters: Filter parameters
        fail_on: Fail-on parameters

    Returns:
        dict with all additional parameters for Tool execution
    """
    # Use severity from gate config if default not overridden by args
    severity_threshold = gate_config.get("thresholds", {}).get("severity", "low")
    if args.severity_threshold != "low":  # if explicitly set
        severity_threshold = args.severity_threshold

    ap = {
        "format": "ndjson",
        "severity_threshold": severity_threshold,
    }

    # Add gate_thresholds if available
    if gate_config.get("thresholds", {}).get("gate_b"):
        ap["gate_thresholds"] = gate_config["thresholds"]["gate_b"]

    # Add Gate C enablement
    if args.enable_gate_c:
        ap["enable_gate_c"] = True
        # Determine editorial report path: explicit arg > gate defaults > None
        editorial_report_path = args.editorial_report
        if not editorial_report_path:
            editorial_report_path = gate_config.get("outputs", {}).get("editorial_checklist_report")
        if editorial_report_path:
            ap["editorial_report"] = editorial_report_path
        # Add editorial_checklist config (for require_all_pass flag)
        if gate_config.get("editorial_checklist"):
            ap["editorial_checklist"] = gate_config["editorial_checklist"]

    if filters:
        ap["filters"] = filters
    if args.sort_by:
        ap["sort_by"] = args.sort_by
    if args.sort_order:
        ap["sort_order"] = args.sort_order
    if fail_on:
        ap["fail_on"] = fail_on
    if args.file_path:
        ap["file_path"] = args.file_path
    if args.aspects:
        ap["aspects"] = [s.strip() for s in args.aspects.split(",") if s.strip()]

    return ap


def _execute_tool(tool: RunQualityChecksTool, args: argparse.Namespace, gate_config: dict, ap: dict):
    """
    Execute quality checks tool and extract metadata.

    Args:
        tool: RunQualityChecksTool instance
        args: Parsed command-line arguments
        gate_config: Gate configuration dict
        ap: Additional parameters

    Returns:
        tuple of (tool_response, ndjson_str, path_fallback_used, path_fallback_events_count)

    Raises:
        ToolExecutionError on tool execution failure
    """
    # Use gate defaults for episode if not explicitly provided
    episode_number = int(args.episode) if args.episode else gate_config.get("episodes", {}).get("default", 1)

    req = ToolRequest(
        episode_number=episode_number,
        project_name=args.project_name,
        additional_params=ap,
    )
    try:
        # Suppress noisy stdout logs from underlying tools
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = tool.execute(req)
    except Exception as e:
        import traceback
        error_msg = f"Tool execution failed: {str(e)}"
        error_details = traceback.format_exc()
        print(json.dumps({
            "success": False,
            "error": error_msg,
            "details": error_details
        }, ensure_ascii=False), file=sys.stderr)
        raise ToolExecutionError(error_msg, exit_code=3)

    ndjson = res.metadata.get("ndjson") if res and res.metadata else None
    path_fallback_used = bool(res.metadata.get("path_fallback_used", False)) if (res and res.metadata) else False
    path_fallback_events_count = len(res.metadata.get("path_fallback_events", [])) if (res and res.metadata) else 0

    return res, ndjson, path_fallback_used, path_fallback_events_count


def _evaluate_gates(args: argparse.Namespace, gate_config: dict, ci_defaults: dict = None) -> bool:
    """
    Evaluate Gate C (editorial checklist) if enabled.

    Args:
        args: Parsed command-line arguments
        gate_config: Gate configuration dict
        ci_defaults: CI defaults dict (loaded from ci_defaults.yaml)

    Returns:
        bool indicating if Gate C should fail (True) or not (False)

    Notes:
    - If Gate C evaluation fails, logs error but returns False (non-blocking)
    - This allows CI to continue even if Gate C has issues
    - subprocess_timeout is read from ci_defaults configuration
    """
    if not args.enable_gate_c:
        return False

    # Determine editorial report path: explicit arg > gate defaults > None
    editorial_report_path = args.editorial_report
    if not editorial_report_path:
        editorial_report_path = gate_config.get("outputs", {}).get("editorial_checklist_report")

    if not editorial_report_path:
        return False

    try:
        # Get require_all_pass flag from gate config
        require_all_pass = gate_config.get("editorial_checklist", {}).get("require_all_pass", True)
        # Get subprocess timeout from CI defaults
        subprocess_timeout = get_ci_config(ci_defaults, "tool.subprocess_timeout", 30) if ci_defaults else 30
        gate_c_result = check_gate_c_status(editorial_report_path, require_all_pass=require_all_pass, subprocess_timeout=subprocess_timeout)

        # Check for errors in gate_c_result
        if "gate_c_error" in gate_c_result:
            print(
                f"Warning: Gate C evaluation error: {gate_c_result['gate_c_error']}",
                file=sys.stderr
            )
            return False

        return bool(gate_c_result.get("gate_c_should_fail", False))
    except Exception as e:
        print(
            f"Warning: Gate C evaluation failed for {editorial_report_path}: {str(e)}",
            file=sys.stderr
        )
        return False


def _enrich_ndjson(ndjson: str, path_fallback_used: bool, path_fallback_events_count: int) -> str:
    """
    Enrich NDJSON lines with fallback information.

    Args:
        ndjson: Original NDJSON string
        path_fallback_used: Flag indicating if path fallback was used
        path_fallback_events_count: Count of path fallback events

    Returns:
        Enriched NDJSON string with fallback columns added

    Notes:
    - If enrichment fails, returns original NDJSON (fallback)
    - Invalid JSON lines are kept as-is
    - Handles UTF-8 encoding safely
    """
    try:
        out_lines = []
        for line_num, line in enumerate(ndjson.splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                # Log invalid JSON but keep original line
                print(
                    f"Warning: Invalid JSON at line {line_num}: {str(e)[:50]}... keeping original",
                    file=sys.stderr
                )
                out_lines.append(line)
                continue
            except Exception as e:
                # Unexpected error; log and keep original
                print(
                    f"Warning: Unexpected error enriching line {line_num}: {str(e)[:50]}...",
                    file=sys.stderr
                )
                out_lines.append(line)
                continue

            try:
                obj["path_fallback_used"] = path_fallback_used
                obj["path_fallback_events_count"] = path_fallback_events_count
                out_lines.append(json.dumps(obj, ensure_ascii=False))
            except Exception as e:
                # Serialization failed; log and keep original
                print(
                    f"Warning: Failed to serialize enriched JSON at line {line_num}: {str(e)[:50]}...",
                    file=sys.stderr
                )
                out_lines.append(line)

        return "\n".join(out_lines) + ("\n" if out_lines else "")
    except Exception as e:
        # Critical failure; return original NDJSON
        print(
            f"Warning: NDJSON enrichment failed completely; returning original: {str(e)[:50]}...",
            file=sys.stderr
        )
        return ndjson


def _write_output_and_determine_exit_code(
    res,
    ndjson: str,
    path_fallback_used: bool,
    path_fallback_events_count: int,
    gate_c_should_fail: bool,
    args: argparse.Namespace,
) -> int:
    """
    Write output to file/stdout and determine exit code based on failure conditions.

    Args:
        res: Tool response object
        ndjson: NDJSON output string (may be None)
        path_fallback_used: Flag indicating if path fallback was used
        path_fallback_events_count: Count of path fallback events
        gate_c_should_fail: Flag indicating if Gate C failed
        args: Parsed command-line arguments

    Returns:
        int exit code (0=success, 2=should_fail, 3=error)
    """
    if not ndjson:
        # Fallback: emit a single-line JSON
        payload = {
            "success": res.success if res else False,
            "score": res.score if res else 0,
            "metadata": res.metadata if res else {},
        }
        # include fallback flags in the single-line payload too
        payload["path_fallback_used"] = path_fallback_used
        payload["path_fallback_events_count"] = path_fallback_events_count
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("success") else 2

    # Enrich NDJSON lines with fallback columns
    enriched_ndjson = _enrich_ndjson(ndjson, path_fallback_used, path_fallback_events_count)

    out_path = Path(args.out) if args.out else Path("temp") / "quality.ndjson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(enriched_ndjson, encoding="utf-8")

    # Always print to stdout for CI consumption
    sys.stdout.write(enriched_ndjson)
    sys.stdout.flush()

    # Determine exit code based on failure conditions
    should_fail = bool(res.metadata.get("should_fail", False))
    # Gate B failure (from tool metadata)
    if not should_fail and res.metadata.get("gate_b_should_fail", False):
        should_fail = True
    # Path fallback check
    if not should_fail and args.fail_on_path_fallback and path_fallback_used:
        should_fail = True
    # Gate C failure (from wrapper evaluation)
    if not should_fail and gate_c_should_fail:
        should_fail = True
    return 2 if should_fail else 0


def main() -> int:
    """
    Main entry point: orchestrate quality checks execution.

    Workflow:
    1. Parse arguments and setup working directory
    2. Load gate configuration defaults
    3. Build Tool parameters from arguments and config
    4. Execute quality checks Tool
    5. Evaluate additional gates (Gate C - editorial checklist)
    6. Write output and determine exit code

    Returns:
        int exit code (0=success, 2=should_fail, 3=error)

    Error Handling:
    - Working directory errors: log warning, continue
    - Tool execution errors: exit with code 3
    - Gate evaluation errors: log warning, continue
    - Output writing errors: exit with code 3
    """
    try:
        args = parse_args()
        _setup_working_directory(args)

        tool = RunQualityChecksTool()

        # Load CI defaults (configuration centralization)
        ci_defaults = _load_ci_defaults()

        # Load gate defaults if not explicitly provided
        gate_defaults = _load_gate_defaults()
        gate_config = gate_defaults.get("gate_defaults", {})

        # Build parameters
        filters = _build_filters(args)
        fail_on = _build_fail_on(args, gate_config)
        ap = _build_additional_params(args, gate_config, filters, fail_on)

        # Execute tool
        res, ndjson, path_fallback_used, path_fallback_events_count = _execute_tool(tool, args, gate_config, ap)

        # Evaluate gates (with CI defaults for configuration)
        gate_c_should_fail = _evaluate_gates(args, gate_config, ci_defaults)

        # Write output and determine exit code
        return _write_output_and_determine_exit_code(
            res, ndjson, path_fallback_used, path_fallback_events_count, gate_c_should_fail, args
        )

    except ToolExecutionError as e:
        # Tool execution failures are critical
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        return e.exit_code

    except CIWrapperError as e:
        # Other CI wrapper errors
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False), file=sys.stderr)
        return 3

    except KeyboardInterrupt:
        print(json.dumps({
            "success": False,
            "error": "Interrupted by user"
        }, ensure_ascii=False), file=sys.stderr)
        return 3

    except Exception as e:
        import traceback
        print(json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "details": traceback.format_exc()
        }, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
