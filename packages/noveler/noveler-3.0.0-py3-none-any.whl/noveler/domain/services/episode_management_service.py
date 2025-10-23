"""TDD-driven Episode Manager
テスト駆動開発によるエピソード管理
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from noveler.domain.interfaces.i_path_service import IPathService

import yaml

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


@dataclass
class EpisodeCreationResult:
    """エピソード作成結果"""

    success: bool
    file_path: Path | None = None
    episode_number: str | None = None
    title: str | None = None
    error_message: str | None = None
    writing_record_created: bool = False


class EpisodeManager:
    """エピソード管理クラス(TDD実装)"""

    def __init__(self,project_root: Path, path_service: "IPathService") -> None:
        self._path_service = path_service
        self.project_root = project_root
        # B20準拠: Path ServiceはDI注入されたものを使用
            # path_service = self._path_service
        self.plot_dir = path_service.get_plot_dir() / "章別プロット"
        # B20準拠: Path ServiceはDI注入されたものを使用
            # path_service = self._path_service
        self.manuscript_dir = path_service.get_manuscript_dir()

    def find_next_unwritten_episode(self) -> str | None:
        """未執筆の次のエピソードを見つける"""
        try:
            plot_data: dict[str, Any] = self._load_all_plot_data()
            existing_episodes = self._get_existing_episodes()

            for episode in sorted(plot_data, key=lambda x: x.get("episode_number", "999")):
                episode_num = str(episode.get("episode_number", ""))
                status = str(episode.get("status", "未執筆"))

                if status == "未執筆" and episode_num not in existing_episodes:
                    return episode_num

            return None
        except (FileNotFoundError, ValueError, KeyError):
            return None

    def extract_title_from_plot(self, plot_title: str) -> str:
        """プロットタイトルからエピソードタイトルを抽出"""
        # "第X話 タイトル" の形式から "タイトル" 部分を抽出
        match = re.search(r"第\d+話[ \s]+(.+)", plot_title)
        if match:
            return match.group(1)

        # その他の形式も対応
        match = re.search(r"第\d+話[_:](.+)", plot_title)
        if match:
            return match.group(1)

        return plot_title

    def create_episode_from_plot(self, plot_info: dict[str, Any]) -> EpisodeCreationResult:
        """プロット情報からエピソードを作成"""
        try:
            episode_num = plot_info.get("episode_number", "001")
            title = self.extract_title_from_plot(plot_info.get("title", ""))

            # ファイルパス生成（共通基盤に統一）
            try:
                num_int = int(episode_num)
            except Exception:
                # 安全側: 数値でない場合はゼロ埋めを取り除いて変換を試行
                num_int = int(re.sub(r"^0+", "", str(episode_num)) or 0)
            file_path = self._path_service.get_manuscript_path(num_int)

            # ディレクトリ作成（念のため）
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 内容生成(最小実装)
            content = self._generate_basic_content(plot_info)

            # ファイル作成
            file_path.write_text(content, encoding="utf-8")

            return EpisodeCreationResult(
                success=True,
                file_path=file_path,
                episode_number=episode_num,
                title=title,
            )

        except Exception as e:
            return EpisodeCreationResult(
                success=False,
                error_message=str(e),
            )

    def update_plot_status(self, episode_number: str, status: str) -> bool:
        """プロットファイルのステータスを更新"""
        try:
            if not self.plot_dir.exists():
                return False

            for yaml_file in self.plot_dir.glob("*.yaml"):
                with Path(yaml_file).open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                    data = yaml.safe_load(f)

                if not data or "episodes" not in data:
                    continue

                # 該当エピソードを探して更新
                for episode in data["episodes"]:
                    if episode.get("episode_number") == episode_number:
                        episode["status"] = status

                        # ファイルに書き戻し
                        with Path(yaml_file).open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                        return True

            return False
        except (OSError, yaml.YAMLError, UnicodeEncodeError):
            return False

    def _load_all_plot_data(self) -> list[dict]:
        """全プロットデータを読み込み"""
        plot_data: list[dict] = []

        if not self.plot_dir.exists():
            return plot_data

        for yaml_file in self.plot_dir.glob("*.yaml"):
            try:
                with Path(yaml_file).open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                    data = yaml.safe_load(f)
                    if data and "episodes" in data:
                        plot_data.extend(data["episodes"])
            except (OSError, yaml.YAMLError, UnicodeDecodeError):
                continue

        return plot_data

    def _get_existing_episodes(self) -> set[str]:
        """既存のエピソードファイルを取得"""
        existing_episodes: set[str] = set()

        if not self.manuscript_dir.exists():
            return existing_episodes

        for md_file in self.manuscript_dir.glob("第*話_*.md"):
            match = re.search(r"第(\d+)話", md_file.name)
            if match:
                existing_episodes.add(match.group(1))

        return existing_episodes

    def _generate_basic_content(self, plot_info: dict[str, Any]) -> str:
        """基本的なコンテンツを生成(最小実装)"""
        episode_num = plot_info.get("episode_number", "001")
        title = self.extract_title_from_plot(plot_info.get("title", ""))
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
