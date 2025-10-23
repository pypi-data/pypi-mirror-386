#!/usr/bin/env python3
import importlib


def test_main_explicit_exports_callable():
    mod = importlib.import_module("src.mcp_servers.noveler.main")
    names = [
        "execute_enhanced_get_writing_tasks",
        "execute_enhanced_execute_writing_step",
        "execute_enhanced_resume_from_partial_failure",
        "execute_get_check_tasks",
        "execute_check_step_command",
        "execute_get_check_status",
        "execute_get_check_history",
        "execute_generate_episode_preview",
    ]
    for n in names:
        assert hasattr(mod, n), f"{n} not exported from main"
        assert callable(getattr(mod, n)), f"{n} is not callable"


def test_main___all_contains_exports():
    mod = importlib.import_module("src.mcp_servers.noveler.main")
    exported = set(getattr(mod, "__all__", []))
    required = {
        "execute_enhanced_get_writing_tasks",
        "execute_enhanced_execute_writing_step",
        "execute_enhanced_resume_from_partial_failure",
        "execute_get_check_tasks",
        "execute_check_step_command",
        "execute_get_check_status",
        "execute_get_check_history",
        "execute_generate_episode_preview",
    }
    assert required.issubset(exported)

