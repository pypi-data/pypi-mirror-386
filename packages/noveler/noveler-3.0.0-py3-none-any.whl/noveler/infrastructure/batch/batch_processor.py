"""バッチ処理最適化実装"""

import asyncio
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Generic, TypeVar

import yaml

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True)
class BatchResult(Generic[R]):
    """バッチ処理結果"""

    success_count: int = 0
    failure_count: int = 0
    results: list[R] = field(default_factory=list)
    errors: list[Exception] = field(default_factory=list)
    elapsed_time: float = 0.0


class BatchProcessor(Generic[T, R]):
    """汎用バッチ処理プロセッサ"""

    def __init__(self, batch_size: int, max_workers: int, use_process_pool: bool = False) -> None:
        """Args:
        batch_size: バッチサイズ
        max_workers: 並列実行ワーカー数
        use_process_pool: プロセスプールを使用するか
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.use_process_pool = use_process_pool
        self._stats_lock = Lock()
        self._stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "batch_count": 0,
        }

    def process_batch(
        self, items: list[T], processor: Callable[[T], R], error_handler: Callable[[Exception], None] | None = None
    ) -> BatchResult[R]:
        """バッチ処理を実行"""
        start_time = time.time()
        result = BatchResult[R]()

        # エグゼキュータの選択
        executor_class = ProcessPoolExecutor if self.use_process_pool else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            # 並列処理の実行
            futures = []
            for item in items:
                future = executor.submit(processor, item)
                futures.append((future, item))

            # 結果の収集
            for future, item in futures:
                try:
                    processed_result = future.result()
                    result.results.append(processed_result)
                    result.success_count += 1
                except Exception as e:
                    result.errors.append(e)
                    result.failure_count += 1
                    if error_handler:
                        error_handler(e, item)

        result.elapsed_time = time.time() - start_time

        # 統計更新
        self._update_stats(len(items), result.elapsed_time)

        return result

    def process_in_batches(
        self,
        items: list[T],
        processor: Callable[[T], R],
        batch_processor: Callable[[list[T]], BatchResult[R]] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BatchResult[R]:
        """アイテムをバッチに分けて処理"""
        total_result = BatchResult[R]()
        total_items = len(items)
        processed_count = 0

        # バッチに分割
        for i in range(0, total_items, self.batch_size):
            batch = items[i : i + self.batch_size]

            # バッチ処理
            batch_result = self.process_batch(batch, processor)

            # 結果をマージ
            total_result.success_count += batch_result.success_count
            total_result.failure_count += batch_result.failure_count
            total_result.results.extend(batch_result.results)
            total_result.errors.extend(batch_result.errors)
            total_result.elapsed_time += batch_result.elapsed_time

            # バッチ後処理
            if batch_processor and batch_result.results:
                batch_processor(batch_result.results)

            # 進捗コールバック
            processed_count += len(batch)
            if progress_callback:
                progress_callback(processed_count, total_items)

        return total_result

    async def process_batch_async(
        self, items: list[T], async_processor: Callable[[T], Any], concurrency_limit: int = 10
    ) -> BatchResult[R]:
        """非同期バッチ処理"""
        start_time = time.time()
        result = BatchResult[R]()

        # セマフォで同時実行数を制限
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def process_with_semaphore(item: T) -> R | None:
            async with semaphore:
                try:
                    return await async_processor(item)
                except Exception as e:
                    result.errors.append(e)
                    result.failure_count += 1
                    return None

        # 非同期処理の実行
        tasks = [process_with_semaphore(item) for item in items]
        processed_results = await asyncio.gather(*tasks)

        # 成功した結果のみ収集
        for processed in processed_results:
            if processed is not None:
                result.results.append(processed)
                result.success_count += 1

        result.elapsed_time = time.time() - start_time

        return result

    def _update_stats(self, item_count: int, elapsed_time: float) -> None:
        """統計情報を更新"""
        with self._stats_lock:
            self._stats["total_processed"] += item_count
            self._stats["total_time"] += elapsed_time
            self._stats["batch_count"] += 1

    def get_stats(self) -> dict[str, Any]:
        """処理統計を取得"""
        with self._stats_lock:
            avg_time_per_batch = (
                self._stats["total_time"] / self._stats["batch_count"] if self._stats["batch_count"] > 0 else 0
            )

            avg_items_per_second = (
                self._stats["total_processed"] / self._stats["total_time"] if self._stats["total_time"] > 0 else 0
            )

            return {
                "total_processed": self._stats["total_processed"],
                "total_time": self._stats["total_time"],
                "batch_count": self._stats["batch_count"],
                "avg_time_per_batch": avg_time_per_batch,
                "avg_items_per_second": avg_items_per_second,
                "batch_size": self.batch_size,
                "max_workers": self.max_workers,
            }


class FileBatchProcessor:
    """ファイル処理特化のバッチプロセッサ"""

    def __init__(self, batch_size: int) -> None:
        self.batch_processor = BatchProcessor[Path, dict[str, Any]](
            batch_size=batch_size,
            max_workers=8,
        )

    def load_yaml_files_batch(
        self,
        file_paths: list[Path],
    ) -> dict[Path, dict[str, Any]]:
        """YAMLファイルをバッチで読み込み"""

        def load_yaml(file_path: Path) -> tuple[Path, dict[str, Any]]:
            """YAMLファイルを読み込む。

            Args:
                file_path: 読み込むYAMLファイルのパス

            Returns:
                tuple[Path, dict[str, Any]]: ファイルパスと読み込んだデータ
            """
            try:
                with Path(file_path).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                return file_path, data
            except Exception:
                return file_path, None

        result = self.batch_processor.process_batch(
            file_paths,
            load_yaml,
        )

        # 辞書形式に変換
        return {path: data for path, data in result.results if data is not None}

    def save_yaml_files_batch(
        self,
        data_map: dict[Path, dict[str, Any]],
    ) -> BatchResult[Path]:
        """YAMLファイルをバッチで保存"""

        def save_yaml(item: tuple[Path, dict[str, Any]]) -> Path:
            """YAMLファイルを保存する。

            Args:
                item: 保存するファイルパスとデータのタプル

            Returns:
                Path: 保存されたファイルのパス
            """
            file_path, data = item
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with Path(file_path).open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

            return file_path

        items = list(data_map.items())
        return self.batch_processor.process_batch(items, save_yaml)

    def process_text_files_batch(
        self, file_paths: list[Path], text_processor: Callable[[str], str], output_dir: Path | None = None
    ) -> BatchResult[Path]:
        """テキストファイルをバッチ処理"""

        def process_file(file_path: Path) -> Path:
            """テキストファイルを処理する。

            Args:
                file_path: 処理するファイルのパス

            Returns:
                Path: 処理後のファイルパス
            """
            # ファイル読み込み
            content = file_path.read_text(encoding="utf-8")

            # 処理実行
            processed_content = text_processor(content)

            # 出力先決定
            if output_dir:
                output_path = output_dir / file_path.name
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = file_path

            # 保存
            output_path.write_text(processed_content, encoding="utf-8")

            return output_path

        return self.batch_processor.process_batch(file_paths, process_file)
