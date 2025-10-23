#!/usr/bin/env python3
"""Regenerate CLI ↔ MCP mapping tables in documentation."""

from __future__ import annotations

from pathlib import Path

from noveler.presentation.cli.cli_mapping import iter_mappings

BEGIN = "<!-- BEGIN CLI_MCP_TABLE -->"
END = "<!-- END CLI_MCP_TABLE -->"


def render_table() -> str:
    lines = ["| CLI Command | MCP Tool | Description |", "| --- | --- | --- |"]
    for mapping in iter_mappings():
        lines.append(
            f"| `{mapping.cli_command}` | `{mapping.mcp_tool}` | {mapping.description} |"
        )
    return "\n".join(lines)


def replace_section(text: str, replacement: str) -> str:
    if BEGIN not in text or END not in text:
        raise RuntimeError("Markers not found in README")
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END)
    return text[:start] + "\n" + replacement + "\n" + text[end:]


def main() -> None:
    readme = Path("README.md")
    table = render_table()
    content = readme.read_text(encoding="utf-8")
    updated = replace_section(content, table)
    readme.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()

