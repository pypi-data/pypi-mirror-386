"""Infrastructure.performance.async_file_processor
Where: Infrastructure module handling asynchronous file processing.
What: Provides utilities to process files concurrently with performance monitoring.
Why: Improves throughput for file-heavy workflows while tracking performance.
"""

from noveler.presentation.shared.shared_utilities import _get_console

console = _get_console()

"""
非同期ファイル処理ユーティリティ

Purpose: 大規模ファイル操作のパフォーマンス最適化
Architecture: Infrastructure Layer (DDD準拠)
Performance: I/O集約タスクの並列化によりスループット向上
"""
import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

try:  # noqa: WPS501 - optional dependency shield
    import aiofiles  # type: ignore[import]
except ImportError:  # pragma: no cover - exercised via unit tests without aiofiles
    aiofiles = None  # type: ignore[assignment]


class AsyncFileProcessor:
    """非同期ファイル処理クラス

    Features:
    - 並列ファイル読み込み・書き込み
    - バッチ処理によるメモリ効率の最適化
    - プログレスバー対応
    - エラー耐性・リトライ機能
    """

    def __init__(self, max_concurrent: int = 10, chunk_size: int = 1024) -> None:
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        from noveler.infrastructure.services.factories.logger_service_factory import get_logger_service

        self.logger_service = get_logger_service()

    async def process_files_batch(
        self,
        file_paths: list[Path],
        processor: Callable[[str, Path], Coroutine[Any, Any, Any]],
        show_progress: bool = True,
    ) -> list[Any]:
        """ファイルバッチ処理

        Args:
            file_paths: 処理対象ファイルリスト
            processor: 非同期処理関数 (content: str, path: Path) -> Any
            show_progress: プログレス表示フラグ

        Returns:
            List[Any]: 処理結果リスト
        """
        if show_progress:
            try:
                from tqdm.asyncio import tqdm

                progress_bar = tqdm(total=len(file_paths), desc="Processing files")
            except ImportError:
                progress_bar = None
                self.logger_service.info(f"Processing {len(file_paths)} files...")
        else:
            progress_bar = None

        async def process_single_file(file_path: Path) -> Any:
            async with self.semaphore:
                try:
                    if aiofiles is not None:
                        async with aiofiles.open(file_path, encoding="utf-8") as f:  # type: ignore[union-attr]
                            content = await f.read()
                    else:
                        content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
                    result = await processor(content, file_path)
                    if progress_bar:
                        progress_bar.update(1)
                    return result
                except Exception as e:
                    self.logger_service.warning(f"Failed to process {file_path}: {e}")
                    if progress_bar:
                        progress_bar.update(1)
                    return None

        try:
            results: Any = await asyncio.gather(
                *[process_single_file(path) for path in file_paths], return_exceptions=False
            )
            if progress_bar:
                progress_bar.close()
            return [r for r in results if r is not None]
        except Exception as e:
            if progress_bar:
                progress_bar.close()
            console.print(f"Batch processing failed: {e}")
            return []

    async def read_files_concurrent(self, file_paths: list[Path]) -> dict[Path, str]:
        """並列ファイル読み込み"""

        async def read_processor(content: str, path: Path) -> tuple[Path, str]:
            return (path, content)

        results: Any = await self.process_files_batch(file_paths, read_processor, show_progress=False)
        return dict(results)

    async def write_files_concurrent(self, file_data: dict[Path, str]) -> list[Path]:
        """並列ファイル書き込み"""

        async def write_single_file(file_path: Path, content: str) -> Path | None:
            async with self.semaphore:
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    if aiofiles is not None:
                        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:  # type: ignore[union-attr]
                            await f.write(content)
                    else:
                        await asyncio.to_thread(file_path.write_text, content, encoding="utf-8")
                    return file_path
                except Exception as e:
                    self.logger_service.warning(f"Failed to write {file_path}: {e}")
                    return None

        tasks = [write_single_file(path, content) for (path, content) in file_data.items()]
        results: Any = await asyncio.gather(*tasks, return_exceptions=False)
        return [r for r in results if r is not None]

    async def scan_directory_async(self, directory: Path, pattern: str = "*.py", max_depth: int = 10) -> list[Path]:
        """非同期ディレクトリスキャン"""

        def scan_sync() -> Any:
            return list(directory.rglob(pattern))

        return await asyncio.to_thread(scan_sync)


async def analyze_python_files_async(directory: Path, max_files: int = 1000) -> dict:
    """Pythonファイルの非同期解析"""
    processor = AsyncFileProcessor(max_concurrent=20)
    python_files = await processor.scan_directory_async(directory, "*.py")
    if len(python_files) > max_files:
        python_files = python_files[:max_files]
        console.print(f"Limited analysis to first {max_files} files")

    async def analyze_content(content: str, path: Path) -> dict:
        return {
            "path": str(path.relative_to(directory)),
            "lines": len(content.splitlines()),
            "chars": len(content),
            "functions": content.count("def "),
            "classes": content.count("class "),
            "todos": content.upper().count("TODO"),
        }

    results: Any = await processor.process_files_batch(python_files, analyze_content)
    total_lines = sum(r["lines"] for r in results)
    total_chars = sum(r["chars"] for r in results)
    total_functions = sum(r["functions"] for r in results)
    total_classes = sum(r["classes"] for r in results)
    total_todos = sum(r["todos"] for r in results)
    return {
        "files_analyzed": len(results),
        "total_lines": total_lines,
        "total_chars": total_chars,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "total_todos": total_todos,
        "avg_lines_per_file": total_lines / len(results) if results else 0,
        "largest_file": max(results, key=lambda x: x["lines"]) if results else None,
    }


async def main() -> None:
    """使用例"""
    project_dir = Path("scripts")
    stats = await analyze_python_files_async(project_dir)
    console.print("📊 Project Analysis Results:")
    console.print(f"   Files: {stats['files_analyzed']}")
    console.print(f"   Lines: {stats['total_lines']:,}")
    console.print(f"   Functions: {stats['total_functions']:,}")
    console.print(f"   Classes: {stats['total_classes']:,}")
    console.print(f"   TODOs: {stats['total_todos']}")
    if stats.get("largest_file"):
        console.print(
            f"   Largest file: {stats['largest_file']['path']} ({stats['largest_file']['lines']} lines)"
        )


if __name__ == "__main__":
    asyncio.run(main())
