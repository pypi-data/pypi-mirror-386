"""Tools.e2e_test_generator
Where: Tool generating end-to-end tests from scenario descriptions.
What: Converts scenario inputs into runnable E2E test suites.
Why: Helps maintain comprehensive E2E coverage with minimal manual coding.
"""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from noveler.presentation.shared.shared_utilities import console

"E2Eテスト生成スクリプト\n\n仕様書からE2Eテストスケルトンを自動生成する。\n仕様ID = E2EテストIDの1対1対応を保証。\n"

from noveler.domain.value_objects.project_time import project_now


@dataclass
class TestSpec:
    """テスト仕様情報"""

    spec_id: str
    spec_name: str
    test_type: str
    test_id: str
    category: str
    description: str
    use_cases: list[dict] = None


class E2ETestGenerator:
    """E2Eテスト生成クラス"""

    def __init__(self, specs_dir: Path, tests_dir: Path) -> None:
        """初期化

        Args:
            specs_dir: 仕様書ディレクトリ
            tests_dir: テストディレクトリ
        """
        self.specs_dir = specs_dir
        self.tests_dir = tests_dir
        self.mapping_file = specs_dir / "E2E_TEST_MAPPING.yaml"
        self._load_mapping()

    def _load_mapping(self) -> None:
        """マッピング情報を読み込み"""
        if self.mapping_file.exists():
            with self.mapping_file.open(encoding="utf-8") as f:
                self.mapping = yaml.safe_load(f)
        else:
            self.mapping = {"e2e_mappings": {}, "supplementary_mappings": {}, "integration_mappings": {}}

    def parse_spec(self, spec_file: Path) -> TestSpec | None:
        """仕様書を解析してテスト仕様を抽出

        Args:
            spec_file: 仕様書ファイルパス

        Returns:
            テスト仕様情報
        """
        content = spec_file.read_text(encoding="utf-8")
        metadata_match = re.search("\\| 仕様ID \\| (SPEC-[A-Z]+-\\d+)", content)
        if not metadata_match:
            return None
        spec_id = metadata_match.group(1)
        id_match = re.match("SPEC-([A-Z]+)-(\\d+)", spec_id)
        if not id_match:
            return None
        category = id_match.group(1)
        number = id_match.group(2)
        test_type_match = re.search("\\| test_type \\| (e2e|integration|unit)", content)
        test_type = test_type_match.group(1) if test_type_match else "unit"
        title_match = re.search("^# SPEC-[A-Z]+-\\d+: (.+)$", content, re.MULTILINE)
        spec_name = title_match.group(1) if title_match else spec_file.stem
        use_cases = self._extract_use_cases(content)
        if test_type == "e2e":
            test_id = f"E2E-{category}-{number}"
        elif test_type == "integration":
            test_id = f"INT-{category}-{number}"
        else:
            test_id = f"UNIT-{category}-{number}"
        return TestSpec(
            spec_id=spec_id,
            spec_name=spec_name,
            test_type=test_type,
            test_id=test_id,
            category=category,
            description=f"{spec_name}のテスト",
            use_cases=use_cases,
        )

    def _extract_use_cases(self, content: str) -> list[dict]:
        """仕様書からユースケースを抽出

        Args:
            content: 仕様書内容

        Returns:
            ユースケースリスト
        """
        use_cases = []
        uc_pattern = "#### UC-(\\d+): (.+)\\n```yaml\\n(.*?)\\n```"
        matches = re.findall(uc_pattern, content, re.DOTALL)
        for match in matches:
            uc_id = match[0]
            uc_name = match[1]
            uc_yaml = match[2]
            try:
                uc_data = yaml.safe_load(uc_yaml)
                use_cases.append({"id": f"UC-{uc_id}", "name": uc_name, "data": uc_data})
            except:
                pass
        return use_cases

    def generate_e2e_test(self, test_spec: TestSpec) -> str:
        """E2Eテストコードを生成

        Args:
            test_spec: テスト仕様

        Returns:
            生成されたテストコード
        """
        test_code = f'''#!/usr/bin/env python3\n"""\n{test_spec.spec_name}のE2Eテスト\n\n仕様書: specs/{test_spec.spec_id}_{test_spec.spec_name}.md\nテストID: {test_spec.test_id}\n生成日: {project_now().datetime.strftime("%Y-%m-%d")}\n"""\n\nimport pytest\nfrom pathlib import Path\nfrom typing import Any, Dict\n\n# Import moved to top-level\nfrom noveler.infrastructure.di.container import get_container\n\n@pytest.mark.spec(\'{test_spec.spec_id}')\n@pytest.mark.e2e\n@pytest.mark.category(\'{test_spec.category.lower()}')\nclass Test{test_spec.category.title()}{test_spec.spec_id.split("-")[-1]}:\n    """{test_spec.description}"""\n\n    @pytest.fixture(autouse=True)\n    def setup(self, tmp_path: Path):\n        """テストセットアップ"""\n        self.project_root = tmp_path / "test_project"\n        self.project_root.mkdir(parents=True)\n        self.container = get_container(project_root=self.project_root)\n'''
        if test_spec.use_cases:
            for uc in test_spec.use_cases:
                test_code += self._generate_test_method(uc, test_spec)
        else:
            test_code += self._generate_default_test_method(test_spec)
        return test_code

    def _generate_test_method(self, use_case: dict, test_spec: TestSpec) -> str:
        """ユースケースからテストメソッドを生成

        Args:
            use_case: ユースケース情報
            test_spec: テスト仕様

        Returns:
            テストメソッドのコード
        """
        uc_id = use_case["id"].replace("-", "_").lower()
        uc_name = use_case["name"]
        uc_data = use_case.get("data", {})
        return f'''\n    def test_{uc_id}_{self._sanitize_name(uc_name)}(self):\n        """\n        {uc_name}のテスト\n\n        Given: {uc_data.get("前提条件", "システムが初期状態")}\n        When: {uc_data.get("アクター", "ユーザー")}が{uc_data.get("入力", "アクション")}を実行\n        Then: {uc_data.get("期待出力", "正常に処理される")}\n        """\n        # Arrange - 前提条件のセットアップ\n        # TODO: 前提条件の実装\n\n        # Act - アクション実行\n        # TODO: ユースケース実行の実装\n        result = None  # 仮の結果\n\n        # Assert - 期待結果の検証\n        assert result is not None, "結果が取得できません"\n        # TODO: 期待結果の検証実装\n'''

    def _generate_default_test_method(self, test_spec: TestSpec) -> str:
        """デフォルトのテストメソッドを生成

        Args:
            test_spec: テスト仕様

        Returns:
            テストメソッドのコード
        """
        return f'''\n    def test_{test_spec.spec_name.lower().replace(" ", "_")}(self):\n        """{test_spec.description}の基本テスト"""\n        # TODO: テストの実装\n        assert True, "テスト未実装"\n'''

    def _sanitize_name(self, name: str) -> str:
        """名前をPython識別子として有効な形式に変換

        Args:
            name: 元の名前

        Returns:
            サニタイズされた名前
        """
        sanitized = re.sub("[^a-zA-Z0-9_]", "_", name)
        sanitized = re.sub("_+", "_", sanitized)
        return sanitized.lower().strip("_")

    def generate_integration_test(self, test_spec: TestSpec) -> str:
        """統合テストコードを生成

        Args:
            test_spec: テスト仕様

        Returns:
            生成されたテストコード
        """
        return f'''#!/usr/bin/env python3\n"""\n{test_spec.spec_name}の統合テスト\n\n仕様書: specs/{test_spec.spec_id}_{test_spec.spec_name}.md\nテストID: {test_spec.test_id}\n生成日: {project_now().datetime.strftime("%Y-%m-%d")}\n"""\n\nimport pytest\nfrom unittest.mock import Mock, MagicMock\nfrom pathlib import Path\n\n# Import moved to top-level\n@pytest.mark.spec(\'{test_spec.spec_id}')\n@pytest.mark.integration\nclass TestIntegration{test_spec.category.title()}{test_spec.spec_id.split("-")[-1]}:\n    """{test_spec.description}の統合テスト"""\n\n    def test_repository_integration(self, tmp_path: Path):\n        """リポジトリ統合テスト"""\n        # TODO: リポジトリ統合テストの実装\n        assert True, "テスト未実装"\n\n    def test_service_integration(self):\n        """サービス統合テスト"""\n        # TODO: サービス統合テストの実装\n        assert True, "テスト未実装"\n'''

    def generate_unit_test(self, test_spec: TestSpec) -> str:
        """単体テストコードを生成

        Args:
            test_spec: テスト仕様

        Returns:
            生成されたテストコード
        """
        return f'''#!/usr/bin/env python3\n"""\n{test_spec.spec_name}の単体テスト\n\n仕様書: specs/{test_spec.spec_id}_{test_spec.spec_name}.md\nテストID: {test_spec.test_id}\n生成日: {project_now().datetime.strftime("%Y-%m-%d")}\n"""\n\nimport pytest\nfrom unittest.mock import Mock, patch\n\n@pytest.mark.spec(\'{test_spec.spec_id}')\n@pytest.mark.unit\nclass TestUnit{test_spec.category.title()}{test_spec.spec_id.split("-")[-1]}:\n    """{test_spec.description}の単体テスト"""\n\n    def test_initialization(self):\n        """初期化テスト"""\n        # TODO: 初期化テストの実装\n        assert True, "テスト未実装"\n\n    def test_validation(self):\n        """バリデーションテスト"""\n        # TODO: バリデーションテストの実装\n        assert True, "テスト未実装"\n\n    def test_edge_cases(self):\n        """エッジケーステスト"""\n        # TODO: エッジケーステストの実装\n        assert True, "テスト未実装"\n'''

    def generate_tests_from_spec(self, spec_file: Path) -> dict[str, str]:
        """仕様書からテストを生成

        Args:
            spec_file: 仕様書ファイル

        Returns:
            生成されたテストコード（test_type別）
        """
        test_spec = self.parse_spec(spec_file)
        if not test_spec:
            return {}
        generated = {}
        if test_spec.test_type == "e2e":
            generated["e2e"] = self.generate_e2e_test(test_spec)
        elif test_spec.test_type == "integration":
            generated["integration"] = self.generate_integration_test(test_spec)
        else:
            generated["unit"] = self.generate_unit_test(test_spec)
        self._update_mapping(test_spec)
        return generated

    def _update_mapping(self, test_spec: TestSpec) -> None:
        """マッピング情報を更新

        Args:
            test_spec: テスト仕様
        """
        mapping_key = f"{test_spec.test_type}_mappings"
        if mapping_key not in self.mapping:
            self.mapping[mapping_key] = {}
        self.mapping[mapping_key][test_spec.spec_id] = {
            "spec_name": test_spec.spec_name,
            "test_type": test_spec.test_type,
            "test_id": test_spec.test_id,
            "test_path": f"tests/{test_spec.test_type}/test_{test_spec.category.lower()}_{test_spec.spec_id.split('-')[-1]}.py",
            "description": test_spec.description,
        }
        with self.mapping_file.open("w", encoding="utf-8") as f:
            yaml.dump(self.mapping, f, allow_unicode=True, default_flow_style=False)


def main():
    """メイン処理"""

    parser = argparse.ArgumentParser(description="E2Eテスト生成スクリプト")
    parser.add_argument("spec_file", type=Path, help="テスト生成対象の仕様書ファイル")
    parser.add_argument("--specs-dir", type=Path, default=Path("specs"), help="仕様書ディレクトリ")
    parser.add_argument("--tests-dir", type=Path, default=Path("tests"), help="テストディレクトリ")
    parser.add_argument("--output", type=Path, help="出力先ファイル（指定しない場合は標準出力）")
    args = parser.parse_args()
    generator = E2ETestGenerator(args.specs_dir, args.tests_dir)
    generated = generator.generate_tests_from_spec(args.spec_file)
    if not generated:
        console.print(f"エラー: {args.spec_file} から仕様情報を抽出できませんでした")
        return
    for test_type, code in generated.items():
        if args.output:
            output_file = args.output.parent / f"{args.output.stem}_{test_type}{args.output.suffix}"
            output_file.write_text(code, encoding="utf-8")
            console.print(f"{test_type}テストを生成しました: {output_file}")
        else:
            console.print(f"\n=== {test_type.upper()} TEST ===")
            console.print(code)


if __name__ == "__main__":
    main()
