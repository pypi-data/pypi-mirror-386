from __future__ import annotations

from typing import List

import pytest

from noveler.domain.utils.domain_console import DomainConsole
from noveler.domain.utils.domain_logging import capture_domain_logs, suppress_domain_console_output


class DummyDelegate:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def print(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.messages.append(" ".join(str(arg) for arg in args))

    def print_warning(self, message: str) -> None:
        self.messages.append(f"warning:{message}")


@pytest.fixture()
def console_fixture() -> tuple[DomainConsole, DummyDelegate]:
    delegate = DummyDelegate()
    console = DomainConsole(delegate)
    return console, delegate


def test_capture_domain_logs_suppresses_delegate(console_fixture: tuple[DomainConsole, DummyDelegate]) -> None:
    console, delegate = console_fixture

    with capture_domain_logs() as logs:
        console.print("hello", "world")
        console.print_warning("caution")

    # UI delegate is suppressed inside capture_domain_logs by default
    assert delegate.messages == []
    assert logs == [
        {"level": "info", "message": "hello world"},
        {"level": "warning", "message": "caution"},
    ]


def test_capture_domain_logs_passes_through_when_requested(console_fixture: tuple[DomainConsole, DummyDelegate]) -> None:
    console, delegate = console_fixture

    with capture_domain_logs(suppress_ui=False) as logs:
        console.print("visible")

    assert delegate.messages == ["visible"]
    assert logs == [{"level": "info", "message": "visible"}]


def test_suppress_domain_console_output_context(console_fixture: tuple[DomainConsole, DummyDelegate]) -> None:
    console, delegate = console_fixture

    with suppress_domain_console_output():
        console.print("hidden")

    assert delegate.messages == []
