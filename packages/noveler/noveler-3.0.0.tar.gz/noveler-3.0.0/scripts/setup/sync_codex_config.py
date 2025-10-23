# File: scripts/setup/sync_codex_config.py
# Purpose: Synchronize the local Codex MCP configuration from the repository template.
# Context: Consumes config/mcp/codex.template.json and updates ~/.codex/config.toml.
#!/usr/bin/env python3
"""
Update ~/.codex/config.toml so its mcp_servers section matches the repository template.

The script loads config/mcp/codex.template.json, transforms the MCP server definitions
into TOML, optionally creates a timestamped backup of the existing config, then rewrites
the [mcp_servers.*] block if differences are detected. It is intentionally focused on
Codex-specific configuration so other sections in config.toml remain untouched.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_ORDER = ("filesystem", "serena", "noveler")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Synchronize ~/.codex/config.toml from config/mcp/codex.template.json",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Path to codex.template.json (defaults to repo config/mcp/codex.template.json)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path.home() / ".codex" / "config.toml",
        help="Codex config.toml location (defaults to ~/.codex/config.toml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show whether an update is required without writing changes",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a timestamped backup before writing",
    )
    return parser.parse_args()


def project_root() -> Path:
    """Return repository root based on this script location."""
    return Path(__file__).resolve().parent.parent.parent


def load_template(path: Path) -> Dict[str, dict]:
    """Load the MCP server definitions from the template JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        raise ValueError(f"{path} does not define any mcpServers entries.")
    return servers


def determine_order(servers: Dict[str, dict]) -> List[str]:
    """Return server keys in preferred order with fallback to template order."""
    ordered: List[str] = [name for name in DEFAULT_ORDER if name in servers]
    ordered.extend(name for name in servers if name not in ordered)
    return ordered


def quote(value: str, allow_single: bool = False) -> str:
    """Format a string for TOML while preserving Windows paths."""
    if allow_single and "\\" in value and "'" not in value:
        return f"'{value}'"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def grouped_args(name: str, args: Iterable[str]) -> List[Tuple[str, ...]]:
    """
    Group CLI arguments for readable TOML output.

    The Serena server has a conventional pair-wise grouping, so mimic that layout
    to avoid needless diffs in existing configs; other servers fall back to pairs.
    """
    values = list(args)
    if not values:
        return []

    if name == "serena":
        pattern = [2, 1, 2, 2, 2]
    else:
        pattern = []

    groups: List[Tuple[str, ...]] = []
    idx = 0
    for size in pattern:
        chunk = values[idx : idx + size]
        if not chunk:
            break
        groups.append(tuple(chunk))
        idx += size

    while idx < len(values):
        chunk = values[idx : idx + 2]
        groups.append(tuple(chunk))
        idx += len(chunk)
    return groups


def format_args(name: str, args: Iterable[str]) -> str | None:
    """Format the args array as TOML assignment."""
    groups = grouped_args(name, args)
    if not groups:
        return None
    if len(groups) == 1:
        elements = ", ".join(quote(item) for item in groups[0])
        return f"args = [{elements}]"
    lines = ["args = ["]
    for chunk in groups:
        text = ", ".join(quote(item) for item in chunk)
        trailing = "," if chunk is not groups[-1] else ""
        lines.append(f"    {text}{trailing}")
    lines.append("]")
    return "\n".join(lines)


def format_server_block(name: str, cfg: Dict[str, object]) -> str:
    """Render a single [mcp_servers.*] TOML block."""
    lines = [f"[mcp_servers.{name}]"]
    command = cfg.get("command")
    if command:
        lines.append(f"command = {quote(str(command))}")

    args_line = format_args(name, cfg.get("args", []))
    if args_line:
        lines.append(args_line)

    cwd = cfg.get("cwd")
    if cwd:
        lines.append(f"cwd = {quote(str(cwd))}")

    description = cfg.get("description")
    if description:
        lines.append(f"description = {quote(str(description))}")

    env = cfg.get("env") or {}
    if env:
        if description:
            lines.append("")
        lines.append(f"[mcp_servers.{name}.env]")
        for key, value in env.items():
            lines.append(f"{key} = {quote(str(value), allow_single=True)}")

    return "\n".join(lines)


def build_servers_block(servers: Dict[str, dict]) -> str:
    """Combine formatted server blocks with blank lines and trailing newline."""
    order = determine_order(servers)
    blocks = [format_server_block(name, servers[name]) for name in order]
    return "\n\n".join(blocks) + "\n"


def split_config(text: str) -> Tuple[str, str, str]:
    """Separate prefix, target block, and suffix from the config text."""
    lines = text.splitlines(keepends=True)
    start_idx = None
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("[mcp_servers."):
            start_idx = idx
            break
    if start_idx is None:
        raise ValueError("config.toml does not contain any [mcp_servers.*] section.")

    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        stripped = lines[idx].lstrip()
        if stripped.startswith("[") and not stripped.startswith("[mcp_servers."):
            end_idx = idx
            break

    prefix = "".join(lines[:start_idx])
    block = "".join(lines[start_idx:end_idx])
    suffix = "".join(lines[end_idx:])
    return prefix, block, suffix


def create_backup(path: Path) -> Path:
    """Create timestamped backup of the target file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{timestamp}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def main() -> int:
    args = parse_args()
    root = project_root()
    template_path = args.template or (root / "config" / "mcp" / "codex.template.json")
    config_path = args.config.expanduser()

    if not template_path.exists():
        print(f"ERROR: Template not found: {template_path}")
        return 1
    if not config_path.exists():
        print(f"ERROR: Target config not found: {config_path}")
        return 1

    servers = load_template(template_path)
    new_block = build_servers_block(servers)
    current_text = config_path.read_text(encoding="utf-8")
    prefix, existing_block, suffix = split_config(current_text)

    if existing_block == new_block:
        print("INFO: Codex config already matches template; no changes needed.")
        return 0

    if args.dry_run:
        print("INFO: Differences detected but --dry-run specified; no changes written.")
        return 0

    if not args.no_backup:
        backup_path = create_backup(config_path)
        print(f"INFO: Created backup at {backup_path}")

    config_path.write_text(prefix + new_block + suffix, encoding="utf-8")
    print(f"INFO: Updated {config_path} from {template_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
