"""Infrastructure.utils.codemap_loader
Where: Infrastructure utility for loading codemap data.
What: Reads codemap configuration and content from storage for downstream services.
Why: Centralises codemap loading logic to avoid duplication.
"""

from noveler.presentation.shared.shared_utilities import console

"CODEMAP遅延読み込みユーティリティ\n\n大規模なCODEMAP_dependencies.yamlファイルの\n効率的な部分読み込みを提供。\n\n設計原則:\n    - ストリーミング読み込み\n    - 必要な部分のみをメモリに展開\n    - YAMLの構造を活用した選択的パース\n"
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.logging.unified_logger import get_logger


class StreamingYAMLReader:
    """ストリーミングYAML読み込みクラス

    大規模YAMLファイルを効率的に読み込むための
    ストリーミングリーダー。
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.logger = get_logger(__name__)
        self._file = None
        self._current_line = 0

    def __enter__(self) -> Any:
        self._file = self.file_path.open(encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._file:
            self._file.close()

    def read_section(self, section_name: str) -> dict[str, Any] | None:
        """特定セクションのみを読み込む

        Args:
            section_name: 読み込むセクション名

        Returns:
            セクションのデータ、見つからない場合はNone
        """
        self._file.seek(0)
        self._current_line = 0
        section_start = self._find_section_start(section_name)
        if section_start is None:
            return None
        section_lines = self._read_until_next_section(section_start)
        section_yaml = "\n".join(section_lines)
        try:
            return yaml.safe_load(section_yaml)
        except yaml.YAMLError:
            self.logger.exception("Failed to parse section %s", section_name)
            return None

    def iterate_modules(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """モジュールを1つずつイテレート

        Yields:
            (モジュール名, モジュールデータ)のタプル
        """
        self._file.seek(0)
        in_core_dependencies = False
        current_module = None
        module_lines = []
        indent_level = 0
        for line in self._file:
            if "core_dependencies:" in line:
                in_core_dependencies = True
                continue
            if not in_core_dependencies:
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent == 4 and line.strip() and (not line.strip().startswith("-")):
                if current_module and module_lines:
                    module_yaml = f"{current_module}:\n" + "\n".join(module_lines)
                    try:
                        module_data: dict[str, Any] = yaml.safe_load(module_yaml)
                        yield (current_module, module_data[current_module])
                    except yaml.YAMLError as e:
                        console.print(f"YAMLパースエラー: {current_module}, エラー: {e}")
                current_module = line.strip().rstrip(":")
                module_lines = []
                indent_level = 4
            elif current_module and current_indent > indent_level:
                module_lines.append(line.rstrip())
            elif in_core_dependencies and current_indent == 2:
                if current_module and module_lines:
                    module_yaml = f"{current_module}:\n" + "\n".join(module_lines)
                    try:
                        module_data: dict[str, Any] = yaml.safe_load(module_yaml)
                        yield (current_module, module_data[current_module])
                    except yaml.YAMLError as e:
                        console.print(f"最終モジュールYAMLパースエラー: {current_module}, エラー: {e}")
                break

    def search_modules(self, pattern: str) -> list[str]:
        """パターンに一致するモジュールを検索

        Args:
            pattern: 検索パターン（正規表現）

        Returns:
            一致するモジュール名のリスト
        """
        regex = re.compile(pattern)
        matching_modules = []
        for module_name, _ in self.iterate_modules():
            if regex.search(module_name):
                matching_modules.append(module_name)
        return matching_modules

    def _find_section_start(self, section_name: str) -> int | None:
        """セクションの開始行を検索"""
        pattern = f"^\\s*{section_name}:"
        regex = re.compile(pattern)
        for i, line in enumerate(self._file):
            if regex.match(line):
                return i
        return None

    def _read_until_next_section(self, start_line: int) -> list[str]:
        """次のセクションまでの行を読み込む"""
        self._file.seek(0)
        lines = []
        current_line = 0
        in_section = False
        base_indent = None
        for line in self._file:
            if current_line < start_line:
                current_line += 1
                continue
            if current_line == start_line:
                in_section = True
                base_indent = len(line) - len(line.lstrip())
                lines.append(line.rstrip())
                current_line += 1
                continue
            if in_section:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= base_indent:
                    break
                lines.append(line.rstrip())
            current_line += 1
        return lines


class LazyCodeMapLoader:
    """遅延読み込みCODEMAPローダー

    必要な部分のみを読み込む遅延評価型ローダー。
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self._cache = {}
        self._file_path = project_root / "CODEMAP_dependencies.yaml"

    def get_module(self, module_name: str) -> dict[str, Any] | None:
        """特定モジュールの情報を取得

        Args:
            module_name: モジュール名

        Returns:
            モジュール情報、見つからない場合はNone
        """
        if module_name in self._cache:
            return self._cache[module_name]
        with StreamingYAMLReader(self._file_path) as reader:
            for mod_name, mod_data in reader.iterate_modules():
                if mod_name == module_name:
                    self._cache[module_name] = mod_data
                    return mod_data
        return None

    def get_layer_violations(self) -> list[dict[str, str]]:
        """レイヤー違反のみを取得"""
        with StreamingYAMLReader(self._file_path) as reader:
            violations_data: dict[str, Any] = reader.read_section("dependency_issues")
            if violations_data:
                return violations_data.get("layer_violations", [])
        return []

    def get_statistics(self) -> dict[str, Any]:
        """統計情報のみを取得"""
        with StreamingYAMLReader(self._file_path) as reader:
            stats_data: dict[str, Any] = reader.read_section("dependency_statistics")
            if stats_data:
                return stats_data
        return {}

    def find_importing_modules(self, target_module: str) -> list[str]:
        """特定モジュールをインポートしているモジュールを検索

        Args:
            target_module: 対象モジュール名

        Returns:
            インポートしているモジュール名のリスト
        """
        importing_modules = []
        with StreamingYAMLReader(self._file_path) as reader:
            for module_name, module_data in reader.iterate_modules():
                imports = module_data.get("imports", [])
                if target_module in imports:
                    importing_modules.append(module_name)
        return importing_modules

    def find_modules_by_layer(self, layer: str) -> list[str]:
        """特定レイヤーのモジュールを検索

        Args:
            layer: レイヤー名 ('domain', 'application', 'infrastructure', 'presentation')

        Returns:
            モジュール名のリスト
        """
        pattern = f"scripts\\.{layer}\\."
        with StreamingYAMLReader(self._file_path) as reader:
            return reader.search_modules(pattern)

    def calculate_coupling_score(self, module_name: str) -> float:
        """モジュールの結合度スコアを計算

        Args:
            module_name: モジュール名

        Returns:
            結合度スコア（0.0-1.0）
        """
        module_data: dict[str, Any] = self.get_module(module_name)
        if not module_data:
            return 0.0
        imports = module_data.get("imports", [])
        imported_by = module_data.get("imported_by", [])
        total_modules = 548
        coupling_score = (len(imports) + len(imported_by)) / total_modules
        return min(coupling_score, 1.0)


class CodeMapSplitter:
    """CODEMAPを分割ファイルに変換するユーティリティ"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self.source_file = project_root / "CODEMAP_dependencies.yaml"

    def split_files(self) -> dict[str, Path]:
        """CODEMAPを複数ファイルに分割

        Returns:
            生成されたファイルのパス辞書
        """
        with self.source_file.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        dependency_map = data.get("dependency_map", {})
        files = {
            "core": self.project_root / "CODEMAP_dependencies_core.yaml",
            "violations": self.project_root / "CODEMAP_dependencies_violations.yaml",
            "stats": self.project_root / "CODEMAP_dependencies_stats.yaml",
        }
        core_data: dict[str, Any] = {
            "dependency_map": {
                "version": dependency_map.get("version"),
                "generated_at": dependency_map.get("generated_at"),
                "generation_tool": dependency_map.get("generation_tool"),
                "core_dependencies": dependency_map.get("core_dependencies", {}),
            }
        }
        violations_data: dict[str, Any] = {
            "dependency_map": {
                "version": dependency_map.get("version"),
                "generated_at": dependency_map.get("generated_at"),
                "dependency_issues": dependency_map.get("dependency_issues", {}),
            }
        }
        stats_data: dict[str, Any] = {
            "dependency_map": {
                "version": dependency_map.get("version"),
                "generated_at": dependency_map.get("generated_at"),
                "dependency_statistics": dependency_map.get("dependency_statistics", {}),
            },
            "quality_metrics": data.get("quality_metrics", {}),
            "automation_config": data.get("automation_config", {}),
        }
        for key, file_path in files.items():
            if key == "core":
                self._write_yaml(file_path, core_data)
            elif key == "violations":
                self._write_yaml(file_path, violations_data)
            elif key == "stats":
                self._write_yaml(file_path, stats_data)
            console.print(f"Created {file_path.name}")
        return files

    def _write_yaml(self, file_path: Path, data: dict[str, Any]) -> None:
        """YAMLファイルを書き込む"""
        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_lazy_loader() -> LazyCodeMapLoader:
    """遅延読み込みローダーのインスタンスを取得"""
    try:
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service()
        project_root = path_service.get_project_root()
    except ImportError:
        project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))
    return LazyCodeMapLoader(project_root)
