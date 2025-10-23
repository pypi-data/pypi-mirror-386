#!/usr/bin/env python3
"""JSON書籍化作品リポジトリ

書籍化作品データの永続化を担当
"""

import json
from pathlib import Path
from typing import Any

from noveler.domain.ai_integration.entities.published_work import PublicationMetrics, PublishedWork, StoryStructure
from noveler.domain.ai_integration.value_objects.genre_configuration import (
    GenreConfiguration,
    MainGenre,
    SubGenre,
    TargetFormat,
)
from noveler.domain.repositories.published_work_repository import PublishedWorkRepository


class JsonPublishedWorkRepository(PublishedWorkRepository):
    """JSON書籍化作品リポジトリ

    書籍化作品データのJSON形式での保存・読み込み機能を提供
    """

    def __init__(self, data_dir: Path | str, logger_service=None, console_service=None) -> None:
        """初期化

        Args:
            data_dir: データディレクトリ
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "published_works.json"
        self.sample_data_file = self.data_dir / "sample_published_works.json"

        # サンプルデータがない場合は作成
        if not self.data_file.exists() and not self.sample_data_file.exists():
            self._create_sample_data()

        self.logger_service = logger_service
        self.console_service = console_service
    def find_all(self) -> list[PublishedWork]:
        """全ての書籍化作品を取得

        Returns:
            書籍化作品のリスト
        """
        data_path = self.data_file if self.data_file.exists() else self.sample_data_file

        if not data_path.exists():
            return []

        try:
            with Path(data_path).open(encoding="utf-8") as f:
                data = json.load(f)

            return [self._dict_to_published_work(item) for item in data.get("works", [])]

        except Exception as e:
            self.console_service.print(f"警告: 公開作品データの読み込みに失敗しました: {e}")
            return []

    def find_by_genre(self, genre_config: GenreConfiguration) -> list[PublishedWork]:
        """ジャンルによる書籍化作品の検索

        Args:
            genre_config: ジャンル設定

        Returns:
            該当する書籍化作品のリスト
        """
        all_works = self.find_all()

        return [work for work in all_works if work.genre_config.similarity_score(genre_config) > 0.3]

    def find_by_success_level(self, min_success_level: str) -> list[PublishedWork]:
        """成功レベルによる書籍化作品の検索

        Args:
            min_success_level: 最低成功レベル

        Returns:
            該当する書籍化作品のリスト
        """
        all_works = self.find_all()

        level_order = ["S級", "A級", "B級", "C級"]
        min_index = level_order.index(min_success_level)

        return [work for work in all_works if level_order.index(work.get_success_level().value) <= min_index]

    def save_work(self, work: PublishedWork) -> None:
        """書籍化作品を保存

        Args:
            work: 保存する書籍化作品
        """
        all_works = self.find_all()

        # 既存の作品を更新または新規追加
        updated = False
        for i, existing_work in enumerate(all_works):
            if existing_work.work_id == work.work_id:
                all_works[i] = work
                updated = True
                break

        if not updated:
            all_works.append(work)

        # ファイルに保存
        data = {
            "works": [self._published_work_to_dict(work) for work in all_works],
            "last_updated": str(Path(__file__).stat().st_mtime),
        }

        with Path(self.data_file).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete_work(self, work_id: str) -> bool:
        """書籍化作品を削除

        Args:
            work_id: 削除する作品ID

        Returns:
            削除が成功したかどうか
        """
        all_works = self.find_all()

        for i, work in enumerate(all_works):
            if work.work_id == work_id:
                all_works.pop(i)

                # ファイルに保存
                data = {
                    "works": [self._published_work_to_dict(work) for work in all_works],
                    "last_updated": str(Path(__file__).stat().st_mtime),
                }

                with Path(self.data_file).open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得

        Returns:
            統計情報
        """
        all_works = self.find_all()

        if not all_works:
            return {
                "total_works": 0,
                "genre_distribution": {},
                "success_distribution": {},
                "avg_rating": 0.0,
                "avg_volumes": 0.0,
            }

        # ジャンル分布
        genre_distribution = {}
        for work in all_works:
            genre_key = work.genre_config.get_genre_combination()
            genre_distribution[genre_key] = genre_distribution.get(genre_key, 0) + 1

        # 成功レベル分布
        success_distribution = {}
        for work in all_works:
            level = work.get_success_level().value
            success_distribution[level] = success_distribution.get(level, 0) + 1

        # 平均値
        avg_rating = sum(work.publication_metrics.ratings for work in all_works) / len(all_works)
        avg_volumes = sum(work.publication_metrics.volumes_published for work in all_works) / len(all_works)

        return {
            "total_works": len(all_works),
            "genre_distribution": genre_distribution,
            "success_distribution": success_distribution,
            "avg_rating": avg_rating,
            "avg_volumes": avg_volumes,
        }

    def _create_sample_data(self) -> None:
        """サンプルデータを作成"""
        sample_works = [
            {
                "work_id": "sample_001",
                "title": "転生したらスライムだった件",
                "author": "伏瀬",
                "genre": {
                    "main": "ファンタジー",
                    "sub": ["異世界", "転生"],
                    "target": "ライトノベル",
                },
                "publication_metrics": {
                    "publication_year": 2014,
                    "volumes_published": 21,
                    "total_pv": 5000000,
                    "bookmarks": 200000,
                    "ratings": 4.5,
                    "reviews_count": 8000,
                },
                "story_structure": {
                    "first_turning_point": 2,
                    "romance_introduction": 0,
                    "mid_boss_battle": 15,
                    "climax_point": 25,
                    "total_episodes": 30,
                },
                "success_factors": ["独自世界観", "キャラクター魅力", "コメディ要素"],
            },
            {
                "work_id": "sample_002",
                "title": "魔法科高校の劣等生",
                "author": "佐島勤",
                "genre": {
                    "main": "ファンタジー",
                    "sub": ["学園", "魔法"],
                    "target": "ライトノベル",
                },
                "publication_metrics": {
                    "publication_year": 2011,
                    "volumes_published": 32,
                    "total_pv": 8000000,
                    "bookmarks": 300000,
                    "ratings": 4.3,
                    "reviews_count": 12000,
                },
                "story_structure": {
                    "first_turning_point": 3,
                    "romance_introduction": 8,
                    "mid_boss_battle": 18,
                    "climax_point": 22,
                    "total_episodes": 25,
                },
                "success_factors": ["詳細設定", "バトル描写", "恋愛要素"],
            },
            {
                "work_id": "sample_003",
                "title": "この素晴らしい世界に祝福を!",
                "author": "暁なつめ",
                "genre": {
                    "main": "ファンタジー",
                    "sub": ["異世界", "コメディ"],
                    "target": "ライトノベル",
                },
                "publication_metrics": {
                    "publication_year": 2013,
                    "volumes_published": 17,
                    "total_pv": 3000000,
                    "bookmarks": 150000,
                    "ratings": 4.4,
                    "reviews_count": 6000,
                },
                "story_structure": {
                    "first_turning_point": 1,
                    "romance_introduction": 12,
                    "mid_boss_battle": 20,
                    "climax_point": 24,
                    "total_episodes": 28,
                },
                "success_factors": ["コメディ要素", "個性的キャラクター", "パロディ要素"],
            },
        ]

        data = {
            "works": sample_works,
            "last_updated": "2024-01-01",
            "note": "This is sample data for testing purposes",
        }

        with Path(self.sample_data_file).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _dict_to_published_work(self, data: dict[str, Any]) -> PublishedWork:
        """辞書からPublishedWorkエンティティに変換"""
        # ジャンル設定の変換
        genre_data: dict[str, Any] = data["genre"]
        genre_config: dict[str, Any] = GenreConfiguration(
            main_genre=MainGenre(genre_data["main"]),
            sub_genres=[SubGenre(sg) for sg in genre_data["sub"]],
            target_format=TargetFormat(genre_data["target"]),
        )

        # 出版メトリクスの変換
        metrics_data: dict[str, Any] = data["publication_metrics"]
        publication_metrics = PublicationMetrics(
            publication_year=metrics_data["publication_year"],
            volumes_published=metrics_data["volumes_published"],
            total_pv=metrics_data["total_pv"],
            bookmarks=metrics_data["bookmarks"],
            ratings=metrics_data["ratings"],
            reviews_count=metrics_data["reviews_count"],
        )

        # 物語構造の変換
        structure_data: dict[str, Any] = data["story_structure"]
        story_structure = StoryStructure(
            first_turning_point=structure_data["first_turning_point"],
            romance_introduction=structure_data["romance_introduction"],
            mid_boss_battle=structure_data["mid_boss_battle"],
            climax_point=structure_data["climax_point"],
            total_episodes=structure_data["total_episodes"],
        )

        return PublishedWork(
            work_id=data["work_id"],
            title=data["title"],
            author=data["author"],
            genre_config=genre_config,
            publication_metrics=publication_metrics,
            story_structure=story_structure,
            success_factors=data["success_factors"],
        )

    def _published_work_to_dict(self, work: PublishedWork) -> dict[str, Any]:
        """PublishedWorkエンティティを辞書に変換"""
        return {
            "work_id": work.work_id,
            "title": work.title,
            "author": work.author,
            "genre": {
                "main": work.genre_config.main_genre.value,
                "sub": [sg.value for sg in work.genre_config.sub_genres],
                "target": work.genre_config.target_format.value,
            },
            "publication_metrics": {
                "publication_year": work.publication_metrics.publication_year,
                "volumes_published": work.publication_metrics.volumes_published,
                "total_pv": work.publication_metrics.total_pv,
                "bookmarks": work.publication_metrics.bookmarks,
                "ratings": work.publication_metrics.ratings,
                "reviews_count": work.publication_metrics.reviews_count,
            },
            "story_structure": {
                "first_turning_point": work.story_structure.first_turning_point,
                "romance_introduction": work.story_structure.romance_introduction,
                "mid_boss_battle": work.story_structure.mid_boss_battle,
                "climax_point": work.story_structure.climax_point,
                "total_episodes": work.story_structure.total_episodes,
            },
            "success_factors": list(work.success_factors),
        }
