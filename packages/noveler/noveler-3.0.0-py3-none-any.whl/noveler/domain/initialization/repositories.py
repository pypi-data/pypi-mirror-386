"""プロジェクト初期化ドメイン - リポジトリインターフェース"""

from abc import ABC, abstractmethod
from functools import wraps
import inspect

from noveler.domain.initialization.entities import ProjectInitialization, ProjectTemplate


class ProjectTemplateRepository(ABC):
    """プロジェクトテンプレートリポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    @abstractmethod
    def find_by_id(self, template_id: str) -> ProjectTemplate | None:
        """テンプレートIDで検索"""

    @abstractmethod
    def find_by_genre(self, genre: str) -> list[ProjectTemplate]:
        """ジャンルでテンプレート検索"""

    @abstractmethod
    def find_all(self) -> list[ProjectTemplate]:
        """全テンプレート取得"""

    @abstractmethod
    def save(self, template: ProjectTemplate) -> None:
        """テンプレート保存"""

    @abstractmethod
    def delete(self, template_id: str) -> None:
        """テンプレート削除"""


class ProjectInitializationRepository(ABC):
    """プロジェクト初期化リポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    @abstractmethod
    def find_by_id(self, initialization_id: str) -> ProjectInitialization | None:
        """初期化IDで検索"""

    @abstractmethod
    def find_by_project_name(self, project_name: str) -> ProjectInitialization | None:
        """プロジェクト名で検索"""

    @abstractmethod
    def save(self, initialization: ProjectInitialization) -> None:
        """初期化情報保存"""

    @abstractmethod
    def find_recent_initializations(self, limit: int) -> list[ProjectInitialization]:
        """最近の初期化履歴取得"""

    @abstractmethod
    def count_by_genre(self, genre: str) -> int:
        """ジャンル別初期化数カウント"""

    def __init_subclass__(cls, **kwargs) -> None:  # pragma: no cover - 登録時の調整
        super().__init_subclass__(**kwargs)

        method = cls.__dict__.get("find_recent_initializations")
        if method and callable(method):
            sig = inspect.signature(method)
            params = sig.parameters
            if "limit" not in params:
                target_param = None
                if "_limit" in params:
                    target_param = "_limit"
                else:
                    for name in params:
                        if name != "self":
                            target_param = name
                            break

                if target_param:

                    @wraps(method)
                    def wrapper(self, *args, **kwargs):
                        if "limit" in kwargs and "limit" not in params:
                            kwargs = kwargs.copy()
                            kwargs[target_param] = kwargs.pop("limit")
                        return method(self, *args, **kwargs)

                    setattr(cls, "find_recent_initializations", wrapper)
