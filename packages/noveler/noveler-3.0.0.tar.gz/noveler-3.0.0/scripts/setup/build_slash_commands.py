#!/usr/bin/env python3
# File: scripts/setup/build_slash_commands.py
# Purpose: Generate slash command configurations from YAML SSOT
# Context: SPEC-CLI-050 - Slash Command Management System

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


class CommandValidationError(Exception):
    """YAML definition validation error."""
    pass


def detect_project_root() -> Path:
    """Detect project root by looking for pyproject.toml."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def load_yaml(path: Path) -> dict:
    """Load and parse YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content

    Raises:
        CommandValidationError: If YAML parsing fails
    """
    try:
        with path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise CommandValidationError(f"YAML parse error: {e}")
    except FileNotFoundError:
        raise CommandValidationError(f"File not found: {path}")


def validate_commands(commands: list[dict]) -> None:
    """Validate command definitions.

    Args:
        commands: List of command definitions

    Raises:
        CommandValidationError: If validation fails
    """
    base_required_fields = ["name", "description"]

    for i, cmd in enumerate(commands):
        # Check base required fields
        for field in base_required_fields:
            if field not in cmd:
                raise CommandValidationError(
                    f"Command {i}: Missing required field '{field}'"
                )

        # Validate name format
        if not cmd["name"].startswith("/"):
            raise CommandValidationError(
                f"Command {i}: name must start with '/' (got: {cmd['name']})"
            )

        # Check command type (script-based or MCP-based)
        cmd_type = cmd.get("type", "script")

        if cmd_type == "mcp":
            # MCP commands require mcp_tools
            if "mcp_tools" not in cmd:
                raise CommandValidationError(
                    f"Command {i}: MCP type requires 'mcp_tools' field"
                )
            if not isinstance(cmd["mcp_tools"], list):
                raise CommandValidationError(
                    f"Command {i}: 'mcp_tools' must be a list"
                )

            # Additional MCP validations
            mcp_tools = cmd["mcp_tools"]

            # mcp_tools must not be empty
            if not mcp_tools:
                raise CommandValidationError(
                    f"Command {i}: 'mcp_tools' must not be empty"
                )

            # Each tool must start with 'mcp__'
            for tool in mcp_tools:
                if not isinstance(tool, str):
                    raise CommandValidationError(
                        f"Command {i}: MCP tool must be a string (got: {type(tool).__name__})"
                    )
                if not tool.startswith("mcp__"):
                    raise CommandValidationError(
                        f"Command {i}: MCP tool '{tool}' must start with 'mcp__'"
                    )
        else:
            # Script-based commands require script field
            if "script" not in cmd:
                raise CommandValidationError(
                    f"Command {i}: Script type requires 'script' field"
                )

        # Validate permissions structure
        if "permissions" in cmd:
            if not isinstance(cmd["permissions"], dict):
                raise CommandValidationError(
                    f"Command {i}: permissions must be a dict"
                )


def merge_permissions(existing: list[str], new: list[str]) -> list[str]:
    """Merge permission lists, removing duplicates.

    Args:
        existing: Existing permissions
        new: New permissions to add

    Returns:
        Merged and sorted permission list
    """
    merged = set(existing) | set(new)
    return sorted(merged)


def generate_claude_settings(commands: list[dict], existing_perms: list[str] | None = None) -> dict:
    """Generate .claude/settings.local.json content.

    Args:
        commands: Command definitions
        existing_perms: Existing permissions to preserve

    Returns:
        Settings dict for Claude Code
    """
    if existing_perms is None:
        existing_perms = []

    # Collect all permissions from all commands
    all_perms = list(existing_perms)

    for cmd in commands:
        if "permissions" not in cmd:
            continue

        perms_dict = cmd["permissions"]
        # Collect permissions for all platforms
        for platform, perms in perms_dict.items():
            all_perms.extend(perms)

    # Remove duplicates and sort
    unique_perms = sorted(set(all_perms))

    return {
        "permissions": {
            "allow": unique_perms,
            "deny": [],
            "ask": []
        }
    }


def validate_templates(templates_dir: Path) -> tuple[bool, list[str]]:
    """Validate template files exist and have required frontmatter.

    Args:
        templates_dir: Path to templates directory

    Returns:
        Tuple of (is_valid, list of warnings/errors)
    """
    issues = []
    required_templates = ["noveler-write.md", "noveler-quality.md", "noveler-polish.md"]

    if not templates_dir.exists():
        issues.append(f"Templates directory not found: {templates_dir}")
        return False, issues

    for template_name in required_templates:
        template_path = templates_dir / template_name
        if not template_path.exists():
            issues.append(f"Required template not found: {template_name}")
            continue

        # Check frontmatter
        try:
            content = template_path.read_text(encoding='utf-8')
            if not content.startswith("---"):
                issues.append(f"Template missing frontmatter: {template_name}")
            elif "allowed-tools" not in content[:500]:  # Check first 500 chars
                issues.append(f"Template missing 'allowed-tools' in frontmatter: {template_name}")
        except Exception as e:
            issues.append(f"Failed to read template {template_name}: {e}")

    is_valid = len([i for i in issues if "not found" in i or "Failed to read" in i]) == 0
    return is_valid, issues


def generate_docs(commands: list[dict]) -> str:
    """Generate docs/slash_commands/README.md content.

    Args:
        commands: Command definitions

    Returns:
        Markdown documentation
    """
    from datetime import datetime

    # Group by category
    by_category: dict[str, list[dict]] = {}
    for cmd in commands:
        category = cmd.get("category", "other")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(cmd)

    lines = [
        "# Slash Commands Reference",
        "",
        "**WARNING: AUTO-GENERATED**: Do not edit manually. Regenerate with `python scripts/setup/build_slash_commands.py`",
        "",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Available Commands",
        ""
    ]

    for category, cmds in sorted(by_category.items()):
        lines.append(f"### {category.capitalize()}")
        lines.append("")

        for cmd in cmds:
            lines.append(f"#### `{cmd['name']}`")
            lines.append("")
            lines.append(cmd['description'])
            lines.append("")

            # Show command type for MCP commands
            if cmd.get("type") == "mcp":
                lines.append("**Type**: MCP-based command")
                lines.append("")

                # Show MCP tools
                if cmd.get("mcp_tools"):
                    lines.append("**MCP Tools**:")
                    for tool in cmd["mcp_tools"]:
                        lines.append(f"- `{tool}`")
                    lines.append("")

                # Add reference to global commands
                global_cmd_path = f"~/.claude/commands/{cmd['name'][1:]}.md"
                lines.append(f"**Global Definition**: [{global_cmd_path}]({global_cmd_path})")
                lines.append("")

            # Show arguments for script-based commands
            if cmd.get("args"):
                lines.append("**Arguments**: " + " ".join(f"`{arg}`" for arg in cmd["args"]))
                lines.append("")

            # Show tags
            if cmd.get("tags"):
                lines.append("**Tags**: " + ", ".join(f"`{tag}`" for tag in cmd["tags"]))
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Generate slash command configurations from YAML"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files"
    )
    parser.add_argument(
        "--user-config",
        action="store_true",
        default=False,
        help="Also update user-level Claude config (~/.claude/...)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (default: project root)"
    )
    parser.add_argument(
        "--sync-global",
        action="store_true",
        help="Also sync Noveler commands to global ~/.claude/commands/"
    )

    args = parser.parse_args(argv)

    # Detect paths
    project_root = detect_project_root()
    yaml_path = project_root / "config" / "slash_commands.yaml"

    # For loading existing settings, always use project root
    source_settings_path = project_root / ".claude" / "settings.local.json"

    # For output, use --output if specified
    if args.output:
        output_root = args.output
        settings_path = output_root / ".claude" / "settings.local.json"
        docs_path = output_root / "docs" / "slash_commands" / "README.md"
    else:
        output_root = project_root
        settings_path = source_settings_path
        docs_path = project_root / "docs" / "slash_commands" / "README.md"

    try:
        # Load YAML
        print(f"[*] Loading: {yaml_path}")
        data = load_yaml(yaml_path)
        commands = data.get("commands", [])

        # Validate
        print(f"[OK] Validating {len(commands)} commands...")
        validate_commands(commands)

        # Load existing settings from source (always from project root)
        existing_perms = []
        if source_settings_path.exists():
            with source_settings_path.open('r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_perms = existing_data.get("permissions", {}).get("allow", [])

        # Generate settings
        print("[*] Generating .claude/settings.local.json...")
        settings = generate_claude_settings(commands, existing_perms)

        # Generate docs
        print("[*] Generating docs/slash_commands/README.md...")
        docs_content = generate_docs(commands)

        # Write or display
        if args.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN: Would write the following files:")
            print("=" * 60)
            print(f"\n[FILE] {settings_path}:")
            print(json.dumps(settings, indent=2, ensure_ascii=False))
            print(f"\n[FILE] {docs_path}:")
            print(docs_content[:500] + "..." if len(docs_content) > 500 else docs_content)
        else:
            # Write settings
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            with settings_path.open('w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            print(f"[OK] Wrote: {settings_path}")

            # Write docs
            docs_path.parent.mkdir(parents=True, exist_ok=True)
            docs_path.write_text(docs_content, encoding='utf-8')
            print(f"[OK] Wrote: {docs_path}")

            # Sync to global if requested
            if args.sync_global:
                print("\n[*] Syncing to global ~/.claude/commands/...")
                templates_dir = project_root / ".claude" / "commands" / "templates"

                # Validate templates before sync
                is_valid, issues = validate_templates(templates_dir)

                if issues:
                    print("[*] Template validation:")
                    for issue in issues:
                        level = "ERROR" if not is_valid else "WARN"
                        print(f"  [{level}] {issue}")

                if not is_valid:
                    print("[ERROR] Template validation failed. Fix templates before syncing.")
                    print("[INFO] To create templates:")
                    print(f"  mkdir -p {templates_dir}")
                    print("  # Add noveler-write.md, noveler-quality.md, noveler-polish.md")
                    return 1

                # Perform sync
                global_dir = Path.home() / ".claude" / "commands"
                global_dir.mkdir(parents=True, exist_ok=True)

                import shutil
                synced_count = 0
                for template in templates_dir.glob("noveler-*.md"):
                    target = global_dir / template.name
                    shutil.copy2(template, target)
                    print(f"[OK] Synced to global: {template.name}")
                    synced_count += 1

                if synced_count == 0:
                    print("[WARN] No templates found matching 'noveler-*.md'")
                else:
                    print(f"[OK] Synced {synced_count} template(s) to global commands")

        print("\n[SUCCESS] Completed!")
        if args.sync_global and not args.dry_run:
            print("[INFO] Global commands synced. Restart Claude Code to use them.")
        return 0

    except CommandValidationError as e:
        print(f"[ERROR] Validation error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
