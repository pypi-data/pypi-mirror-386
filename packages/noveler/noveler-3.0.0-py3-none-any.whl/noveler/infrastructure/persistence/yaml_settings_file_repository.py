#!/usr/bin/env python3
"""YAMLベース設定ファイルリポジトリ実装

SettingsFileRepositoryインターフェースの実装
YAMLファイルから固有名詞を抽出する
"""

import re
from pathlib import Path

import yaml

from noveler.domain.repositories.settings_file_repository import SettingsFileRepository
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class YamlSettingsFileRepository(SettingsFileRepository):
    """YAML設定ファイルリポジトリ実装"""

    def __init__(self, project_root: Path | str) -> None:
        """Args:
        project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = Path(project_root)
        path_service = create_path_service(self.project_root)
        self.settings_dir = path_service.get_settings_dir()

        # 固有名詞抽出対象のYAMLキー
        self._extraction_patterns = {
            "name_keys": ["name", "names", "名前", "名称", "title", "titles", "タイトル"],
            "organization_keys": ["organization", "organizations", "組織", "団体", "company", "companies"],
            "location_keys": ["location", "locations", "場所", "地名", "place", "places"],
            "technology_keys": ["technology", "technologies", "技術", "skill", "skills", "スキル"],
            "term_keys": ["term", "terms", "用語", "word", "words", "単語"],
            "character_keys": ["character", "characters", "キャラクター", "キャラ"],
            "magic_keys": [
                "magic",
                "spell",
                "spells",
                "魔法",
                "呪文",
                "magic_types",
                "magical_items",
                "magic_items",
                "item",
                "items",
                "アイテム",
            ],
        }

        # 除外パターン(一般的すぎる語句)
        self._exclusion_patterns = {
            # 一般的な単語
            r"^(の|が|を|に|で|と|から|まで|より|など|等|他)$",
            # 数字のみ
            r"^\d+$",
            # 一般的すぎる1文字(助詞・記号など)- 日本語の人名は除外しない
            r"^[a-zA-Z0-9\u3040-\u309F]$",  # ひらがな・英数字の1文字のみ除外
            # 記号のみ
            r"^[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+$",
        }

    def extract_proper_nouns_from_file(self, file_path: Path | str) -> set[str]:
        """指定されたファイルから固有名詞を抽出

        Args:
            file_path: 抽出対象ファイルのパス

        Returns:
            Set[str]: 抽出された固有名詞のセット

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: ファイル形式が不正な場合
        """
        if not file_path.exists():
            msg = f"ファイルが存在しません: {file_path}"
            raise FileNotFoundError(msg)

        if not self.is_file_supported(file_path):
            return set()

        try:
            with Path(file_path).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return set()

            extracted_terms = set()
            self._extract_terms_recursive(data, extracted_terms)

            # 除外パターンでフィルタリング
            return self._filter_terms(extracted_terms)

        except yaml.YAMLError as e:
            msg = f"YAML解析エラー: {e}"
            raise ValueError(msg) from e
        except OSError as e:
            msg = f"ファイル読み込みエラー: {e}"
            raise FileNotFoundError(msg) from e

    def extract_all_proper_nouns(self) -> set[str]:
        """全設定ファイルから固有名詞を抽出

        Returns:
            Set[str]: 抽出された固有名詞のセット
        """
        all_terms = set()

        for file_path in self.get_supported_files():
            try:
                file_terms = self.extract_proper_nouns_from_file(file_path)
                all_terms.update(file_terms)
            except (FileNotFoundError, ValueError):
                # エラーは無視して他のファイルを処理続行
                continue

        return all_terms

    def get_supported_files(self) -> set[Path]:
        """サポートされているファイルの一覧を取得

        Returns:
            Set[Path]: サポートファイルのパスセット
        """
        if not self.settings_dir.exists():
            return set()

        supported_files = set()
        for file_path in self.settings_dir.iterdir():
            if self.is_file_supported(file_path):
                supported_files.add(file_path)

        return supported_files

    def is_file_supported(self, file_path: Path | str) -> bool:
        """ファイルがサポートされているかどうかの判定

        Args:
            file_path: 判定対象ファイルのパス

        Returns:
            bool: サポートされている場合True
        """
        if not file_path.is_file():
            return False

        # YAML拡張子チェック
        return file_path.suffix.lower() in [".yaml", ".yml"]

    def _extract_terms_recursive(self, data: object, extracted_terms: set[str]) -> None:
        """再帰的に固有名詞を抽出

        Args:
            data: 抽出対象データ
            extracted_terms: 抽出結果を格納するセット
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # キー名から固有名詞候補を判定
                if self._is_proper_noun_key(key):
                    self._extract_from_value(value, extracted_terms)
                    # カテゴリキーの場合、その子キーも固有名詞として抽出
                    if isinstance(value, dict):
                        for sub_key in value:
                            if self._is_potential_proper_noun(sub_key):
                                extracted_terms.add(sub_key)
                else:
                    # 値を再帰的に処理
                    self._extract_terms_recursive(value, extracted_terms)

        elif isinstance(data, list):
            for item in data:
                self._extract_terms_recursive(item, extracted_terms)

        elif isinstance(data, str):
            # 文字列値から直接抽出
            candidate = data.strip()
            if candidate and self._is_potential_proper_noun(candidate):
                extracted_terms.add(candidate)

    def _is_proper_noun_key(self, key: str) -> bool:
        """キーが固有名詞を含む可能性があるかどうかの判定

        Args:
            key: 判定対象キー

        Returns:
            bool: 固有名詞キーの場合True
        """
        key_lower = key.lower()

        return any(key_lower in pattern_group for pattern_group in self._extraction_patterns.values())

    def _extract_from_value(self, value: object, extracted_terms: set[str]) -> None:
        """値から固有名詞を抽出

        Args:
            value: 抽出対象値
            extracted_terms: 抽出結果を格納するセット
        """
        if isinstance(value, str):
            candidate = value.strip()
            if candidate and self._is_potential_proper_noun(candidate):
                extracted_terms.add(candidate)

        elif isinstance(value, list):
            for item in value:
                self._extract_from_value(item, extracted_terms)

        elif isinstance(value, dict):
            # ネストした辞書から再帰的に抽出
            self._extract_terms_recursive(value, extracted_terms)

    def _is_potential_proper_noun(self, text: str) -> bool:
        """テキストが固有名詞の可能性があるかどうかの判定

        Args:
            text: 判定対象テキスト

        Returns:
            bool: 固有名詞の可能性がある場合True
        """
        # 最小長チェック(ただし日本語1文字は人名として有効)
        if len(text) < 1:
            return False
        if len(text) == 1 and not re.match(r"[\u30A0-\u30FF\u4E00-\u9FAF]", text):
            # 1文字でカタカナ・漢字以外は除外
            return False

        # 除外パターンチェック
        for pattern in self._exclusion_patterns:
            if re.match(pattern, text):
                return False

        # 日本語・英数字・ハイフンを含む文字列を対象
        return bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\w\-]", text))

    def _filter_terms(self, terms: set[str]) -> set[str]:
        """抽出された用語をフィルタリング

        Args:
            terms: フィルタリング対象用語セット

        Returns:
            Set[str]: フィルタリング後の用語セット
        """
        filtered = set()

        for term in terms:
            if self._is_potential_proper_noun(term):
                # 前後の空白・記号を除去して正規化
                normalized = re.sub(
                    r"^[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+|[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+$",
                    "",
                    term,
                )

                if normalized and (len(normalized) >= 2 or re.match(r"[\u30A0-\u30FF\u4E00-\u9FAF]", normalized)):
                    # 2文字以上、または日本語1文字(カタカナ・漢字)
                    filtered.add(normalized)

        return filtered
