"""プロジェクト初期化ドメインのリポジトリインターフェーステスト

TDD準拠テスト:
    - ProjectTemplateRepository (ABC)
- ProjectInitializationRepository (ABC)


仕様書: SPEC-UNIT-TEST
"""

from abc import ABC

import pytest

from noveler.domain.initialization.entities import (
    InitializationStatus,
    ProjectInitialization,
    ProjectTemplate,
)
from noveler.domain.initialization.repositories import (
    ProjectInitializationRepository,
    ProjectTemplateRepository,
)
from noveler.domain.initialization.value_objects import (
    Genre,
    InitializationConfig,
    UpdateFrequency,
    WritingStyle,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestProjectTemplateRepository:
    """ProjectTemplateRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_is_abstract(self) -> None:
        """ProjectTemplateRepositoryが抽象クラスであることを確認"""
        assert issubclass(ProjectTemplateRepository, ABC)

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_abstract_methods(self) -> None:
        """ProjectTemplateRepositoryの抽象メソッド確認"""
        abstract_methods = ProjectTemplateRepository.__abstractmethods__
        expected_methods = {
            "find_by_id",
            "find_by_genre",
            "find_all",
            "save",
            "delete",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_find_by_id_signature(self) -> None:
        """find_by_idメソッドのシグネチャ確認"""

        class MockTemplateRepo(ProjectTemplateRepository):
            def find_by_id(self, _template_id: str) -> ProjectTemplate | None:
                if _template_id == "fantasy-basic":
                    return ProjectTemplate(
                        template_id="fantasy-basic",
                        name="ファンタジー基本テンプレート",
                        description="基本的なファンタジー小説のテンプレート",
                        _genre=Genre.FANTASY,
                        structure={"chapters": 20, "episodes_per_chapter": 5, "target_words_per_episode": 3000},
                        metadata={"tags": ["fantasy", "basic"]},
                    )

                return None

            def find_by_genre(self, _genre: Genre) -> list[ProjectTemplate]:
                return []

            def find_all(self) -> list[ProjectTemplate]:
                return []

            def save(self, template: ProjectTemplate) -> None:
                pass

            def delete(self, template_id: str) -> None:
                pass

        repo = MockTemplateRepo()

        # 存在するテンプレート
        result = repo.find_by_id("fantasy-basic")
        assert isinstance(result, ProjectTemplate)
        assert result.template_id == "fantasy-basic"
        assert result._genre == Genre.FANTASY

        # 存在しないテンプレート
        result_none = repo.find_by_id("nonexistent")
        assert result_none is None

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_find_by_genre_signature(self) -> None:
        """find_by_genreメソッドのシグネチャ確認"""

        class MockTemplateRepo(ProjectTemplateRepository):
            def find_by_id(self, _template_id: str) -> ProjectTemplate | None:
                return None

            def find_by_genre(self, _genre: Genre) -> list[ProjectTemplate]:
                templates = {
                    Genre.FANTASY: [
                        ProjectTemplate(
                            template_id="fantasy-basic",
                            name="ファンタジー基本",
                            description="基本的なファンタジー",
                            _genre=Genre.FANTASY,
                            structure={},
                            metadata={},
                        ),
                        ProjectTemplate(
                            template_id="fantasy-advanced",
                            name="ファンタジー上級",
                            description="上級ファンタジー",
                            _genre=Genre.FANTASY,
                            structure={},
                            metadata={},
                        ),
                    ],
                    Genre.ROMANCE: [
                        ProjectTemplate(
                            template_id="romance-basic",
                            name="恋愛基本",
                            description="基本的な恋愛小説",
                            _genre=Genre.ROMANCE,
                            structure={},
                            metadata={},
                        )
                    ],
                }
                return templates.get(_genre, [])

            def find_all(self) -> list[ProjectTemplate]:
                return []

            def save(self, template: ProjectTemplate) -> None:
                pass

            def delete(self, template_id: str) -> None:
                pass

        repo = MockTemplateRepo()

        # ファンタジーテンプレート
        fantasy_templates = repo.find_by_genre(Genre.FANTASY)
        assert isinstance(fantasy_templates, list)
        assert len(fantasy_templates) == 2
        assert all(t.genre == Genre.FANTASY for t in fantasy_templates)

        # 恋愛テンプレート
        romance_templates = repo.find_by_genre(Genre.ROMANCE)
        assert len(romance_templates) == 1
        assert romance_templates[0].genre == Genre.ROMANCE

        # テンプレートが存在しないジャンル
        sf_templates = repo.find_by_genre(Genre.SCIFI)
        assert sf_templates == []

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_find_all_signature(self) -> None:
        """find_allメソッドのシグネチャ確認"""

        class MockTemplateRepo(ProjectTemplateRepository):
            def find_by_id(self, _template_id: str) -> ProjectTemplate | None:
                return None

            def find_by_genre(self, _genre: Genre) -> list[ProjectTemplate]:
                return []

            def find_all(self) -> list[ProjectTemplate]:
                return [
                    ProjectTemplate(
                        template_id="template1",
                        name="テンプレート1",
                        description="説明1",
                        genre=Genre.FANTASY,
                        structure={},
                        metadata={},
                    ),
                    ProjectTemplate(
                        template_id="template2",
                        name="テンプレート2",
                        description="説明2",
                        genre=Genre.ROMANCE,
                        structure={},
                        metadata={},
                    ),
                ]

            def save(self, template: ProjectTemplate) -> None:
                pass

            def delete(self, template_id: str) -> None:
                pass

        repo = MockTemplateRepo()
        result = repo.find_all()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(t, ProjectTemplate) for t in result)

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_save_signature(self) -> None:
        """saveメソッドのシグネチャ確認"""

        class MockTemplateRepo(ProjectTemplateRepository):
            def __init__(self) -> None:
                self.templates = {}

            def find_by_id(self, template_id: str) -> ProjectTemplate | None:
                return self.templates.get(template_id)

            def find_by_genre(self, _genre: Genre) -> list[ProjectTemplate]:
                return []

            def find_all(self) -> list[ProjectTemplate]:
                return list(self.templates.values())

            def save(self, template: ProjectTemplate) -> None:
                self.templates[template.template_id] = template

            def delete(self, template_id: str) -> None:
                pass

        repo = MockTemplateRepo()
        template = ProjectTemplate(
            template_id="new-template",
            name="新規テンプレート",
            description="新しいテンプレート",
            genre=Genre.MYSTERY,
            structure={"chapters": 15},
            metadata={"created_at": "2025-01-23"},
        )

        # 保存前は存在しない
        assert repo.find_by_id("new-template") is None

        # 保存
        repo.save(template)

        # 保存後は取得可能
        saved = repo.find_by_id("new-template")
        assert saved is not None
        assert saved.name == "新規テンプレート"

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_TEMPLATE_REP")
    def test_project_template_repository_delete_signature(self) -> None:
        """deleteメソッドのシグネチャ確認"""

        class MockTemplateRepo(ProjectTemplateRepository):
            def __init__(self) -> None:
                self.templates = {
                    "template1": ProjectTemplate(
                        template_id="template1",
                        name="テンプレート1",
                        description="説明",
                        genre=Genre.FANTASY,
                        structure={},
                        metadata={},
                    )
                }

            def find_by_id(self, template_id: str) -> ProjectTemplate | None:
                return self.templates.get(template_id)

            def find_by_genre(self, _genre: Genre) -> list[ProjectTemplate]:
                return []

            def find_all(self) -> list[ProjectTemplate]:
                return list(self.templates.values())

            def save(self, template: ProjectTemplate) -> None:
                pass

            def delete(self, template_id: str) -> None:
                self.templates.pop(template_id, None)

        repo = MockTemplateRepo()

        # 削除前は存在
        assert repo.find_by_id("template1") is not None

        # 削除
        repo.delete("template1")

        # 削除後は存在しない
        assert repo.find_by_id("template1") is None

        # 存在しないIDの削除も例外を投げない
        repo.delete("nonexistent")  # 例外が発生しないことを確認


class TestProjectInitializationRepository:
    """ProjectInitializationRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_is_abstract(self) -> None:
        """ProjectInitializationRepositoryが抽象クラスであることを確認"""
        assert issubclass(ProjectInitializationRepository, ABC)

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_abstract_methods(self) -> None:
        """ProjectInitializationRepositoryの抽象メソッド確認"""
        abstract_methods = ProjectInitializationRepository.__abstractmethods__
        expected_methods = {
            "find_by_id",
            "find_by_project_name",
            "save",
            "find_recent_initializations",
            "count_by_genre",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_find_by_id_signature(self) -> None:
        """find_by_idメソッドのシグネチャ確認"""

        class MockInitRepo(ProjectInitializationRepository):
            def find_by_id(self, _initialization_id: str) -> ProjectInitialization | None:
                if _initialization_id == "init-001":
                    config = InitializationConfig(
                        genre=Genre.FANTASY,
                        writing_style=WritingStyle.LIGHT,
                        update_frequency=UpdateFrequency.WEEKLY,
                        _project_name="ファンタジープロジェクト",
                        author_name="テスト作者",
                    )

                    return ProjectInitialization(
                        _initialization_id="init-001", config=config, created_at=project_now().datetime
                    )

                return None

            def find_by_project_name(self, _project_name: str) -> ProjectInitialization | None:
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                pass

            def find_recent_initializations(self, _limit: int = 10) -> list[ProjectInitialization]:
                return []

            def count_by_genre(self, _genre: Genre) -> int:
                return 0

        repo = MockInitRepo()

        # 存在する初期化
        result = repo.find_by_id("init-001")
        assert isinstance(result, ProjectInitialization)
        assert result.initialization_id == "init-001"
        assert result.config.genre == Genre.FANTASY

        # 存在しない初期化
        result_none = repo.find_by_id("nonexistent")
        assert result_none is None

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_find_by_project_name_signature(self) -> None:
        """find_by_project_nameメソッドのシグネチャ確認"""

        class MockInitRepo(ProjectInitializationRepository):
            def __init__(self) -> None:
                config = InitializationConfig(
                    genre=Genre.ROMANCE,
                    writing_style=WritingStyle.SERIOUS,
                    update_frequency=UpdateFrequency.DAILY,
                    _project_name="恋愛小説プロジェクト",
                    author_name="作者名",
                )

                self.project_init = ProjectInitialization(
                    initialization_id="init-002", config=config, created_at=project_now().datetime
                )

            def find_by_id(self, _initialization_id: str) -> ProjectInitialization | None:
                return None

            def find_by_project_name(self, project_name: str) -> ProjectInitialization | None:
                if project_name == "恋愛小説プロジェクト":
                    return self.project_init
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                pass

            def find_recent_initializations(self, _limit: int = 10) -> list[ProjectInitialization]:
                return []

            def count_by_genre(self, _genre: Genre) -> int:
                return 0

        repo = MockInitRepo()

        # 存在するプロジェクト名
        result = repo.find_by_project_name("恋愛小説プロジェクト")
        assert isinstance(result, ProjectInitialization)
        assert result.config.project_name == "恋愛小説プロジェクト"
        assert result.config.genre == Genre.ROMANCE

        # 存在しないプロジェクト名
        result_none = repo.find_by_project_name("存在しないプロジェクト")
        assert result_none is None

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_save_signature(self) -> None:
        """saveメソッドのシグネチャ確認"""

        class MockInitRepo(ProjectInitializationRepository):
            def __init__(self) -> None:
                self.initializations = {}

            def find_by_id(self, initialization_id: str) -> ProjectInitialization | None:
                return self.initializations.get(initialization_id)

            def find_by_project_name(self, project_name: str) -> ProjectInitialization | None:
                for init in self.initializations.values():
                    if init.config.project_name == project_name:
                        return init
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                self.initializations[initialization.initialization_id] = initialization

            def find_recent_initializations(self, _limit: int = 10) -> list[ProjectInitialization]:
                return []

            def count_by_genre(self, _genre: Genre) -> int:
                return 0

        repo = MockInitRepo()

        config = InitializationConfig(
            genre=Genre.SCIFI,
            writing_style=WritingStyle.COMICAL,
            update_frequency=UpdateFrequency.MONTHLY,
            project_name="SF小説",
            author_name="SF作家",
        )

        initialization = ProjectInitialization(
            initialization_id="init-003", config=config, created_at=project_now().datetime
        )

        # 保存前は存在しない
        assert repo.find_by_id("init-003") is None

        # 保存
        repo.save(initialization)

        # 保存後は取得可能
        saved = repo.find_by_id("init-003")
        assert saved is not None
        assert saved.config.project_name == "SF小説"

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_find_recent_initializations_signature(self) -> None:
        """find_recent_initializationsメソッドのシグネチャ確認"""

        class MockInitRepo(ProjectInitializationRepository):
            def __init__(self) -> None:
                self.initializations = []
                for i in range(15):
                    config = InitializationConfig(
                        genre=Genre.FANTASY,
                        writing_style=WritingStyle.LIGHT,
                        update_frequency=UpdateFrequency.WEEKLY,
                        project_name=f"プロジェクト{i}",
                        author_name="作者",
                    )

                    init = ProjectInitialization(
                        initialization_id=f"init-{i:03d}", config=config, created_at=project_now().datetime
                    )

                    self.initializations.append(init)

            def find_by_id(self, _initialization_id: str) -> ProjectInitialization | None:
                return None

            def find_by_project_name(self, _project_name: str) -> ProjectInitialization | None:
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                pass

            def find_recent_initializations(self, _limit: int = 10) -> list[ProjectInitialization]:
                # 最新のものから返す(逆順)
                return self.initializations[-_limit:][::-1]

            def count_by_genre(self, _genre: Genre) -> int:
                return 0

        repo = MockInitRepo()

        # デフォルトlimit
        recent = repo.find_recent_initializations()
        assert isinstance(recent, list)
        assert len(recent) == 10
        assert all(isinstance(init, ProjectInitialization) for init in recent)

        # カスタムlimit
        recent_5 = repo.find_recent_initializations(limit=5)
        assert len(recent_5) == 5

        # 大きなlimit
        recent_20 = repo.find_recent_initializations(limit=20)
        assert len(recent_20) == 15  # 実際のデータ数まで

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-PROJECT_INITIALIZATI")
    def test_project_initialization_repository_count_by_genre_signature(self) -> None:
        """count_by_genreメソッドのシグネチャ確認"""

        class MockInitRepo(ProjectInitializationRepository):
            def __init__(self) -> None:
                self.genre_counts = {
                    Genre.FANTASY: 25,
                    Genre.ROMANCE: 15,
                    Genre.MYSTERY: 10,
                    Genre.SCIFI: 8,
                    Genre.HORROR: 3,
                    Genre.LITERARY: 5,
                }

            def find_by_id(self, _initialization_id: str) -> ProjectInitialization | None:
                return None

            def find_by_project_name(self, _project_name: str) -> ProjectInitialization | None:
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                pass

            def find_recent_initializations(self, _limit: int = 10) -> list[ProjectInitialization]:
                return []

            def count_by_genre(self, genre: Genre) -> int:
                return self.genre_counts.get(genre, 0)

        repo = MockInitRepo()

        # 各ジャンルのカウント
        assert repo.count_by_genre(Genre.FANTASY) == 25
        assert repo.count_by_genre(Genre.ROMANCE) == 15
        assert repo.count_by_genre(Genre.MYSTERY) == 10

        # データがないジャンル
        assert repo.count_by_genre(Genre.OTHER) == 0


class TestRepositoryImplementationExample:
    """リポジトリ実装例のテスト"""

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-IN_MEMORY_PROJECT_TE")
    def test_in_memory_project_template_repository(self) -> None:
        """インメモリProjectTemplateRepository実装例"""

        class InMemoryProjectTemplateRepo(ProjectTemplateRepository):
            def __init__(self) -> None:
                self.templates = {}
                self.next_id = 1

            def find_by_id(self, template_id: str) -> ProjectTemplate | None:
                return self.templates.get(template_id)

            def find_by_genre(self, genre: Genre) -> list[ProjectTemplate]:
                return [t for t in self.templates.values() if t.genre == genre]

            def find_all(self) -> list[ProjectTemplate]:
                return list(self.templates.values())

            def save(self, template: ProjectTemplate) -> None:
                # IDが設定されていない場合は自動採番
                if not template.template_id:
                    template.template_id = f"template-{self.next_id:04d}"
                    self.next_id += 1
                self.templates[template.template_id] = template

            def delete(self, template_id: str) -> None:
                self.templates.pop(template_id, None)

        repo = InMemoryProjectTemplateRepo()

        # テンプレートの作成と保存
        template1 = ProjectTemplate(
            template_id="",  # 自動採番される
            name="基本ファンタジー",
            description="初心者向けファンタジーテンプレート",
            genre=Genre.FANTASY,
            structure={"total_chapters": 20, "episodes_per_chapter": 5, "words_per_episode": 3000},
            metadata={"difficulty": "beginner", "tags": ["fantasy", "beginner", "template"]},
        )

        repo.save(template1)
        assert template1.template_id == "template-0001"

        # ジャンル別検索
        fantasy_templates = repo.find_by_genre(Genre.FANTASY)
        assert len(fantasy_templates) == 1
        assert fantasy_templates[0].name == "基本ファンタジー"

        # 複数テンプレートの管理
        template2 = ProjectTemplate(
            template_id="romance-001",
            name="恋愛小説テンプレート",
            description="恋愛小説用",
            genre=Genre.ROMANCE,
            structure={},
            metadata={},
        )

        repo.save(template2)

        # 全件取得
        all_templates = repo.find_all()
        assert len(all_templates) == 2

        # 削除
        repo.delete("template-0001")
        assert repo.find_by_id("template-0001") is None
        assert len(repo.find_all()) == 1

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-IN_MEMORY_PROJECT_IN")
    def test_in_memory_project_initialization_repository(self) -> None:
        """インメモリProjectInitializationRepository実装例"""

        class InMemoryProjectInitRepo(ProjectInitializationRepository):
            def __init__(self) -> None:
                self.initializations = {}
                self.project_name_index = {}  # プロジェクト名での高速検索用
                self.creation_order = []  # 作成順序を保持

            def find_by_id(self, initialization_id: str) -> ProjectInitialization | None:
                return self.initializations.get(initialization_id)

            def find_by_project_name(self, project_name: str) -> ProjectInitialization | None:
                init_id = self.project_name_index.get(project_name)
                if init_id:
                    return self.initializations.get(init_id)
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                init_id = initialization.initialization_id
                project_name = initialization.config.project_name

                # 既存のプロジェクト名の場合は更新
                if project_name in self.project_name_index:
                    old_id = self.project_name_index[project_name]
                    if old_id != init_id and old_id in self.creation_order:
                        self.creation_order.remove(old_id)

                self.initializations[init_id] = initialization
                self.project_name_index[project_name] = init_id

                if init_id not in self.creation_order:
                    self.creation_order.append(init_id)

            def find_recent_initializations(self, limit: int = 10) -> list[ProjectInitialization]:
                # 最新のものから返す
                recent_ids = self.creation_order[-limit:][::-1]
                return [self.initializations[init_id] for init_id in recent_ids if init_id in self.initializations]

            def count_by_genre(self, genre: Genre) -> int:
                count = 0
                for init in self.initializations.values():
                    if init.config.genre == genre:
                        count += 1
                return count

        repo = InMemoryProjectInitRepo()

        # 複数の初期化を作成
        for i in range(5):
            config = InitializationConfig(
                genre=Genre.FANTASY if i % 2 == 0 else Genre.ROMANCE,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name=f"プロジェクト{i}",
                author_name="テスト作者",
            )

            init = ProjectInitialization(
                initialization_id=f"init-{i:03d}", config=config, created_at=project_now().datetime
            )
            repo.save(init)

        # プロジェクト名での検索
        found = repo.find_by_project_name("プロジェクト2")
        assert found is not None
        assert found.initialization_id == "init-002"

        # 最近の初期化取得
        recent = repo.find_recent_initializations(limit=3)
        assert len(recent) == 3
        assert recent[0].initialization_id == "init-004"  # 最新
        assert recent[1].initialization_id == "init-003"
        assert recent[2].initialization_id == "init-002"

        # ジャンル別カウント
        assert repo.count_by_genre(Genre.FANTASY) == 3  # 0, 2, 4
        assert repo.count_by_genre(Genre.ROMANCE) == 2  # 1, 3
        assert repo.count_by_genre(Genre.MYSTERY) == 0

        # プロジェクト名の更新
        config_updated = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.DAILY,
            project_name="プロジェクト2",  # 既存のプロジェクト名
            author_name="更新された作者",
        )

        init_updated = ProjectInitialization(
            initialization_id="init-new", config=config_updated, created_at=project_now().datetime
        )

        repo.save(init_updated)

        # 更新後の確認
        found_updated = repo.find_by_project_name("プロジェクト2")
        assert found_updated.initialization_id == "init-new"
        assert found_updated.config.writing_style == WritingStyle.SERIOUS


class TestRepositoryIntegration:
    """初期化リポジトリ統合テスト"""

    @pytest.mark.spec("SPEC-INITIALIZATION_REPOSITORIES-TEMPLATE_AND_INITIAL")
    def test_template_and_initialization_workflow(self) -> None:
        """テンプレートと初期化の完全なワークフロー"""

        class MockTemplateRepo(ProjectTemplateRepository):
            def __init__(self) -> None:
                self.templates = {
                    "fantasy-standard": ProjectTemplate(
                        template_id="fantasy-standard",
                        name="標準ファンタジー",
                        description="標準的なファンタジー小説構成",
                        genre=Genre.FANTASY,
                        structure={
                            "chapters": 25,
                            "episodes_per_chapter": 4,
                            "words_per_episode": 3000,
                            "total_words": 300000,
                        },
                        metadata={"recommended_update": "weekly", "difficulty": "intermediate"},
                    )
                }

            def find_by_id(self, template_id: str) -> ProjectTemplate | None:
                return self.templates.get(template_id)

            def find_by_genre(self, genre: Genre) -> list[ProjectTemplate]:
                return [t for t in self.templates.values() if t.genre == genre]

            def find_all(self) -> list[ProjectTemplate]:
                return list(self.templates.values())

            def save(self, template: ProjectTemplate) -> None:
                self.templates[template.template_id] = template

            def delete(self, template_id: str) -> None:
                self.templates.pop(template_id, None)

        class MockInitRepo(ProjectInitializationRepository):
            def __init__(self) -> None:
                self.initializations = {}

            def find_by_id(self, initialization_id: str) -> ProjectInitialization | None:
                return self.initializations.get(initialization_id)

            def find_by_project_name(self, project_name: str) -> ProjectInitialization | None:
                for init in self.initializations.values():
                    if init.config.project_name == project_name:
                        return init
                return None

            def save(self, initialization: ProjectInitialization) -> None:
                self.initializations[initialization.initialization_id] = initialization

            def find_recent_initializations(self, limit: int = 10) -> list[ProjectInitialization]:
                return list(self.initializations.values())[-limit:][::-1]

            def count_by_genre(self, genre: Genre) -> int:
                return sum(1 for init in self.initializations.values() if init.config.genre == genre)

        # リポジトリ作成
        template_repo = MockTemplateRepo()
        init_repo = MockInitRepo()

        # 1. テンプレートを選択
        fantasy_templates = template_repo.find_by_genre(Genre.FANTASY)
        assert len(fantasy_templates) == 1
        selected_template = fantasy_templates[0]

        # 2. テンプレートに基づいて初期化設定を作成
        config = InitializationConfig(
            genre=selected_template.genre,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,  # テンプレートの推奨に従う
            project_name="異世界転生の魔法使い",
            author_name="ファンタジー作家",
            template_id=selected_template.template_id,  # テンプレートIDを保持
            additional_settings={
                "based_on_template": selected_template.template_id,
                "template_structure": selected_template.structure,
            },
        )

        # 3. プロジェクト初期化を作成
        initialization = ProjectInitialization(
            initialization_id="init-001", config=config, created_at=project_now().datetime
        )

        initialization.template_applied(selected_template)
        initialization.start()

        # 4. 初期化を保存
        init_repo.save(initialization)

        # 5. 保存された初期化を確認
        saved_init = init_repo.find_by_project_name("異世界転生の魔法使い")
        assert saved_init is not None
        assert saved_init.status == InitializationStatus.IN_PROGRESS
        assert saved_init.config.genre == Genre.FANTASY

        # 6. ジャンル統計を確認
        fantasy_count = init_repo.count_by_genre(Genre.FANTASY)
        assert fantasy_count == 1

        # 7. 初期化を完了
        saved_init.complete()
        init_repo.save(saved_init)

        # 8. 完了状態を確認
        completed_init = init_repo.find_by_id("init-001")
        assert completed_init.status == InitializationStatus.COMPLETED
        assert completed_init.completion_rate == 100.0
