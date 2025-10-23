"""Application Use Case: Create Episode from Plot
プロット情報からエピソード作成ユースケース

アプリケーション層のビジネスロジック調整
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from noveler.domain.writing.entities import Episode, EpisodeStatus

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.writing_record_repository import WritingRecordRepository
from noveler.domain.writing.value_objects import EpisodeNumber, EpisodeTitle, WordCount


@dataclass(frozen=True)
class CreateEpisodeCommand:
    """エピソード作成コマンド"""

    project_id: str
    plot_info: dict[str, Any]


@dataclass(frozen=True)
class CreateEpisodeResult:
    """エピソード作成結果"""

    success: bool
    episode: Episode | None = None
    error_message: str | None = None


class CreateEpisodeFromPlotUseCase:
    """プロット情報からエピソードを作成するユースケース

    ビジネスフロー:
    1. プロット情報の検証
    2. エピソード重複チェック
    3. エピソード作成
    4. プロットステータス更新
    5. 執筆記録初期化
    """

    def __init__(
        self, episode_repository: "EpisodeRepository", writing_record_repository: "WritingRecordRepository"
    ) -> None:
        self.episode_repository = episode_repository
        self.writing_record_repository = writing_record_repository

    def execute(self, command: CreateEpisodeCommand) -> CreateEpisodeResult:
        """エピソード作成を実行"""
        try:
            # 1. プロット情報の検証
            validation_result = self._validate_plot_info(command.plot_info)
            if not validation_result.is_valid:
                return CreateEpisodeResult(
                    success=False,
                    error_message=validation_result.error_message,
                )

            # 2. エピソード重複チェック
            episode_number = EpisodeNumber(int(command.plot_info["episode_number"]))
            existing_episode = self.episode_repository.find_by_number(
                command.project_id,
                episode_number,
            )

            if existing_episode:
                return CreateEpisodeResult(
                    success=False,
                    error_message=f"エピソード {episode_number.value} は既に存在します",
                )

            # 3. エピソード作成
            episode = self._create_episode_from_plot(command.project_id, command.plot_info)

            # 4. エピソード保存
            saved_episode = self.episode_repository.save(episode)

            # 5. プロットステータス更新
            self.episode_repository.update_plot_status(
                command.project_id,
                command.plot_info["episode_number"],
                "執筆中",
            )

            return CreateEpisodeResult(
                success=True,
                episode=saved_episode,
            )

        except Exception as e:
            return CreateEpisodeResult(
                success=False,
                error_message=f"エピソード作成に失敗しました: {e!s}",
            )

    def _validate_plot_info(self, plot_info: dict[str, Any]) -> "ValidationResult":
        """プロット情報の検証"""
        required_fields = ["episode_number", "title"]

        for field in required_fields:
            if field not in plot_info:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"必須フィールド '{field}' が不足しています",
                )

        # 話数の検証
        try:
            episode_num = int(plot_info["episode_number"])
            if episode_num < 1:
                return ValidationResult(
                    is_valid=False,
                    error_message="話数は1以上である必要があります",
                )

        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message="話数は数値である必要があります",
            )

        # タイトルの検証
        title = plot_info["title"]
        if not isinstance(title, str) or len(title.strip()) == 0:
            return ValidationResult(
                is_valid=False,
                error_message="タイトルは空文字列以外の文字列である必要があります",
            )

        return ValidationResult(is_valid=True)

    def _create_episode_from_plot(self, project_id: str, plot_info: dict[str, Any]) -> Episode:
        """プロット情報からエピソードを作成"""
        # タイトルから「第X話 」部分を除去
        title_text = plot_info["title"]
        clean_title = self._extract_clean_title(title_text)

        return Episode(
            project_id=project_id,
            episode_number=EpisodeNumber(int(plot_info["episode_number"])),
            title=EpisodeTitle(clean_title),
            content=self._generate_initial_content(plot_info),
            word_count=WordCount(0),
            status=EpisodeStatus.UNWRITTEN,
            plot_info=plot_info.copy(),
        )

    def _extract_clean_title(self, title_text: str) -> str:
        """タイトルテキストから純粋なタイトル部分を抽出"""

        # "第X話 タイトル" の形式から "タイトル" 部分を抽出
        patterns = [
            r"第\d+話[ \s]+(.+)",  # 第1話 タイトル
            r"第\d+話[::_\-\s]+(.+)",  # 第1話:タイトル
            r"^\d+[..]\s*(.+)",  # 1. タイトル
        ]

        for pattern in patterns:
            match = re.search(pattern, title_text)
            if match:
                return match.group(1).strip()

        return title_text.strip()

    def _generate_initial_content(self, plot_info: dict[str, Any]) -> str:
        """初期コンテンツを生成"""
        episode_num = plot_info["episode_number"]
        title = self._extract_clean_title(plot_info["title"])
        summary = plot_info.get("summary", "")
        word_target = plot_info.get("word_count_target", 3000)
        plot_points = plot_info.get("plot_points", [])
        characters = plot_info.get("character_focus", [])

        plot_section = ""
        if plot_points:
            plot_section = "\n".join([f"- {point}" for point in plot_points])

        character_section = ""
        if characters:
            character_section = f"**登場キャラクター:** {', '.join(characters)}"

        return f"""# 第{episode_num}話 {title}

## あらすじ
{summary}

## 構成プロット
{plot_section}

{character_section}
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


@dataclass(frozen=True)
class ValidationResult:
    """検証結果"""

    is_valid: bool
    error_message: str | None = None
