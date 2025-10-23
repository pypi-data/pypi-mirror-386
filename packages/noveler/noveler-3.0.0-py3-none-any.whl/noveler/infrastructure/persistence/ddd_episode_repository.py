"""Infrastructure Layer: File-based Episode Repository Implementation
ファイルベースのエピソードリポジトリ実装

DDD原則に従ったインフラストラクチャ層実装
- ドメインリポジトリインターフェースの実装
- ファイルシステムへの永続化
- 依存性逆転の原則を適用
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.writing.entities import Episode, EpisodeStatus
from noveler.domain.writing.repositories import EpisodeRepository
from noveler.domain.writing.value_objects import EpisodeNumber, EpisodeTitle, WordCount, WritingPhase

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class FileEpisodeRepository(EpisodeRepository):
    """ファイルベースのエピソードリポジトリ実装

    責務:
    - エピソードの永続化とファイルシステムからの読み込み
    - プロットファイルとの連携
    - ドメインオブジェクトとファイル形式の変換
    """

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = project_root
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        self.path_service = create_path_service(project_root)
        self.manuscripts_dir = self.path_service.get_manuscript_dir()
        self.plot_dir = self.path_service.get_plot_dir() / "章別プロット"
        self.management_dir = self.path_service.get_management_dir()

        # ディレクトリ作成
        self.manuscripts_dir.mkdir(parents=True, exist_ok=True)
        self.plot_dir.mkdir(parents=True, exist_ok=True)
        self.management_dir.mkdir(parents=True, exist_ok=True)

    def find_by_id(self, _episode_id: str) -> Episode | None:
        """IDでエピソードを取得"""
        # IDベースの検索は実装要件に応じて拡張
        # 現在はファイル名ベースでの管理のため、話数ベースの検索を推奨
        return None

    def find_by_number(self, _project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトと話数でエピソードを取得"""
        try:
            # B20準拠: PathServiceで原稿パスを一元解決
            num = episode_number.value if hasattr(episode_number, "value") else int(episode_number)
            manuscript_file = self.path_service.get_manuscript_path(num)
            
            if not manuscript_file.exists():
                # タイトル付きファイル名のパターン探索
                pattern = f"第{num:03d}話*.md"
                matching_files = list(self.manuscripts_dir.glob(pattern))
                if matching_files:
                    manuscript_file = matching_files[0]
                else:
                    # フォールバック: 既存の命名ゆらぎに備えてパターン探索
                    pattern = f"第{num:03d}話_*.md"
                    matching_files = list(self.manuscripts_dir.glob(pattern))
                    if not matching_files:
                        return None
                    manuscript_file = matching_files[0]

            # プロット情報を取得
            plot_info = self._find_plot_info_for_episode(str(episode_number.value).zfill(3))

            # ファイルからエピソードを構築
            return self._build_episode_from_file(manuscript_file, plot_info)

        except Exception:
            return None

    def find_by_status(self, _project_id: str, status: EpisodeStatus) -> list[Episode]:
        """ステータス別にエピソードを取得"""
        episodes = self.find_all_by_project(_project_id)
        return [ep for ep in episodes if ep.status == status]

    def find_next_unwritten(self, project_id: str) -> Episode | None:
        """次の未執筆エピソードを取得"""
        plot_data: dict[str, Any] = self._load_all_plot_data()
        existing_episodes = self._get_existing_episode_numbers()

        for episode_info in sorted(plot_data, key=lambda x: int(x.get("episode_number", "999"))):
            episode_num = episode_info.get("episode_number", "")
            status = episode_info.get("status", "未執筆")

            if status == "未執筆" and episode_num not in existing_episodes:
                # プロット情報からエピソードオブジェクトを作成
                return self._create_episode_from_plot_info(project_id, episode_info)

        return None

    def find_all_by_project(self, _project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得"""
        episodes = []

        # マニュスクリプトファイルを全て取得
        for manuscript_file in self.manuscripts_dir.glob("第*話_*.md"):
            try:
                # ファイル名から話数を抽出
                match = re.search(r"第(\d+)話", manuscript_file.name)
                if match:
                    episode_num = match.group(1)
                    plot_info = self._find_plot_info_for_episode(episode_num)
                    episode = self._build_episode_from_file(manuscript_file, plot_info)
                    if episode:
                        episodes.append(episode)
            except Exception:
                continue

        return sorted(episodes, key=lambda ep: ep.episode_number.value)

    def find_by_phase(self, project_id: str, phase: WritingPhase) -> list[Episode]:
        """フェーズ別にエピソードを取得"""
        episodes = self.find_all_by_project(project_id)
        return [ep for ep in episodes if ep.phase == phase]

    def find_by_publication_status(self, project_id: str, status: EpisodeStatus) -> list[Episode]:
        """公開ステータス別にエピソードを取得"""
        episodes = self.find_all_by_project(project_id)
        return [ep for ep in episodes if ep.publication_status == status]

    def find_latest_episode(self, project_id: str) -> Episode | None:
        """最新のエピソードを取得"""
        episodes = self.find_all_by_project(project_id)
        if not episodes:
            return None
        return max(episodes, key=lambda ep: ep.episode_number.value)

    def save(self, episode: Episode) -> Episode:
        """エピソードを保存し、保存後のエンティティを返却"""
        try:
            # B20準拠: PathServiceで原稿パスを一元解決
            num = episode.episode_number.value if hasattr(episode.episode_number, "value") else int(episode.episode_number)
            
            # タイトルがある場合はファイル名に含める
            episodes_dir = self.path_service.get_manuscript_dir()
            episodes_dir.mkdir(parents=True, exist_ok=True)
            
            if episode.title and episode.title.value != "無題":
                title_value = episode.title.value if hasattr(episode.title, "value") else str(episode.title)
                file_path = episodes_dir / f"第{num:03d}話_{title_value}.md"
            else:
                file_path = self.path_service.get_manuscript_path(num)

            # 内容をファイルに保存
            file_path.write_text(episode.content, encoding="utf-8")

            # 更新日時を設定
            episode.updated_at = project_now().datetime

            return episode

        except Exception as e:
            msg = f"エピソードの保存に失敗しました: {e!s}"
            raise RuntimeError(msg) from e

    def create_from_plot(self, project_id: str, plot_info: dict[str, str | int]) -> Episode:
        """プロット情報からエピソードを作成"""
        return self._create_episode_from_plot_info(project_id, plot_info)

    def update_plot_status(self, _project_id: str, episode_number: int, status: str) -> bool:
        """プロットファイルのステータスを更新"""
        try:
            if not self.plot_dir.exists():
                return False

            for yaml_file in self.plot_dir.glob("*.yaml"):
                with Path(yaml_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data or "episodes" not in data:
                    continue

                # 該当エピソードを探して更新
                for episode in data["episodes"]:
                    if episode.get("episode_number") == episode_number:
                        episode["status"] = status

                        # ファイルに書き戻し
                        with Path(yaml_file).open("w", encoding="utf-8") as f:
                            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                        return True

            return False
        except Exception:
            return False

    def delete(self, _episode_id: str) -> None:
        """エピソードを削除"""
        # 実装要件に応じて拡張
        # 現在はファイルベースのため、ファイル削除を実装

    def _build_episode_from_file(self, manuscript_file: Path, plot_info: dict[str, str | int] | None) -> Episode | None:
        """ファイルからエピソードオブジェクトを構築"""
        try:
            # ファイル名から話数とタイトルを抽出
            match = re.search(r"第(\d+)話_(.+)\.md", manuscript_file.name)
            if not match:
                return None

            episode_num = int(match.group(1))
            title_text = match.group(2)

            # ファイル内容を読み込み
            content = manuscript_file.read_text(encoding="utf-8")

            # ステータス判定
            status = self._determine_episode_status(content, plot_info)

            # エピソード作成
            return Episode(
                id=f"ep_{episode_num:03d}",
                project_id="",  # プロジェクトIDは上位レイヤーで設定
                episode_number=EpisodeNumber(episode_num),
                title=EpisodeTitle(title_text),
                content=content,
                word_count=self._calculate_word_count(content),
                status=status,
                created_at=datetime.fromtimestamp(manuscript_file.stat().st_ctime, tz=timezone.utc),
                updated_at=datetime.fromtimestamp(manuscript_file.stat().st_mtime, tz=timezone.utc),
                plot_info=plot_info or {},
            )

        except Exception:
            return None

    def _determine_episode_status(self, content: str, _plot_info: dict[str, str | int] | None) -> EpisodeStatus:
        """エピソードの現在のステータスを判定"""
        # 内容の充実度で判定
        word_count = self._calculate_word_count(content).value

        if word_count == 0:
            return EpisodeStatus.UNWRITTEN
        if word_count < 1000:
            return EpisodeStatus.IN_PROGRESS
        if word_count < 2000:
            return EpisodeStatus.DRAFT_COMPLETE
        return EpisodeStatus.REVISED

    def _calculate_word_count(self, content: str) -> WordCount:
        """実際の小説部分の文字数を計算"""
        if not content:
            return WordCount(0)

        lines = content.split("\n")
        novel_lines = []

        for line in lines:
            line = line.strip()
            # メタ情報行を除外
            if line.startswith(("#", "**", "---", "- ")) or line == "":
                continue
            novel_lines.append(line)

        novel_content = "".join(novel_lines)
        return WordCount(len(novel_content))

    def _load_all_plot_data(self) -> list[dict[str, Any]]:
        """全プロットデータを読み込み"""
        plot_data: dict[str, Any] = []

        if not self.plot_dir.exists():
            return plot_data

        for yaml_file in self.plot_dir.glob("*.yaml"):
            try:
                with Path(yaml_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "episodes" in data:
                        plot_data.extend(data["episodes"])
            except Exception:
                continue

        return plot_data

    def _get_existing_episode_numbers(self) -> set:
        """既存のエピソード番号を取得"""
        existing_episodes = set()

        if not self.manuscripts_dir.exists():
            return existing_episodes

        for md_file in self.manuscripts_dir.glob("第*話_*.md"):
            match = re.search(r"第(\d+)話", md_file.name)
            if match:
                existing_episodes.add(match.group(1))

        return existing_episodes

    def _find_plot_info_for_episode(self, episode_number: int) -> dict[str, str | int] | None:
        """指定されたエピソードのプロット情報を取得"""
        plot_data: dict[str, Any] = self._load_all_plot_data()

        for episode in plot_data:
            if episode.get("episode_number") == episode_number:
                return episode

        return None

    def _create_episode_from_plot_info(self, project_id: str, plot_info: dict[str, str | int]) -> Episode:
        """プロット情報からエピソードオブジェクトを作成"""
        episode_num = int(plot_info["episode_number"])
        title_text = self._extract_clean_title(plot_info.get("title", ""))
        initial_content = self._generate_initial_content(plot_info)

        return Episode(
            id=f"ep_{episode_num:03d}",
            project_id=project_id,
            episode_number=EpisodeNumber(episode_num),
            title=EpisodeTitle(title_text),
            content=initial_content,
            word_count=WordCount(0),
            status=EpisodeStatus.UNWRITTEN,
            plot_info=plot_info.copy(),
        )

    def _extract_clean_title(self, title_text: str) -> str:
        """タイトルテキストから純粋なタイトル部分を抽出"""

        patterns = [
            r"第\d+話[ \s]+(.+)",
            r"第\d+話[::_\-\s]+(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, title_text)
            if match:
                return match.group(1).strip()

        return title_text.strip()

    def _generate_initial_content(self, plot_info: dict[str, Any]) -> str:
        """初期コンテンツを生成"""
        episode_num = plot_info.get("episode_number", "001")
        title = self._extract_clean_title(plot_info.get("title", ""))
        summary = plot_info.get("summary", "")
        word_target = plot_info.get("word_count_target", 3000)

        return f"""# 第{episode_num}話 {title}

## あらすじ
{summary}

**目標文字数:** {word_target}文字

---

## 導入部


## 展開部


## 転換部


## 結末部


---

**執筆メモ:**
-
"""
