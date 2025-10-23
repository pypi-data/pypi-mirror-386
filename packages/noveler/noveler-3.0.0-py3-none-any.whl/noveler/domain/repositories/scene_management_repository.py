#!/usr/bin/env python3
"""シーン管理リポジトリインターフェース

シーン管理のリポジトリ抽象定義。
DDD原則に基づくドメイン層のインターフェース分離。
"""

from abc import ABC


class SceneManagementRepository(ABC):
    """シーン管理リポジトリインターフェース

    Note: このインターフェースは未実装のため削除対象
    現在の実装ではYamlSceneManagementRepositoryが直接使用されており、
    抽象化レイヤーは不要と判断される。
    """

    # インターフェースとして保持し、未実装メソッドは削除
