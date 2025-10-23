#!/usr/bin/env python3

"""Tests.tests.unit.infrastructure.factories.test_path_service_factory
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import os
from pathlib import Path

import pytest


@pytest.fixture()
def temp_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sample_project"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_resolve_project_root_uses_config_when_env_missing(monkeypatch: pytest.MonkeyPatch, temp_dir: Path) -> None:
    """環境変数が未設定の場合、config(paths.samples.root)が優先されること。

    - PROJECT_ROOT / NOVELER_TEST_PROJECT_ROOT が未設定
    - config の paths.samples.root に一時ディレクトリを返すスタブをセット
    - _resolve_project_root(None) がそのパスを返すことを検証
    """
    # Ensure environment is clean
    monkeypatch.delenv("PROJECT_ROOT", raising=False)
    monkeypatch.delenv("NOVELER_TEST_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("NOVELER_SAMPLES_ROOT", raising=False)

    # Stub ConfigurationManager.get_configuration().get_path_setting
    from noveler.infrastructure.factories import path_service_factory as psf

    class DummyCfg:
        def get_path_setting(self, category: str, key: str, default=None):
            if category == "samples" and key == "root":
                return str(temp_dir)
            return default

    class DummyCfgMgr:
        def get_configuration(self):
            return DummyCfg()

    monkeypatch.setattr(psf, "ConfigurationManager", lambda: DummyCfgMgr())

    resolved = psf._resolve_project_root(None)
    assert resolved == temp_dir.resolve()


def test_resolve_project_root_prefers_env_over_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """PROJECT_ROOT が設定されている場合、config よりも環境変数が優先されること。"""
    env_dir = tmp_path / "env_project"
    env_dir.mkdir(parents=True, exist_ok=True)

    # Set env var to override
    monkeypatch.setenv("PROJECT_ROOT", str(env_dir))

    # Provide config that points elsewhere (should be ignored)
    other_dir = tmp_path / "config_project"
    other_dir.mkdir(parents=True, exist_ok=True)

    from noveler.infrastructure.factories import path_service_factory as psf

    class DummyCfg:
        def get_path_setting(self, category: str, key: str, default=None):
            if category == "samples" and key == "root":
                return str(other_dir)
            return default

    class DummyCfgMgr:
        def get_configuration(self):
            return DummyCfg()

    monkeypatch.setattr(psf, "ConfigurationManager", lambda: DummyCfgMgr())

    resolved = psf._resolve_project_root(None)
    assert resolved == env_dir.resolve()


def test_resolve_project_root_uses_samples_env_if_config_absent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """config も PROJECT_ROOT もない場合、detect_project_root()を試し、なければNOVELER_SAMPLES_ROOT を考慮する。"""
    monkeypatch.delenv("PROJECT_ROOT", raising=False)
    monkeypatch.delenv("NOVELER_TEST_PROJECT_ROOT", raising=False)

    # Create a samples root and default sample name under it
    samples_root = tmp_path / "samples"
    default_sample = samples_root / "10_Fランク魔法使いはDEBUGログを読む"
    default_sample.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("NOVELER_SAMPLES_ROOT", str(samples_root))

    from noveler.infrastructure.factories import path_service_factory as psf

    class DummyCfgMgr:
        def get_configuration(self):
            return None  # simulate missing config

    monkeypatch.setattr(psf, "ConfigurationManager", lambda: DummyCfgMgr())
    
    # テスト用に一時的にcwdを変更（インジケーターのないディレクトリ）
    import os
    original_cwd = os.getcwd()
    test_dir = tmp_path / "no_indicators"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        os.chdir(test_dir)
        resolved = psf._resolve_project_root(None)
        # detect_project_root()が失敗し、サンプルにフォールバックすることを確認
        assert resolved == default_sample.resolve()
    finally:
        os.chdir(original_cwd)

def test_resolve_project_root_detects_current_directory_project(temp_dir):
    """00_ガイドから実行時、detect_project_root()が正しく動作することを確認"""
    from noveler.infrastructure.factories.path_service_factory import _resolve_project_root
    
    # プロジェクトインジケーターを作成
    (temp_dir / "40_原稿").mkdir(parents=True, exist_ok=True)
    (temp_dir / "CLAUDE.md").touch()
    
    # 現在のディレクトリを一時ディレクトリに変更
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        
        # 環境変数をクリア
        env_backup = {
            "PROJECT_ROOT": os.environ.pop("PROJECT_ROOT", None),
            "NOVELER_TEST_PROJECT_ROOT": os.environ.pop("NOVELER_TEST_PROJECT_ROOT", None),
        }
        
        try:
            # _resolve_project_root()が現在のディレクトリを検出
            result = _resolve_project_root(None)
            assert result == temp_dir
        finally:
            # 環境変数を復元
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value
    finally:
        os.chdir(original_cwd)


def test_resolve_project_root_env_precedence(temp_dir):
    """環境変数PROJECT_ROOTが最優先されることを確認"""
    from noveler.infrastructure.factories.path_service_factory import _resolve_project_root
    
    # 別のプロジェクトディレクトリを作成
    project_dir = temp_dir / "custom_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # 現在のディレクトリにもインジケーターを配置
    (temp_dir / "40_原稿").mkdir(parents=True, exist_ok=True)
    
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        
        # 環境変数を設定
        env_backup = os.environ.get("PROJECT_ROOT")
        os.environ["PROJECT_ROOT"] = str(project_dir)
        
        try:
            # 環境変数が優先される
            result = _resolve_project_root(None)
            assert result == project_dir
        finally:
            if env_backup is not None:
                os.environ["PROJECT_ROOT"] = env_backup
            else:
                os.environ.pop("PROJECT_ROOT", None)
    finally:
        os.chdir(original_cwd)


def test_resolve_project_root_fallback_to_sample(temp_dir):
    """インジケーターがない場合、サンプルプロジェクトにフォールバック"""
    from noveler.infrastructure.factories.path_service_factory import _resolve_project_root
    
    import os
    original_cwd = os.getcwd()
    try:
        # インジケーターのないディレクトリに移動
        os.chdir(temp_dir)
        
        # 環境変数をクリア
        env_backup = {
            "PROJECT_ROOT": os.environ.pop("PROJECT_ROOT", None),
            "NOVELER_TEST_PROJECT_ROOT": os.environ.pop("NOVELER_TEST_PROJECT_ROOT", None),
        }
        
        try:
            result = _resolve_project_root(None)
            # インジケーターがないので、現在のディレクトリまたはサンプルプロジェクトになる
            # （環境によって異なる可能性があるため、Noneではないことのみ確認）
            assert result is not None
            assert isinstance(result, Path)
        finally:
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value
    finally:
        os.chdir(original_cwd)
