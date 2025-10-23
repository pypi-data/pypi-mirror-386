#!/usr/bin/env python3

"""Tests.tests.integration.test_project_root_precedence
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.integration
def test_project_root_priority_env_over_config(monkeypatch, tmp_path: Path):
    from noveler.infrastructure.factories import path_service_factory as psf

    # Ensure clean env
    for k in ["PROJECT_ROOT", "NOVELER_TEST_PROJECT_ROOT", "NOVELER_SAMPLES_ROOT"]:
        monkeypatch.delenv(k, raising=False)

    # Prepare env PROJECT_ROOT
    env_root = tmp_path / "env_root"
    env_root.mkdir()
    monkeypatch.setenv("PROJECT_ROOT", str(env_root))

    # Also prepare a config that would point elsewhere (should be ignored)
    class DummyConfig:
        def get_path_setting(self, category: str, key: str, default: str | None = None):
            return str(tmp_path / "config_root") if (category, key) == ("samples", "root") else default

    monkeypatch.setattr(
        psf,
        "ConfigurationManager",
        lambda: type("_M", (), {"get_configuration": lambda self, force_reload=False: DummyConfig()})(),
    )

    resolved = psf._resolve_project_root(None)
    assert resolved == env_root.resolve()


@pytest.mark.integration
def test_project_root_from_config_when_env_absent(monkeypatch, tmp_path: Path):
    from noveler.infrastructure.factories import path_service_factory as psf

    # Ensure no env roots
    for k in ["PROJECT_ROOT", "NOVELER_TEST_PROJECT_ROOT", "NOVELER_SAMPLES_ROOT"]:
        monkeypatch.delenv(k, raising=False)

    config_root = tmp_path / "config_root"
    config_root.mkdir()

    class DummyConfig:
        def get_path_setting(self, category: str, key: str, default: str | None = None):
            if (category, key) == ("samples", "root"):
                return str(config_root)
            return default

    monkeypatch.setattr(
        psf,
        "ConfigurationManager",
        lambda: type("_M", (), {"get_configuration": lambda self, force_reload=False: DummyConfig()})(),
    )

    resolved = psf._resolve_project_root(None)
    assert resolved == config_root.resolve()


@pytest.mark.integration
def test_project_root_from_samples_root_with_default_name_present(monkeypatch, tmp_path: Path):
    from noveler.infrastructure.factories import path_service_factory as psf

    # Clean env and config
    for k in ["PROJECT_ROOT", "NOVELER_TEST_PROJECT_ROOT"]:
        monkeypatch.delenv(k, raising=False)

    # Return None config (so it falls through to NOVELER_SAMPLES_ROOT)
    monkeypatch.setattr(
        psf,
        "ConfigurationManager",
        lambda: type("_M", (), {"get_configuration": lambda self, force_reload=False: None})(),
    )

    samples_root = tmp_path / "samples"
    default_name = "10_Fランク魔法使いはDEBUGログを読む"

    target = samples_root / default_name
    target.mkdir(parents=True)
    monkeypatch.setenv("NOVELER_SAMPLES_ROOT", str(samples_root))

    resolved = psf._resolve_project_root(None)
    assert resolved == target.resolve()


@pytest.mark.integration
def test_project_root_from_samples_root_without_default_name(monkeypatch, tmp_path: Path):
    from noveler.infrastructure.factories import path_service_factory as psf

    for k in ["PROJECT_ROOT", "NOVELER_TEST_PROJECT_ROOT"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(
        psf,
        "ConfigurationManager",
        lambda: type("_M", (), {"get_configuration": lambda self, force_reload=False: None})(),
    )

    samples_root = tmp_path / "samples"
    samples_root.mkdir()
    # 既定名ディレクトリは作らない → サンプル親を返すはず
    monkeypatch.setenv("NOVELER_SAMPLES_ROOT", str(samples_root))

    resolved = psf._resolve_project_root(None)
    assert resolved == samples_root.resolve()


@pytest.mark.integration
def test_project_root_fallback_to_cwd(monkeypatch, tmp_path: Path):
    from noveler.infrastructure.factories import path_service_factory as psf

    # すべて未設定 → CWD
    for k in ["PROJECT_ROOT", "NOVELER_TEST_PROJECT_ROOT", "NOVELER_SAMPLES_ROOT"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(
        psf,
        "ConfigurationManager",
        lambda: type("_M", (), {"get_configuration": lambda self, force_reload=False: None})(),
    )

    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        resolved = psf._resolve_project_root(None)
        assert resolved == tmp_path.resolve()
