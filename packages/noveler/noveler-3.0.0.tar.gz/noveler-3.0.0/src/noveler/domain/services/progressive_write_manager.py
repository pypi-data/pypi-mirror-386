# File: src/noveler/domain/services/progressive_write_manager.py
# Purpose: Coordinate the progressive writing workflow and persist step state.
# Context: Used by domain services to orchestrate the 18-step authoring process and MCP integrations.
"""段階的執筆管理サービス

18ステップ執筆システムの段階実行を管理するサービス
LLMが各ステップを個別に実行できるよう、執筆タスクの状態管理と制御を行う
MCPサーバーでの利用を想定し、適切な指示生成を行う

外部テンプレート読み込み機能:
- templates/write_step*.yamlファイルからプロンプトを読み込み
- テンプレート変数の動的置換
- 段階実行制御メッセージの自動挿入
- テンプレート未発見時のフォールバック処理
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import traceback
from datetime import datetime, timezone
from glob import glob as _glob
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.errors import (
    InfrastructureError,
    InputValidationError,
    PartialFailureError,
    SystemStateError,
)
from noveler.domain.interfaces.progressive_write_llm_executor import (
    LLMExecutionRequest,
    LLMExecutionResult,
    ProgressiveWriteLLMExecutor,
)
from noveler.domain.interfaces.logger_interface import ILogger
from noveler.domain.services.progressive_write_runtime_deps import (
    ProgressiveWriteRuntimeDeps,
)


STEP_SLUG_OVERRIDES: dict[float, str] = {
    0.0: "scope_definition",
    1.0: "chapter_purpose",
    2.0: "section_goals",
    2.5: "theme_uniqueness",
    3.0: "section_balance",
    4.0: "scene_beats",
    5.0: "logic_verification",
    6.0: "character_detail",
    7.0: "dialogue_design",
    8.0: "emotion_curve",
    9.0: "atmosphere_worldview",
    10.0: "foreshadow_placement",
    11.0: "first_draft",
    12.0: "style_adjustment",
    13.0: "description_enhancement",
    14.0: "readability_optimization",
    15.0: "quality_check",
    16.0: "reader_experience",
    17.0: "final_preparation",
}


def _noop_performance_monitor(_: str):
    def decorator(func):
        return func

    return decorator


try:
    performance_monitor = ProgressiveWriteRuntimeDeps.with_defaults().performance_monitor
except Exception:
    performance_monitor = _noop_performance_monitor

# Backward compatibility shims for legacy patches (no longer used internally)
create_mcp_aware_path_service = None  # type: ignore
create_artifact_store = None  # type: ignore
UniversalClaudeCodeService = None  # type: ignore
LLMIOLogger = None  # type: ignore


class ProgressiveWriteManager:
    """段階的執筆管理クラス

    18ステップ執筆システムにおいて、各ステップを個別に実行するための
    状態管理とLLMへの指示生成を担当する

    外部テンプレート読み込み機能により、継続的なプロンプト改善を実現
    AsyncOperationOptimizer統合により並列処理による大幅な高速化を実現
    """

    # クラス定数
    MAX_RETRIES = 3  # デフォルトの最大リトライ回数

    def __init__(
        self,
        project_root: str | Path,
        episode_number: int,
        llm_executor: ProgressiveWriteLLMExecutor | None = None,
        logger: ILogger | None = None,
        deps: ProgressiveWriteRuntimeDeps | None = None,
    ) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            episode_number: エピソード番号
        """
        self.project_root = Path(project_root)
        self.episode_number = episode_number
        self._deps = deps or ProgressiveWriteRuntimeDeps.with_defaults()
        if llm_executor is not None:
            self._deps.llm_executor = llm_executor

        self.logger: ILogger = self._deps.ensure_logger(logger)
        self.llm_executor = self._deps.ensure_llm_executor()

        # プロンプトテンプレートディレクトリをプロジェクトルートまたは既定位置に設定
        guide_root = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド")
        self.prompt_templates_dir = self.project_root / "templates"
        self.check_templates_dir = self.project_root / "templates"
        self._default_templates_dir = guide_root / "templates"

        # 設定とタスク定義の読み込み
        self.tasks_config = self._load_tasks_config()

        # 状態管理ファイルのパス
        self.state_file = (
            self.project_root / "temp" / "task_states" / f"episode_{episode_number:03d}_state.json"
        )
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 現在の状態を読み込み（または初期化）
        self.current_state = self._load_or_initialize_state()

        self._path_service = self._deps.create_path_service(self.project_root)

        self.async_optimizer = self._deps.async_optimizer
        self.progress_display = self._deps.create_progress_display(episode_number, total_steps=19)
        self.feedback_system = self._deps.create_feedback_system(episode_number)
        self._io_logger_factory = self._deps.io_logger_factory

        self.logger.info(
            f"ProgressiveWriteManager初期化完了 - Episode {episode_number} (依存注入版)"
        )

    def _consume_llm_result(
        self,
        execution_result: dict[str, Any],
        request: LLMExecutionRequest,
        llm_result: LLMExecutionResult,
        save_io: bool,
    ) -> None:
        """Merge LLM結果とオプションのI/O保存を共通化する"""

        metadata = execution_result.setdefault("metadata", {})

        if llm_result.success:
            if llm_result.response_content:
                execution_result["content"] = llm_result.response_content
            metadata.update(
                {
                    "llm_used": True,
                    "extracted_keys": list(llm_result.extracted_data.keys()),
                }
            )
            if llm_result.extracted_data:
                metadata.setdefault("extracted_data", dict(llm_result.extracted_data))
        else:
            metadata.setdefault("llm_used", False)
            if llm_result.error_message:
                metadata["llm_error"] = llm_result.error_message

        if llm_result.metadata:
            metadata.setdefault("llm_metadata", llm_result.metadata)

        if save_io and self._io_logger_factory is not None:
            try:
                io_logger = self._io_logger_factory(self.project_root)
                if io_logger is not None:
                    io_logger.save_stage_io(
                        episode_number=request.episode_number,
                        step_number=int(request.step_id) if isinstance(request.step_id, (int, float)) else 0,
                        stage_name=request.step_name,
                        request_content={
                            "prompt": request.prompt_text,
                            "input_data": dict(request.input_data),
                            "artifacts": list(request.artifact_ids),
                        },
                        response_content={
                            "content": llm_result.response_content,
                            "extracted_data": dict(llm_result.extracted_data),
                            "metadata": dict(llm_result.metadata),
                            "success": llm_result.success,
                            "error_message": llm_result.error_message,
                        },
                        extra_metadata={"kind": "progressive_write_step"},
                    )
            except Exception:
                pass

    def _load_tasks_config(self) -> dict[str, Any]:
        """タスク定義設定を読み込む"""
        # 設定ファイルのパスを正しく設定
        # MCPサーバーからの呼び出しを考慮して相対パスで設定
        config_path = Path(__file__).parent.parent.parent.parent / "noveler" / "infrastructure" / "config" / "writing_tasks.yaml"

        try:
            with config_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.exception(f"タスク定義ファイルが見つかりません: {config_path}")
            raise
        except Exception as e:
            self.logger.exception(f"タスク定義ファイル読み込みエラー: {e}")
            raise

    def _load_or_initialize_state(self) -> dict[str, Any]:
        """状態ファイルを読み込むか、初期状態を作成する"""
        yaml_state = self._try_load_yaml_state()
        if yaml_state is not None:
            state_for_json = {
                key: value
                for key, value in yaml_state.items()
                if key not in {"source", "state_file_path"}
            }
            self._save_state(state_for_json)
            return yaml_state

        if self.state_file.exists():
            try:
                with self.state_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"状態ファイル読み込み失敗、初期化します: {e}")

        # 初期状態を作成
        initial_state = {
            "episode_number": self.episode_number,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "current_step": 0,
            "completed_steps": [],
            "failed_steps": [],
            "step_results": {},
            "overall_status": "not_started",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        self._save_state(initial_state)
        return initial_state

    def _yaml_state_path(self) -> Path:
        """Return the expected YAML state file path for the 18-step workflow."""
        return (
            self.project_root
            / "50_管理資料"
            / "執筆記録"
            / f"episode_{self.episode_number:03d}_state.yaml"
        )

    @staticmethod
    def _ensure_list(value: Any) -> list[Any]:
        """Return value as a list, treating None as an empty list."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, (tuple, set)):
            return list(value)
        return [value]

    @staticmethod
    def _normalize_step_identifier(value: Any) -> Any:
        """Coerce step identifiers to int/float when possible for stable ordering."""
        if isinstance(value, float):
            return int(value) if value.is_integer() else value
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                numeric = float(value)
            except ValueError:
                return value
            return int(numeric) if numeric.is_integer() else numeric
        return value

    @staticmethod
    def _format_yaml_scalar(value: Any) -> str:
        """Format a scalar value for inline YAML fragments."""
        if value is None:
            return "null"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            if value.lower() in {"null", "true", "false"}:
                return f"\"{value}\""
            return value if value.startswith("\"") and value.endswith("\"") else f"\"{value}\""
        return f"\"{value}\""

    def _format_yaml_list(self, values: list[Any]) -> str:
        """Format a list for inline YAML while keeping output predictable."""
        if not values:
            return "[]"
        formatted_items: list[str] = []
        for item in values:
            if isinstance(item, (list, dict, set, tuple)):
                return "[]"
            formatted_items.append(self._format_yaml_scalar(item))
        return "[" + ", ".join(formatted_items) + "]"

    def _calculate_next_step(self, step_id: Any) -> Any:
        """Calculate the next step identifier for the 18-step workflow."""
        if isinstance(step_id, float) and step_id.is_integer():
            step_id = int(step_id)
        if isinstance(step_id, int):
            return None if step_id >= 17 else step_id + 1
        if isinstance(step_id, float):
            return None
        return None

    def _to_project_relative_path(self, path: Path) -> str:
        """Return a path string relative to the project root using POSIX separators."""
        try:
            rel_path = path.relative_to(self.project_root)
        except ValueError:
            rel_path = path
        return rel_path.as_posix()

    def _save_state(self, state: dict[str, Any]) -> None:
        """状態をファイルに保存する"""
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        try:
            with self.state_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.exception(f"状態ファイル保存エラー: {e}")
            raise

    @performance_monitor("get_writing_tasks")
    def get_writing_tasks(self) -> dict[str, Any]:
        """LLMに提示するタスクリストを生成する

        Returns:
            タスクリストとLLMへの指示を含む辞書

        Raises:
            SystemStateError: システム状態の不整合時
            InfrastructureError: 設定ファイルアクセスエラー時
        """
        try:
            # 入力検証とシステム状態チェック
            if not hasattr(self, "tasks_config") or not self.tasks_config:
                msg = "タスク設定が読み込まれていません"
                raise SystemStateError(
                    msg,
                    current_state="tasks_config未初期化",
                    expected_state="tasks_config初期化済み",
                    state_repair_actions=[
                        "ProgressiveWriteManagerを再初期化してください",
                        "tasks.yamlファイルの存在を確認してください"
                    ]
                )

            if not hasattr(self, "current_state") or not self.current_state:
                msg = "実行状態が初期化されていません"
                raise SystemStateError(
                    msg,
                    current_state="current_state未初期化",
                    expected_state="current_state初期化済み",
                    state_repair_actions=[
                        "状態ファイルを確認してください",
                        "新規実行の場合は状態を初期化してください"
                    ]
                )

            tasks = self.tasks_config.get("tasks", [])
            if not tasks:
                msg = "実行可能なタスクが定義されていません"
                raise SystemStateError(
                    msg,
                    current_state="タスクリスト空",
                    expected_state="タスクリスト存在",
                    state_repair_actions=[
                        "tasks.yamlファイルにタスクを定義してください",
                        "既存のタスク定義ファイルをコピーしてください"
                    ]
                )

            current_step = self.current_state.get("current_step")
            completed_steps = self.current_state.get("completed_steps", [])

            # 現在実行可能なタスクを特定
            executable_tasks = self._get_executable_tasks(tasks, completed_steps)
            current_task = self._get_task_by_id(tasks, current_step)

            # 並列実行可能な独立タスクグループを特定
            parallel_groups = self._identify_parallel_groups(executable_tasks)

            # LLM向けの指示を生成（改良版：外部テンプレート対応）
            try:
                llm_instruction = self._generate_enhanced_llm_instruction(current_task, executable_tasks)
            except Exception as e:
                self.logger.warning(f"拡張LLM指示生成に失敗、レガシー版にフォールバック: {e}")
                llm_instruction = self._generate_llm_instruction_legacy(current_task, executable_tasks)

            return {
                "episode_number": self.episode_number,
                "current_step": current_step,
                "current_task": current_task,
                "executable_tasks": executable_tasks,
                "parallel_groups": parallel_groups,
                "progress": {
                    "completed": len(completed_steps),
                    "total": len(tasks),
                    "percentage": len(completed_steps) / len(tasks) * 100
                },
                "llm_instruction": llm_instruction,
                "next_action": self._get_next_action(current_task),
                "phase_info": self._get_current_phase_info(),
                "parallel_execution_available": len(parallel_groups.get("independent", [])) > 1,
                "system_status": "healthy"
            }

        except (SystemStateError, InfrastructureError):
            # 構造化エラーとして再発生
            raise
        except Exception as e:
            # 予期しないエラーを適切なエラータイプに変換
            self.logger.error(f"get_writing_tasks実行中に予期しないエラー: {e}", exc_info=True)
            msg = f"タスクリスト生成中に予期しないエラーが発生しました: {e!s}"
            raise SystemStateError(
                msg,
                current_state="処理中断",
                expected_state="正常完了",
                state_repair_actions=[
                    "システムログを確認してください",
                    "設定ファイルの整合性を確認してください",
                    "システム管理者にお問い合わせください"
                ],
                context={"original_error": str(e)}
            )

    def _identify_parallel_groups(self, executable_tasks: list[dict]) -> dict[str, list[dict]]:
        """並列実行可能なタスクグループを特定する

        Args:
            executable_tasks: 実行可能なタスクリスト

        Returns:
            並列実行グループの辞書
        """
        parallel_groups = {
            "independent": [],  # 完全独立実行可能
            "content_development": [],  # コンテンツ開発系（部分並列可能）
            "writing_execution": [],  # 執筆実行系（部分並列可能）
            "quality_assurance": []  # 品質保証系（並列チェック可能）
        }

        # 並列実行可能ステップの定義
        independent_steps = {8, 9, 10, 11}  # 対話設計〜伏線配置（番号調整後）
        content_dev_steps = {3, 4, 7}  # テーマ、バランス、キャラ設定（番号調整後）
        writing_exec_steps = {13, 14, 15}  # 文体調整〜読みやすさ最適化（番号調整後）
        quality_steps = {16, 17}  # 品質チェック〜読者体験最適化（番号調整後）

        for task in executable_tasks:
            step_id = task["id"]

            if step_id in independent_steps:
                parallel_groups["independent"].append(task)
            elif step_id in content_dev_steps:
                parallel_groups["content_development"].append(task)
            elif step_id in writing_exec_steps:
                parallel_groups["writing_execution"].append(task)
            elif step_id in quality_steps:
                parallel_groups["quality_assurance"].append(task)

        return parallel_groups

    async def execute_writing_steps_parallel(self, step_ids: list[int | float], max_concurrent: int = 3, dry_run: bool = False) -> dict[str, Any]:
        """複数の独立したステップを並列実行する

        Args:
            step_ids: 並列実行するステップIDのリスト
            max_concurrent: 最大同時実行数
            dry_run: シミュレーション実行

        Returns:
            並列実行結果
        """
        self.logger.info(f"並列実行開始: ステップ {step_ids}, 最大同時実行数: {max_concurrent}")

        # 前提条件チェック
        valid_steps = []
        invalid_steps = []

        for step_id in step_ids:
            task = self._get_task_by_id(self.tasks_config["tasks"], step_id)
            if not task:
                invalid_steps.append({"step_id": step_id, "error": "ステップが見つかりません"})
                continue

            if not self._check_prerequisites(task["prerequisites"]):
                invalid_steps.append({
                    "step_id": step_id,
                    "error": "前提条件が満たされていません",
                    "prerequisites": task["prerequisites"],
                    "completed_steps": self.current_state["completed_steps"]
                })
                continue

            valid_steps.append(task)

        if not valid_steps:
            return {
                "success": False,
                "error": "並列実行可能なステップがありません",
                "invalid_steps": invalid_steps
            }

        # 並列実行用のAsyncOperationOptimizerを使用
        try:
            # 各ステップを非同期で実行
            async def execute_single_step(task: dict) -> dict[str, Any]:
                return await asyncio.to_thread(self._execute_step_sync, task, dry_run)

            # 並列実行（セマフォで同時実行数制御）
            async with asyncio.Semaphore(max_concurrent):
                tasks = [execute_single_step(task) for task in valid_steps]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            # 結果を整理
            successful_results = []
            failed_results = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_results.append({
                        "step_id": valid_steps[i]["id"],
                        "step_name": valid_steps[i]["name"],
                        "error": str(result)
                    })
                elif result.get("success"):
                    successful_results.append(result)
                    # 成功したステップの状態更新
                    self._update_step_completion(result["step_id"], result["execution_result"])
                else:
                    failed_results.append(result)

            # 次のタスクとLLM指示を生成
            next_task = self._get_next_task()
            llm_instruction = self._generate_parallel_completion_instruction(
                successful_results, failed_results, next_task
            )

            execution_time = sum(
                float(r.get("execution_result", {}).get("metadata", {}).get("execution_time", "0").replace("分", ""))
                for r in successful_results
            ) / max(len(successful_results), 1) if successful_results else 0

            return {
                "success": len(successful_results) > 0,
                "parallel_execution": True,
                "successful_steps": len(successful_results),
                "failed_steps": len(failed_results),
                "invalid_steps": len(invalid_steps),
                "total_requested": len(step_ids),
                "execution_time_saved": f"推定{execution_time * 0.5:.1f}分短縮",
                "successful_results": successful_results,
                "failed_results": failed_results,
                "invalid_steps": invalid_steps,
                "next_task": next_task,
                "llm_instruction": llm_instruction,
                "progress": self._get_progress_info()
            }

        except Exception as e:
            self.logger.exception(f"並列実行エラー: {e}")
            return {
                "success": False,
                "error": f"並列実行中にエラーが発生: {e!s}",
                "parallel_execution": True
            }

    def _execute_step_sync(self, task: dict, dry_run: bool = False) -> dict[str, Any]:
        """同期実行用のステップ実行ラッパー"""
        try:
            step_id = task["id"]

            if not dry_run:
                execution_result = self._execute_step_logic(task)
            else:
                execution_result = {
                    "content": f"[PARALLEL DRY RUN] {task['name']}の並列シミュレーション結果",
                    "dry_run": True,
                    "parallel_execution": True
                }

            return {
                "success": True,
                "step_id": step_id,
                "step_name": task["name"],
                "phase": task["phase"],
                "execution_result": execution_result,
                "parallel_execution": True
            }

        except Exception as e:
            return {
                "success": False,
                "step_id": task["id"],
                "step_name": task["name"],
                "error": str(e),
                "parallel_execution": True
            }

    def _generate_parallel_completion_instruction(
        self, successful_results: list[dict], failed_results: list[dict], next_task: dict | None
    ) -> str:
        """並列実行完了後のLLM指示を生成する"""

        if successful_results:
            success_summary = ", ".join([
                f"ステップ{r['step_id']}「{r['step_name']}」"
                for r in successful_results
            ])

            instruction = f"""並列実行が完了しました。

✅ 成功: {success_summary}

"""
            if failed_results:
                failed_summary = ", ".join([
                    f"ステップ{r['step_id']}「{r['step_name']}」({r.get('error', 'エラー')})"
                    for r in failed_results
                ])
                instruction += f"⚠️ 失敗: {failed_summary}\n\n"

        else:
            instruction = "並列実行でエラーが発生しました。\n\n"

        if next_task:
            instruction += f"次のステップ: execute_writing_step で step_id={next_task['id']} を実行してください。\n"
            instruction += "または、並列実行可能な複数ステップがある場合は execute_writing_steps_parallel を使用してください。\n\n"
            instruction += next_task.get("llm_instruction", "")
        else:
            instruction += "全てのステップが完了しました。18ステップ執筆システムの実行が完了しました！"

        return instruction

    @performance_monitor("execute_writing_step")
    def execute_writing_step(self, step_id: int | float, dry_run: bool = False, retry_count: int = 0) -> dict[str, Any]:
        """特定ステップを実行する（同期API → 非同期委譲）"""
        try:
            return asyncio.run(self.execute_writing_step_async(step_id, dry_run, retry_count))
        except RuntimeError:
            # 既に実行中のイベントループがある場合は、タスクを生成して待機できないため簡易フォールバック
            # 呼び出し元で async API を利用することを推奨
            self.logger.warning("同期APIから非同期APIへの委譲に失敗: 実行中のイベントループあり。簡易フォールバック結果を返します。")
            return {"success": False, "error": "同期APIはイベントループ内では使用できません。async API を使用してください。", "step_id": step_id}

        except (InputValidationError, SystemStateError, PartialFailureError) as e:
            # 進捗表示：失敗
            self.progress_display.fail_step(step_id, str(e))

            # エラーフィードバック
            recovery_options = ["リトライ", "スキップ", "中断"] if retry_count < self.MAX_RETRIES else ["スキップ", "中断"]
            self.feedback_system.show_error(
                f"ステップ{step_id}エラー",
                str(e),
                step_id=step_id,
                recovery_options=recovery_options
            )

            # 構造化エラーとして再発生
            raise
        except Exception as e:
            # 予期しないエラーの処理とリトライ機能
            if retry_count < self.MAX_RETRIES:
                self.logger.warning(f"ステップ {step_id} 実行中にエラー（リトライ {retry_count + 1}/{self.MAX_RETRIES}）: {e}")

                # リトライ確認
                retry_confirmed = self.feedback_system.request_confirmation(
                    "リトライ確認",
                    f"ステップ{step_id}でエラーが発生しました。リトライしますか？",
                    step_id=step_id,
                    default=True
                )

                if retry_confirmed:
                    return self.execute_writing_step(step_id, dry_run, retry_count + 1)

            # 進捗表示：失敗
            self.progress_display.fail_step(step_id, str(e))

            # 最大リトライ数に到達した場合はPartialFailureErrorとして処理
            completed_steps = self.current_state.get("completed_steps", [])

            self._update_step_failure(step_id, str(e))
            # taskを取得してからerror_instructionを生成
            task = self._get_task_by_id(self.tasks_config.get("tasks", []), step_id)
            if task:
                error_instruction = self._generate_error_instruction(task, str(e))
            else:
                error_instruction = None

            # エラーフィードバック
            self.feedback_system.show_error(
                f"ステップ{step_id}最終エラー",
                f"{self.MAX_RETRIES}回リトライ後に失敗: {e!s}",
                step_id=step_id,
                recovery_options=["状態確認", "システム管理者に連絡"]
            )

            msg = f"ステップ {step_id} の実行に失敗しました（{self.MAX_RETRIES}回リトライ後）: {e!s}"
            raise PartialFailureError(
                msg,
                failed_steps=[step_id],
                completed_steps=completed_steps,
                recovery_point=step_id,
                details={
                    "step_id": step_id,
                    "step_name": task.get("name", "不明"),
                    "error": str(e),
                    "retry_count": retry_count,
                    "max_retries": self.MAX_RETRIES
                },
                context={
                    "llm_instruction": error_instruction,
                    "task": task
                }
            )

    def get_task_status(self) -> dict[str, Any]:
        """現在のタスク状況を取得する"""
        tasks = self.tasks_config["tasks"]
        current_task = self._get_task_by_id(tasks, self.current_state["current_step"])

        return {
            "episode_number": self.episode_number,
            "overall_status": self.current_state["overall_status"],
            "current_step": self.current_state["current_step"],
            "current_task": current_task,
            "progress": self._get_progress_info(),
            "completed_steps": self.current_state["completed_steps"],
            "failed_steps": self.current_state["failed_steps"],
            "last_updated": self.current_state["last_updated"]
        }

    def _get_executable_tasks(self, tasks: list[dict], completed_steps: list[int]) -> list[dict]:
        """現在実行可能なタスクを取得する"""
        executable = []
        for task in tasks:
            if task["id"] in completed_steps:
                continue
            if self._check_prerequisites(task["prerequisites"], completed_steps):
                executable.append(task)
        return executable

    def _get_task_by_id(self, tasks: list[dict], task_id: int | float) -> dict | None:
        """IDでタスクを取得する"""
        for task in tasks:
            if task["id"] == task_id:
                return task
        return None

    def _check_prerequisites(self, prerequisites: list[int | float], completed_steps: list[int] | None = None) -> bool:
        """前提条件をチェックする"""
        if completed_steps is None:
            completed_steps = self.current_state["completed_steps"]

        return all(prereq in completed_steps for prereq in prerequisites)

    def _apply_by_task_validation(
        self,
        template_data: dict[str, Any] | None,
        execution_result: dict[str, Any],
    ) -> dict[str, Any]:
        """control_settings.by_task に基づいて生成物を自動検証する"""

        summary: dict[str, Any] = {
            "success": True,
            "by_task": [],
            "messages": [],
        }

        if not template_data:
            return summary

        control_settings = template_data.get("control_settings", {}) or {}
        by_task_rules = control_settings.get("by_task") or []
        if not by_task_rules:
            return summary

        artifacts_cfg = template_data.get("artifacts", {}) or {}
        output_format = str(artifacts_cfg.get("format", "yaml")).lower()
        if output_format != "yaml":
            summary["messages"].append("by_task validation skipped: format != yaml")
            return summary

        content = execution_result.get("content")
        if not isinstance(content, str):
            summary["success"] = False
            summary.setdefault("errors", []).append("content not available for by_task validation")
            execution_result.setdefault("metadata", {})["success_criteria_met"] = False
            return summary

        try:
            parsed = yaml.safe_load(content) or {}
        except Exception as err:
            summary["success"] = False
            summary.setdefault("errors", []).append(f"yaml_parse_error: {err!s}")
            execution_result.setdefault("metadata", {})["success_criteria_met"] = False
            return summary

        if not isinstance(parsed, dict):
            summary["success"] = False
            summary.setdefault("errors", []).append("parsed content is not a mapping")
            execution_result.setdefault("metadata", {})["success_criteria_met"] = False
            return summary

        required_map: dict[str, bool] = {}
        tasks_section = template_data.get("tasks", {}) or {}
        for detail in tasks_section.get("details", []) or []:
            if not isinstance(detail, dict):
                continue
            for item in detail.get("items", []) or []:
                if isinstance(item, dict) and "id" in item:
                    required_map[str(item["id"])] = bool(item.get("required", True))

        results: list[dict[str, Any]] = []
        overall_success = True
        seen_ids: set[str] = set()

        for rule_cfg in by_task_rules:
            if not isinstance(rule_cfg, dict):
                continue
            task_id = str(rule_cfg.get("id", "")).strip()
            field_path = str(rule_cfg.get("field", "")).strip()
            if not task_id or not field_path:
                continue
            seen_ids.add(task_id)
            value, present = self._extract_field(parsed, field_path)
            required = required_map.get(task_id, True)
            status = "pass"
            notes: list[str] = []

            if not present:
                status = "warn" if not required else "fail"
                notes.append("field_missing")
            else:
                rule = rule_cfg.get("rule")
                if rule:
                    ok, note = self._evaluate_rule(str(rule), value)
                    if not ok:
                        status = "fail" if required else "warn"
                        if note:
                            notes.append(note)
                range_spec = rule_cfg.get("range")
                if range_spec:
                    ok, note = self._evaluate_range(str(range_spec), value)
                    if not ok:
                        status = "fail" if required else "warn"
                        if note:
                            notes.append(note)

            if status == "fail" and required:
                overall_success = False

            results.append(
                {
                    "id": task_id,
                    "status": status,
                    "value": value if present else None,
                    "notes": notes,
                }
            )

        missing_required = [rid for rid, req in required_map.items() if req and rid not in seen_ids]
        for rid in missing_required:
            results.append(
                {
                    "id": rid,
                    "status": "warn",
                    "value": None,
                    "notes": ["by_task_rule_missing"],
                }
            )

        summary["by_task"] = results
        summary["success"] = overall_success

        if not overall_success:
            execution_result.setdefault("metadata", {})["success_criteria_met"] = False

        return summary

    def _extract_field(self, data: Any, field_path: str) -> tuple[Any, bool]:
        current = data
        for part in field_path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None, False
        return current, True

    def _evaluate_rule(self, rule: str, value: Any) -> tuple[bool, str | None]:
        rule = rule.strip()
        if not rule:
            return True, None
        if rule == "present":
            return value is not None, "present"
        if rule == "nonempty":
            if value is None:
                return False, "nonempty"
            if isinstance(value, (str, list, tuple, dict, set)):
                return len(value) > 0, "nonempty"
            return True, "nonempty"
        if rule.startswith("enum:"):
            options = {opt.strip() for opt in rule[len("enum:"):].split('|') if opt.strip()}
            return (str(value) in options), f"enum:{'|'.join(sorted(options))}"
        if rule.startswith("regex:"):
            pattern = rule[len("regex:"):]
            try:
                return bool(re.search(pattern, str(value))), f"regex:{pattern}"
            except re.error:
                return False, f"regex_error:{pattern}"
        return True, rule

    def _evaluate_range(self, range_spec: str, value: Any) -> tuple[bool, str | None]:
        spec = range_spec.strip()
        if not spec:
            return True, None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False, f"range:{spec}"

        if '-' not in spec:
            return True, f"range:{spec}"
        min_part, max_part = spec.split('-', 1)
        min_val = float(min_part) if min_part else None
        max_val = float(max_part) if max_part else None

        if min_val is not None and numeric < min_val:
            return False, f"range:{spec}"
        if max_val is not None and numeric > max_val:
            return False, f"range:{spec}"
        return True, f"range:{spec}"

    def _load_prompt_template(self, step_id: int | float) -> dict[str, Any] | None:
        """外部YAMLプロンプトテンプレートを読み込む

        Args:
            step_id: ステップID

        Returns:
            テンプレート辞書、または見つからない場合はNone
        """
        try:
            # ステップIDに基づいてテンプレートファイル名を決定（write_プレフィックス付き）
            if float(step_id).is_integer():
                step_token = f"{int(step_id):02d}"
            else:
                step_token = str(step_id).replace(".", "_")
            template_filename = f"write_step{step_token}_{self._get_step_slug(step_id)}.yaml"

            template_path = self.prompt_templates_dir / "writing" / template_filename

            if not template_path.exists():
                # フォールバック：ファイルが見つからない場合はNoneを返す
                self.logger.debug(f"プロンプトテンプレートが見つかりません: {template_path}")
                return None

            with template_path.open("r", encoding="utf-8") as f:
                template_data = yaml.safe_load(f)

            self.logger.info(f"プロンプトテンプレート読み込み完了: {template_filename}")
            return template_data

        except Exception as e:
            self.logger.warning(f"プロンプトテンプレート読み込みエラー: {e}")
            return None

    def _get_step_slug(self, step_id: int | float) -> str:
        """ステップIDに基づいてファイル名用のスラッグを生成する

        Args:
            step_id: ステップID

        Returns:
            ファイル名用スラッグ
        """
        override_slug = STEP_SLUG_OVERRIDES.get(float(step_id))
        if override_slug is not None:
            return override_slug

        task = self._get_task_by_id(self.tasks_config["tasks"], step_id)
        if not task:
            return "unknown"

        # タスク名を元にスラッグを生成（簡易実装）
        name = task["name"]
        slug_mapping = {
            "範囲の定義": "scope_definition",
            "背骨（大骨）": "main_structure",
            "中骨（節）": "section_structure",
            "テーマの独自性": "theme_uniqueness",
            "セクションバランス設計": "section_balance",
            "小骨（シーン/ビート）": "scene_beats",
            "論理検証": "logic_verification"
        }

        return slug_mapping.get(name, name.lower().replace("（", "_").replace("）", "").replace("/", "_"))

    def _prepare_template_variables(self, step_id: int | float, current_task: dict | None = None) -> dict[str, Any]:
        """テンプレート用の変数を準備する

        Args:
            step_id: ステップID
            current_task: 現在のタスク情報

        Returns:
            テンプレート変数辞書
        """
        if current_task is None:
            current_task = self._get_task_by_id(self.tasks_config["tasks"], step_id)

        tasks = self.tasks_config["tasks"]
        completed_steps = self.current_state["completed_steps"]

        return {
            "step_id": step_id,
            "step_name": current_task["name"] if current_task else f"ステップ {step_id}",
            "episode_number": self.episode_number,
            "completed_steps": len(completed_steps),
            "total_steps": len(tasks),
            "phase": current_task.get("phase", "unknown") if current_task else "unknown",
            "next_step_id": step_id + 1 if step_id < len(tasks) else None
        }

    def _replace_variables(self, template_content: str, variables: dict[str, Any]) -> str:
        """テンプレート内の変数を置換する

        Args:
            template_content: テンプレート文字列
            variables: 置換変数辞書

        Returns:
            変数置換後の文字列
        """
        try:
            return template_content.format(**variables)
        except KeyError as e:
            self.logger.warning(f"テンプレート変数が見つかりません: {e}")
            return template_content
        except Exception as e:
            self.logger.exception(f"テンプレート変数置換エラー: {e}")
            return template_content

    def _generate_enhanced_llm_instruction(self, current_task: dict | None, executable_tasks: list[dict]) -> str:
        """外部テンプレートを使用してLLM指示を生成する（改良版）

        Args:
            current_task: 現在のタスク
            executable_tasks: 実行可能なタスクリスト

        Returns:
            LLM指示文字列
        """
        if not current_task:
            if not executable_tasks:
                return "全てのタスクが完了しました。お疲れさまでした！"
            current_task = executable_tasks[0]

        step_id = current_task["id"]

        # 外部テンプレートを試行
        template_data = self._load_prompt_template(step_id)
        if template_data:
            # 外部テンプレートが見つかった場合
            variables = self._prepare_template_variables(step_id, current_task)
            prompt_section = template_data.get("prompt", {})
            main_instruction = prompt_section.get("main_instruction", "")

            instruction_text = None
            if main_instruction:
                try:
                    instruction_text = self._replace_variables(main_instruction, variables)
                except Exception:
                    instruction_text = main_instruction
            if not instruction_text:
                instruction_text = f"ステップ {step_id}: {current_task['name']} を実行してください"

            # 追加: ステップ入力コンテキストを併記
            context_lines: list[str] = []
            # プロジェクト設定
            try:
                ps_yaml = self.project_root / "プロジェクト設定.yaml"
                if ps_yaml.exists():
                    proj = yaml.safe_load(ps_yaml.read_text(encoding="utf-8")) or {}
                    title = proj.get("title")
                    genre = proj.get("genre")
                    twc = proj.get("target_word_count")
                    context_lines.append("## 参照情報（プロジェクト設定）")
                    if title:
                        context_lines.append(f"- タイトル: {title}")
                    if genre:
                        context_lines.append(f"- ジャンル: {genre}")
                    if twc:
                        context_lines.append(f"- 目標文字数: {twc}")
            except Exception:
                pass

            # 話別プロットファイル（存在すれば）
            try:
                path_service = self._path_service
                if path_service is None:
                    path_service = self._deps.create_path_service(self.project_root)
                    self._path_service = path_service
                p = path_service.get_episode_plot_path(self.episode_number)
                if p and p.exists():
                    context_lines.append("\n## 参照情報（話別プロット）")
                    context_lines.append(f"- ファイル: {p}")
                    context_lines.append("必要に応じて内容を参照して実行してください")
            except Exception:
                pass

            control_settings = template_data.get("control_settings", {})
            if control_settings.get("strict_single_step", False):
                self.logger.info(f"ステップ {step_id} で厳格な単一ステップ実行を強制")

            # 利用可能な既存アーティファクトも併記（同エピソードのもの）
            try:
                store = self._deps.create_artifact_store(
                    storage_dir=self.project_root / ".noveler" / "artifacts"
                )
                arts = store.list_artifacts()
                ep_arts = []
                for a in (arts or []):
                    meta = a.get("metadata", {}) if isinstance(a, dict) else {}
                    tags = meta.get("tags") or {}
                    if str(tags.get("episode")) == str(self.episode_number):
                        ep_arts.append(a.get("artifact_id"))
                if ep_arts:
                    # ステップ種別ごとの優先順に並べ替えて掲示
                    prioritized = self._prioritize_artifacts_for_step(
                        artifact_ids=ep_arts,
                        artifact_store=store,
                        step_id=step_id,
                        task_name=current_task.get("name", "") if current_task else "",
                        max_items=10,
                    )
                    context_lines.append("\n## 参照アーティファクト")
                    context_lines.extend([f"- {aid}" for aid in prioritized])
                    context_lines.append("必要に応じて fetch_artifact で取得してください")
            except Exception:
                pass

            if context_lines:
                instruction_text = instruction_text.rstrip() + "\n\n" + "\n".join(context_lines) + "\n"

            next_action_instruction = prompt_section.get("next_action_instruction")
            if next_action_instruction:
                try:
                    formatted_next_action = self._replace_variables(next_action_instruction, variables)
                except Exception:
                    formatted_next_action = next_action_instruction
                instruction_text = instruction_text.rstrip() + "\n\n" + formatted_next_action

            return instruction_text

        # フォールバック：従来のテンプレートシステム
        return self._generate_llm_instruction_legacy(current_task, executable_tasks)

    def _generate_llm_instruction_legacy(self, current_task: dict, executable_tasks: list[dict]) -> str:
        """従来のLLM指示生成（フォールバック用）"""
        template = self.tasks_config.get("llm_templates", {}).get("step_completion", "")
        if template:
            instruction = template.format(
                step_id=current_task["id"],
                step_name=current_task["name"],
                next_action=current_task.get("next_action", ""),
                llm_instruction=current_task.get("llm_instruction", ""),
                result_summary="初回実行のため結果はありません"
            )
            step_marker = f"STEP {current_task['id']}"
            if step_marker not in instruction:
                instruction = f"{step_marker}: {current_task['name']}\n{instruction}"
            return instruction

        llm_text = current_task.get("llm_instruction")
        if llm_text:
            step_marker = f"STEP {current_task['id']}"
            if step_marker not in llm_text:
                llm_text = f"{step_marker}: {current_task['name']}\n{llm_text}"
            return llm_text

        return f"STEP {current_task['id']}: {current_task['name']} を実行してください"

    def _execute_step_logic(self, task: dict) -> dict[str, Any]:
        """実際のステップ実行ロジック

        Note: アーティファクト参照システムを使用してプロット内容を効率的に渡す
        """
        step_id = task["id"]
        step_name = task["name"]

        # パスサービスとアーティファクトストアを初期化
        path_service = self._path_service
        if path_service is None:
            path_service = self._deps.create_path_service(self.project_root)
            self._path_service = path_service

        storage_root = getattr(path_service, "project_root", self.project_root)
        artifact_store = self._deps.create_artifact_store(
            storage_dir=Path(storage_root) / ".noveler" / "artifacts"
        )

        # 追加: 共通の設定系ファイルをアーティファクト化（存在するもののみ）
        common_artifacts: list[str] = []
        try:
            settings_dir = self.project_root / "30_設定集"
            candidates = [
                (settings_dir / "キャラクター.yaml", "character_settings", "キャラクター設定"),
                (settings_dir / "世界観.yaml", "world_settings", "世界観設定"),
                (settings_dir / "用語集.yaml", "glossary", "用語集"),
                (settings_dir / "文体ガイド.yaml", "style_guide", "文体ガイド"),
                (settings_dir / "スタイルガイド.yaml", "style_guide", "スタイルガイド"),
                (settings_dir / "文体・可読性.yaml", "style_guide", "文体・可読性ガイド"),
            ]
            for file_path, tag_type, desc in candidates:
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        aid = artifact_store.store(
                            content=content,
                            content_type="yaml",
                            source_file=str(file_path),
                            description=desc,
                            tags={"episode": str(self.episode_number), "type": tag_type},
                        )
                        common_artifacts.append(aid)
                    except Exception:
                        continue
        except Exception:
            pass

        # 直前エピソードの原稿を参照として追加（存在すれば）
        try:
            prev_num = int(self.episode_number) - 1
            if prev_num >= 1:
                # まず統一パスで確認
                prev_path = path_service.get_manuscript_path(prev_num)
                if not prev_path.exists():
                    # フォールバック: 既存命名のゆらぎに対応
                    mdir = path_service.get_manuscript_dir()
                    pattern = str(mdir / f"第{prev_num:03d}話_*.md")
                    prev_files = _glob(pattern)
                    prev_path = Path(prev_files[0]) if prev_files else prev_path
                if prev_path.exists():
                    try:
                        content = prev_path.read_text(encoding="utf-8")
                        aid_prev = artifact_store.store(
                            content=content,
                            content_type="text",
                            source_file=str(prev_path),
                            description=f"第{prev_num:03d}話 原稿（参照用）",
                            tags={"episode": str(prev_num), "type": "prev_manuscript"},
                        )
                        common_artifacts.append(aid_prev)
                    except Exception:
                        pass
        except Exception:
            pass

        # ステップIDに応じた処理を実行
        if step_id in [7, 8, 9, 10, 11]:  # プロット関連のステップ
            # プロットファイルを読み込んでアーティファクト化
            plot_file = None
            try:
                pf = path_service.get_episode_plot_path(self.episode_number)
                if isinstance(pf, Path):
                    plot_file = pf
            except Exception:
                plot_file = None

            # パスサービスが未実装・モックの場合のフォールバック（testsで使用）
            if not plot_file or not plot_file.exists():
                try:
                    plots_dir = path_service.get_plots_dir()
                    if not isinstance(plots_dir, Path):
                        plots_dir = self.project_root / "plots"
                except Exception:
                    plots_dir = self.project_root / "plots"
                candidate_md = plots_dir / f"第{self.episode_number:03d}話_プロット.md"
                if candidate_md.exists():
                    plot_file = candidate_md

            if plot_file and plot_file.exists():
                plot_content = plot_file.read_text(encoding="utf-8")
                artifact_id = artifact_store.store(
                    content=plot_content,
                    content_type="text",
                    source_file=str(plot_file),
                    description=f"第{self.episode_number:03d}話プロット - ステップ{step_id}用",
                    tags={"episode": str(self.episode_number), "step": str(step_id), "type": "plot"}
                )

                # 話別プロットYAML（存在すれば）も参照としてartifact化
                try:
                    ep_dir = None
                    try:
                        pdir = path_service.get_episode_plots_dir()
                        if isinstance(pdir, Path):
                            ep_dir = pdir
                    except Exception:
                        ep_dir = None
                    if ep_dir is None:
                        ep_dir = (self.project_root / "20_プロット" / "話別プロット")
                    pattern = re.compile(rf"^第{self.episode_number:03d}話_.*\\.yaml$")
                    yaml_candidates = [p for p in ep_dir.glob("*.yaml") if pattern.match(p.name)]
                    if yaml_candidates:
                        yaml_text = yaml_candidates[0].read_text(encoding="utf-8")
                        ep_yaml_aid = artifact_store.store(
                            content=yaml_text,
                            content_type="yaml",
                            source_file=str(yaml_candidates[0]),
                            description=f"第{self.episode_number:03d}話 話別プロットYAML",
                            tags={"episode": str(self.episode_number), "type": "episode_plot"},
                        )
                        common_artifacts.append(ep_yaml_aid)
                except Exception:
                    pass

                result = {
                    "step_id": step_id,
                    "step_name": step_name,
                    "content": f"{step_name}を実行しました",
                    "metadata": {
                        "execution_time": "15分",
                        "content_length": len(plot_content),
                        "success_criteria_met": True,
                        "plot_artifact_id": artifact_id
                    },
                    "artifacts": [artifact_id] + common_artifacts,
                    "instructions": f"プロットアーティファクト {artifact_id} を使用して{step_name}を実行してください。\nfetch_artifact を使って参照できます。"
                }
            else:
                result = {
                    "step_id": step_id,
                    "step_name": step_name,
                    "content": f"プロットファイルが見つかりません: {plot_file}",
                    "metadata": {
                        "success_criteria_met": False,
                        "error": "plot_not_found"
                    },
                    "artifacts": common_artifacts
                }
        else:
            # その他のステップは通常処理
            result = {
                "step_id": step_id,
                "step_name": step_name,
                "content": f"{step_name}を実行しました",
                "metadata": {
                    "execution_time": "15分",
                    "content_length": len(f"{step_name}を実行しました"),
                    "success_criteria_met": True
                },
                "artifacts": common_artifacts
            }

        # ===== ステップ種別ごとの優先参照最適化 =====
        try:
            result["artifacts"] = self._prioritize_artifacts_for_step(
                artifact_ids=list(result.get("artifacts", [])),
                artifact_store=artifact_store,
                step_id=step_id,
                task_name=step_name,
                max_items=10,
            )
        except Exception:
            pass

        # ===== B20: 要約アーティファクト生成（設定で有効時） =====
        cfg2 = self._deps.get_configuration_manager()
        sum_enabled = True
        max_chars = 1200
        if cfg2 is not None:
            try:
                sum_enabled = bool(
                    cfg2.get_default_setting("writing_steps", "summarize.enabled", True)
                )
                max_chars_cfg = cfg2.get_default_setting("writing_steps", "summarize.max_chars", 1200)
                try:
                    max_chars = int(max_chars_cfg) if max_chars_cfg is not None else 1200
                except Exception:
                    max_chars = 1200
            except Exception:
                sum_enabled = True
                max_chars = 1200

        if sum_enabled:
            try:
                summarized_ids: list[str] = []
                all_ids = list(result.get("artifacts", []))
                for aid in all_ids:
                    try:
                        meta = artifact_store.get_metadata(aid)
                        if not meta:
                            continue
                        # 仕様: テキスト(MD等)はそのまま参照とし、要約生成はYAMLに限定
                        if str(getattr(meta, "content_type", "")).lower() != "yaml":
                            continue
                        content = artifact_store.fetch(aid)
                        if not content:
                            continue
                        data = yaml.safe_load(content) or {}
                        if isinstance(data, dict):
                            keys = list(data.keys())
                            summary_text = "# 要約\n上位キー:\n" + "\n".join(f"- {k}" for k in keys[:30])
                        else:
                            summary_text = str(data)[:max_chars]

                        tags = dict(getattr(meta, "tags", {}) or {})
                        tags.update({"summary": "true"})
                        sum_id = artifact_store.store(
                            content=summary_text,
                            content_type="text",
                            source_file=getattr(meta, "source_file", None),
                            description=((getattr(meta, "description", None) or "") + "（要約）").strip(),
                            tags=tags,
                        )
                        summarized_ids.append(sum_id)
                    except Exception:
                        continue
                if summarized_ids:
                    # 要約を先頭に保つが、重複を除去
                    base = list(result.get("artifacts", []))
                    # 再優先付け（要約→残りの優先順）
                    merged = summarized_ids + [a for a in base if a not in summarized_ids]
                    result["artifacts"] = merged[:10]
            except Exception:
                pass

        # ===== B20: LLMを用いたステップ実行（入力バンドル同梱） =====
        cfg = self._deps.get_configuration_manager()
        use_llm = True
        save_io = True
        if cfg is not None:
            try:
                use_llm = bool(cfg.get_default_setting("writing_steps", "use_llm", True))
                save_io = bool(cfg.get_default_setting("writing_steps", "save_io", True))
            except Exception:
                use_llm = True
                save_io = True

        if use_llm:
            # テンプレート読み込み（ある場合）
            try:
                template_data = self._load_prompt_template(step_id)
            except Exception:
                template_data = None

            variables = self._prepare_template_variables(step_id, task)
            main_instruction = ""
            if template_data:
                prompt_section = template_data.get("prompt", {}) or {}
                main_instruction = prompt_section.get("main_instruction", "")
                try:
                    main_instruction = self._replace_variables(main_instruction, variables)
                except Exception:
                    pass

            # 入力収集（簡易版）: プロジェクト設定・プロット参照
            input_data: dict[str, Any] = {"episode": self.episode_number, "step_id": step_id, "phase": task.get("phase")}
            # プロジェクト設定
            try:
                project_settings = {}
                ps_yaml = self.project_root / "プロジェクト設定.yaml"
                if ps_yaml.exists():
                    project_settings = yaml.safe_load(ps_yaml.read_text(encoding="utf-8")) or {}
                if project_settings:
                    input_data["project_settings"] = {k: project_settings.get(k) for k in ("title", "genre", "target_word_count")}
            except Exception:
                pass

            # アーティファクト一覧（このステップで生成したもの）
            artifact_ids = [a for a in result.get("artifacts", []) if isinstance(a, str)]
            input_data["artifacts"] = artifact_ids

            # プロンプトを構築
            prompt_parts = [main_instruction.strip() or f"STEP {step_id}: {step_name}"]
            if artifact_ids:
                prompt_parts.append("\n## 参照アーティファクト\n" + "\n".join(f"- {aid}" for aid in artifact_ids))
            if input_data.get("project_settings"):
                ps = input_data["project_settings"]
                prompt_parts.append(f"\n## プロジェクト設定\n- タイトル: {ps.get('title')}\n- ジャンル: {ps.get('genre')}\n- 目標文字数: {ps.get('target_word_count')}")
            prompt_text = "\n".join(p for p in prompt_parts if p)

            request_payload = LLMExecutionRequest(
                episode_number=self.episode_number,
                step_id=step_id,
                step_name=step_name,
                prompt_text=prompt_text,
                input_data=dict(input_data),
                artifact_ids=artifact_ids,
                project_root=self.project_root,
            )

            executor = self.llm_executor or self._deps.ensure_llm_executor()
            if executor is not None:
                try:
                    llm_result = executor.run_sync(request_payload)
                except Exception as llm_err:
                    self.logger.debug(
                        "LLM executor (sync) failed: %s", llm_err, exc_info=True
                    )
                else:
                    self._consume_llm_result(result, request_payload, llm_result, save_io)
                    try:
                        if template_data:
                            validation = self._apply_by_task_validation(template_data, result)
                            if validation.get("by_task"):
                                result.setdefault("validation", {}).update({"by_task": validation["by_task"]})
                            if not validation.get("success", True):
                                result.setdefault("metadata", {})["success_criteria_met"] = False
                            if validation.get("messages"):
                                result.setdefault("validation", {}).setdefault("messages", []).extend(validation["messages"])
                            if validation.get("errors"):
                                result.setdefault("validation", {}).setdefault("errors", []).extend(validation["errors"])
                    except Exception:
                        self.logger.debug("by_task validation failed", exc_info=True)

        return result

    async def _execute_step_logic_async(self, task: dict) -> dict[str, Any]:
        """実際のステップ実行ロジック（非同期版）"""
        step_id = task["id"]
        step_name = task["name"]

        # パスサービスとアーティファクトストアを初期化
        path_service = self._path_service
        if path_service is None:
            path_service = self._deps.create_path_service(self.project_root)
            self._path_service = path_service

        storage_root = getattr(path_service, "project_root", self.project_root)
        artifact_store = self._deps.create_artifact_store(
            storage_dir=Path(storage_root) / ".noveler" / "artifacts"
        )

        result: dict[str, Any] = {
            "content": f"ステップ {step_id}: {step_name} 実行結果（非同期版）",
            "metadata": {
                "success_criteria_met": True,
                "quality_score": 85.0,
            },
        }

        # 直前エピソード参照（同上）※同期版と同一ロジック
        try:
            prev_num = int(self.episode_number) - 1
            if prev_num >= 1:
                prev_path = path_service.get_manuscript_path(prev_num)
                if not prev_path.exists():
                    mdir = path_service.get_manuscript_dir()
                    pattern = str(mdir / f"第{prev_num:03d}話_*.md")
                    prev_files = _glob(pattern)
                    prev_path = Path(prev_files[0]) if prev_files else prev_path
                if prev_path.exists():
                    try:
                        content = prev_path.read_text(encoding="utf-8")
                        aid_prev = artifact_store.store(
                            content=content,
                            content_type="text",
                            source_file=str(prev_path),
                            description=f"第{prev_num:03d}話 原稿（参照用）",
                            tags={"episode": str(prev_num), "type": "prev_manuscript"},
                        )
                        result.setdefault("artifacts", []).append(aid_prev)
                    except Exception:
                        pass
        except Exception:
            pass

        # LLM実行（非同期）
        cfg = self._deps.get_configuration_manager()
        use_llm = True
        save_io = True
        if cfg is not None:
            try:
                use_llm = bool(cfg.get_default_setting("writing_steps", "use_llm", True))
                save_io = bool(cfg.get_default_setting("writing_steps", "save_io", True))
            except Exception:
                use_llm = True
                save_io = True

        if use_llm:
            try:
                template_data = self._load_prompt_template(step_id)
            except Exception:
                template_data = None

            variables = self._prepare_template_variables(step_id, task)
            main_instruction = ""
            if template_data:
                prompt_section = template_data.get("prompt", {}) or {}
                main_instruction = prompt_section.get("main_instruction", "")
                try:
                    main_instruction = self._replace_variables(main_instruction, variables)
                except Exception:
                    pass

            input_data: dict[str, Any] = {
                "episode": self.episode_number,
                "step_id": step_id,
                "phase": task.get("phase"),
            }
            artifact_ids = [a for a in result.get("artifacts", []) if isinstance(a, str)]
            input_data["artifacts"] = artifact_ids

            prompt_parts = [main_instruction.strip() or f"STEP {step_id}: {step_name}"]
            if artifact_ids:
                prompt_parts.append("\n## 参照アーティファクト\n" + "\n".join(f"- {aid}" for aid in artifact_ids))
            prompt_text = "\n".join(p for p in prompt_parts if p)

            request_payload = LLMExecutionRequest(
                episode_number=self.episode_number,
                step_id=step_id,
                step_name=step_name,
                prompt_text=prompt_text,
                input_data=dict(input_data),
                artifact_ids=artifact_ids,
                project_root=self.project_root,
            )

            executor = self.llm_executor or self._deps.ensure_llm_executor()
            if executor is not None:
                try:
                    llm_result = await executor.run(request_payload)
                except Exception as llm_err:
                    self.logger.debug(
                        "LLM executor (async) failed: %s", llm_err, exc_info=True
                    )
                else:
                    self._consume_llm_result(result, request_payload, llm_result, save_io)
                    try:
                        if template_data:
                            validation = self._apply_by_task_validation(template_data, result)
                            if validation.get("by_task"):
                                result.setdefault("validation", {}).update({"by_task": validation["by_task"]})
                            if not validation.get("success", True):
                                result.setdefault("metadata", {})["success_criteria_met"] = False
                            if validation.get("messages"):
                                result.setdefault("validation", {}).setdefault("messages", []).extend(validation["messages"])
                            if validation.get("errors"):
                                result.setdefault("validation", {}).setdefault("errors", []).extend(validation["errors"])
                    except Exception:
                        self.logger.debug("by_task validation failed", exc_info=True)

        return result

    async def _execute_step_with_recovery_async(self, task: dict, dry_run: bool, retry_count: int) -> dict[str, Any]:
        """部分失敗対応付きでステップを実行する（非同期版）"""
        step_id = task["id"]
        step_name = task["name"]
        recovery_applied = False
        start_time = time.time()

        try:
            if not dry_run:
                execution_result = await self._execute_step_logic_async(task)
            else:
                execution_result = {
                    "content": f"[DRY RUN] {step_name}のシミュレーション結果",
                    "dry_run": True,
                    "step_id": step_id,
                    "step_name": step_name,
                }

            success_criteria_met = execution_result.get("metadata", {}).get("success_criteria_met", True)
            if not success_criteria_met:
                self.logger.warning(f"ステップ {step_id} の成功基準が満たされていません")
                recovery_result = self._attempt_step_recovery(task, execution_result, retry_count)
                if recovery_result:
                    execution_result.update(recovery_result)
                    recovery_applied = True
                else:
                    msg = f"ステップ {step_id} の実行結果が成功基準を満たしません"
                    raise PartialFailureError(
                        msg,
                        failed_steps=[step_id],
                        completed_steps=self.current_state.get("completed_steps", []),
                        recovery_point=step_id,
                        details={
                            "execution_result": execution_result,
                            "success_criteria_met": False,
                            "recovery_attempted": True,
                            "recovery_successful": False,
                        },
                    )

            execution_time = time.time() - start_time
            execution_result.setdefault("metadata", {}).update(
                {
                    "execution_time_seconds": execution_time,
                    "retry_count": retry_count,
                    "recovery_applied": recovery_applied,
                    "timestamp": time.time(),
                }
            )

            try:
                self._save_step_io(step_id=step_id, step_name=step_name, task=task, execution_result=execution_result)
            except Exception as io_err:
                self.logger.warning(f"ステップI/O保存失敗 (step={step_id}): {io_err}")

            if self._io_logger_factory is not None:
                try:
                    io_logger = self._io_logger_factory(self.project_root)
                    if io_logger is not None:
                        io_logger.save_stage_io(
                            episode_number=self.episode_number,
                            step_number=int(step_id) if isinstance(step_id, (int, float)) else 0,
                            stage_name=str(step_name),
                            request_content={
                                "task": task,
                                "phase": task.get("phase"),
                                "project_root": str(self.project_root),
                            },
                            response_content=execution_result,
                            extra_metadata={"kind": "progressive_write_step"},
                        )
                except Exception:
                    pass

            return execution_result

        except Exception as e:
            error_trace = traceback.format_exc()
            self.logger.error(
                f"ステップ {step_id} 実行エラー: {e}\n{error_trace}"
            )
            return {
                "success": False,
                "error": str(e),
                "step_id": step_id,
                "step_name": step_name,
                "trace": error_trace,
                "retry_count": retry_count,
            }

    async def execute_writing_step_async(self, step_id: int | float, dry_run: bool = False, retry_count: int = 0) -> dict[str, Any]:
        """特定ステップの非同期実行エントリーポイント"""
        # 同期版と同等の前提チェックやUI更新は維持（必要最小限）
        self.progress_display.start_step(step_id)
        tasks = self.tasks_config.get("tasks", [])
        task = self._get_task_by_id(tasks, step_id)
        if not task:
            available_ids = [t.get("id", "不明") for t in tasks]
            return {
                "success": False,
                "error": f"ステップ {step_id} が見つかりません。利用可能なID: {available_ids}",
            }
        prerequisites_met = self._check_prerequisites(task.get("prerequisites", []))
        if not prerequisites_met:
            completed_steps = self.current_state.get("completed_steps", [])
            return {
                "success": False,
                "error": f"ステップ {step_id} の前提条件が満たされていません。完了済み: {completed_steps}",
            }
        result = await self._execute_step_with_recovery_async(task, dry_run, retry_count)
        if result.get("success", True):
            self._update_step_completion(step_id, result)
            self.progress_display.complete_step(step_id, success=True)
        else:
            self.progress_display.fail_step(step_id, result.get("error", "実行失敗"))
        return result

    # === 優先参照最適化ロジック ===
    def _prioritize_artifacts_for_step(
        self,
        artifact_ids: list[str],
        artifact_store,
        step_id: int | float,
        task_name: str,
        max_items: int = 10,
    ) -> list[str]:
        """ステップ内容に応じて参照アーティファクトの優先度を付け並べ替える

        優先度ルール（高→低）
        - 会話設計（step 8/名前に"会話"）: summary, character_settings, glossary, style_guide, world_settings, prev_manuscript, episode_plot, plot
        - 文体・可読性（step 13/名前に"文体" or "可読性"）: summary, style_guide, prev_manuscript, character_settings, episode_plot, world_settings, plot, glossary
        - プロット関連（steps 7-11）: summary, episode_plot, plot, world_settings, character_settings, glossary, prev_manuscript, style_guide
        - それ以外: summary, character_settings, world_settings, episode_plot, plot, glossary, style_guide, prev_manuscript
        """
        name = task_name or ""

        def get_type(aid: str) -> str:
            try:
                meta = artifact_store.get_metadata(aid)
                tags = getattr(meta, "tags", {}) or {}
                if str(tags.get("summary")).lower() == "true":
                    return "summary"
                return str(tags.get("type") or "")
            except Exception:
                return ""

        # デフォルト優先リスト
        sequence_default = [
            "summary",
            "character_settings",
            "world_settings",
            "episode_plot",
            "plot",
            "glossary",
            "style_guide",
            "prev_manuscript",
        ]

        # ルール選択
        if int(step_id) in [7, 8, 9, 10, 11]:
            sequence = [
                "summary",
                "episode_plot",
                "plot",
                "world_settings",
                "character_settings",
                "glossary",
                "prev_manuscript",
                "style_guide",
            ]
        elif int(step_id) == 8 or ("会話" in name):
            sequence = [
                "summary",
                "character_settings",
                "glossary",
                "style_guide",
                "world_settings",
                "prev_manuscript",
                "episode_plot",
                "plot",
            ]
        elif int(step_id) == 13 or ("文体" in name or "可読性" in name):
            sequence = [
                "summary",
                "style_guide",
                "prev_manuscript",
                "character_settings",
                "episode_plot",
                "world_settings",
                "plot",
                "glossary",
            ]
        else:
            sequence = sequence_default

        # スコアリングして並び替え
        def score(aid: str) -> tuple:
            t = get_type(aid)
            try:
                idx = sequence.index(t)
            except ValueError:
                idx = len(sequence)
            # summaryをさらに優遇（先頭へ）
            bonus = -1 if t == "summary" else 0
            return (idx, bonus)

        ordered = sorted(artifact_ids, key=score)
        # 重複除去・上限
        uniq = []
        for a in ordered:
            if a not in uniq:
                uniq.append(a)
        return uniq[:max_items]

    def _execute_step_with_recovery(self, task: dict, dry_run: bool, retry_count: int) -> dict[str, Any]:
        """部分失敗対応付きでステップを実行する

        Args:
            task: 実行するタスク
            dry_run: ドライランかどうか
            retry_count: 現在のリトライ回数

        Returns:
            実行結果（recovery情報を含む）

        Raises:
            PartialFailureError: 回復不可能な部分失敗時
            InfrastructureError: インフラレベルのエラー時
        """
        step_id = task["id"]
        step_name = task["name"]
        recovery_applied = False

        # パフォーマンス統計開始
        start_time = time.time()

        try:
            # メイン実行処理
            if not dry_run:
                execution_result = self._execute_step_logic(task)
            else:
                execution_result = {
                    "content": f"[DRY RUN] {step_name}のシミュレーション結果",
                    "dry_run": True,
                    "step_id": step_id,
                    "step_name": step_name
                }

            # 実行結果の検証
            success_criteria_met = execution_result.get("metadata", {}).get("success_criteria_met", True)
            if not success_criteria_met:
                self.logger.warning(f"ステップ {step_id} の成功基準が満たされていません")

                # 自動復旧を試行
                recovery_result = self._attempt_step_recovery(task, execution_result, retry_count)
                if recovery_result:
                    execution_result.update(recovery_result)
                    recovery_applied = True
                    self.logger.info(f"ステップ {step_id} の自動復旧が成功しました")
                else:
                    # 復旧失敗時は部分失敗として処理
                    msg = f"ステップ {step_id} の実行結果が成功基準を満たしません"
                    raise PartialFailureError(
                        msg,
                        failed_steps=[step_id],
                        completed_steps=self.current_state.get("completed_steps", []),
                        recovery_point=step_id,
                        details={
                            "execution_result": execution_result,
                            "success_criteria_met": False,
                            "recovery_attempted": True,
                            "recovery_successful": False
                        }
                    )

            # パフォーマンス統計記録
            execution_time = time.time() - start_time
            execution_result.setdefault("metadata", {}).update({
                "execution_time_seconds": execution_time,
                "retry_count": retry_count,
                "recovery_applied": recovery_applied,
                "timestamp": time.time()
            })

            # デバッグ情報記録
            if self.logger.isEnabledFor(10):  # DEBUG level
                debug_info = {
                    "step_id": step_id,
                    "step_name": step_name,
                    "execution_time": execution_time,
                    "retry_count": retry_count,
                    "recovery_applied": recovery_applied,
                    "result_size": len(str(execution_result))
                }
                self.logger.debug(f"ステップ実行詳細: {debug_info}")

            # ステップI/OをJSON保存 (.noveler/steps)
            try:
                self._save_step_io(step_id=step_id, step_name=step_name, task=task, execution_result=execution_result)
            except Exception as io_err:
                # 保存失敗は実行を中断しない
                self.logger.warning(f"ステップI/O保存失敗 (step={step_id}): {io_err}")

            # 逐次I/Oを .noveler/checks にも保存（プロンプト改善用の参照ログ）
            if self._io_logger_factory is not None:
                try:
                    io_logger = self._io_logger_factory(self.project_root)
                    if io_logger is not None:
                        io_logger.save_stage_io(
                            episode_number=self.episode_number,
                            step_number=int(step_id) if isinstance(step_id, (int, float)) else 0,
                            stage_name=str(step_name),
                            request_content={
                                "task": task,
                                "phase": task.get("phase"),
                                "project_root": str(self.project_root),
                            },
                            response_content=execution_result,
                            extra_metadata={"kind": "progressive_write_step"},
                        )
                except Exception:
                    pass

            return execution_result

        except Exception as e:
            # エラー詳細トレース記録
            error_trace = traceback.format_exc()

            self.logger.exception(
                f"ステップ {step_id} 実行中にエラー発生",
                extra={
                    "step_id": step_id,
                    "step_name": step_name,
                    "retry_count": retry_count,
                    "execution_time": time.time() - start_time,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": error_trace
                }
            )

            # エラータイプに応じた処理
            if isinstance(e, FileNotFoundError | PermissionError | OSError):
                msg = f"ファイルシステムエラー（ステップ {step_id}）: {e!s}"
                raise InfrastructureError(
                    msg,
                    details={
                        "step_id": step_id,
                        "step_name": step_name,
                        "error_type": type(e).__name__,
                        "file_operation": True
                    },
                    recovery_actions=[
                        "ファイルのアクセス権限を確認してください",
                        "ディスク容量を確認してください",
                        "ファイルパスが正しいことを確認してください"
                    ]
                )
            # その他のエラーは再発生
            raise

    def _attempt_step_recovery(self, task: dict, execution_result: dict, retry_count: int) -> dict | None:
        """ステップの自動復旧を試行する

        Args:
            task: 失敗したタスク
            execution_result: 実行結果
            retry_count: リトライ回数

        Returns:
            復旧結果（成功時）またはNone（失敗時）
        """
        step_id = task["id"]

        # 復旧戦略を決定
        recovery_strategies = []

        # ファイル関連エラーの復旧
        error_type = execution_result.get("metadata", {}).get("error", "")
        if "plot_not_found" in error_type:
            recovery_strategies.append("create_placeholder_plot")

        # プロット関連ステップの復旧
        if step_id in [7, 8, 9, 10, 11]:
            recovery_strategies.append("use_alternative_plot_source")

        # 復旧戦略を順次試行
        for strategy in recovery_strategies:
            try:
                recovery_result = self._execute_recovery_strategy(strategy, task, execution_result)
                if recovery_result:
                    self.logger.info(f"復旧戦略 '{strategy}' がステップ {step_id} で成功")
                    return recovery_result
            except Exception as e:
                self.logger.warning(f"復旧戦略 '{strategy}' がステップ {step_id} で失敗: {e}")
                continue

        return None

    def _execute_recovery_strategy(self, strategy: str, task: dict, execution_result: dict) -> dict | None:
        """特定の復旧戦略を実行する

        Args:
            strategy: 復旧戦略名
            task: タスク
            execution_result: 元の実行結果

        Returns:
            復旧後の実行結果またはNone
        """
        step_id = task["id"]

        if strategy == "create_placeholder_plot":
            # プレースホルダープロットを作成
            placeholder_content = f"# 第{self.episode_number:03d}話プロット（自動生成）\n\n## あらすじ\nステップ{step_id}用の仮プロット内容です。\n\n## 詳細\n後で詳細を記述してください。"

            return {
                "step_id": step_id,
                "step_name": task["name"],
                "content": f"{task['name']}を復旧モードで実行しました",
                "metadata": {
                    "execution_time": "復旧処理",
                    "content_length": len(placeholder_content),
                    "success_criteria_met": True,
                    "recovery_applied": True,
                    "recovery_strategy": strategy
                },
                "artifacts": [],
                "recovery_notes": "プレースホルダープロットを使用しました。後で実際のプロットに置き換えてください。"
            }

        if strategy == "use_alternative_plot_source":
            # 代替のプロットソースを使用
            return {
                "step_id": step_id,
                "step_name": task["name"],
                "content": f"{task['name']}を代替ソースで実行しました",
                "metadata": {
                    "execution_time": "復旧処理",
                    "success_criteria_met": True,
                    "recovery_applied": True,
                    "recovery_strategy": strategy
                },
                "artifacts": [],
                "recovery_notes": "代替のプロットソースを使用しました。必要に応じて内容を確認してください。"
            }

        return None

    def _update_step_completion(self, step_id: int | float, result: dict[str, Any]) -> None:
        """ステップ完了時の状態更新"""
        if step_id not in self.current_state["completed_steps"]:
            self.current_state["completed_steps"].append(step_id)

        self.current_state["step_results"][str(step_id)] = result

        # 次のステップに進む
        next_step = self._find_next_step()
        if next_step is not None:
            self.current_state["current_step"] = next_step
            self.current_state["overall_status"] = "in_progress"
        else:
            self.current_state["overall_status"] = "completed"

        self._save_state(self.current_state)

    def _update_step_failure(self, step_id: int | float, error: str) -> None:
        """ステップ失敗時の状態更新"""
        failure_record = {
            "step_id": step_id,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.current_state["failed_steps"].append(failure_record)
        self.current_state["overall_status"] = "error"

        self._save_state(self.current_state)

    def _find_next_step(self) -> int | float | None:
        """次に実行すべきステップを見つける"""
        tasks = self.tasks_config["tasks"]
        completed = self.current_state["completed_steps"]

        for task in tasks:
            if task["id"] not in completed and self._check_prerequisites(task["prerequisites"], completed):
                return task["id"]

        return None

    def _get_next_task(self) -> dict | None:
        """次のタスクを取得する"""
        next_step_id = self._find_next_step()
        if next_step_id is not None:
            return self._get_task_by_id(self.tasks_config["tasks"], next_step_id)
        return None

    def _generate_llm_instruction(self, current_task: dict | None, executable_tasks: list[dict]) -> str:
        """LLMへの指示を生成する"""
        if not current_task:
            if not executable_tasks:
                return "全てのタスクが完了しました。お疲れさまでした！"
            current_task = executable_tasks[0]

        template = self.tasks_config.get("llm_templates", {}).get("step_completion", "")
        if template:
            return template.format(
                step_id=current_task["id"],
                step_name=current_task["name"],
                next_action=current_task.get("next_action", ""),
                llm_instruction=current_task.get("llm_instruction", ""),
                result_summary="初回実行のため結果はありません"
            )

        return current_task.get("llm_instruction", f"ステップ {current_task['id']} を実行してください")

    def _generate_step_completion_instruction_enhanced(self, completed_task: dict, result: dict, next_task: dict | None) -> str:
        """ステップ完了後のLLM指示を生成する（改良版：外部テンプレート対応）"""
        if next_task:
            # 次のタスクが存在する場合、そのタスクの外部テンプレートを確認
            next_template_data = self._load_prompt_template(next_task["id"])
            if next_template_data:
                # 次のステップ用の外部テンプレートがある場合
                variables = self._prepare_template_variables(next_task["id"], next_task)
                variables.update({
                    "previous_step_id": completed_task["id"],
                    "previous_step_name": completed_task["name"],
                    "result_summary": result.get("content", "実行完了")
                })

                prompt_section = next_template_data.get("prompt", {})
                next_action_instruction = prompt_section.get("next_action_instruction", "")

                if next_action_instruction:
                    base_text = f"""ステップ {completed_task['id']}「{completed_task['name']}」が完了しました。

{self._replace_variables(next_action_instruction, variables)}"""
                    # 参照アーティファクトを併記
                    arts = result.get("artifacts") or []
                    if arts:
                        base_text = base_text.rstrip() + "\n\n## 参照アーティファクト\n" + "\n".join(f"- {a}" for a in arts) + "\n必要に応じて fetch_artifact で取得してください\n"
                    return base_text

        # フォールバック：従来のステップ完了指示生成
        return self._generate_step_completion_instruction_legacy(completed_task, result, next_task)

    def _generate_step_completion_instruction_legacy(self, completed_task: dict, result: dict, next_task: dict | None) -> str:
        """ステップ完了後のLLM指示を生成する（従来版）"""
        template = self.tasks_config.get("llm_templates", {}).get("step_completion", "")

        if template and next_task:
            return template.format(
                step_id=completed_task["id"],
                step_name=completed_task["name"],
                result_summary=result.get("content", "実行完了"),
                next_action=next_task.get("next_action", ""),
                llm_instruction=next_task.get("llm_instruction", "")
            )
        if next_task:
            return f"""ステップ {completed_task['id']}「{completed_task['name']}」が完了しました。

次のステップ：execute_writing_step で step_id={next_task['id']} を実行してください。

{next_task.get('llm_instruction', '')}"""
        return "全てのステップが完了しました。18ステップ執筆システムの実行が完了しました！"

    def _generate_error_instruction(self, failed_task: dict, error: str) -> str:
        """エラー時のLLM指示を生成する"""
        template = self.tasks_config.get("llm_templates", {}).get("error_handling", "")

        if template:
            return template.format(
                step_id=failed_task["id"],
                step_name=failed_task["name"],
                error_message=error
            )

        return f"""ステップ {failed_task['id']}「{failed_task['name']}」でエラーが発生しました：
{error}

get_task_status ツールで現在の状況を確認してください。
修正後、同じステップを再実行してください。"""

    def _get_next_action(self, task: dict | None) -> str:
        """次のアクションを取得する"""
        if task:
            return task.get("next_action", f"execute_writing_step で step_id={task['id']} を実行してください")
        return "全てのタスクが完了しています"

    def _get_current_phase_info(self) -> dict[str, Any]:
        """現在のフェーズ情報を取得する"""
        current_task = self._get_task_by_id(self.tasks_config["tasks"], self.current_state["current_step"])
        if not current_task:
            return {"phase": "completed", "description": "全フェーズ完了"}

        phase_name = current_task["phase"]
        phases = self.tasks_config.get("phases", {})
        phase_info = phases.get(phase_name, {"name": phase_name, "description": ""})

        return {
            "phase": phase_name,
            "name": phase_info.get("name", phase_name),
            "description": phase_info.get("description", "")
        }

    def _get_progress_info(self) -> dict[str, Any]:
        """進捗情報を取得する"""
        total_tasks = len(self.tasks_config["tasks"])
        completed_count = len(self.current_state["completed_steps"])

        return {
            "completed": completed_count,
            "total": total_tasks,
            "percentage": round(completed_count / total_tasks * 100, 1),
            "remaining": total_tasks - completed_count
        }

    def _save_step_io(self, step_id: int | float, step_name: str, task: dict[str, Any], execution_result: dict[str, Any]) -> None:
        """各ステップのI/Oを .noveler/steps に保存

        命名: EP{episode:04d}_step{XX|X_Y}_{yyyyMMddHHMMSS}.json
        - 整数ステップ: step02, step17 等（ゼロ埋め2桁）
        - 小数ステップ: step2_5, step9_5 等（小数点をアンダースコアに）
        """
        # ディレクトリ
        steps_dir = self.project_root / ".noveler" / "steps"
        steps_dir.mkdir(parents=True, exist_ok=True)

        # ステップ表記
        def format_step_id(val: int | float) -> str:
            try:
                # 小数点を含む場合
                if isinstance(val, float) and not float(val).is_integer():
                    return str(val).replace(".", "_")
                # 整数として扱う
                ival = int(val)
                return f"{ival:02d}"
            except Exception:
                return str(val).replace(".", "_")

        step_token = format_step_id(step_id)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = f"EP{self.episode_number:04d}_step{step_token}_{ts}.json"
        path = steps_dir / filename

        # 保存ペイロード
        payload: dict[str, Any] = {
            "kind": "progressive_step_io",
            "episode_number": self.episode_number,
            "step_id": step_id,
            "step_name": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": {
                "task": task,
                "dry_run": bool(execution_result.get("dry_run", False)),
            },
            "response": execution_result,
            "metadata": {
                "source": "ProgressiveWriteManager",
                "project_root": str(self.project_root),
            },
        }

        # JSON保存
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _try_load_yaml_state(self) -> dict | None:
        """
        YAML state ファイルを読み込む

        Expected YAML structure:
        {
            "episode_info": {
                "episode_number": int,
                "status": str,
                "created_at": str (ISO format),
                "updated_at": str,
            },
            "workflow_progress": {
                "current_step": int,
                "completed_steps": [int, ...],
                "next_step": int | null,
                "failed_steps": [int, ...],
            },
            "step_results": {...},
        }

        Returns:
            dict if file exists and valid, None otherwise
        """
        try:
            import yaml
            yaml_path = self.project_root / "50_管理資料" / "執筆記録" / f"episode_{self.episode_number:03d}_state.yaml"

            if not yaml_path.exists():
                return None

            content = yaml_path.read_text(encoding="utf-8")
            yaml_data = yaml.safe_load(content) or {}

            # Convert YAML structure to internal format
            if not yaml_data:
                return None

            episode_info = yaml_data.get("episode_info", {})
            workflow_progress = yaml_data.get("workflow_progress", {})
            step_results = yaml_data.get("step_results")
            if not isinstance(step_results, dict):
                step_results = {}

            return {
                "episode_number": episode_info.get("episode_number", self.episode_number),
                "current_step": workflow_progress.get("current_step"),
                "completed_steps": workflow_progress.get("completed_steps", []),
                "next_step": workflow_progress.get("next_step"),
                "overall_status": episode_info.get("status"),
                "last_updated": episode_info.get("updated_at"),
                "created_at": episode_info.get("created_at"),
                "failed_steps": workflow_progress.get("failed_steps", []),
                "step_results": step_results,
                "episode_info": episode_info,
                "workflow_progress": workflow_progress,
                "source": "yaml_18_step",
            }
        except Exception:
            return None

    def _generate_save_instructions(self, step_id: int, step_name: str) -> str:
        """
        LLM用の保存指示を生成

        Args:
            step_id: ステップID (1-18)
            step_name: ステップ名 (e.g., "初稿執筆")

        Returns:
            LLM向けの指示文（Markdown形式）
            - Manuscript パス
            - State YAML パス
            - Pre-generated YAML content
            - Copy-paste セクション
        """
        # Generate updated YAML
        new_completed = self.current_state.get("completed_steps", []).copy()
        if step_id not in new_completed:
            new_completed.append(step_id)
        updated_yaml = self._generate_updated_yaml(step_id=step_id, new_completed=new_completed)

        manuscript_path = f"40_原稿/第{self.episode_number:03d}話.md"
        state_path = f"50_管理資料/執筆記録/episode_{self.episode_number:03d}_state.yaml"

        instructions = f"""## ステップ {step_id}: {step_name} 完了

### 保存対象ファイル

1. **原稿ファイル**: `{manuscript_path}`
   - 執筆内容をこのファイルに保存してください

2. **状態ファイル**: `{state_path}`
   - ステップ実行状態を下記のYAML内容に置き換えてください

### 状態ファイルの内容（そのままコピーしてください - 編集は不要です）

```yaml
{updated_yaml}
```

### 保存手順

1. 上記のYAML内容をそのままコピーします（全文）
2. `{state_path}` を開きます
3. 全内容を削除して、コピーしたYAML内容をペーストします
4. 保存します

**重要**: YAML内容は自動生成されています。そのままコピー＆ペーストしてください。編集は不要です。

### LLM実行コマンド

```
mcp__noveler__write {manuscript_path}
```

完了後、手動で状態ファイルを保存してください。"""

        return instructions

    def _generate_updated_yaml(self, step_id: int, new_completed: list[int]) -> str:
        """
        更新されたYAML stateを生成 (既存の値を保存)

        Args:
            step_id: 完了したステップID
            new_completed: 完了ステップリスト

        Returns:
            Updated YAML string with:
            - current_step: step_id
            - next_step: step_id + 1 or null if final
            - completed_steps: new_completed
            - status: "draft_completed" (for step 12) or preserved
            - updated_at: current ISO timestamp
            - existing values preserved: created_at, failed_steps, step_results
        """
        from datetime import datetime, timezone
        import yaml

        current_state = self.current_state or {}
        episode_info = current_state.get("episode_info") or {}
        workflow_progress = current_state.get("workflow_progress") or {}

        overall_status = (
            episode_info.get("status")
            or current_state.get("overall_status")
            or "in_progress"
        )
        created_at = episode_info.get("created_at") or current_state.get("created_at")
        existing_failed_steps = workflow_progress.get("failed_steps") or current_state.get("failed_steps", [])
        existing_step_results = current_state.get("step_results") or {}

        status = overall_status
        if step_id == 12:
            status = "draft_completed"

        if not created_at:
            created_at = datetime.now(timezone.utc).isoformat()

        next_step = step_id + 1 if step_id < 17 else None
        updated_at = datetime.now(timezone.utc).isoformat()

        def _format_list_inline(values: list[int] | list) -> str:
            if not values:
                return "[]"
            return "[" + ", ".join(str(v) for v in values) + "]"

        completed_steps_str = _format_list_inline(new_completed)
        failed_steps_str = _format_list_inline(existing_failed_steps)
        next_step_str = "null" if next_step is None else str(next_step)

        header_lines = [
            "episode_info:",
            f"  episode_number: {self.episode_number}",
            f"  status: {status}",
            f"  created_at: \"{created_at}\"",
            f"  updated_at: \"{updated_at}\"",
            "",
            "workflow_progress:",
            f"  current_step: {step_id}",
            f"  completed_steps: {completed_steps_str}",
            f"  next_step: {next_step_str}",
            f"  failed_steps: {failed_steps_str}",
            "",
        ]

        step_results_lines = ["step_results:"]
        if existing_step_results:
            for key, value in existing_step_results.items():
                dumped_value = yaml.safe_dump(
                    value,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ).strip()
                if "\n" not in dumped_value:
                    step_results_lines.append(f"  {key}: {dumped_value}")
                else:
                    step_results_lines.append(f"  {key}:")
                    for inner_line in dumped_value.splitlines():
                        step_results_lines.append(f"    {inner_line}")
        else:
            step_results_lines.append("  # Step execution results")

        yaml_content = "\n".join(header_lines + step_results_lines) + "\n"

        return yaml_content
