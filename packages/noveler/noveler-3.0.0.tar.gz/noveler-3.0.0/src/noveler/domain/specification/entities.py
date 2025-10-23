"""Domain.specification.entities
Where: Domain entities representing specification documents and metadata.
What: Encapsulate specification state, identifiers, and relationships.
Why: Support validation and synchronization of specification data.
"""

from __future__ import annotations

"""仕様書管理ドメインエンティティ

仕様書とテストの紐付けを管理するドメインモデル
"""


from dataclasses import dataclass, field
from datetime import datetime

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class SpecificationId:
    """仕様書ID値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = "仕様書IDは空にできません"
            raise ValueError(msg)
        if not self.value.startswith("SPEC-"):
            msg = "仕様書IDはSPEC-で始まる必要があります"
            raise ValueError(msg)


@dataclass
class SpecificationTestReference:
    """テスト参照値オブジェクト"""

    file_path: str
    function_name: str
    line_number: int | None = None

    def __str__(self) -> str:
        if self.line_number:
            return f"{self.file_path}::{self.function_name}:{self.line_number}"
        return f"{self.file_path}::{self.function_name}"


@dataclass(frozen=True)
class RequirementId:
    """要件ID値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = "要件IDは空にできません"
            raise ValueError(msg)
        if not self.value.startswith("REQ-"):
            msg = "要件IDはREQ-で始まる必要があります"
            raise ValueError(msg)


@dataclass
class Specification:
    """仕様書エンティティ"""

    id: SpecificationId
    title: str
    description: str
    test_references: list[SpecificationTestReference] = field(default_factory=list)
    requirement_ids: list[RequirementId] = field(default_factory=list)
    implementation_references: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_test_reference(self, test_ref: SpecificationTestReference) -> None:
        """テスト参照を追加"""
        if test_ref not in self.test_references:
            self.test_references.append(test_ref)
            self.updated_at = project_now().datetime

    def remove_test_reference(self, test_ref: SpecificationTestReference) -> None:
        """テスト参照を削除"""
        if test_ref in self.test_references:
            self.test_references.remove(test_ref)
            self.updated_at = project_now().datetime

    def add_requirement(self, req_id: RequirementId) -> None:
        """要件IDを追加"""
        if req_id not in self.requirement_ids:
            self.requirement_ids.append(req_id)
            self.updated_at = project_now().datetime

    def add_implementation_reference(self, impl_ref: str) -> None:
        """実装参照を追加"""
        if impl_ref not in self.implementation_references:
            self.implementation_references.append(impl_ref)
            self.updated_at = project_now().datetime

    def has_tests(self) -> bool:
        """テストが存在するか確認"""
        return len(self.test_references) > 0

    def get_test_coverage_status(self) -> str:
        """テストカバレッジステータスを取得"""
        if not self.test_references:
            return "未実装"
        if len(self.test_references) < 2:
            return "部分実装"
        return "実装済み"

    def get_related_files(self) -> set[str]:
        """関連するファイルパスを取得"""
        files = set()
        for test_ref in self.test_references:
            files.add(test_ref.file_path)
        files.update(self.implementation_references)
        return files


@dataclass
class SpecificationTest:
    """テスト仕様エンティティ"""

    test_file_path: str
    test_function_name: str
    specification_ids: list[SpecificationId] = field(default_factory=list)
    requirement_ids: list[RequirementId] = field(default_factory=list)
    description: str | None = None

    def add_specification(self, spec_id: SpecificationId) -> None:
        """仕様IDを追加"""
        if spec_id not in self.specification_ids:
            self.specification_ids.append(spec_id)

    def add_requirement(self, req_id: RequirementId) -> None:
        """要件IDを追加"""
        if req_id not in self.requirement_ids:
            self.requirement_ids.append(req_id)

    def has_specifications(self) -> bool:
        """仕様が紐付けられているか確認"""
        return len(self.specification_ids) > 0

    def get_test_reference(self) -> SpecificationTestReference:
        """SpecificationTestReferenceオブジェクトを生成"""
        return SpecificationTestReference(file_path=self.test_file_path, function_name=self.test_function_name)
