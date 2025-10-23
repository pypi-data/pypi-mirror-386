# File: tests/unit/hooks/test_check_anemic_domain.py
# Purpose: Unit tests for Anemic Domain Model detection hook
# Context: Validates detection logic for various patterns and edge cases

"""Anemic Domain Model検知フックのユニットテスト

check_anemic_domain.pyの検知ロジックを網羅的にテストする。
"""

import ast
from pathlib import Path
import tempfile
import pytest

from scripts.hooks.check_anemic_domain import AnemicDomainDetector, check_file


class TestEnumExclusion:
    """Enum型の除外テスト"""

    def test_enum_excluded_from_anemic_detection(self):
        """Enum型が貧血症検知の対象外になることを確認

        Given: Enumを継承したクラス
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from enum import Enum

class Status(Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
"""

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            # domain層のパスをシミュレート
            fake_path = "src/noveler/domain/value_objects/status.py"
            f.write(code)
            f.flush()

            detector = AnemicDomainDetector(fake_path)
            tree = ast.parse(code, filename=fake_path)
            detector.visit(tree)
            detector.finalize()

            # Enumは検知されない
            assert len(detector.issues) == 0


class TestDataclassValidation:
    """dataclass バリデーション付きのテスト"""

    def test_dataclass_with_validation_passes(self):
        """__post_init__バリデーションがあるdataclassは合格

        Given: __post_init__でバリデーションを行うdataclass
        When: Anemic Domain検知を実行
        Then: 貧血症として検知されない
        """
        code = """
from dataclasses import dataclass

@dataclass
class EpisodeNumber:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Episode number must be positive")
"""

        fake_path = "src/noveler/domain/value_objects/episode_number.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # バリデーションがあるので検知されない
        assert len(detector.issues) == 0

    def test_dataclass_with_domain_logic_passes(self):
        """ビジネスロジックメソッドがあるdataclassは合格

        Given: ビジネスロジックメソッドを持つdataclass
        When: Anemic Domain検知を実行
        Then: 貧血症として検知されない
        """
        code = """
from dataclasses import dataclass

@dataclass
class WordCount:
    value: int

    def is_within_limit(self, max_words: int) -> bool:
        return self.value <= max_words

    def exceeds_minimum(self, min_words: int) -> bool:
        return self.value >= min_words
"""

        fake_path = "src/noveler/domain/value_objects/word_count.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # ビジネスロジックがあるので検知されない
        assert len(detector.issues) == 0


class TestAnemicDetection:
    """貧血症モデルの検知テスト"""

    def test_anemic_dataclass_detected(self):
        """ビジネスロジックのないdataclassは貧血症として検知

        Given: メソッドが一切ないdataclass
        When: Anemic Domain検知を実行
        Then: ANEMIC_DATACLASSとして検知される
        """
        code = """
from dataclasses import dataclass

@dataclass
class PlainData:
    name: str
    value: int
"""

        fake_path = "src/noveler/domain/entities/plain_data.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # 貧血症として検知される
        assert len(detector.issues) == 1
        line, code_type, message = detector.issues[0]
        assert code_type == "ANEMIC_DATACLASS"
        assert "PlainData" in message
        assert "no business logic methods" in message

    def test_plain_dataclass_without_methods_detected(self):
        """メソッドなしのシンプルなdataclassは貧血症として検知

        Given: フィールドのみのdataclass（バリデーションなし）
        When: Anemic Domain検知を実行
        Then: ANEMIC_DATACLASSとして検知される
        """
        code = """
from dataclasses import dataclass

@dataclass
class SimpleEntity:
    id: int
    name: str
    description: str
"""

        fake_path = "src/noveler/domain/entities/simple_entity.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # 貧血症として検知される
        assert len(detector.issues) == 1
        assert detector.issues[0][1] == "ANEMIC_DATACLASS"


class TestProtocolExclusion:
    """Protocol/Interfaceの除外テスト"""

    def test_protocol_interface_excluded(self):
        """IXxxプレフィックス、XxxProtocolサフィックスのクラスは除外

        Given: IXxx または XxxProtocol の命名規則に従うクラス
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from dataclasses import dataclass
from typing import Protocol

@dataclass
class IRepository:
    pass

class EntityProtocol:
    pass
"""

        fake_path = "src/noveler/domain/entities/repository.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # Protocol/Interfaceは検知されない
        assert len(detector.issues) == 0

    def test_abstract_base_class_excluded(self):
        """Protocolサフィックスを持つ抽象クラスは除外

        Given: XxxProtocolという命名のクラス
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
class UserServiceProtocol:
    def create_user(self, name: str) -> None:
        pass
"""

        fake_path = "src/noveler/domain/entities/user_service_protocol.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # Protocolサフィックスは検知されない
        assert len(detector.issues) == 0


class TestDTOExclusion:
    """DTO (Request/Response/DTO) の除外テスト"""

    def test_request_suffix_excluded(self):
        """Requestサフィックスを持つクラスは除外

        Given: XxxRequestという命名のクラス
        When: Anemic Domain検知を実行
        Then: DTOとして検知対象外になる
        """
        code = """
from dataclasses import dataclass

@dataclass
class CreateEpisodeRequest:
    title: str
    content: str
"""

        fake_path = "src/noveler/domain/value_objects/create_episode_request.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # DTOは検知されない
        assert len(detector.issues) == 0

    def test_response_suffix_excluded(self):
        """Responseサフィックスを持つクラスは除外

        Given: XxxResponseという命名のクラス
        When: Anemic Domain検知を実行
        Then: DTOとして検知対象外になる
        """
        code = """
from dataclasses import dataclass

@dataclass
class EpisodeResponse:
    id: int
    title: str
    published: bool
"""

        fake_path = "src/noveler/domain/value_objects/episode_response.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # DTOは検知されない
        assert len(detector.issues) == 0

    def test_dto_suffix_excluded(self):
        """DTOサフィックスを持つクラスは除外

        Given: XxxDTOという命名のクラス
        When: Anemic Domain検知を実行
        Then: DTOとして検知対象外になる
        """
        code = """
from dataclasses import dataclass

@dataclass
class EpisodeUpdateDTO:
    title: str
    content: str
    tags: list
"""

        fake_path = "src/noveler/domain/value_objects/episode_update_dto.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # DTOは検知されない
        assert len(detector.issues) == 0


class TestCompositePattern:
    """Composite Value Objectの誤検知回避テスト"""

    def test_composite_vo_with_child_vos_passes(self):
        """他のValue Objectを組み合わせたComposite VOは合格

        Given: 他のVOを子フィールドとして持つComposite VO
        When: Anemic Domain検知を実行
        Then: 貧血症として検知されない（子VOがロジックを持つため）
        """
        code = """
from dataclasses import dataclass

@dataclass
class Address:
    street: str
    city: str

    def __post_init__(self):
        if not self.street or not self.city:
            raise ValueError("Address must have street and city")

@dataclass
class UserProfile:
    name: str
    address: Address  # Composite: 子VOを持つ

    def __post_init__(self):
        # 子VOのバリデーションが実行される
        pass
"""

        fake_path = "src/noveler/domain/value_objects/user_profile.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # __post_init__があるので検知されない
        assert len(detector.issues) == 0

    def test_aggregate_root_with_entities_passes(self):
        """複数のEntityを管理するAggregate Rootは合格

        Given: 複数のEntityを子として持ち、集約管理するAggregate Root
        When: Anemic Domain検知を実行
        Then: 貧血症として検知されない（集約管理メソッドがあるため）
        """
        code = """
from dataclasses import dataclass, field
from typing import List

@dataclass
class Episode:
    id: int
    title: str

    def __post_init__(self):
        if not self.title:
            raise ValueError("Title is required")

@dataclass
class Story:
    title: str
    episodes: List[Episode] = field(default_factory=list)

    def add_episode(self, episode: Episode) -> None:
        '''エピソードを追加'''
        self.episodes.append(episode)

    def remove_episode(self, episode_id: int) -> None:
        '''エピソードを削除'''
        self.episodes = [e for e in self.episodes if e.id != episode_id]
"""

        fake_path = "src/noveler/domain/entities/story.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # ビジネスロジックメソッドがあるので検知されない
        assert len(detector.issues) == 0


class TestDataclassArgumentsParsing:
    """@dataclass引数の解析テスト"""

    def test_frozen_dataclass_with_eq_passes(self):
        """@dataclass(frozen=True, eq=True)のimmutable VOは合格

        Given: frozen=True, eq=Trueで自動生成される__eq__を持つdataclass
        When: Anemic Domain検知を実行
        Then: 貧血症として検知されない（__eq__が自動生成されるため）
        """
        code = """
from dataclasses import dataclass

@dataclass(frozen=True, eq=True)
class ImmutableEpisodeNumber:
    value: int
"""

        fake_path = "src/noveler/domain/value_objects/immutable_episode_number.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # dataclassが__eq__を自動生成するので検知されない
        # ただしバリデーションがないため、NO_VALIDATIONとして検知される可能性がある
        # しかし、eq=Trueにより__eq__が生成されるため、条件を満たす
        assert len(detector.issues) == 0

    def test_dataclass_eq_false_detected(self):
        """@dataclass(eq=False)でバリデーションなしは貧血症検知

        Given: eq=Falseで__eq__が自動生成されず、バリデーションもないdataclass
        When: Anemic Domain検知を実行
        Then: ANEMIC_DATACLASSとNO_VALIDATIONの両方として検知される
        """
        code = """
from dataclasses import dataclass

@dataclass(eq=False)
class NoEqValue:
    value: int
"""

        fake_path = "src/noveler/domain/value_objects/no_eq_value.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # eq=Falseで__eq__が生成されず、__post_init__もないため2つ検知される
        assert len(detector.issues) == 2
        issue_types = [issue[1] for issue in detector.issues]
        assert "ANEMIC_DATACLASS" in issue_types
        assert "NO_VALIDATION" in issue_types


class TestNonDomainLayerFiles:
    """domain層以外のファイルは検知対象外"""

    def test_application_layer_not_checked(self):
        """application層のファイルは検知されない

        Given: application層のファイル
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from dataclasses import dataclass

@dataclass
class ApplicationData:
    value: int
"""

        fake_path = "src/noveler/application/use_cases/some_use_case.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # domain層以外は検知されない
        assert len(detector.issues) == 0

    def test_infrastructure_layer_not_checked(self):
        """infrastructure層のファイルは検知されない

        Given: infrastructure層のファイル
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from dataclasses import dataclass

@dataclass
class InfrastructureData:
    value: int
"""

        fake_path = "src/noveler/infrastructure/adapters/some_adapter.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # domain層以外は検知されない
        assert len(detector.issues) == 0


class TestFileIntegration:
    """check_file()統合テスト"""

    def test_check_file_with_anemic_model(self, tmp_path):
        """check_file()で貧血症モデルが検知される

        Given: 貧血症モデルを含むファイル
        When: check_file()を実行
        Then: issuesが返される
        """
        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "test_entity.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class AnemicEntity:
    id: int
    name: str
""", encoding='utf-8')

        issues = check_file(test_file)

        # 貧血症として検知される
        assert len(issues) == 1
        assert issues[0][1] == "ANEMIC_DATACLASS"

    def test_check_file_with_valid_model(self, tmp_path):
        """check_file()で正常なモデルはパスする

        Given: バリデーション付きの正常なモデル
        When: check_file()を実行
        Then: issuesが空
        """
        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "value_objects"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "test_vo.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class ValidVO:
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Value must be non-negative")
""", encoding='utf-8')

        issues = check_file(test_file)

        # 検知されない
        assert len(issues) == 0

    def test_check_file_syntax_error_ignored(self, tmp_path):
        """check_file()でSyntaxErrorは無視される

        Given: 構文エラーのあるファイル
        When: check_file()を実行
        Then: 空のissuesが返される
        """
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "syntax_error.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class SyntaxError
    id: int  # コロンが欠落
""", encoding='utf-8')

        issues = check_file(test_file)

        # SyntaxErrorは無視され、空のissuesが返される
        assert len(issues) == 0


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_multiple_classes_in_same_file(self):
        """同じファイル内の複数クラスを正しく検知

        Given: 複数のクラスを含むファイル（一部は貧血症）
        When: Anemic Domain検知を実行
        Then: 貧血症のクラスのみが検知される
        """
        code = """
from dataclasses import dataclass

@dataclass
class ValidVO:
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Value must be non-negative")

@dataclass
class AnemicVO:
    value: int
"""

        fake_path = "src/noveler/domain/value_objects/mixed.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # AnemicVOのみが検知される
        assert len(detector.issues) == 1
        assert "AnemicVO" in detector.issues[0][2]

    def test_private_methods_not_counted_as_business_logic(self):
        """プライベートメソッドはビジネスロジックとして扱われない

        Given: プライベートメソッドのみを持つdataclass
        When: Anemic Domain検知を実行
        Then: 貧血症として検知される
        """
        code = """
from dataclasses import dataclass

@dataclass
class WithPrivateMethod:
    value: int

    def _internal_check(self) -> bool:
        return self.value > 0
"""

        fake_path = "src/noveler/domain/entities/with_private_method.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # プライベートメソッドはビジネスロジックとして扱われないため検知される
        assert len(detector.issues) == 1
        assert detector.issues[0][1] == "ANEMIC_DATACLASS"

    def test_dunder_methods_counted_as_business_logic(self):
        """__post_init__, __eq__, __hash__はビジネスロジックとして扱われる

        Given: __eq__や__hash__を明示的に実装したdataclass
        When: Anemic Domain検知を実行
        Then: 貧血症として検知されない
        """
        code = """
from dataclasses import dataclass

@dataclass
class WithDunderMethods:
    value: int

    def __eq__(self, other):
        return isinstance(other, WithDunderMethods) and self.value == other.value

    def __hash__(self):
        return hash(self.value)
"""

        fake_path = "src/noveler/domain/value_objects/with_dunder_methods.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)
        detector.visit(tree)
        detector.finalize()

        # __eq__と__hash__があるため検知されない
        assert len(detector.issues) == 0


class TestMainFunction:
    """main()関数の統合テスト"""

    def test_main_with_no_domain_files(self, tmp_path, monkeypatch):
        """Git staged filesにdomain層ファイルがない場合

        Given: domain層以外のファイルのみがステージされている
        When: main()を実行
        Then: 終了コード0が返される
        """
        import subprocess
        from unittest.mock import MagicMock

        # Gitコマンドのモック
        def mock_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = "src/noveler/application/use_cases/test.py\n"
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        from scripts.hooks.check_anemic_domain import main
        exit_code = main()

        # domain層ファイルがないため、終了コード0
        assert exit_code == 0

    def test_main_with_valid_domain_files(self, tmp_path, monkeypatch):
        """正常なdomain層ファイルの場合

        Given: バリデーション付きの正常なdomain層ファイルがステージされている
        When: main()を実行
        Then: 終了コード0が返される
        """
        import subprocess
        from unittest.mock import MagicMock

        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "value_objects"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "test_vo.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class ValidVO:
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Value must be non-negative")
""", encoding='utf-8')

        # Gitコマンドのモック
        def mock_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = f"{test_file}\n"
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        monkeypatch.chdir(tmp_path)

        from scripts.hooks.check_anemic_domain import main
        exit_code = main()

        # 正常なファイルなので終了コード0
        assert exit_code == 0

    def test_main_with_anemic_domain_files(self, tmp_path, monkeypatch, capsys):
        """貧血症domain層ファイルの場合

        Given: 貧血症モデルを含むdomain層ファイルがステージされている
        When: main()を実行
        Then: 終了コード1が返され、エラーメッセージが出力される
        """
        import subprocess
        from unittest.mock import MagicMock

        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "anemic_entity.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class AnemicEntity:
    id: int
    name: str
""", encoding='utf-8')

        # Gitコマンドのモック
        def mock_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = f"{test_file}\n"
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        monkeypatch.chdir(tmp_path)

        from scripts.hooks.check_anemic_domain import main
        exit_code = main()

        # 貧血症が検知されたので終了コード1
        assert exit_code == 1

        # エラーメッセージが出力されている
        captured = capsys.readouterr()
        assert "ANEMIC_DATACLASS" in captured.out
        assert "AnemicEntity" in captured.out

    def test_main_with_git_command_failure(self, tmp_path, monkeypatch):
        """Gitコマンドが失敗した場合

        Given: Git diff-indexコマンドが失敗する環境
        When: main()を実行
        Then: 終了コード0が返される（エラーは無視）
        """
        import subprocess
        from unittest.mock import MagicMock

        # Gitコマンドのモック（失敗）
        def mock_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = ""
            result.returncode = 128  # Git error code
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        from scripts.hooks.check_anemic_domain import main
        exit_code = main()

        # Git失敗は無視され、終了コード0
        assert exit_code == 0

    def test_main_with_multiple_files(self, tmp_path, monkeypatch, capsys):
        """複数のdomain層ファイルを処理する場合

        Given: 複数のdomain層ファイルがステージされている（一部は貧血症）
        When: main()を実行
        Then: 貧血症ファイルの数だけエラーが報告される
        """
        import subprocess
        from unittest.mock import MagicMock

        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        # 正常なファイル
        valid_file = domain_dir / "valid_entity.py"
        valid_file.write_text("""
from dataclasses import dataclass

@dataclass
class ValidEntity:
    id: int

    def __post_init__(self):
        if self.id <= 0:
            raise ValueError("ID must be positive")
""", encoding='utf-8')

        # 貧血症ファイル
        anemic_file = domain_dir / "anemic_entity.py"
        anemic_file.write_text("""
from dataclasses import dataclass

@dataclass
class AnemicEntity:
    id: int
    name: str
""", encoding='utf-8')

        # Gitコマンドのモック
        def mock_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = f"{valid_file}\n{anemic_file}\n"
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        monkeypatch.chdir(tmp_path)

        from scripts.hooks.check_anemic_domain import main
        exit_code = main()

        # 貧血症が検知されたので終了コード1
        assert exit_code == 1

        # 貧血症ファイルのエラーのみが報告される
        captured = capsys.readouterr()
        assert "AnemicEntity" in captured.out
        assert "ValidEntity" not in captured.out


class TestNoqaCommentSupport:
    """P3-2: noqa コメントサポートのテスト"""

    def test_noqa_comment_on_class_line(self):
        """クラス定義行の noqa コメントで検知抑制

        Given: クラス定義行に # noqa: anemic-domain コメントがある
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from dataclasses import dataclass

@dataclass
class AnemicEntity:  # noqa: anemic-domain
    id: int
    name: str
"""

        fake_path = "src/noveler/domain/entities/anemic_entity.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)

        # ファイルを一時作成して noqa チェックを有効化
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            # 実際のファイルパスで検知実行
            detector.file_path = temp_path
            detector.visit(tree)
            detector.finalize()

            # noqa コメントにより検知されない
            assert len(detector.issues) == 0
        finally:
            import os
            os.unlink(temp_path)

    def test_noqa_comment_on_decorator_line(self):
        """デコレータ行の noqa コメントで検知抑制

        Given: デコレータ行に # noqa: anemic-domain コメントがある
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from dataclasses import dataclass

@dataclass  # noqa: anemic-domain
class AnemicEntity:
    id: int
    name: str
"""

        fake_path = "src/noveler/domain/entities/anemic_entity.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)

        # ファイルを一時作成
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            detector.file_path = temp_path
            detector.visit(tree)
            detector.finalize()

            # noqa コメントにより検知されない
            assert len(detector.issues) == 0
        finally:
            import os
            os.unlink(temp_path)

    def test_noqa_comment_without_space(self):
        """スペースなし noqa コメントも対応

        Given: # noqa:anemic-domain (スペースなし) コメントがある
        When: Anemic Domain検知を実行
        Then: 検知対象外として扱われる
        """
        code = """
from dataclasses import dataclass

@dataclass
class AnemicEntity:  # noqa:anemic-domain
    id: int
    name: str
"""

        fake_path = "src/noveler/domain/entities/anemic_entity.py"
        detector = AnemicDomainDetector(fake_path)
        tree = ast.parse(code, filename=fake_path)

        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        try:
            detector.file_path = temp_path
            detector.visit(tree)
            detector.finalize()

            assert len(detector.issues) == 0
        finally:
            import os
            os.unlink(temp_path)

    def test_noqa_does_not_affect_other_classes(self, tmp_path):
        """noqa コメントは対象クラスのみに影響

        Given: 複数クラスがあり、一部のみ noqa コメント付き
        When: Anemic Domain検知を実行
        Then: noqa なしのクラスのみ検知される
        """
        code = """
from dataclasses import dataclass

@dataclass
class ValidEntity:  # noqa: anemic-domain
    id: int
    name: str

@dataclass
class AnemicEntity:
    id: int
    name: str
"""

        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "mixed.py"
        test_file.write_text(code, encoding='utf-8')

        detector = AnemicDomainDetector(str(test_file))
        tree = ast.parse(code, filename=str(test_file))
        detector.visit(tree)
        detector.finalize()

        # AnemicEntity のみ検知される
        assert len(detector.issues) == 1
        assert "AnemicEntity" in detector.issues[0][2]


class TestErrorHandling:
    """P3-3: エラーハンドリング強化のテスト"""

    def test_unicode_decode_error_handling(self, tmp_path, capsys):
        """UnicodeDecodeError 発生時の処理

        Given: UTF-8でデコードできないファイル
        When: check_file()を実行
        Then: 空のissuesが返され、警告がstderrに出力される
        """
        # domain層のパス構造を作成
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "bad_encoding.py"
        # Shift_JIS でファイルを作成（UTF-8として読むとエラー）
        test_file.write_bytes(b'\x82\xa0\x82\xa2\x82\xa4')  # あいう in Shift_JIS

        issues = check_file(test_file)

        # エラーは握りつぶされ、空のissuesが返される
        assert len(issues) == 0

        # 警告がstderrに出力される
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.err
        assert "bad_encoding.py" in captured.err
        assert "decoding error" in captured.err.lower() or "decode" in captured.err.lower()

    def test_io_error_handling(self, tmp_path, capsys, monkeypatch):
        """IOError 発生時の処理

        Given: 読み込み不可能なファイル
        When: check_file()を実行
        Then: 空のissuesが返され、警告がstderrに出力される
        """
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "inaccessible.py"

        # IOErrorをシミュレート（openをモック）
        original_open = open
        def mock_open(*args, **kwargs):
            if str(test_file) in str(args[0]):
                raise IOError("Permission denied")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        issues = check_file(test_file)

        # エラーは握りつぶされ、空のissuesが返される
        assert len(issues) == 0

        # 警告がstderrに出力される
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.err
        assert "inaccessible.py" in captured.err

    def test_syntax_error_returns_empty_issues(self, tmp_path):
        """SyntaxError 発生時は空のissuesを返す

        Given: 構文エラーのあるファイル
        When: check_file()を実行
        Then: 空のissuesが返される（警告なし）
        """
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "syntax_error.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class SyntaxError
    id: int  # コロンが欠落
""", encoding='utf-8')

        issues = check_file(test_file)

        # SyntaxErrorは無視され、空のissuesが返される
        assert len(issues) == 0

    def test_unexpected_error_handling(self, tmp_path, capsys, monkeypatch):
        """予期しないエラーの処理

        Given: ast.parse()で予期しないエラーが発生
        When: check_file()を実行
        Then: 空のissuesが返され、警告がstderrに出力される
        """
        domain_dir = tmp_path / "src" / "noveler" / "domain" / "entities"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "unexpected_error.py"
        test_file.write_text("""
from dataclasses import dataclass

@dataclass
class ValidEntity:
    id: int
""", encoding='utf-8')

        # ast.parseをモックして予期しないエラーを発生させる
        import ast as ast_module
        original_parse = ast_module.parse
        def mock_parse(*args, **kwargs):
            if "unexpected_error.py" in str(kwargs.get("filename", "")):
                raise RuntimeError("Unexpected parsing error")
            return original_parse(*args, **kwargs)

        monkeypatch.setattr(ast_module, "parse", mock_parse)

        issues = check_file(test_file)

        # エラーは握りつぶされ、空のissuesが返される
        assert len(issues) == 0

        # 警告がstderrに出力される
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.err
        assert "unexpected_error.py" in captured.err
        assert "RuntimeError" in captured.err or "Unexpected" in captured.err


class TestConfigFileSupport:
    """P3-1: 設定ファイルサポートのテスト"""

    def test_config_loading_with_yaml(self, tmp_path):
        """YAML設定ファイル読み込み

        Given: .anemic-domain.yaml が存在する
        When: AnemicDomainConfigを初期化
        Then: YAML設定が読み込まれる
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        # 設定ファイルを作成
        config_file = tmp_path / ".anemic-domain.yaml"
        config_file.write_text("""
domain_properties:
  - custom_property
excluded_suffixes:
  - CustomDTO
validation_keywords:
  - custom_validate
""", encoding='utf-8')

        config = AnemicDomainConfig(config_file)

        # カスタム設定が読み込まれている
        assert "custom_property" in config.get_domain_properties()
        assert "CustomDTO" in config.get_excluded_suffixes()
        assert "custom_validate" in config.get_validation_keywords()

    def test_config_fallback_to_defaults(self, tmp_path):
        """設定ファイルがない場合のデフォルト使用

        Given: .anemic-domain.yaml が存在しない
        When: AnemicDomainConfigを初期化
        Then: デフォルト設定が使用される
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        # 存在しないパスを指定
        non_existent = tmp_path / "non_existent.yaml"
        config = AnemicDomainConfig(non_existent)

        # デフォルト設定が使用される
        assert "episode_number" in config.get_domain_properties()
        assert "Protocol" in config.get_excluded_suffixes()
        assert "validate" in config.get_validation_keywords()

    def test_config_partial_override(self, tmp_path):
        """部分的な設定のマージ

        Given: 一部の設定のみを含むYAMLファイル
        When: AnemicDomainConfigを初期化
        Then: 指定された設定は上書き、未指定はデフォルト使用
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        config_file = tmp_path / ".anemic-domain.yaml"
        config_file.write_text("""
excluded_suffixes:
  - MyCustomDTO
""", encoding='utf-8')

        config = AnemicDomainConfig(config_file)

        # excluded_suffixes は上書きされる
        assert "MyCustomDTO" in config.get_excluded_suffixes()
        # 他の設定はデフォルトのまま
        assert "episode_number" in config.get_domain_properties()

    def test_config_without_pyyaml(self, tmp_path, monkeypatch):
        """PyYAML未インストール時のフォールバック

        Given: PyYAMLがインポートできない環境
        When: AnemicDomainConfigを初期化
        Then: デフォルト設定が使用される
        """
        config_file = tmp_path / ".anemic-domain.yaml"
        config_file.write_text("""
domain_properties:
  - custom_property
""", encoding='utf-8')

        # yamlモジュールをモック（check_anemic_domain モジュール内で）
        import scripts.hooks.check_anemic_domain as check_module
        original_yaml = check_module.yaml
        monkeypatch.setattr(check_module, 'yaml', None)

        config = check_module.AnemicDomainConfig(config_file)

        # YAMLが読めないため、デフォルト設定が使用される
        assert "episode_number" in config.get_domain_properties()
        assert "custom_property" not in config.get_domain_properties()

        # 元に戻す
        monkeypatch.setattr(check_module, 'yaml', original_yaml)

    def test_is_excluded_path(self):
        """除外パス判定

        Given: excluded_paths に特定のパスが設定されている
        When: is_excluded_path()を呼び出す
        Then: 正しく判定される
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        config = AnemicDomainConfig()

        # デフォルト設定で tests/fixtures/domain は除外される
        assert config.is_excluded_path("tests/fixtures/domain/anemic_entity.py") is True
        assert config.is_excluded_path("src/noveler/domain/entities/episode.py") is False

    def test_is_target_path(self):
        """対象パス判定

        Given: target_paths に特定のパスが設定されている
        When: is_target_path()を呼び出す
        Then: 正しく判定される
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        config = AnemicDomainConfig()

        # デフォルト設定で domain/entities と domain/value_objects が対象
        assert config.is_target_path("src/noveler/domain/entities/episode.py") is True
        assert config.is_target_path("src/noveler/domain/value_objects/episode_number.py") is True
        assert config.is_target_path("src/noveler/application/use_cases/create_episode.py") is False

    def test_config_with_invalid_yaml(self, tmp_path):
        """無効なYAMLファイルの処理

        Given: 構文エラーのあるYAMLファイル
        When: AnemicDomainConfigを初期化
        Then: デフォルト設定が使用される（エラーにならない）
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        config_file = tmp_path / ".anemic-domain.yaml"
        config_file.write_text("""
invalid_yaml:
  - item1
    - item2  # インデントエラー
""", encoding='utf-8')

        config = AnemicDomainConfig(config_file)

        # YAML読み込みエラーは無視され、デフォルト設定が使用される
        assert "episode_number" in config.get_domain_properties()

    def test_config_search_in_repository_root(self, tmp_path, monkeypatch):
        """リポジトリルートの設定ファイル検索

        Given: リポジトリルート（.git存在）に .anemic-domain.yaml がある
        When: AnemicDomainConfig(None) で初期化
        Then: 自動的に設定ファイルが見つかる
        """
        from scripts.hooks.check_anemic_domain import AnemicDomainConfig

        # リポジトリ構造を作成
        (tmp_path / ".git").mkdir()
        config_file = tmp_path / ".anemic-domain.yaml"
        config_file.write_text("""
domain_properties:
  - found_property
""", encoding='utf-8')

        # サブディレクトリから検索
        subdir = tmp_path / "src" / "domain"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        config = AnemicDomainConfig(None)

        # ルートの設定ファイルが見つかる
        assert "found_property" in config.get_domain_properties()
