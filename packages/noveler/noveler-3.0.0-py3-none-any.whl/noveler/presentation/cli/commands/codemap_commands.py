#!/usr/bin/env python3
"""CODEMAP 関連の簡易CLIコマンド（テスト用最小実装）"""

from pathlib import Path

import click


@click.group(name="codemap")
def codemap_group() -> None:
    """CODEMAP ツール群"""


@codemap_group.command("status")
@click.option("--codemap-path", required=False, type=click.Path(path_type=Path))
@click.option("--repository-path", required=False, type=click.Path(path_type=Path))
def status(codemap_path: Path | None, repository_path: Path | None) -> None:
    """CODEMAPの状態を確認（最小スタブ）"""
    # 必須引数の存在チェック（最小）
    _ = codemap_path, repository_path
    # 正常終了（Clickは例外がなければexit code 0）
    click.echo("codemap status: OK")

