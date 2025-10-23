"""仕様書エンティティのユニットテスト

仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime

import pytest

from noveler.domain.specification.entities import (
    RequirementId,
    Specification,
    SpecificationId,
    SpecificationTest,
    SpecificationTestReference,
)


class TestSpecificationId:
    """SpecificationId値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-ID_CREATE")
    def test_id_create(self) -> None:
        """SPEC-で始まる正常な仕様書IDを作成できる"""
        spec_id = SpecificationId("SPEC-001")
        assert spec_id.value == "SPEC-001"

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-EMPTY_ID")
    def test_empty_id(self) -> None:
        """空の仕様書IDはValueErrorを発生させる"""
        with pytest.raises(ValueError, match="仕様書IDは空にできません"):
            SpecificationId("")

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-SPEC_ID")
    def test_spec_id(self) -> None:
        """SPEC-以外で始まる仕様書IDはValueErrorを発生させる"""
        with pytest.raises(ValueError, match="仕様書IDはSPEC-で始まる必要があります"):
            SpecificationId("ID-001")


class TestSpecificationTestReference:
    """SpecificationTestReference値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-TESTCREATE")
    def test_testcreate(self) -> None:
        """行番号なしでテスト参照を作成できる"""
        ref = SpecificationTestReference("tests/test_example.py", "test_function")
        assert ref.file_path == "tests/test_example.py"
        assert ref.function_name == "test_function"
        assert ref.line_number is None
        assert str(ref) == "tests/test_example.py::test_function"

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_unnamed(self) -> None:
        """行番号ありでテスト参照を作成できる"""
        ref = SpecificationTestReference("tests/test_example.py", "test_function", 42)
        assert ref.line_number == 42
        assert str(ref) == "tests/test_example.py::test_function:42"


class TestRequirementId:
    """RequirementId値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-ID_CREATE")
    def test_id_create(self) -> None:
        """REQ-で始まる正常な要件IDを作成できる"""
        req_id = RequirementId("REQ-2.3.1")
        assert req_id.value == "REQ-2.3.1"

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-EMPTY_ID")
    def test_empty_id(self) -> None:
        """空の要件IDはValueErrorを発生させる"""
        with pytest.raises(ValueError, match="要件IDは空にできません"):
            RequirementId("")

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-REQ_ID")
    def test_req_id(self) -> None:
        """REQ-以外で始まる要件IDはValueErrorを発生させる"""
        with pytest.raises(ValueError, match="要件IDはREQ-で始まる必要があります"):
            RequirementId("REQUIREMENT-001")


class TestSpecification:
    """Specificationエンティティのテスト"""

    @pytest.fixture
    def basic_specification(self):
        """基本的な仕様書を作成"""
        return Specification(
            id=SpecificationId("SPEC-001"),
            title="ユーザー認証機能",
            description="ユーザーがシステムにログインできる機能",
        )

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_basic_functionality(self, basic_specification: object) -> None:
        """仕様書を基本情報で作成できる"""
        spec = basic_specification
        assert spec.id.value == "SPEC-001"
        assert spec.title == "ユーザー認証機能"
        assert spec.description == "ユーザーがシステムにログインできる機能"
        assert spec.test_references == []
        assert spec.requirement_ids == []
        assert spec.implementation_references == []
        assert isinstance(spec.created_at, datetime)
        assert isinstance(spec.updated_at, datetime)

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-DUPLICATE_TEST_ADD")
    def test_duplicate_test_add(self, basic_specification: object) -> None:
        """重複するテスト参照は追加されない"""
        spec = basic_specification
        test_ref = SpecificationTestReference("tests/test_auth.py", "test_login")

        spec.add_test_reference(test_ref)
        spec.add_test_reference(test_ref)
        assert len(spec.test_references) == 1

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_edge_cases(self, basic_specification: object) -> None:
        """テスト参照を削除できる"""
        spec = basic_specification
        test_ref = SpecificationTestReference("tests/test_auth.py", "test_login")

        spec.add_test_reference(test_ref)
        spec.remove_test_reference(test_ref)
        assert len(spec.test_references) == 0

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-ID")
    def test_id(self, basic_specification: object) -> None:
        """要件IDを追加できる"""
        spec = basic_specification
        req_id = RequirementId("REQ-2.3.1")

        spec.add_requirement(req_id)
        assert len(spec.requirement_ids) == 1
        assert spec.requirement_ids[0] == req_id

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_error_handling(self, basic_specification: object) -> None:
        """実装参照を追加できる"""
        spec = basic_specification
        impl_ref = "src/auth/login.py::login_user"

        spec.add_implementation_reference(impl_ref)
        assert len(spec.implementation_references) == 1
        assert spec.implementation_references[0] == impl_ref

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-TESTSTATUS")
    def test_teststatus(self, basic_specification: object) -> None:
        """テストカバレッジステータスを取得できる"""
        spec = basic_specification

        # テストなし
        assert spec.get_test_coverage_status() == "未実装"

        # テスト1つ
        spec.add_test_reference(SpecificationTestReference("tests/test_auth.py", "test_login"))
        assert spec.get_test_coverage_status() == "部分実装"

        # テスト2つ以上
        spec.add_test_reference(SpecificationTestReference("tests/test_auth.py", "test_logout"))
        assert spec.get_test_coverage_status() == "実装済み"

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-FILE")
    def test_file(self, basic_specification: object) -> None:
        """関連ファイルのパスを取得できる"""
        spec = basic_specification

        spec.add_test_reference(SpecificationTestReference("tests/test_auth.py", "test_login"))
        spec.add_test_reference(SpecificationTestReference("tests/test_auth.py", "test_logout"))
        spec.add_test_reference(SpecificationTestReference("tests/test_user.py", "test_create"))
        spec.add_implementation_reference("src/auth/login.py")
        spec.add_implementation_reference("src/auth/logout.py")

        files = spec.get_related_files()
        assert len(files) == 4
        assert "tests/test_auth.py" in files
        assert "tests/test_user.py" in files
        assert "src/auth/login.py" in files
        assert "src/auth/logout.py" in files


class TestSpecificationTest:
    """SpecificationTestエンティティのテスト"""

    @pytest.fixture
    def basic_test_specification(self):
        """基本的なテスト仕様を作成"""
        return SpecificationTest(
            test_file_path="tests/test_auth.py",
            test_function_name="test_login",
            description="ログイン機能の正常系テスト",
        )

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_validation(self, basic_test_specification: object) -> None:
        """テスト仕様を基本情報で作成できる"""
        test_spec = basic_test_specification
        assert test_spec.test_file_path == "tests/test_auth.py"
        assert test_spec.test_function_name == "test_login"
        assert test_spec.description == "ログイン機能の正常系テスト"
        assert test_spec.specification_ids == []
        assert test_spec.requirement_ids == []

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-ID")
    def test_id_1(self, basic_test_specification: object) -> None:
        """仕様IDを追加できる"""
        test_spec = basic_test_specification
        spec_id = SpecificationId("SPEC-001")

        test_spec.add_specification(spec_id)
        assert len(test_spec.specification_ids) == 1
        assert test_spec.specification_ids[0] == spec_id

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-DUPLICATE_ID_ADD")
    def test_duplicate_id_add(self, basic_test_specification: object) -> None:
        """重複する仕様IDは追加されない"""
        test_spec = basic_test_specification
        spec_id = SpecificationId("SPEC-001")

        test_spec.add_specification(spec_id)
        test_spec.add_specification(spec_id)
        assert len(test_spec.specification_ids) == 1

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-ID")
    def test_id_2(self, basic_test_specification: object) -> None:
        """要件IDを追加できる"""
        test_spec = basic_test_specification
        req_id = RequirementId("REQ-2.3.1")

        test_spec.add_requirement(req_id)
        assert len(test_spec.requirement_ids) == 1
        assert test_spec.requirement_ids[0] == req_id

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_integration(self, basic_test_specification: object) -> None:
        """仕様の存在を確認できる"""
        test_spec = basic_test_specification
        assert not test_spec.has_specifications()

        spec_id = SpecificationId("SPEC-001")
        test_spec.add_specification(spec_id)
        assert test_spec.has_specifications()

    @pytest.mark.spec("SPEC-SPECIFICATION_ENTITIES-UNNAMED")
    def test_performance(self, basic_test_specification: object) -> None:
        """TestReferenceオブジェクトを生成できる"""
        test_spec = basic_test_specification
        test_ref = test_spec.get_test_reference()

        assert test_ref.file_path == "tests/test_auth.py"
        assert test_ref.function_name == "test_login"
        assert str(test_ref) == "tests/test_auth.py::test_login"
