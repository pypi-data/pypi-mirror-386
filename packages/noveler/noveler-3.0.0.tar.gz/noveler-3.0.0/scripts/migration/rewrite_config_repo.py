from pathlib import Path

path = Path("src/noveler/infrastructure/repositories/configuration_repository.py")
text = path.read_text(encoding="utf-8")
class_marker = text.index("class ConfigurationRepository")
method_marker = text.index("    def get_project_paths", class_marker)
# find end of method
method_end = text.find("\n    def ", method_marker + 1)
if method_end == -1:
    method_end = len(text)
old_method = text[method_marker:method_end]
new_method = '''    @staticmethod\n    def _as_posix(path_value: str | Path) -> str:\n        """Normalize filesystem paths to POSIX-style strings."""\n        return str(Path(path_value)).replace('\\\\', '/').replace('\\', '/')\n\n    def get_project_paths(self) -> dict[str, str]:\n        """プロジェクトの主要パス情報をPOSIX形式で返す。"""\n        def _normalize(result: dict[str, str]) -> dict[str, str]:\n            return {key: self._as_posix(value) for key, value in result.items()}\n\n        paths: dict[str, str] = {}\n\n        env_project_root = os.environ.get("PROJECT_ROOT")\n        if env_project_root:\n            project_root = Path(env_project_root)\n            guide_override = os.environ.get("GUIDE_ROOT")\n            guide_root = Path(guide_override) if guide_override else project_root.parent / "00_ガイド"\n            paths["project_root"] = str(project_root)\n            paths["guide_root"] = str(guide_root)\n            return _normalize(paths)\n\n        config = self.load_project_config()\n        path_settings = config.get("paths", {})\n        project_root_config = path_settings.get("project_root")\n        if project_root_config:\n            project_root = Path(project_root_config)\n            guide_root_config = path_settings.get("guide_root")\n            guide_root = Path(guide_root_config) if guide_root_config else project_root.parent / "00_ガイド"\n            paths["project_root"] = str(project_root)\n            paths["guide_root"] = str(guide_root)\n            return _normalize(paths)\n\n        config_path = self.find_project_config()\n        if config_path:\n            project_root = config_path.parent\n            paths["project_root"] = str(project_root)\n            paths["guide_root"] = str(project_root.parent / "00_ガイド")\n            return _normalize(paths)\n\n        return paths\n'''
text = text[:method_marker] + new_method + text[method_end:]
path.write_text(text, encoding="utf-8")
