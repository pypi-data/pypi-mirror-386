#!/usr/bin/env python3
"""Provide compatibility helpers for the lightweight MCP JSON adapter.

The helpers in this module expose lean versions of the JSON conversion
utilities so that the MCP main module and the surrounding test harness can
interact without importing the heavy production server.
"""

from pathlib import Path
from typing import Any

from noveler.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager

# B20準拠: 共有コンポーネント利用（必須）
from noveler.presentation.shared.shared_utilities import get_common_path_service, get_logger


def convert_cli_to_json(cli_result: dict[str, Any]) -> dict[str, Any]:
    """Convert a CLI execution payload into a compact JSON response.

    Args:
        cli_result (dict[str, Any]): Raw CLI execution payload returned by the
            subprocess adapter.

    Returns:
        dict[str, Any]: Normalized payload containing stdout and stderr
        summaries together with basic execution metadata.
    """
    try:
        # 基本情報の抽出
        success = cli_result.get("success", False)
        command = cli_result.get("command", "")
        returncode = cli_result.get("returncode", 1)

        # 出力の要約（95%トークン削減アプローチ）
        stdout = cli_result.get("stdout", "")
        stderr = cli_result.get("stderr", "")

        # 長い出力は要約
        stdout_summary = stdout[:500] + "\n...(省略)...\n" + stdout[-500:] if len(stdout) > 1000 else stdout

        stderr_summary = stderr[:250] + "\n...(省略)...\n" + stderr[-250:] if len(stderr) > 500 else stderr

        # JSON変換結果
        return {
            "success": success,
            "command": command,
            "returncode": returncode,
            "stdout_summary": stdout_summary,
            "stderr_summary": stderr_summary,
            "token_reduction_applied": True,
            "mcp_server_version": "1.0.0",
            "conversion_time": "now"  # 簡易版
        }


    except Exception as e:
        return {
            "success": False,
            "error": f"JSON変換エラー: {e!s}",
            "original_data": cli_result
        }


def validate_json_response(json_data: dict[str, Any]) -> dict[str, Any]:
    """Validate the structural requirements of a JSON response payload.

    Args:
        json_data (dict[str, Any]): JSON object returned by
            :func:`convert_cli_to_json` or an equivalent helper.

    Returns:
        dict[str, Any]: Validation result that reports missing fields and the
        overall structural status.
    """
    try:
        # 基本構造の確認
        required_fields = ["success"]
        missing_fields = [field for field in required_fields if field not in json_data]

        if missing_fields:
            return {
                "valid": False,
                "error": f"必須フィールドが不足しています: {missing_fields}"
            }

        return {
            "valid": True,
            "structure": "valid",
            "field_count": len(json_data)
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"検証エラー: {e!s}"
        }


def get_file_by_hash(hash: str) -> dict[str, Any]:
    """Retrieve a stored file by its SHA256 digest.

    Args:
        hash (str): SHA256 digest expressed as a 64 character hexadecimal
            string.

    Returns:
        dict[str, Any]: Lookup result that echoes the hash, indicates whether
        the file was found, and, if available, returns file metadata and
        content.
    """
    logger = get_logger(__name__)

    try:
        # Use injectable manager factory to avoid heavy dependencies in tests
        output_dir = Path.cwd() / "temp" / "json_output"
        file_manager = _get_file_reference_manager(output_dir)

        # ハッシュ検索・内容取得
        result = file_manager.get_file_by_hash(hash)

        if not result:
            logger.debug(f"File not found for hash: {hash[:16]}...")
            return {
                "found": False,
                "hash": hash,
                "file": None,
                "error": "指定されたハッシュのファイルが見つかりません"
            }

        file_ref, content = result

        logger.info(f"File found for hash: {hash[:16]}..., path: {file_ref.path}")

        return {
            "found": True,
            "hash": hash,
            "file": {
                "path": file_ref.path,
                "size": file_ref.size_bytes,
                "content": content,
                "content_type": file_ref.content_type,
                "created_at": file_ref.created_at.isoformat()
            },
            "error": None
        }

    except Exception as e:
        logger.exception(f"get_file_by_hash error: {e}")
        return {
            "found": False,
            "hash": hash,
            "file": None,
            "error": f"ファイル取得エラー: {e!s}"
        }


# For tests: injectable factory
def _get_file_reference_manager(output_dir: Path) -> FileReferenceManager:
    """Instantiate a ``FileReferenceManager`` with the provided output path.

    Args:
        output_dir (Path): Directory that stores the serialized JSON output
            files managed by the adapter.

    Returns:
        FileReferenceManager: Manager that offers hash-aware file lookups and
        persistence utilities.
    """

    return FileReferenceManager(output_dir)


def check_file_changes(file_paths: list[str]) -> dict[str, Any]:
    """Determine whether tracked files changed since the previous snapshot.

    Args:
        file_paths (list[str]): Iterable of absolute or relative file paths
            whose content changes should be inspected.

    Returns:
        dict[str, Any]: Detailed per-file results and a summary counter that
        lists totals, changed files, and errors.
    """
    logger = get_logger(__name__)

    try:
        # Use injectable manager factory to avoid heavy dependencies in tests
        output_dir = Path.cwd() / "temp" / "json_output"
        file_manager = _get_file_reference_manager(output_dir)

        results = {}
        changed_count = 0
        error_count = 0

        for file_path_str in file_paths:
            try:
                file_path = Path(file_path_str)

                if not file_path.exists():
                    results[file_path_str] = {
                        "changed": False,
                        "previous_hash": "",
                        "current_hash": "",
                        "error": "ファイルが存在しません"
                    }
                    error_count += 1
                    continue

                # 変更検知（ハッシュインデックスから前回ハッシュ取得）
                changes = file_manager.track_changes()
                changed = changes.get(file_path_str, True)  # デフォルト変更あり

                # 現在のハッシュ計算
                from noveler.infrastructure.json.utils.hash_utils import calculate_sha256
                current_hash = calculate_sha256(file_path)

                # ハッシュインデックスから前回ハッシュ取得
                previous_hash = ""
                for hash_val, paths in file_manager._hash_index.items():
                    if file_path in paths:
                        previous_hash = hash_val
                        break

                results[file_path_str] = {
                    "changed": changed,
                    "previous_hash": previous_hash,
                    "current_hash": current_hash,
                    "error": None
                }

                if changed:
                    changed_count += 1

            except Exception as e:
                logger.exception(f"Error checking file {file_path_str}: {e}")
                results[file_path_str] = {
                    "changed": False,
                    "previous_hash": "",
                    "current_hash": "",
                    "error": f"チェックエラー: {e!s}"
                }
                error_count += 1

        logger.info(f"File change check completed: {len(file_paths)} files, {changed_count} changed, {error_count} errors")

        return {
            "results": results,
            "summary": {
                "total": len(file_paths),
                "changed": changed_count,
                "errors": error_count
            }
        }

    except Exception as e:
        logger.exception(f"check_file_changes error: {e}")
        return {
            "results": {},
            "summary": {"total": 0, "changed": 0, "errors": len(file_paths)},
            "error": f"変更チェックエラー: {e!s}"
        }


def list_files_with_hashes() -> dict[str, Any]:
    """List stored files grouped by their SHA256 digest.

    Returns:
        dict[str, Any]: Mapping of digests to file descriptors together with a
        summary of hash and file counts.
    """
    logger = get_logger(__name__)

    try:
        # B20準拠: 共有コンポーネント経由でパス取得
        path_service = get_common_path_service()
        output_dir = path_service.get_work_dir() / "json_output"

        # FileReferenceManager初期化
        file_manager = FileReferenceManager(output_dir)

        # ハッシュ・ファイル一覧取得
        hash_files = file_manager.list_files_with_hashes()

        # 詳細情報付きで整形
        files = {}
        total_files = 0

        for hash_val, file_paths in hash_files.items():
            file_details = []

            for file_path_str in file_paths:
                file_path = Path(file_path_str)
                if file_path.exists():
                    file_detail = {
                        "path": file_path_str,
                        "size": file_path.stat().st_size,
                        "content_type": _get_content_type_from_extension(file_path.suffix)
                    }
                    file_details.append(file_detail)
                    total_files += 1

            if file_details:
                files[hash_val] = file_details

        logger.info(f"File list retrieved: {len(files)} hashes, {total_files} files")

        return {
            "files": files,
            "summary": {
                "total_hashes": len(files),
                "total_files": total_files
            },
            "error": None
        }

    except Exception as e:
        logger.exception(f"list_files_with_hashes error: {e}")
        return {
            "files": {},
            "summary": {"total_hashes": 0, "total_files": 0},
            "error": f"ファイル一覧取得エラー: {e!s}"
        }


def _get_content_type_from_extension(extension: str) -> str:
    """Map a filename extension to an approximate content type.

    Args:
        extension (str): File extension including the leading dot (``.md``,
            ``.json`` and so on).

    Returns:
        str: MIME-like content type string understood by downstream consumers.
    """
    extension_map = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".yaml": "text/yaml",
        ".yml": "text/yaml"
    }
    return extension_map.get(extension.lower(), "text/plain")


def get_file_reference_info(file_path: str) -> dict[str, Any]:
    """Return lightweight metadata about the requested file path.

    Args:
        file_path (str): Absolute or relative path that should be inspected.

    Returns:
        dict[str, Any]: Metadata containing existence flags, the absolute path,
        file size, and basic classification fields.
    """
    try:
        from pathlib import Path

        path = Path(file_path)

        if not path.exists():
            return {
                "exists": False,
                "error": "ファイルが存在しません"
            }

        return {
            "exists": True,
            "path": str(path.absolute()),
            "size": path.stat().st_size,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "name": path.name
        }

    except Exception as e:
        return {
            "exists": False,
            "error": f"ファイル情報取得エラー: {e!s}"
        }
