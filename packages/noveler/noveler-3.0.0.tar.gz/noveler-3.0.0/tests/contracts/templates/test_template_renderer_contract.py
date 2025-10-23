"""Contract tests for TemplateRenderer.

Tests verify that TemplateRenderer honors its public interface contract:
- render_template() returns dict
- Cache invalidation on config change
- Proper dependency injection
- Exception handling
"""

import pytest
import tempfile
from pathlib import Path
import yaml
from src.noveler.templates import TemplateRenderer
from src.noveler.templates.domain.variable_expander import Jinja2TemplateError


class TestTemplateRendererContract:
    """Contract tests for TemplateRenderer public interface."""

    def setup_method(self):
        """Setup test fixture with temp directory and config."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create .novelerrc.yaml
        self.config_data = {
            "writing_style": {
                "active_preset": "test",
                "presets": {
                    "test": {
                        "target_chars_per_episode": 5000,
                        "target_average": 40,
                        "dialogue_mode": "balanced",
                        "section_ratio": [20, 60, 20],
                    }
                },
            }
        }

        config_path = self.temp_dir / ".novelerrc.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config_data, f)

        # Create template file
        self.template_content = {
            "metadata": {"name": "test_template"},
            "settings": {
                "target_average": "{{ writing_style.target_average }}",
                "dialogue_mode": "{{ writing_style.dialogue_mode }}",
            },
        }

        self.template_path = self.temp_dir / "test_template.yaml"
        with open(self.template_path, "w", encoding="utf-8") as f:
            yaml.dump(self.template_content, f)

        self.renderer = TemplateRenderer(self.temp_dir)

    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_render_template_returns_dict(self):
        """Contract: render_template() must return dict."""
        result = self.renderer.render_template(self.template_path)

        assert isinstance(result, dict)

    def test_render_template_expands_variables(self):
        """Contract: render_template() must expand all Jinja2 variables."""
        result = self.renderer.render_template(self.template_path)

        assert result["settings"]["target_average"] == "40"
        assert result["settings"]["dialogue_mode"] == "balanced"

        # No Jinja2 syntax should remain in values
        import yaml

        result_yaml = yaml.dump(result)
        assert "{{" not in result_yaml
        assert "}}" not in result_yaml

    def test_render_template_caches_result(self):
        """Contract: render_template() should cache results for performance."""
        # First call
        result1 = self.renderer.render_template(self.template_path)

        # Check cache hit (size should be 1)
        assert self.renderer.cache_manager.size() == 1

        # Second call (cache hit)
        result2 = self.renderer.render_template(self.template_path)

        assert result1 == result2

    def test_render_template_invalidates_cache_on_config_change(self):
        """Contract: Cache must be invalidated when .novelerrc.yaml changes."""
        import time

        # First render (cached)
        self.renderer.render_template(self.template_path)
        assert self.renderer.cache_manager.size() == 1

        # Modify config
        time.sleep(0.1)
        config_path = self.temp_dir / ".novelerrc.yaml"
        self.config_data["writing_style"]["presets"]["test"][
            "target_average"
        ] = 50
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config_data, f)

        # Render again (cache should be cleared)
        result = self.renderer.render_template(self.template_path)

        # Verify new value
        assert result["settings"]["target_average"] == "50"

    def test_render_template_raises_on_nonexistent_file(self):
        """Contract: render_template() must raise FileNotFoundError if missing."""
        nonexistent = self.temp_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError) as exc_info:
            self.renderer.render_template(nonexistent)

        assert "Template not found" in str(exc_info.value)

    def test_render_template_raises_on_template_error(self):
        """Contract: render_template() must raise Jinja2TemplateError on invalid syntax."""
        # Create template with invalid Jinja2 syntax
        bad_template_path = self.temp_dir / "bad_template.yaml"
        with open(bad_template_path, "w") as f:
            f.write("value: {{ invalid syntax }}")

        with pytest.raises(Jinja2TemplateError):
            self.renderer.render_template(bad_template_path)

    def test_render_template_raises_on_invalid_yaml_after_expansion(self):
        """Contract: render_template() must raise yaml.YAMLError if expanded result invalid."""
        # Create template that expands to invalid YAML
        invalid_yaml_template = self.temp_dir / "invalid_yaml.yaml"
        with open(invalid_yaml_template, "w") as f:
            f.write("value: {{ writing_style.target_average }}\ninvalid: yaml: syntax:")

        with pytest.raises(yaml.YAMLError):
            self.renderer.render_template(invalid_yaml_template)

    def test_render_template_validates_result_is_dict(self):
        """Contract: render_template() must raise ValueError if result not dict."""
        # Create template that produces a list
        list_template_path = self.temp_dir / "list_template.yaml"
        with open(list_template_path, "w") as f:
            f.write("- item1\n- item2")

        with pytest.raises(ValueError) as exc_info:
            self.renderer.render_template(list_template_path)

        assert "must produce a dict" in str(exc_info.value)

    def test_dependency_injection_config_loader(self):
        """Contract: ConfigLoader can be injected via constructor."""
        from src.noveler.templates.infrastructure.config_loader import (
            ConfigLoader,
        )

        custom_loader = ConfigLoader()
        renderer = TemplateRenderer(
            self.temp_dir, config_loader=custom_loader
        )

        assert renderer.config_loader is custom_loader

    def test_dependency_injection_cache_manager(self):
        """Contract: CacheManager can be injected via constructor."""
        from src.noveler.templates.infrastructure.cache_manager import (
            CacheManager,
        )

        custom_cache = CacheManager(max_size=50)
        renderer = TemplateRenderer(
            self.temp_dir, cache_manager=custom_cache
        )

        assert renderer.cache_manager is custom_cache

    def test_dependency_injection_expander(self):
        """Contract: VariableExpander can be injected via constructor."""
        from src.noveler.templates.domain.variable_expander import (
            VariableExpander,
        )

        custom_expander = VariableExpander()
        renderer = TemplateRenderer(
            self.temp_dir, expander=custom_expander
        )

        assert renderer.expander is custom_expander

    def test_supports_relative_template_paths(self):
        """Contract: render_template() should accept relative paths."""
        # Create template in subdirectory
        subdir = self.temp_dir / "templates"
        subdir.mkdir()

        template_in_subdir = subdir / "sub_template.yaml"
        with open(template_in_subdir, "w") as f:
            yaml.dump({"value": "{{ writing_style.target_average }}"}, f)

        # Render with relative path
        result = self.renderer.render_template(
            Path("templates/sub_template.yaml")
        )

        assert result["value"] == "40"


class TestTemplateRendererSpecCompliance:
    """Verify TemplateRenderer complies with design specifications."""

    def test_has_required_methods(self):
        """Spec: TemplateRenderer must have __init__() and render_template()."""
        temp_dir = Path(tempfile.mkdtemp())
        renderer = TemplateRenderer(temp_dir)

        assert hasattr(renderer, "render_template")
        assert callable(renderer.render_template)

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_render_template_signature(self):
        """Spec: render_template(template_path: Path) -> Dict[str, Any]"""
        import inspect

        sig = inspect.signature(TemplateRenderer.render_template)
        params = list(sig.parameters.keys())

        assert params == ["self", "template_path"]

    def test_init_signature(self):
        """Spec: __init__(project_root, config_loader, cache_manager, expander)"""
        import inspect

        sig = inspect.signature(TemplateRenderer.__init__)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "project_root" in params
        assert "config_loader" in params
        assert "cache_manager" in params
        assert "expander" in params

    def test_depends_on_domain_and_infrastructure(self):
        """Spec: Application layer depends on Domain and Infrastructure."""
        temp_dir = Path(tempfile.mkdtemp())
        renderer = TemplateRenderer(temp_dir)

        # Verify dependencies
        from src.noveler.templates.domain.variable_expander import (
            VariableExpander,
        )
        from src.noveler.templates.infrastructure.config_loader import (
            ConfigLoader,
        )
        from src.noveler.templates.infrastructure.cache_manager import (
            CacheManager,
        )

        assert isinstance(renderer.expander, VariableExpander)
        assert isinstance(renderer.config_loader, ConfigLoader)
        assert isinstance(renderer.cache_manager, CacheManager)

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)
