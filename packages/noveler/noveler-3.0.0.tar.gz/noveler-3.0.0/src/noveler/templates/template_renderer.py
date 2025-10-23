"""Template Renderer - Orchestrates template rendering with variable expansion.

Application Layer: Coordinates Domain and Infrastructure components.
Responsible for: Template loading → Variable expansion → YAML parsing

SOLID Principles:
- SRP: Single responsibility (orchestration only)
- OCP: Open for extension (expander can be injected)
- LSP: N/A (no inheritance)
- ISP: Minimal interface (__init__, render_template)
- DIP: Depends on abstractions (injected components)
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .domain.variable_expander import VariableExpander, Jinja2TemplateError
from .infrastructure.config_loader import ConfigLoader
from .infrastructure.cache_manager import CacheManager


class TemplateRenderer:
    """Renders YAML templates with Jinja2 variable expansion.

    This class orchestrates the template rendering workflow:
    1. Check cache for previously rendered template
    2. Load .novelerrc.yaml configuration
    3. Read template file
    4. Expand Jinja2 variables with config values
    5. Parse expanded YAML
    6. Cache result for future use

    Attributes:
        project_root: Path to project root directory
        config_loader: ConfigLoader instance (Infrastructure)
        cache_manager: CacheManager instance (Infrastructure)
        expander: VariableExpander instance (Domain)
        _last_config_mtime: Last known .novelerrc.yaml modification time
    """

    def __init__(
        self,
        project_root: Path,
        config_loader: Optional[ConfigLoader] = None,
        cache_manager: Optional[CacheManager] = None,
        expander: Optional[VariableExpander] = None,
    ) -> None:
        """Initialize TemplateRenderer with dependency injection.

        Args:
            project_root: Path to project root directory
            config_loader: Optional ConfigLoader (default: new instance)
            cache_manager: Optional CacheManager (default: new instance)
            expander: Optional VariableExpander (default: new instance)

        Precondition:
            - project_root is a valid directory
            - project_root contains .novelerrc.yaml

        Postcondition:
            - Renderer is ready to render templates

        Design Pattern:
            Constructor injection for testability and flexibility
        """
        self.project_root = Path(project_root)
        self.config_loader = config_loader or ConfigLoader()
        self.cache_manager = cache_manager or CacheManager()
        self.expander = expander or VariableExpander()
        self._last_config_mtime: Optional[float] = None

    def render_template(self, template_path: Path) -> Dict[str, Any]:
        """Render YAML template with variable expansion.

        Args:
            template_path: Path to template file (relative or absolute)

        Returns:
            Dictionary containing expanded YAML data

        Raises:
            FileNotFoundError: If template file doesn't exist
            Jinja2TemplateError: If template has syntax errors
            yaml.YAMLError: If expanded result is invalid YAML

        Workflow:
            1. Check and invalidate cache if config changed
            2. Check cache for existing result
            3. Load configuration
            4. Read template file
            5. Expand variables
            6. Parse YAML
            7. Cache result
            8. Return dictionary

        Performance:
            - Cache hit: <5ms (from Phase 2 metrics)
            - Cache miss: ~80-100ms (Phase 2 metrics)
        """
        # Ensure absolute path
        if not template_path.is_absolute():
            template_path = self.project_root / template_path

        # Step 1: Invalidate cache if config changed
        self._invalidate_cache_if_needed()

        # Step 2: Check cache
        cache_key = str(template_path)
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Step 3: Load configuration
        config = self.config_loader.load(self.project_root)
        active_settings = self.config_loader.extract_active_preset(config)

        # Flatten writing_style namespace for Jinja2
        context = {"writing_style": active_settings}

        # Step 4: Read template file
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template_text = f.read()

        # Step 5: Expand variables
        try:
            expanded_text = self.expander.expand(template_text, context)
        except Jinja2TemplateError as e:
            raise Jinja2TemplateError(
                f"Failed to expand template {template_path}: {e}"
            ) from e

        # Step 6: Parse YAML
        try:
            expanded_yaml = yaml.safe_load(expanded_text)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Invalid YAML after expansion in {template_path}: {e}"
            ) from e

        if not isinstance(expanded_yaml, dict):
            raise ValueError(
                f"Template must produce a dict, got {type(expanded_yaml)}"
            )

        # Step 7: Cache result
        self.cache_manager.set(cache_key, expanded_yaml)

        # Step 8: Return result
        return expanded_yaml

    def _invalidate_cache_if_needed(self) -> None:
        """Invalidate cache if .novelerrc.yaml has been modified.

        Checks modification time (mtime) of configuration file.
        If changed since last check, clears entire cache.

        Postcondition:
            - If config unchanged: cache preserved
            - If config changed: cache cleared, mtime updated

        Design Decision:
            Clear entire cache (not individual entries) because any
            template might reference changed configuration values.
        """
        try:
            current_mtime = self.config_loader.get_config_mtime(
                self.project_root
            )

            # First time check or config changed
            if (
                self._last_config_mtime is None
                or current_mtime != self._last_config_mtime
            ):
                self.cache_manager.clear()
                self._last_config_mtime = current_mtime

        except FileNotFoundError:
            # Config doesn't exist yet - clear cache to be safe
            self.cache_manager.clear()
            self._last_config_mtime = None
