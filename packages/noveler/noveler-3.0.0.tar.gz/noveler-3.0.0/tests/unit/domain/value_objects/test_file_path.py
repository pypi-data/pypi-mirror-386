"""FilePath値オブジェクトのテスト"""

from pathlib import Path

import pytest

from noveler.domain.value_objects.file_path import FilePath


pytestmark = pytest.mark.vo_smoke


@pytest.mark.spec("SPEC-API-001")
class TestFilePath:
    """FilePath値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-API-001")
    def test_valid_path_creation(self) -> None:
        """有効なパスで作成できること"""
        # 相対パス
        path1 = FilePath("test.txt")
        assert str(path1) == "test.txt"

        # 絶対パス(Unix)
        path2 = FilePath("/home/user/test.txt")
        assert str(path2) == "/home/user/test.txt"

        # Windows形式のパス
        path3 = FilePath("C:\\Users\\test.txt")
        assert str(path3) == "C:\\Users\\test.txt"

        # 階層のあるパス
        path4 = FilePath("path/to/file.txt")
        assert str(path4) == "path/to/file.txt"

    @pytest.mark.spec("SPEC-API-001")
    def test_invalid_path_rejection(self) -> None:
        """無効なパスを拒否すること"""
        # 空文字列
        with pytest.raises(ValueError, match="File path cannot be empty"):
            FilePath("")

        # None
        with pytest.raises(TypeError, match=".*"):
            FilePath(None)

        # 空白のみ
        with pytest.raises(ValueError, match="File path cannot be empty"):
            FilePath("   ")

    @pytest.mark.spec("SPEC-API-001")
    def test_exists(self, tmp_path: object) -> None:
        """ファイルの存在確認が正しく動作すること"""
        # 存在するファイル
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        path1 = FilePath(str(test_file))
        assert path1.exists() is True

        # 存在しないファイル
        path2 = FilePath(str(tmp_path / "nonexistent.txt"))
        assert path2.exists() is False

        # 存在するディレクトリ
        path3 = FilePath(str(tmp_path))
        assert path3.exists() is True

    @pytest.mark.spec("SPEC-API-001")
    def test_is_absolute(self) -> None:
        """絶対パスの判定が正しく行われること"""
        # 相対パス
        path1 = FilePath("test.txt")
        assert path1.is_absolute() is False

        path2 = FilePath("path/to/file.txt")
        assert path2.is_absolute() is False

        # 絶対パス(Unix)
        path3 = FilePath("/home/user/test.txt")
        assert path3.is_absolute() is True

        # 絶対パス(Windows - ドライブレター付き)
        FilePath("C:\\Users\\test.txt")
        # Windowsパスの判定はプラットフォーム依存
        # Unix環境では相対パスとして扱われる可能性がある

    @pytest.mark.spec("SPEC-API-001")
    def test_parent(self) -> None:
        """親ディレクトリの取得が正しく行われること"""
        # ファイルの親ディレクトリ
        path1 = FilePath("path/to/file.txt")
        parent1 = path1.parent()
        assert str(parent1) == str(Path("path/to"))

        # ルートディレクトリ
        path2 = FilePath("/")
        parent2 = path2.parent()
        assert str(parent2) == "/"

        # 深い階層
        path3 = FilePath("/home/user/documents/test.txt")
        parent3 = path3.parent()
        assert str(parent3) == "/home/user/documents"

    @pytest.mark.spec("SPEC-API-001")
    def test_equality(self) -> None:
        """等価性の判定が正しく行われること"""
        path1 = FilePath("test.txt")
        path2 = FilePath("test.txt")
        path3 = FilePath("other.txt")

        assert path1 == path2
        assert path1 != path3
        assert path1 != "test.txt"  # 文字列との比較

    @pytest.mark.spec("SPEC-API-001")
    def test_hash(self) -> None:
        """ハッシュ値が正しく生成されること"""
        path1 = FilePath("test.txt")
        path2 = FilePath("test.txt")
        path3 = FilePath("other.txt")

        # 同じパスは同じハッシュ値
        assert hash(path1) == hash(path2)
        # 異なるパスは異なるハッシュ値(高確率で)
        assert hash(path1) != hash(path3)

        # 辞書のキーとして使用可能
        file_dict = {path1: "content"}
        assert file_dict[path2] == "content"

    @pytest.mark.spec("SPEC-API-001")
    def test_immutability(self) -> None:
        """値オブジェクトが不変であること"""
        path = FilePath("test.txt")

        # 属性の変更を試みる
        with pytest.raises(AttributeError, match=".*"):
            path.path = "new_path.txt"

        # 元の値が変わっていないことを確認
        assert str(path) == "test.txt"

    @pytest.mark.spec("SPEC-API-001")
    def test_with_suffix(self) -> None:
        """拡張子の追加が正しく行われること"""
        # 拡張子なしのファイル
        path1 = FilePath("test")
        new_path1 = path1.with_suffix(".txt")
        assert str(new_path1) == "test.txt"

        # 既に拡張子があるファイル
        path2 = FilePath("test.txt")
        new_path2 = path2.with_suffix(".md")
        assert str(new_path2) == "test.md"

        # 複数の拡張子
        path3 = FilePath("test.tar")
        new_path3 = path3.with_suffix(".gz")
        assert str(new_path3) == "test.gz"

    @pytest.mark.spec("SPEC-API-001")
    def test_join(self) -> None:
        """パスの結合が正しく行われること"""
        # 基本的な結合
        path1 = FilePath("path/to")
        joined1 = path1.join("file.txt")
        assert str(joined1) == str(Path("path/to/file.txt"))

        # 複数要素の結合
        path2 = FilePath("/home/user")
        joined2 = path2.join("documents", "test.txt")
        assert str(joined2) == "/home/user/documents/test.txt"
