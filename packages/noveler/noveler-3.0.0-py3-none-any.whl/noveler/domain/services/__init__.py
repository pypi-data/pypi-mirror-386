# File: src/noveler/domain/services/__init__.py
# Purpose: Expose domain service modules and maintain legacy import aliases.
# Context: Legacy tests import `domain.services.*`; keep compatibility with new package path.

"""ドメインサービス"""

import sys as _sys

_sys.modules.setdefault("domain.services", _sys.modules[__name__])
