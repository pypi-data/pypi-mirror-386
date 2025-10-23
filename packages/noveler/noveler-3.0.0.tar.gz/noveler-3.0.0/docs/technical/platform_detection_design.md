# Platform Detection Utility Design

## Purpose
- Provide a single source of truth for determining runtime platform categories: Windows (native), Windows Subsystem for Linux (WSL), Linux, macOS.
- Reduce duplicated `os.environ` / path sniffing logic scattered across infrastructure modules (e.g., Claude Code integrations, path services).
- Serve both runtime feature flags and diagnostic tooling (e.g., environment checks, logging context).

## Target Module
- Proposed location: `src/noveler/infrastructure/utils/platform.py`.
- Expose immutable data structures and light helper functions; avoid side effects.

## Public API (draft)
```python
from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache

class PlatformKind(Enum):
    WINDOWS = auto()
    WSL = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()

@dataclass(frozen=True)
class PlatformInfo:
    kind: PlatformKind
    is_wsl: bool
    is_windows: bool
    is_unix: bool
    raw_system: str
    details: dict[str, str]

@lru_cache(maxsize=1)
def detect_platform() -> PlatformInfo:
    ...
```
- Provide helper wrappers (`is_wsl()`, `is_windows_native()`, `is_macos()` etc.) around `detect_platform()`.

## Detection Strategy
- Base signal: `platform.system()`, `sys.platform`, `os.name`.
- WSL detection: check `/proc/version`, `/proc/sys/kernel/osrelease`, env vars (`WSL_DISTRO_NAME`, `WSL_INTEROP`), and UNC path prefix `\\wsl$`.
- Windows native detection: `platform.system() == "Windows"` and not WSL.
- macOS detection: `platform.system() == "Darwin"`.
- Linux detection: `platform.system() == "Linux"` with not WSL.

## Replacement Targets
- `src/noveler/infrastructure/claude_code_session_integration.py`: replace hard-coded `/mnt/c/...` checks.
- `src/noveler/infrastructure/adapters/path_service_adapter.py`: fallback logic relying on Unix paths.
- Future use in diagnostic scripts, installers (`bin/install.*`), Git wrapper automation.

## Non-goals
- No direct manipulation of environment variables.
- No filesystem writes; detection remains read-only.
- Container detection and cloud runners are out of scope for this iteration.

## Validation Plan
- Unit tests under `tests/unit/infrastructure/utils/test_platform.py` with environment mocking.
- Integration smoke via `scripts/diagnostics/check_env.py` to print detected platform info.

## Open Questions
- Should we expose additional detail (WSL distro, Windows build)? Store under `details` for optional logging.
- Is process-wide caching sufficient? Document expectation that platform does not change mid-run.
