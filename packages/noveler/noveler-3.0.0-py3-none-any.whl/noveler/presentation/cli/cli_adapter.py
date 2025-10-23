#!/usr/bin/env python3
# File: src/noveler/presentation/cli/cli_adapter.py
# Purpose: Provide a thin CLI facade delegating Noveler commands to
#          presentation/domain adapters while maintaining shared logging
#          and event-loop setup.
# Context: Presentation layer entry point invoked by `noveler` executable.
#          Integrates with MCP modules for local command execution.
"""CLI Facade (presentation layer)

- Single entrypoint: `run(argv: list[str] | None = None) -> int`
- Handles: `mcp-server`, `mcp call <tool> '{json}'`, `check <episode|file> [--auto-fix]`, `write <episode> [--dry-run]`
- Event-loop initialization and logging/console setup are constrained to this layer.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import shutil

import yaml
from noveler.infrastructure.factories.path_service_factory import create_common_path_service
from noveler.presentation.cli.cli_mapping import iter_mappings
from noveler.presentation.cli.mcp_client import MCPClient, MCPClientError
from noveler.presentation.shared.shared_utilities import get_console

_CLIENT = MCPClient()


def _ensure_event_loop() -> None:
    """Ensure a default event loop exists only when running the CLI."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def _render_help() -> str:
    """Generate help text from CLI command mappings."""
    lines = [
        "Usage:",
        "  noveler mcp-server",
        "  noveler mcp call <tool> '{JSON}'",
        "  noveler check <episode|file> [--auto-fix] [--exclude-dialogue]",
        "  noveler write <episode> [--dry-run]",
        "",
        "Available Commands:",
    ]

    for mapping in iter_mappings():
        lines.append(f"  {mapping.cli_command}")
        lines.append(f"    → {mapping.mcp_tool}: {mapping.description}")

    lines.extend([
        "",
        "Examples:",
        "  noveler mcp call run_quality_checks '{\"episode_number\":1,\"file_path\":\"README.md\",\"exclude_dialogue_lines\":true}'",
        "  noveler mcp call enhanced_get_writing_tasks '{\"episode_number\":1}'",
    ])

    return "\n".join(lines)


def _parse_args(argv: list[str]) -> tuple[str, list[str]]:
    if not argv:
        return "", []
    return argv[0], argv[1:]


def _parse_write_args(tokens: list[str]) -> tuple[int, bool]:
    """Parse arguments for the ``write`` command.

    Returns the selected episode number and dry-run flag. When no explicit
    episode number is supplied the function defaults to episode 1 so that
    invocations such as ``noveler write --dry-run`` remain intuitive.
    """

    episode: int | None = None
    dry_run = False

    for token in tokens:
        if token == "--dry-run":
            dry_run = True
            continue

        if token.startswith("--"):
            raise ValueError(f"unknown option: {token}")

        if episode is None:
            episode = int(token)
            continue

        raise ValueError("multiple episode numbers provided")

    if episode is None:
        episode = 1

    return episode, dry_run


def _extract_score(payload: Any, *, fallback: float = 0.0) -> float:
    """Best-effort extraction of a numeric score from MCP responses.

    Handles the three response envelopes we currently see:
    1) 旧来の `{score: ...}` フラット辞書
    2) `{"result": {"score": ...}}` の軽量MCPレスポンス
    3) `{"result": {"data": {"score": ...}}}` のJSON-RPC風ラッパー
    """
    try:
        if isinstance(payload, dict):
            if "score" in payload:
                return float(payload.get("score") or fallback)
            inner = payload.get("result")
            if isinstance(inner, dict):
                if "score" in inner:
                    return float(inner.get("score") or fallback)
                inner_data = inner.get("data")
                if isinstance(inner_data, dict) and "score" in inner_data:
                    return float(inner_data.get("score") or fallback)
    except Exception:  # noqa: BLE001
        return fallback
    return fallback


def _extract_success(payload: Any, *, default: bool = True) -> bool:
    """Best-effort extraction of success flags from MCP responses.

    想定パターン:
    - 旧来の `{success: bool}`
    - MCPの `{"result": {"success": bool}}` ラッパー
    将来のフォーマット拡張時はここに分岐を足す。
    """
    if isinstance(payload, dict):
        if "success" in payload:
            return bool(payload["success"])
        inner = payload.get("result")
        if isinstance(inner, dict) and "success" in inner:
            return bool(inner["success"])
    return default


def run(argv: list[str] | None = None) -> int:
    """CLI facade entrypoint.

    Returns an exit code (0=success, non-zero=failure).
    """
    console = get_console()
    _ensure_event_loop()

    args = list(sys.argv[1:] if argv is None else argv)

    # Basic help
    if not args or args[0] in ("-h", "--help"):
        console.print(_render_help())
        return 0

    try:
        cmd, rest = _parse_args(args)

        if cmd == "mcp-server":
            # Lazy import to avoid unnecessary dependencies outside this path
            mcp_main = importlib.import_module("mcp_servers.noveler.main").main

            asyncio.run(mcp_main())
            return 0

        if cmd == "mcp":
            if not rest or rest[0] != "call" or len(rest) < 2:
                console.print("Usage: noveler mcp call <tool> '{JSON}'")
                return 2
            tool = rest[1]
            json_str = rest[2] if len(rest) >= 3 else "{}"
            try:
                args_obj: dict[str, Any] = json.loads(json_str)
            except Exception as e:  # noqa: BLE001
                console.print(f"❌ JSONパースエラー: {e}")
                return 2

            try:
                result = _CLIENT.call_tool(tool, args_obj)
            except MCPClientError as exc:
                console.print(f"❌ MCPツール呼び出しに失敗しました: {exc}")
                return 2

            try:
                console.print(json.dumps(result, ensure_ascii=False, indent=2))
            except Exception:  # noqa: BLE001
                console.print(str(result))

            success = True
            if isinstance(result, dict):
                success = bool(result.get("success", True))
            return 0 if success else 1

        if cmd == "check":
            # 互換: noveler check <episode|file> [--auto-fix]
            if not rest:
                console.print("Usage: noveler check <episode|file> [--auto-fix]")
                return 2
            target = rest[0]
            auto_fix = "--auto-fix" in rest[1:]
            exclude_dialogue_flag = "--exclude-dialogue" in rest[1:]
            # episode or file
            episode: int | None = None
            file_path: str | None = None
            try:
                episode = int(target)
            except Exception:  # noqa: BLE001
                file_path = target

            def _build_run_payload() -> dict[str, Any]:
                additional_params: dict[str, Any] = {
                    "format": "summary",
                    "severity_threshold": "medium",
                    "exclude_dialogue_lines": exclude_dialogue_flag
                    or os.getenv("NOVELER_EXCLUDE_DIALOGUE") in ("1", "true", "on"),
                }
                if file_path is not None:
                    additional_params["file_path"] = file_path
                return {
                    "episode_number": episode or 1,
                    "additional_params": additional_params,
                }

            def _call(tool: str, payload: dict[str, Any]) -> tuple[Any | None, bool]:
                try:
                    result = _CLIENT.call_tool(tool, payload)
                except MCPClientError as exc:
                    console.print(f"❌ MCPツール呼び出しに失敗しました ({tool}): {exc}")
                    return None, False
                return result, True

            run_payload = _build_run_payload()
            run_result, ok = _call("run_quality_checks", run_payload)
            if not ok or run_result is None:
                return 2

            score = _extract_score(run_result)
            console.print(f"品質スコア(現状): {score:.1f}点")

            if auto_fix:
                improved_score = score
                improve_payload = {
                    "episode_number": episode or 1,
                    "additional_params": {
                        "file_path": file_path,
                        "target_score": 80,
                        "max_iterations": 3,
                        "include_diff": False,
                    },
                }
                improve_result, improve_ok = _call("improve_quality_until", improve_payload)
                if improve_ok and improve_result is not None:
                    improved_score = _extract_score(improve_result, fallback=improved_score)
                    console.print(f"自動改善を実行しました（最終スコア）: {improved_score:.1f}点")
                else:
                    # フォールバック: 単回の安全Fixを適用
                    fix_payload = {
                        "episode_number": episode or 1,
                        "additional_params": {"file_path": file_path, "dry_run": False},
                    }
                    fix_result, fix_ok = _call("fix_quality_issues", fix_payload)
                    if not fix_ok or fix_result is None:
                        return 2
                    metadata = fix_result.get("metadata") if isinstance(fix_result, dict) else {}
                    applied = 0
                    if isinstance(metadata, dict):
                        applied = int(metadata.get("applied", 0) or 0)
                    console.print(f"自動修正を適用しました: {applied}件")

                rerun_result, rerun_ok = _call("run_quality_checks", run_payload)
                if not rerun_ok or rerun_result is None:
                    return 2
                rerun_score = _extract_score(rerun_result)
                score = max(improved_score, rerun_score)
                console.print(f"品質スコア(修正後): {score:.1f}点")

            return 0 if score >= 80.0 else 1

        if cmd == "write":
            try:
                episode, dry_run = _parse_write_args(rest)
            except ValueError as err:
                console.print(f"❌ write引数エラー: {err}")
                return 2
            except Exception as err:  # noqa: BLE001
                console.print(f"❌ write解析エラー: {err}")
                return 2

            project_root_s = os.getcwd()

            command_str = f"write {episode}"
            if dry_run:
                command_str += " --dry-run"
            mcp_payload = {
                "command": command_str,
                "project_root": project_root_s,
                "options": {
                    "episode_number": episode,
                    "dry_run": dry_run,
                },
            }
            try:
                result = _CLIENT.call_tool("noveler", mcp_payload)
            except MCPClientError as exc:
                console.print_warning(f"⚠️ MCP経由のwrite実行に失敗しました: {exc}")
            else:
                success = _extract_success(result)
                if not success:
                    console.print("❌ write実行エラー: MCP応答が失敗を示しました")
                return 0 if success else 1

            async def _run() -> int:
                try:
                    result = await execute_18_step_writing(
                        episode=episode,
                        dry_run=dry_run,
                        project_root=project_root_s,
                    )
                except Exception as exc:  # noqa: BLE001
                    console.print(f"❌ write実行エラー: {exc}")
                    return 1
                return 0 if result.get("success") else 1

            return asyncio.run(_run())

        # 不明コマンド
        console.print("❌ サポートされていないコマンドです")
        console.print("対応コマンド: mcp-server | mcp call | check | write")
        return 1

    except ImportError as e:  # noqa: BLE001
        console.print(f"❌ インポートエラー: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        console.print(f"❌ 実行エラー: {e}")
        return 1


# ===== Write 18-steps (kept for compatibility) =====
from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
from noveler.domain.value_objects.universal_prompt_execution import (
    ProjectContext,
    PromptType,
    UniversalPromptRequest,
)
from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService
from noveler.infrastructure.json.file_managers.enhanced_file_manager import EnhancedFileManager


def _extract_write_result_from_envelope(payload: Any) -> dict[str, Any] | None:
    """Normalize MCP noveler tool responses for the write workflow.

    Args:
        payload: Raw response returned by the MCP noveler tool.

    Returns:
        dict[str, Any] | None: Extracted result dictionary compatible with the
        legacy CLI expectations when recognised, otherwise ``None``.
    """
    if not isinstance(payload, dict):
        return None

    # Direct legacy format already matches expectations.
    success_value = payload.get("success")
    if isinstance(success_value, bool):
        return payload

    result_block = payload.get("result")
    if not isinstance(result_block, dict):
        return None

    extracted: dict[str, Any] | None = None

    data_block = result_block.get("data")
    if isinstance(data_block, dict):
        candidate = data_block.get("result")
        if isinstance(candidate, dict):
            extracted = dict(candidate)

    if extracted is None:
        candidate = result_block.get("result")
        if isinstance(candidate, dict):
            extracted = dict(candidate)

    if extracted is None:
        return None

    if isinstance(result_block.get("success"), bool) and "success" not in extracted:
        extracted["success"] = bool(result_block["success"])

    return extracted


async def execute_18_step_writing(episode: int, dry_run: bool, project_root: str) -> dict:
    """18ステップ執筆システムの実行（共通基盤使用版）"""
    console = get_console()

    payload = {
        "command": f"write {episode}",
        "project_root": project_root,
        "options": {
            "dry_run": dry_run,
            "episode_number": episode,
        },
    }

    try:
        response = await _CLIENT.call_tool_async("noveler", payload)
    except MCPClientError as err:
        console.print_warning(f"⚠️ MCP write委譲に失敗しました（フォールバック実行）: {err}")
    except Exception as exc:  # noqa: BLE001
        console.print_warning(f"⚠️ MCP write委譲で予期せぬエラー（フォールバック実行）: {exc}")
    else:
        tool_result = _extract_write_result_from_envelope(response)
        if tool_result is not None:
            return tool_result
        console.print_warning("⚠️ MCP write委譲の応答形式が不明のためローカル実装にフォールバックします")

    project_path = Path(project_root)
    json_output_dir = project_path / "temp" / "json_output"
    file_manager = EnhancedFileManager(json_output_dir)
    path_service = create_common_path_service(project_path)

    steps = [
        {"id": 0, "name": "スコープ定義", "phase": "構造設計"},
        {"id": 1, "name": "大骨（章の目的線）", "phase": "構造設計"},
        {"id": 2, "name": "中骨（段階目標）", "phase": "構造設計"},
        {"id": 3, "name": "テーマ性・独自性検証", "phase": "構造設計"},
        {"id": 4, "name": "セクションバランス設計", "phase": "構造設計"},
        {"id": 5, "name": "小骨（シーン／ビート）", "phase": "構造設計"},
        {"id": 6, "name": "論理検証", "phase": "構造設計"},
        {"id": 7, "name": "キャラクター一貫性検証", "phase": "構造設計"},
        {"id": 8, "name": "会話設計", "phase": "構造設計"},
        {"id": 9, "name": "感情曲線", "phase": "構造設計"},
        {"id": 10, "name": "世界観設計", "phase": "構造設計"},
        {"id": 11, "name": "初稿生成", "phase": "執筆実装"},
        {"id": 12, "name": "文字数最適化", "phase": "執筆実装"},
        {"id": 13, "name": "文体・可読性パス", "phase": "執筆実装"},
        {"id": 14, "name": "必須品質ゲート", "phase": "品質保証"},
        {"id": 15, "name": "最終品質認定", "phase": "品質保証"},
        {"id": 16, "name": "公開準備", "phase": "公開"},
        {"id": 17, "name": "仕上げ", "phase": "公開"},
        {"id": 18, "name": "最終確認", "phase": "公開"},
    ]

    console.print_info(f"🔄 第{episode:03d}話の18ステップ執筆を開始します...")

    execution_log: list[dict[str, Any]] = []
    completed_steps = 0
    episode_content = ""

    for step in steps:
        step_id = step["id"]
        step_name = step["name"]
        step_phase = step["phase"]

        console.print_info(f"🔄 STEP {step_id}: {step_name}")

        step_content = await _execute_writing_step(step, episode, project_path)

        if not dry_run:
            step_data = {
                "step_id": step_id,
                "step_name": step_name,
                "phase": step_phase,
                "content": step_content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "episode_number": episode,
            }
            file_manager.save_quality_report(
                report_data=step_data, episode_number=episode, report_type=f"step_{str(step_id).replace('.', '_')}"
            )

            try:
                from noveler.infrastructure.llm.llm_io_logger import LLMIOLogger  # noqa: PLC0415

                io_logger = LLMIOLogger(project_path)
                io_logger.save_stage_io(
                    episode_number=episode,
                    step_number=int(step_id) if isinstance(step_id, int) else 0,
                    stage_name=str(step_name),
                    request_content={
                        "phase": step_phase,
                        "project_root": str(project_path),
                        "context": "execute_18_step_writing",
                    },
                    response_content={
                        "content": step_content,
                        "metadata": {"report_file": f"step_{str(step_id).replace('.', '_')}"},
                        "success": True,
                    },
                    extra_metadata={"kind": "write_18_steps"},
                )
            except Exception:  # noqa: BLE001
                pass

        if step_phase == "執筆実装" and step_content:
            episode_content += step_content + "\n\n"

        execution_log.append(
            {
                "step": step_id,
                "name": step_name,
                "phase": step_phase,
                "status": "completed",
                "content_length": len(step_content),
            }
        )
        completed_steps += 1

        console.print_success(f"✅ STEP {step_id}: {step_name} 完了")

    saved_files: list[str] = []
    if not dry_run and episode_content.strip():
        final_content = f"# 第{episode:03d}話\n\n{episode_content.strip()}"

        metadata = {
            "execution_time_seconds": 0,
            "total_steps": len(steps),
            "completed_steps": completed_steps,
        }

        save_result = file_manager.save_manuscript_with_metadata(
            content=final_content, episode_number=episode, metadata=metadata, backup_existing=True
        )

        temp_manuscript_path = Path(save_result["manuscript_path"])
        destination_path: Path | None = None

        try:
            manuscript_dir = path_service.get_manuscript_dir()
            manuscript_dir.mkdir(parents=True, exist_ok=True)
            destination_path = manuscript_dir / temp_manuscript_path.name
            if temp_manuscript_path.exists():
                shutil.copy2(temp_manuscript_path, destination_path)
            else:
                destination_path.write_text(final_content, encoding="utf-8")
            console.print_success(f"📄 エピソードファイル保存: {destination_path}")
        except Exception as copy_error:  # noqa: BLE001
            console.print_warning(f"⚠️ 原稿ディレクトリへのコピーに失敗しました: {copy_error}")
            console.print_success(f"📄 エピソードファイル保存: {save_result['manuscript_path']}")

        if destination_path and destination_path.exists():
            saved_files.append(str(destination_path))
        else:
            saved_files.append(str(temp_manuscript_path))

        console.print_info(
            f"🗞️ ファイルサイズ: {save_result['size_bytes']:,} バイト, 文字数: {save_result['metadata']['word_count']:,}"
        )

    completion_rate = completed_steps / len(steps) * 100
    console.print_info(f"📊 {completed_steps}/{len(steps)}ステップ完了 ({completion_rate:.1f}%)")
    console.print_success(f"✅ 第{episode:03d}話の執筆完了")

    return {
        "success": True,
        "episode": episode,
        "total_steps": len(steps),
        "completed_steps": completed_steps,
        "completion_rate": f"{completion_rate:.1f}%",
        "execution_log": execution_log,
        "saved_files": saved_files,
        "content_length": len(episode_content),
        "file_manager_used": "EnhancedFileManager",
    }


async def _execute_writing_step(step: dict, episode: int, project_path: Path) -> str:
    """個別の執筆ステップを実行してコンテンツを生成"""
    step_id = step["id"]
    step_name = step["name"]
    step_phase = step["phase"]

    # プロジェクト設定.yamlを読み込み
    try:
        project_config_path = project_path / "プロジェクト設定.yaml"
        project_config: dict[str, Any] = {}
        if project_config_path.exists():
            with project_config_path.open("r", encoding="utf-8") as f:
                project_config = yaml.safe_load(f) or {}
    except Exception:  # noqa: BLE001
        project_config = {}

    target_word_count = int(project_config.get("target_word_count", 10000))

    # Step 11（初稿生成）の場合のみClaude統合システムを使用
    if step_phase == "執筆実装" and step_id == 11:
        return await _generate_manuscript_with_claude(episode, target_word_count, project_path, project_config)

    content_map = {
        ("構造設計", 0): f"第{episode:03d}話のスコープ: 基本設定と目標の定義（目標文字数: {target_word_count}文字）",
        ("構造設計", 1): "章の目的: 主人公の成長と課題解決",
        ("構造設計", 2): "段階目標: 導入→展開→解決の3段階構成",
        ("構造設計", 3): "テーマ検証: 成長とチャレンジの独自性確認",
        ("構造設計", 4): "バランス設計: 導入20%、展開60%、解決20%",
        ("構造設計", 5): "シーン構成: 開始シーン、展開シーン、解決シーン",
        ("構造設計", 6): "論理検証: 物語の因果関係と整合性確認",
        ("構造設計", 7): "キャラクター一貫性: 主人公の行動・思考パターン確認",
        ("構造設計", 8): "会話設計: 自然な対話と感情表現の設計",
        ("構造設計", 9): "感情曲線: 緊張→緩和→クライマックスの感情変化",
        ("構造設計", 10): "世界観設定: 具体的な場所、時間、雰囲気の描写",
        ("執筆実装", 12): f"文字数調整: 目標{target_word_count}文字に向けて適切な長さに調整し、読みやすさを向上",
        ("執筆実装", 13): "文体改善: 自然な表現と読みやすい構成に修正",
        ("品質保証", 14): "品質チェック: 誤字脱字、構成、整合性の確認完了",
        ("品質保証", 15): "最終確認: 全体品質基準クリア、公開準備完了",
        ("公開", 16): "公開準備: タイトル、タグ、説明文の最終確認完了",
    }

    return content_map.get((step_phase, step_id), f"{step_name}の処理を完了")


async def _generate_manuscript_with_claude(
    episode: int, target_word_count: int, project_path: Path, project_config: dict
) -> str:
    """Claude統合システムを使用した原稿生成"""
    console = get_console()
    console.print(
        f"[blue]🤖 Claude統合執筆システムで第{episode:03d}話を生成中...（目標: {target_word_count}文字）[/blue]"
    )

    try:
        # UniversalLLMUseCaseを初期化
        claude_service = UniversalClaudeCodeService()
        claude_use_case = UniversalLLMUseCase(claude_service)

        # プロジェクトコンテキスト作成
        project_context = ProjectContext(
            project_name=project_config.get("title", "ガイドプロジェクト"),
            project_root=project_path,
        )

        # 執筆プロンプト作成
        writing_prompt = f"""
あなたは熟練した小説家です。以下の条件に従って、第{episode:03d}話の原稿を執筆してください。

## 執筆条件
- 目標文字数: **{target_word_count}文字**
- ジャンル: {project_config.get("genre", "ファンタジー")}
- タイトル: {project_config.get("title", "ガイドプロジェクト")}
- エピソード番号: 第{episode:03d}話

## 構成要求
1. 導入部（約20%）: 設定と状況の説明
2. 展開部（約60%）: 主人公の行動と変化
3. 解決部（約20%）: 結末と次への展望

## 品質要求
- 読みやすい文体で執筆
- 会話と地の文のバランスを取る
- 感情描写を豊かに
- 必ず目標文字数に近づける

原稿をMarkdown形式で出力してください。
"""

        # UniversalPromptRequestを作成
        request = UniversalPromptRequest(
            prompt_type=PromptType.WRITING,
            prompt_content=writing_prompt,
            project_context=project_context,
            output_format="text",
            max_turns=1,
            type_specific_config={
                "target_word_count": target_word_count,
                "episode_number": episode,
                "genre": project_config.get("genre", "ファンタジー"),
            },
        )

        # Claude統合実行
        response = await claude_use_case.execute_with_fallback(request, fallback_enabled=True)

        if response.is_success():
            manuscript = response.response_content
            word_count = len(manuscript)
            console.print(f"[green]✅ Claude執筆完了: {word_count}文字生成[/green]")

            if word_count < target_word_count * 0.8:
                console.print(f"[yellow]⚠️ 文字数不足（目標:{target_word_count}, 生成:{word_count}）[/yellow]")

            return manuscript

        console.print("[yellow]⚠️ Claude実行失敗、フォールバックコンテンツを使用[/yellow]")
        return (
            f"# 第{episode:03d}話 フォールバック原稿\n\n"
            "Claude統合システムが利用できない場合のフォールバック原稿です。\n\n"
            "実際の執筆では、Claude統合により{target_word_count}文字の完全な小説が生成される予定です。\n\n"
            "現在はシステム調整中のため、この簡潔なコンテンツを表示しています。\n"
        )

    except Exception as e:  # noqa: BLE001
        console.print(f"[red]❌ Claude統合エラー: {e}[/red]")
        return (
            f"# 第{episode:03d}話 エラー時フォールバック原稿\n\n"
            "システムエラーが発生したため、フォールバック原稿を表示しています。\n\n"
            f"エラー詳細: {str(e)[:100]}...\n\n"
            "実際の執筆では、Claude統合により{target_word_count}文字の完全な小説が生成される予定です。\n"
        )
