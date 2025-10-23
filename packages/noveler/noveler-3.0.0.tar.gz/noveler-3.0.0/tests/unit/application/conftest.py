#!/usr/bin/env python3
"""Application層テスト用共通フィクスチャ

ユースケースやアプリケーションサービステストで使用する共通フィクスチャ群
"""

from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_episode_repository() -> Any:
    """モックエピソードリポジトリ"""
    return Mock()


@pytest.fixture
def mock_project_info_repository() -> Any:
    """モックプロジェクト情報リポジトリ"""
    return Mock()


@pytest.fixture
def mock_character_repository() -> Any:
    """モックキャラクターリポジトリ"""
    return Mock()


@pytest.fixture
def sample_command_data() -> dict[str, Any]:
    """テスト用コマンドデータ"""
    return {"project_name": "テストプロジェクト", "episode_number": 1, "episode_title": "第1話", "user_id": "test_user"}
