"""Scripts.infrastructure.json.file_managers.file_reference_manager
Where: Script helper managing JSON file references for infrastructure tasks.
What: Loads, updates, and resolves JSON file references used by tooling.
Why: Keeps JSON reference management logic centralised for reuse.
"""

from noveler.infrastructure.json.file_managers.file_reference_manager import (
    FileReferenceManager,  # re-export for compatibility
)

__all__ = ["FileReferenceManager"]
