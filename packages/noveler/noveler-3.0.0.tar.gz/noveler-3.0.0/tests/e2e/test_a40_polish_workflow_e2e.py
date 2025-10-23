#!/usr/bin/env python3
"""A40 推敲（Stage2/3）ワークフローのE2Eテスト

polish_manuscript_apply（dry_run）でアーティファクトが返ること、
restore_manuscript_from_artifact（dry_run）で差分が生成されることを確認。
"""

import pytest

from mcp_servers.noveler import main as mcp_mod


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_polish_apply_and_restore_dry_run() -> None:
    # 1) Apply（dry_run）: 改稿・差分・レポートの参照IDが返る
    apply_args = {
        "episode_number": 1,
        "file_path": "temp/test_data/40_原稿/第001話_スモークテスト.md",
        "stages": ["stage2", "stage3"],
        "dry_run": True,
        "save_report": True,
    }
    apply_res = await mcp_mod.execute_polish_manuscript_apply(apply_args)
    assert isinstance(apply_res, dict) and apply_res.get("success"), "polish_manuscript_apply failed"
    meta = apply_res.get("metadata") or {}
    assert "diff_artifact" in meta and "report_artifact" in meta, "artifacts not found in metadata"
    assert "improved_artifact" in meta, "improved manuscript artifact missing"

    improved_artifact = (meta.get("improved_artifact") or {}).get("artifact_id")
    assert improved_artifact, "improved_artifact id missing"

    # 2) Restore（dry_run）: artifact_idで差分が生成される
    restore_args = {
        "episode_number": 1,
        "file_path": "temp/test_data/40_原稿/第001話_スモークテスト.md",
        "artifact_id": improved_artifact,
        "dry_run": True,
        "create_backup": True,
    }
    restore_res = await mcp_mod.execute_restore_manuscript_from_artifact(restore_args)
    assert isinstance(restore_res, dict) and restore_res.get("success"), "restore_manuscript_from_artifact failed"
    rmeta = restore_res.get("metadata") or {}
    assert "diff_artifact" in rmeta, "restore diff artifact missing"
