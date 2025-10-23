"""互換用 common_path_service モジュール

Phase6 で presentation 層へ移動した path サービスを、旧インポート経路
`noveler.infrastructure.services.common_path_service` からも利用できるようにする。
"""

from __future__ import annotations

from noveler.presentation.shared.shared_utilities import get_common_path_service as _get_common_path_service

__all__ = ["get_common_path_service"]


def get_common_path_service(*args, **kwargs):
    """互換ラッパー: presentation 層の実装へ委譲"""

    return _get_common_path_service(*args, **kwargs)
