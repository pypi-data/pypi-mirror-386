"""YAML形式の仕様書リポジトリ実装"""

from datetime import datetime
from pathlib import Path

import yaml

from noveler.domain.specification.entities import (
    RequirementId,
    Specification,
    SpecificationId,
    SpecificationTest,
    SpecificationTestReference,
)
from noveler.domain.specification.repositories import SpecificationRepository, SpecificationTestRepository
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class YamlSpecificationRepository(SpecificationRepository):
    """YAML形式の仕様書リポジトリ実装"""

    def __init__(self, spec_dir: Path) -> None:
        self.spec_dir = spec_dir
        self.spec_dir.mkdir(parents=True, exist_ok=True)

    def find_by_id(self, spec_id: SpecificationId) -> Specification | None:
        """IDで仕様書を検索"""
        file_path = self.spec_dir / f"{spec_id.value}.yaml"
        if not file_path.exists():
            return None

        with Path(file_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return self._yaml_to_specification(data)

    def find_all(self) -> list[Specification]:
        """すべての仕様書を取得"""
        specifications = []

        for file_path in self.spec_dir.glob("SPEC-*.yaml"):
            with Path(file_path).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            spec = self._yaml_to_specification(data)
            if spec:
                specifications.append(spec)

        return specifications

    def find_by_test_file(self, test_file_path: str) -> list[Specification]:
        """テストファイルに関連する仕様書を検索"""
        specifications = []

        for spec in self.find_all():
            for test_ref in spec.test_references:
                if test_ref.file_path == test_file_path:
                    specifications.append(spec)
                    break

        return specifications

    def save(self, specification: Specification) -> None:
        """仕様書を保存"""
        file_path = self.spec_dir / f"{specification.id.value}.yaml"
        data = self._specification_to_yaml(specification)

        with Path(file_path).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def save_all(self, specifications: list[Specification]) -> None:
        """複数の仕様書を保存"""
        for spec in specifications:
            self.save(spec)

    def delete(self, spec_id: SpecificationId) -> None:
        """仕様書を削除"""
        file_path = self.spec_dir / f"{spec_id.value}.yaml"
        if file_path.exists():
            file_path.unlink()

    def _yaml_to_specification(self, data: dict[str, str | list | None]) -> Specification | None:
        """YAMLデータを仕様書エンティティに変換"""
        if not data:
            return None

        spec = Specification(
            id=SpecificationId(data["id"]),
            title=data["title"],
            description=data["description"],
            created_at=datetime.fromisoformat(data.get("created_at", project_now().datetime.isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", project_now().datetime.isoformat())),
        )

        # テスト参照を追加
        for test_ref_data in data.get("test_references", []):
            test_ref = SpecificationTestReference(
                file_path=test_ref_data["file_path"],
                function_name=test_ref_data["function_name"],
                line_number=test_ref_data.get("line_number"),
            )

            spec.test_references.append(test_ref)

        # 要件IDを追加
        for req_id in data.get("requirement_ids", []):
            spec.requirement_ids.append(RequirementId(req_id))

        # 実装参照を追加
        spec.implementation_references = data.get("implementation_references", [])

        return spec

    def _specification_to_yaml(self, specification: Specification) -> dict[str, str | list | int]:
        """仕様書エンティティをYAMLデータに変換"""
        return {
            "id": specification.id.value,
            "title": specification.title,
            "description": specification.description,
            "test_references": [
                {"file_path": ref.file_path, "function_name": ref.function_name, "line_number": ref.line_number}
                for ref in specification.test_references
            ],
            "requirement_ids": [req.value for req in specification.requirement_ids],
            "implementation_references": specification.implementation_references,
            "created_at": specification.created_at.isoformat(),
            "updated_at": specification.updated_at.isoformat(),
        }


class YamlSpecificationTestRepository(SpecificationTestRepository):
    """YAML形式のテスト仕様リポジトリ実装"""

    def __init__(self, test_spec_dir: Path) -> None:
        self.test_spec_dir = test_spec_dir
        self.test_spec_dir.mkdir(parents=True, exist_ok=True)

    def find_by_test_reference(self, test_file_path: str, function_name: str) -> SpecificationTest | None:
        """テスト参照でテスト仕様を検索"""
        file_name = self._create_file_name(test_file_path, function_name)
        file_path = self.test_spec_dir / file_name

        if not file_path.exists():
            return None

        with Path(file_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return self._yaml_to_test_specification(data)

    def find_all(self) -> list[SpecificationTest]:
        """すべてのテスト仕様を取得"""
        test_specifications = []

        for file_path in self.test_spec_dir.glob("*.yaml"):
            with Path(file_path).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            test_spec = self._yaml_to_test_specification(data)
            if test_spec:
                test_specifications.append(test_spec)

        return test_specifications

    def find_by_specification_id(self, spec_id: SpecificationId) -> list[SpecificationTest]:
        """仕様IDに関連するテスト仕様を検索"""
        test_specifications = []

        for test_spec in self.find_all():
            for sid in test_spec.specification_ids:
                if sid.value == spec_id.value:
                    test_specifications.append(test_spec)
                    break

        return test_specifications

    def find_orphaned_tests(self) -> list[SpecificationTest]:
        """仕様に紐付いていないテストを検索"""
        orphaned = []

        for test_spec in self.find_all():
            if not test_spec.has_specifications():
                orphaned.append(test_spec)

        return orphaned

    def save(self, test_specification: SpecificationTest) -> None:
        """テスト仕様を保存"""
        file_name = self._create_file_name(test_specification.test_file_path, test_specification.test_function_name)
        file_path = self.test_spec_dir / file_name

        data = self._test_specification_to_yaml(test_specification)

        with Path(file_path).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def save_all(self, test_specifications: list[SpecificationTest]) -> None:
        """複数のテスト仕様を保存"""
        for test_spec in test_specifications:
            self.save(test_spec)

    def delete_by_test_reference(self, test_file_path: str, function_name: str) -> None:
        """テスト参照でテスト仕様を削除"""
        file_name = self._create_file_name(test_file_path, function_name)
        file_path = self.test_spec_dir / file_name

        if file_path.exists():
            file_path.unlink()

    def _create_file_name(self, test_file_path: str, function_name: str) -> str:
        """テスト参照からファイル名を生成"""
        # パスを正規化
        path_parts = test_file_path.replace("/", "_").replace("\\", "_")
        return f"{path_parts}__{function_name}.yaml"

    def _yaml_to_test_specification(self, data: dict[str, str | list | None]) -> SpecificationTest | None:
        """YAMLデータをテスト仕様エンティティに変換"""
        if not data:
            return None

        test_spec = SpecificationTest(
            test_file_path=data["test_file_path"],
            test_function_name=data["test_function_name"],
            description=data.get("description"),
        )

        # 仕様IDを追加
        for spec_id in data.get("specification_ids", []):
            test_spec.specification_ids.append(SpecificationId(spec_id))

        # 要件IDを追加
        for req_id in data.get("requirement_ids", []):
            test_spec.requirement_ids.append(RequirementId(req_id))

        return test_spec

    def _test_specification_to_yaml(self, test_specification: SpecificationTest) -> dict[str, str | list]:
        """テスト仕様エンティティをYAMLデータに変換"""
        return {
            "test_file_path": test_specification.test_file_path,
            "test_function_name": test_specification.test_function_name,
            "specification_ids": [spec_id.value for spec_id in test_specification.specification_ids],
            "requirement_ids": [req_id.value for req_id in test_specification.requirement_ids],
            "description": test_specification.description,
        }
