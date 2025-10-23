#!/usr/bin/env python3
"""A38ステップ出力保存管理サービス

仕様: A38各ステップのLLM出力を.novelerフォルダに保存し、
     トレーサビリティとデバッグ性を向上させる機能を提供する。
"""

import json
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_path_service import IPathService
from noveler.domain.value_objects.structured_step_output import StructuredStepOutput
from noveler.domain.value_objects.project_time import project_now


class StepOutputManager:
    """A38ステップ出力保存管理サービス

    各A38ステップのLLM出力を構造化してファイルシステムに保存する。
    ファイル名形式: EP{episode_number:03d}_step{step:02d}_{timestamp}.json

    Attributes:
        _path_service: パスサービス（.novelerディレクトリ管理用）
    """

    def __init__(self, path_service: IPathService) -> None:
        """初期化

        Args:
            path_service: パスサービス
        """
        self._path_service = path_service

    async def save_step_output(
        self,
        episode_number: int,
        step_number: int,
        step_name: str,
        llm_response_content: str,
        structured_data: dict[str, Any],
        quality_metrics: dict[str, Any] | None = None,
        execution_metadata: dict[str, Any] | None = None,
    ) -> Path:
        """ステップ出力を保存"""
        if not 1 <= step_number <= 18:
            msg = f"ステップ番号は1-18の範囲である必要があります: {step_number}"
            raise ValueError(msg)

        if episode_number < 1:
            msg = f"エピソード番号は1以上である必要があります: {episode_number}"
            raise ValueError(msg)

        noveler_dir = await self._get_noveler_output_dir()
        noveler_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = project_now().datetime.strftime("%Y%m%d%H%M%S")

        filename = f"EP{episode_number:03d}_step{step_number:02d}_{timestamp_str}.json"
        file_path = noveler_dir / filename

        output_data = {
            "episode_number": episode_number,
            "step_number": step_number,
            "step_name": step_name,
            "timestamp": project_now().datetime.isoformat(),
            "llm_response": {
                "raw_content": llm_response_content,
                "content_length": len(llm_response_content),
                "content_preview": llm_response_content[:200] + ("..." if len(llm_response_content) > 200 else ""),
            },
            "structured_data": structured_data,
            "quality_metrics": quality_metrics or {},
            "execution_metadata": {
                **(execution_metadata or {}),
                "saved_at": project_now().datetime.isoformat(),
                "file_path": str(file_path),
                "format_version": "1.0.0",
            },
        }

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        return file_path

    async def save_structured_step_output(
        self,
        episode_number: int,
        step_number: int,
        structured_output: StructuredStepOutput,
        llm_response_content: str,
    ) -> Path:
        """StructuredStepOutputを保存

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号
            structured_output: 構造化ステップ出力
            llm_response_content: LLMからの生応答

        Returns:
            保存されたファイルのPath
        """
        return await self.save_step_output(
            episode_number=episode_number,
            step_number=step_number,
            step_name=structured_output.step_name,
            llm_response_content=llm_response_content,
            structured_data=structured_output.structured_data,
            quality_metrics={
                "overall_score": structured_output.quality_metrics.overall_score,
                "specific_metrics": structured_output.quality_metrics.specific_metrics,
            },
            execution_metadata=structured_output.execution_metadata,
        )

    async def load_step_output(self, file_path: Path) -> dict[str, Any]:
        """ステップ出力ファイルを読み込み

        Args:
            file_path: 読み込むファイルのパス

        Returns:
            保存されたステップ出力データ

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            json.JSONDecodeError: JSONが不正な場合
        """
        if not file_path.exists():
            msg = f"ステップ出力ファイルが見つかりません: {file_path}"
            raise FileNotFoundError(msg)

        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    async def list_step_outputs(
        self,
        episode_number: int | None = None,
        step_number: int | None = None,
    ) -> list[Path]:
        """ステップ出力ファイル一覧を取得

        Args:
            episode_number: フィルタするエピソード番号（オプション）
            step_number: フィルタするステップ番号（オプション）

        Returns:
            条件に一致するファイルパスのリスト
        """
        noveler_dir = await self._get_noveler_output_dir()

        if not noveler_dir.exists():
            return []

        # パターンマッチング用の文字列構築
        pattern = "EP"
        if episode_number is not None:
            pattern += f"{episode_number:03d}_step"
            if step_number is not None:
                pattern += f"{step_number:02d}_*.json"
            else:
                pattern += "*.json"
        else:
            pattern += "*_step"
            if step_number is not None:
                pattern += f"{step_number:02d}_*.json"
            else:
                pattern += "*.json"

        # ファイル一覧を取得してソート
        files = list(noveler_dir.glob(pattern))
        return sorted(files, key=lambda f: f.name)

    async def cleanup_old_outputs(
        self,
        episode_number: int,
        keep_latest: int = 5,
    ) -> int:
        """古いステップ出力ファイルをクリーンアップ

        Args:
            episode_number: 対象エピソード番号
            keep_latest: 保持する最新ファイル数（デフォルト: 5）

        Returns:
            削除されたファイル数
        """
        files = await self.list_step_outputs(episode_number=episode_number)

        if len(files) <= keep_latest:
            return 0

        # ファイル作成時刻でソート（古い順）
        files_with_time = []
        for file_path in files:
            if file_path.exists():
                try:
                    mtime = file_path.stat().st_mtime
                    files_with_time.append((mtime, file_path))
                except OSError:
                    pass

        # 作成時刻でソート（古い順）
        files_with_time.sort(key=lambda x: x[0])
        sorted_files = [f[1] for f in files_with_time]

        if len(sorted_files) <= keep_latest:
            return 0

        # 古いファイルを削除
        files_to_delete = sorted_files[:-keep_latest]
        deleted_count = 0

        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
            except OSError:
                # ファイル削除エラーは無視（ログに記録する場合は将来的に追加）
                pass

        return deleted_count

    async def _get_noveler_output_dir(self) -> Path:
        """.novelerディレクトリパスを取得"""
        try:
            if hasattr(self._path_service, "get_noveler_output_dir"):
                candidate = self._path_service.get_noveler_output_dir()
                if isinstance(candidate, Path):
                    return candidate
                if isinstance(candidate, str):
                    return Path(candidate)
        except Exception:
            pass

        try:
            project_root = getattr(self._path_service, "project_root", None)
            if callable(project_root):
                project_root = project_root()
            if project_root is None:
                raise AttributeError
            return Path(project_root) / ".noveler"
        except Exception:
            return Path.cwd() / ".noveler"

    async def get_step_output_statistics(
        self,
        episode_number: int | None = None,
    ) -> dict[str, Any]:
        """ステップ出力の統計情報を取得

        Args:
            episode_number: 対象エピソード番号（オプション）

        Returns:
            統計情報（ファイル数、総サイズなど）
        """
        files = await self.list_step_outputs(episode_number=episode_number)

        total_size = 0
        step_counts: dict[int, int] = {}

        for file_path in files:
            if file_path.exists():
                total_size += file_path.stat().st_size

                # ファイル名からステップ番号を抽出
                try:
                    name_parts = file_path.stem.split("_")
                    if len(name_parts) >= 2 and name_parts[1].startswith("step"):
                        step_num = int(name_parts[1][4:])  # "step01" -> 1
                        step_counts[step_num] = step_counts.get(step_num, 0) + 1
                except (ValueError, IndexError):
                    pass

        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "steps_coverage": len(step_counts),
            "step_file_counts": step_counts,
            "episode_filter": episode_number,
        }
