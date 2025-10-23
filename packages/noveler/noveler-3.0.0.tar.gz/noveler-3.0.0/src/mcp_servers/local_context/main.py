#!/usr/bin/env python3
# File: src/mcp_servers/local_context/main.py
# Purpose: Provide a minimal, API‑key‑free MCP server that offers fast
#          workspace text search, file snippet reading, and simple file listing
#          to supply local context to LLM tools.
# Context: Runs as an MCP stdio server. Prefers ripgrep (rg) if available but
#          falls back to a pure-Python scan. No network/API dependencies. Safe
#          for use in restricted environments.
"""
Local Context MCP Server (API-key free)

Purpose:
  Provide simple, fast text search and file read utilities over the current
  working directory to supply context to the model without any external APIs.

Side Effects:
  - Spawns subprocesses when ripgrep is available (stdout captured).
  - Opens and reads files under the current working directory.

Tools:
- search_text: ripgrep-backed keyword search with optional before/after context
- read_file_snippet: read a file with line slicing helpers
- list_files: glob list files with basic metadata

Requires: Python 3.10+, ripgrep (rg) recommended. No API keys, no network.
"""

import asyncio
import importlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool


SERVER_NAME = "local-context-mcp"
ROOT = Path(os.getcwd())


def has_rg() -> bool:
    """Check if ripgrep (rg) is available in the current shell.

    Purpose:
        Detect availability of `rg` to choose a faster search path.

    Returns:
        bool: True when `rg` is found on PATH, otherwise False.

    Side Effects:
        Spawns a short-lived shell process to probe PATH.
    """
    return subprocess.call(["bash", "-lc", "command -v rg >/dev/null 2>&1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def safe_relpath(p: Path) -> str:
    """Safely convert an absolute path to a path relative to ROOT.

    Purpose:
        Normalise file paths for stable, compact JSON payloads.

    Args:
        p (Path): The candidate path.

    Returns:
        str: A relative path if possible, otherwise the original path string.

    Side Effects:
        None.
    """
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


class LocalContextServer:
    """MCP stdio server exposing local context tools.

    Purpose:
        Provide keyword search, file snippet reading, and file listing over the
        current workspace via MCP stdio.

    Side Effects:
        Registers tool handlers on a `Server` instance and may spawn rg.
    """

    def __init__(self) -> None:
        """Initialise the server and register tools.

        Purpose:
            Construct the underlying MCP `Server` and register handlers.

        Side Effects:
            Registers decorated functions on the server instance.
        """
        self.server = Server(SERVER_NAME)
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register tools on the MCP server instance.

        Purpose:
            Define list_tools/call_tool and tool schemas for this server.

        Returns:
            None

        Side Effects:
            Binds decorated functions to the `Server` instance.
        """
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List supported tools and their input schemas.

            Purpose:
                Advertise available tools to the MCP client.

            Returns:
                List[Tool]: Tool descriptors with input schemas.

            Side Effects:
                None.
            """
            return [
                Tool(
                    name="search_text",
                    description="キーワードでワークスペース内を高速検索（ripgrep使用可）。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "検索クエリ（正規表現可）"},
                            "glob": {"type": "string", "description": "rgの--glob（例: **/*.md）", "default": "**/*"},
                            "context_before": {"type": "integer", "default": 1},
                            "context_after": {"type": "integer", "default": 1},
                            "max_results": {"type": "integer", "default": 50}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="read_file_snippet",
                    description="ファイルの一部を行番号指定で取得。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "start_line": {"type": "integer", "default": 1},
                            "end_line": {"type": "integer", "description": "この行を含む"},
                            "before": {"type": "integer", "default": 0},
                            "after": {"type": "integer", "default": 0}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="list_files",
                    description="globでファイル一覧とサイズを取得。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "glob": {"type": "string", "default": "**/*"},
                            "max_files": {"type": "integer", "default": 200}
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Dispatch tool calls by name.

            Purpose:
                Route a generic MCP call to the corresponding tool handler.

            Args:
                name (str): Tool name.
                arguments (dict): Tool arguments.

            Returns:
                List[TextContent]: Text content payload with JSON string body.

            Side Effects:
                May spawn ripgrep and/or read files depending on the tool.
            """
            if name == "search_text":
                return await self._tool_search_text(arguments)
            if name == "read_file_snippet":
                return await self._tool_read_file_snippet(arguments)
            if name == "list_files":
                return await self._tool_list_files(arguments)
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False))]

    async def _tool_search_text(self, args: dict[str, Any]) -> List[TextContent]:
        """Search text in the workspace using rg if available.

        Purpose:
            Provide fast, contextual text search over the workspace.

        Args:
            args (dict[str, Any]): query, glob, context_before, context_after, max_results.

        Returns:
            List[TextContent]: JSON string with match results.

        Side Effects:
            May spawn ripgrep; reads files when falling back to Python scan.
        """
        query: str = args.get("query", "").strip()
        glob: str = args.get("glob", "**/*")
        before: int = int(args.get("context_before", 1))
        after: int = int(args.get("context_after", 1))
        max_results: int = int(args.get("max_results", 50))

        if not query:
            return [TextContent(type="text", text=json.dumps({"error": "query is required"}, ensure_ascii=False))]

        results: list[dict[str, Any]] = []

        if has_rg():
            # Use ripgrep JSON output
            cmd = [
                "bash", "-lc",
                f"rg --json --hidden --no-ignore --context {before}:{after} --max-count {max_results} --glob '{glob}' {json.dumps(query)}"
            ]
            try:
                proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
                for line in proc.stdout.splitlines():
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if obj.get("type") == "match":
                        data = obj.get("data", {})
                        path = data.get("path", {}).get("text")
                        lines = data.get("lines", {}).get("text", "")
                        line_number = data.get("line_number")
                        submatches = data.get("submatches", [])
                        results.append({
                            "file": path,
                            "line": line_number,
                            "text": lines,
                            "submatches": [s.get("match", {}).get("text") for s in submatches],
                        })
                        if len(results) >= max_results:
                            break
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": f"rg failed: {e}"}, ensure_ascii=False))]
        else:
            # Fallback: naive scan
            count = 0
            for p in ROOT.glob(glob):
                if p.is_file():
                    try:
                        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                    except Exception:
                        continue
                    for idx, line in enumerate(lines, start=1):
                        if query in line:
                            s = max(1, idx - before)
                            e = min(len(lines), idx + after)
                            snippet = "\n".join(lines[s-1:e])
                            results.append({"file": safe_relpath(p), "line": idx, "text": snippet})
                            count += 1
                            if count >= max_results:
                                break
                if len(results) >= max_results:
                    break

        payload = {"count": len(results), "results": results}
        return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

    async def _tool_read_file_snippet(self, args: dict[str, Any]) -> List[TextContent]:
        """Read a snippet of a file with optional line padding.

        Purpose:
            Extract a bounded region from a file for focused context.

        Args:
            args (dict[str, Any]): path, start_line, end_line, before, after.

        Returns:
            List[TextContent]: JSON string with meta and extracted text.

        Side Effects:
            Opens and reads the target file from disk.
        """
        rel = args.get("path")
        start = int(args.get("start_line", 1))
        end = args.get("end_line")
        before = int(args.get("before", 0))
        after = int(args.get("after", 0))

        if not rel:
            return [TextContent(type="text", text=json.dumps({"error": "path is required"}, ensure_ascii=False))]
        p = ROOT / rel
        if not p.exists() or not p.is_file():
            return [TextContent(type="text", text=json.dumps({"error": f"not a file: {rel}"}, ensure_ascii=False))]
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

        if end is None:
            end = start
        start = max(1, start - before)
        end = min(len(lines), end + after)
        snippet = "\n".join(lines[start-1:end])

        meta = {"file": safe_relpath(p), "start": start, "end": end, "length": end - start + 1}
        return [TextContent(type="text", text=json.dumps({"meta": meta, "text": snippet}, ensure_ascii=False))]

    async def _tool_list_files(self, args: dict[str, Any]) -> List[TextContent]:
        """List files by glob with basic metadata.

        Purpose:
            Provide a quick overview of files in the workspace.

        Args:
            args (dict[str, Any]): glob and max_files.

        Returns:
            List[TextContent]: JSON string with file entries.

        Side Effects:
            Accesses file metadata via os.stat; no file contents read.
        """
        glob = args.get("glob", "**/*")
        max_files = int(args.get("max_files", 200))
        files: list[dict[str, Any]] = []
        count = 0
        for p in ROOT.glob(glob):
            if p.is_file():
                try:
                    size = p.stat().st_size
                except Exception:
                    size = None
                files.append({"path": safe_relpath(p), "size": size})
                count += 1
                if count >= max_files:
                    break
        return [TextContent(type="text", text=json.dumps({"count": len(files), "files": files}, ensure_ascii=False))]


async def amain() -> None:
    """Async entrypoint to run the stdio MCP server.

    Purpose:
        Initialise and run the stdio-based MCP server for local context.

    Returns:
        None

    Side Effects:
        Imports bootstrap module (if present) to harden stdio, and starts the
        stdio server loop which reads from stdin and writes to stdout.
    """
    # Ensure stdout is protocol-only and logs go to stderr
    try:
        importlib.import_module("bootstrap_stdio")
    except Exception:
        pass
    srv = LocalContextServer()
    async with stdio_server() as (read_stream, write_stream):
        await srv.server.run(read_stream, write_stream)


def main() -> None:
    """Synchronous entrypoint wrapping the async server run.

    Purpose:
        Provide a simple blocking entrypoint for CLI execution.

    Returns:
        None

    Side Effects:
        Runs the asyncio event loop until server completion.
    """
    asyncio.run(amain())


if __name__ == "__main__":
    main()
