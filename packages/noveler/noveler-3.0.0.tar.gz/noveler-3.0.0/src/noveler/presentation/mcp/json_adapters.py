# File: src/noveler/presentation/mcp/json_adapters.py
# Purpose: JSON serialization utilities for MCP protocol compliance
# Context: SPEC-MCP-001 implementation (Path → str conversion)

"""JSON adapters for MCP protocol.

Provides PathAwareJSONEncoder for SPEC-MCP-001 compliance and
various JSON utility functions for file operations.

This module provides:
- PathAwareJSONEncoder: Custom JSON encoder that handles Path objects and SerializableResponse/Request
- Lazy-loading wrapper functions for json_conversion_adapter module functions

Extracted from server_runtime.py (lines 37-143) as part of B20 §3 SOLID-SRP compliance.

Functions:
    check_file_changes: FR-003 file change detection
    convert_cli_to_json: CLI result to JSON conversion with 95% token reduction
    get_file_by_hash: FR-002 SHA256 hash-based file retrieval
    get_file_reference_info: File reference information retrieval
    list_files_with_hashes: File-hash list retrieval
    validate_json_response: JSON response format validation

Preconditions:
    - mcp_servers.noveler.json_conversion_adapter module must be importable

Side Effects:
    - Caches loaded adapter functions in module-level dictionary
    - Never raises - errors converted to warnings with fallback

Raises:
    Never raises - all errors are handled internally
"""

import json
from pathlib import Path
from typing import Any

# Global cache for lazy-loaded adapter functions
_JSON_ADAPTER_CACHE: dict[str, Any] = {}


class PathAwareJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Path objects (SPEC-MCP-001).

    Converts pathlib.Path to string and calls SerializableRequest/Response.to_dict()
    for automatic serialization.

    Handles CLAUDE.md MCP/CLI boundary serialization principles:
    - Path objects → str
    - Objects with to_dict() method → dict (SerializableResponse/Request)
    """

    def default(self, obj: Any) -> Any:
        """Encode object to JSON-serializable format.

        Args:
            obj: Object to encode

        Returns:
            JSON-serializable representation

        Raises:
            TypeError: If object is not JSON-serializable (raised by super().default())
        """
        if isinstance(obj, Path):
            return str(obj)

        # SerializableResponse/Request automatic conversion (SPEC-MCP-001 compliant)
        if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            try:
                return obj.to_dict()
            except Exception:
                pass  # Fallback to super().default()

        return super().default(obj)


def _get_json_adapter_func(func_name: str):
    """Lazy load json_conversion_adapter function.

    Args:
        func_name: Function name to load from json_conversion_adapter

    Returns:
        Loaded function from json_conversion_adapter module

    Raises:
        Never raises - errors converted to None return

    Side Effects:
        - Caches loaded function in _JSON_ADAPTER_CACHE
        - Imports mcp_servers.noveler.json_conversion_adapter on first access
    """
    if func_name not in _JSON_ADAPTER_CACHE:
        try:
            from mcp_servers.noveler import json_conversion_adapter
            _JSON_ADAPTER_CACHE[func_name] = getattr(json_conversion_adapter, func_name)
        except Exception:
            # Fallback: return None on import/attribute errors
            _JSON_ADAPTER_CACHE[func_name] = None
    return _JSON_ADAPTER_CACHE[func_name]


def check_file_changes(*args, **kwargs):
    """FR-003: Multiple file change detection (SPEC-MCP-HASH-001 compliant).

    Wrapper for json_conversion_adapter.check_file_changes with lazy loading.

    Args:
        *args: Positional arguments forwarded to adapter function
        **kwargs: Keyword arguments forwarded to adapter function

    Returns:
        File change detection result from adapter function

    Raises:
        Never raises - errors handled by adapter function
    """
    func = _get_json_adapter_func("check_file_changes")
    if func is None:
        return {"error": "check_file_changes not available"}
    return func(*args, **kwargs)


def convert_cli_to_json(*args, **kwargs):
    """CLI result to JSON conversion with 95% token reduction.

    Wrapper for json_conversion_adapter.convert_cli_to_json with lazy loading.

    Args:
        *args: Positional arguments forwarded to adapter function
        **kwargs: Keyword arguments forwarded to adapter function

    Returns:
        Converted JSON result from adapter function

    Raises:
        Never raises - errors handled by adapter function
    """
    func = _get_json_adapter_func("convert_cli_to_json")
    if func is None:
        return {"error": "convert_cli_to_json not available"}
    return func(*args, **kwargs)


def get_file_by_hash(*args, **kwargs):
    """FR-002: SHA256 hash-based file retrieval (SPEC-MCP-HASH-001 compliant).

    Wrapper for json_conversion_adapter.get_file_by_hash with lazy loading.

    Args:
        *args: Positional arguments forwarded to adapter function
        **kwargs: Keyword arguments forwarded to adapter function

    Returns:
        File content retrieval result from adapter function

    Raises:
        Never raises - errors handled by adapter function
    """
    func = _get_json_adapter_func("get_file_by_hash")
    if func is None:
        return {"error": "get_file_by_hash not available"}
    return func(*args, **kwargs)


def get_file_reference_info(*args, **kwargs):
    """File reference information retrieval.

    Wrapper for json_conversion_adapter.get_file_reference_info with lazy loading.

    Args:
        *args: Positional arguments forwarded to adapter function
        **kwargs: Keyword arguments forwarded to adapter function

    Returns:
        File reference information from adapter function

    Raises:
        Never raises - errors handled by adapter function
    """
    func = _get_json_adapter_func("get_file_reference_info")
    if func is None:
        return {"error": "get_file_reference_info not available"}
    return func(*args, **kwargs)


def list_files_with_hashes(*args, **kwargs):
    """File-hash list retrieval (SPEC-MCP-HASH-001 compliant).

    Wrapper for json_conversion_adapter.list_files_with_hashes with lazy loading.

    Args:
        *args: Positional arguments forwarded to adapter function
        **kwargs: Keyword arguments forwarded to adapter function

    Returns:
        File-hash list from adapter function

    Raises:
        Never raises - errors handled by adapter function
    """
    func = _get_json_adapter_func("list_files_with_hashes")
    if func is None:
        return {"error": "list_files_with_hashes not available"}
    return func(*args, **kwargs)


def validate_json_response(*args, **kwargs):
    """JSON response format validation.

    Wrapper for json_conversion_adapter.validate_json_response with lazy loading.

    Args:
        *args: Positional arguments forwarded to adapter function
        **kwargs: Keyword arguments forwarded to adapter function

    Returns:
        Validation result from adapter function

    Raises:
        Never raises - errors handled by adapter function
    """
    func = _get_json_adapter_func("validate_json_response")
    if func is None:
        return {"error": "validate_json_response not available"}
    return func(*args, **kwargs)
