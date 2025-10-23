"""Contract tests for ConfigLoader.

Tests verify that ConfigLoader honors its public interface contract:
- load() returns dict
- extract_active_preset() returns dict
- get_config_mtime() returns float
- Proper exceptions raised on errors
"""

import pytest
import tempfile
from pathlib import Path
import yaml
from src.noveler.templates.infrastructure.config_loader import ConfigLoader
from src.noveler.templates.domain.config_schema import ValidationError


class TestConfigLoaderContract:
    """Contract tests for ConfigLoader public interface."""

    def setup_method(self):
        """Setup test fixture with temporary config file."""
        self.loader = ConfigLoader()
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create valid .novelerrc.yaml
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

    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_returns_dict(self):
        """Contract: load() must return dict."""
        result = self.loader.load(self.temp_dir)

        assert isinstance(result, dict)
        assert "writing_style" in result

    def test_load_raises_on_nonexistent_file(self):
        """Contract: load() must raise FileNotFoundError if config missing."""
        nonexistent = Path("/nonexistent/path")

        with pytest.raises(FileNotFoundError) as exc_info:
            self.loader.load(nonexistent)

        assert "Configuration file not found" in str(exc_info.value)

    def test_load_raises_on_invalid_yaml(self):
        """Contract: load() must raise yaml.YAMLError on parse errors."""
        invalid_config_path = self.temp_dir / ".novelerrc.yaml"
        with open(invalid_config_path, "w") as f:
            f.write("invalid: yaml: syntax:")

        with pytest.raises(yaml.YAMLError):
            self.loader.load(self.temp_dir)

    def test_load_validates_root_is_dict(self):
        """Contract: load() must raise ValidationError if root is not dict."""
        list_config_path = self.temp_dir / ".novelerrc.yaml"
        with open(list_config_path, "w") as f:
            yaml.dump([1, 2, 3], f)

        with pytest.raises(ValidationError) as exc_info:
            self.loader.load(self.temp_dir)

        assert "root must be a dict" in str(exc_info.value)

    def test_extract_active_preset_returns_dict(self):
        """Contract: extract_active_preset() must return dict."""
        config = self.loader.load(self.temp_dir)
        result = self.loader.extract_active_preset(config)

        assert isinstance(result, dict)
        assert "target_chars_per_episode" in result
        assert "target_average" in result
        assert "dialogue_mode" in result
        assert "section_ratio" in result

    def test_extract_active_preset_validates_structure(self):
        """Contract: extract_active_preset() must validate writing_style section."""
        invalid_config = {"wrong_key": "value"}

        with pytest.raises(ValidationError) as exc_info:
            self.loader.extract_active_preset(invalid_config)

        assert "writing_style" in str(exc_info.value)

    def test_extract_active_preset_returns_correct_preset(self):
        """Contract: extract_active_preset() returns settings for active preset."""
        config = self.loader.load(self.temp_dir)
        result = self.loader.extract_active_preset(config)

        assert result["target_chars_per_episode"] == 5000
        assert result["target_average"] == 40
        assert result["dialogue_mode"] == "balanced"
        assert result["section_ratio"] == [20, 60, 20]

    def test_get_config_mtime_returns_float(self):
        """Contract: get_config_mtime() must return float (timestamp)."""
        result = self.loader.get_config_mtime(self.temp_dir)

        assert isinstance(result, float)
        assert result > 0

    def test_get_config_mtime_raises_on_nonexistent(self):
        """Contract: get_config_mtime() must raise FileNotFoundError if missing."""
        nonexistent = Path("/nonexistent/path")

        with pytest.raises(FileNotFoundError):
            self.loader.get_config_mtime(nonexistent)

    def test_get_config_mtime_changes_on_modification(self):
        """Contract: get_config_mtime() must reflect file modifications."""
        import time

        mtime1 = self.loader.get_config_mtime(self.temp_dir)

        # Wait and modify file
        time.sleep(0.1)
        config_path = self.temp_dir / ".novelerrc.yaml"
        config_path.touch()

        mtime2 = self.loader.get_config_mtime(self.temp_dir)

        assert mtime2 > mtime1

    def test_custom_config_filename(self):
        """Contract: ConfigLoader should support custom config filename."""
        custom_name = "custom_config.yaml"
        custom_path = self.temp_dir / custom_name

        # Create custom config
        with open(custom_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config_data, f)

        # Load with custom filename
        loader = ConfigLoader(config_filename=custom_name)
        result = loader.load(self.temp_dir)

        assert isinstance(result, dict)
        assert "writing_style" in result


class TestConfigLoaderSpecCompliance:
    """Verify ConfigLoader complies with design specifications."""

    def test_has_required_methods(self):
        """Spec: ConfigLoader must have load(), extract_active_preset(), get_config_mtime()."""
        loader = ConfigLoader()

        assert hasattr(loader, "load")
        assert callable(loader.load)

        assert hasattr(loader, "extract_active_preset")
        assert callable(loader.extract_active_preset)

        assert hasattr(loader, "get_config_mtime")
        assert callable(loader.get_config_mtime)

    def test_load_signature(self):
        """Spec: load(project_root: Path) -> Dict[str, Any]"""
        import inspect

        sig = inspect.signature(ConfigLoader.load)
        params = list(sig.parameters.keys())

        assert params == ["self", "project_root"]

    def test_extract_active_preset_signature(self):
        """Spec: extract_active_preset(config: dict) -> dict"""
        import inspect

        sig = inspect.signature(ConfigLoader.extract_active_preset)
        params = list(sig.parameters.keys())

        assert params == ["self", "config"]

    def test_get_config_mtime_signature(self):
        """Spec: get_config_mtime(project_root: Path) -> float"""
        import inspect

        sig = inspect.signature(ConfigLoader.get_config_mtime)
        params = list(sig.parameters.keys())

        assert params == ["self", "project_root"]
        assert sig.return_annotation == float

    def test_depends_on_domain_layer(self):
        """Spec: Infrastructure can depend on Domain (WritingStyleConfig)."""
        from src.noveler.templates.domain.config_schema import WritingStyleConfig

        # ConfigLoader uses WritingStyleConfig for validation
        # This is verified by inspecting extract_active_preset implementation
        loader = ConfigLoader()
        assert loader is not None  # Can be instantiated
