"""Domain.writing.entities
Where: Domain entities modelling writing-related data.
What: Capture writing sessions, content, and associated metadata.
Why: Support writing workflows with structured domain models.
"""

from __future__ import annotations

"""Domain Entities for Writing Context
執筆コンテキストのドメインエンティティ

DDD原則に従い、ビジネスロジックと振る舞いを持つリッチなモデル
"""


import importlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from pathlib import Path

from noveler.domain.value_objects.path_configuration import (
    get_default_manuscript_dir,
    get_default_management_dir,
    get_default_plot_dir,
)
from typing import Any

import yaml

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.writing.value_objects import (
    EpisodeNumber,
    EpisodeTitle,
    PublicationSchedule,
    PublicationStatus,
    WordCount,
    WritingDuration,
    WritingPhase,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class EpisodeStatus(Enum):
    """エピソードステータス"""

    UNWRITTEN = "未執筆"
    IN_PROGRESS = "執筆中"
    DRAFT_COMPLETE = "初稿完了"
    REVISED = "推敲済み"
    PUBLISHED = "公開済み"


@dataclass
class Episode:
    """エピソードエンティティ

    ビジネス要求:
    - エピソードは一意のIDを持つ
    - 話数、タイトル、内容、文字数を管理
    - 執筆状態の遷移を制御
    - 公開可能性をビジネスルールで判定
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    episode_number: EpisodeNumber | None = None
    title: EpisodeTitle | None = None
    content: str = ""
    word_count: WordCount | None = None
    status: EpisodeStatus = EpisodeStatus.UNWRITTEN
    phase: WritingPhase = WritingPhase.DRAFT
    publication_status: PublicationStatus = PublicationStatus.UNPUBLISHED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: datetime | None = None
    publication_schedule: PublicationSchedule | None = None
    plot_info: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 文字数を自動計算
        if self.word_count is None and self.content:
            self.word_count = WordCount(len(self.content))

    def update_content(self, content: str) -> None:
        """内容を更新"""
        self.content = content
        self.word_count = WordCount(len(content))
        self.updated_at = project_now().datetime

    def update_title(self, title: str) -> None:
        """タイトルを更新"""
        self.title = title
        self.updated_at = project_now().datetime

    def advance_phase(self) -> None:
        """次のフェーズに進める"""
        phase_order = [
            WritingPhase.DRAFT,
            WritingPhase.REVISION,
            WritingPhase.FINAL_CHECK,
            WritingPhase.PUBLISHED,
        ]

        current_index = phase_order.index(self.phase)
        if current_index < len(phase_order) - 1:
            self.phase = phase_order[current_index + 1]
            self.updated_at = project_now().datetime

    def revert_phase(self) -> None:
        """前のフェーズに戻す"""
        phase_order = [
            WritingPhase.DRAFT,
            WritingPhase.REVISION,
            WritingPhase.FINAL_CHECK,
            WritingPhase.PUBLISHED,
        ]

        current_index = phase_order.index(self.phase)
        if current_index > 0:
            self.phase = phase_order[current_index - 1]
            self.updated_at = project_now().datetime

    def schedule_publication(self, schedule: PublicationSchedule) -> None:
        """公開をスケジュール"""
        if self.phase != WritingPhase.FINAL_CHECK:
            msg = "最終チェックフェーズでのみ公開スケジュールを設定できます"
            raise ValueError(msg)

        self.publication_schedule = schedule
        self.publication_status = PublicationStatus.SCHEDULED
        self.updated_at = project_now().datetime

    def start_writing(self) -> None:
        """執筆開始"""
        if self.status != EpisodeStatus.UNWRITTEN:
            msg = f"執筆開始できません。現在のステータス: {self.status.value}"
            raise ValueError(msg)

        self.status = EpisodeStatus.IN_PROGRESS
        self.updated_at = project_now().datetime

    def complete_draft(self) -> None:
        """初稿完了"""
        if self.status != EpisodeStatus.IN_PROGRESS:
            msg = f"初稿完了できません。現在のステータス: {self.status.value}"
            raise ValueError(msg)

        if len(self.content.strip()) == 0:
            msg = "内容が空のため初稿完了できません"
            raise ValueError(msg)

        self.status = EpisodeStatus.DRAFT_COMPLETE
        self.word_count = self._calculate_actual_word_count()
        self.updated_at = project_now().datetime

    def complete_revision(self) -> None:
        """推敲完了"""
        if self.status != EpisodeStatus.DRAFT_COMPLETE:
            msg = f"推敲完了できません。現在のステータス: {self.status.value}"
            raise ValueError(msg)

        self.status = EpisodeStatus.REVISED
        self.word_count = self._calculate_actual_word_count()
        self.updated_at = project_now().datetime

    def publish(self) -> None:
        """エピソード公開"""
        if not self.can_publish():
            msg = "公開条件を満たしていません"
            raise ValueError(msg)

        self.status = EpisodeStatus.PUBLISHED
        self.phase = WritingPhase.PUBLISHED
        self.publication_status = PublicationStatus.PUBLISHED
        self.published_at = project_now().datetime
        self.updated_at = project_now().datetime

    def can_publish(self) -> bool:
        """公開可能性判定(ビジネスルール)"""
        # 推敲済みまたは初稿完了状態
        if self.status not in [EpisodeStatus.REVISED, EpisodeStatus.DRAFT_COMPLETE]:
            return False

        minimum_required = 1500
        if not self.word_count or self.word_count.value < minimum_required:
            return False

        # 内容の存在チェック
        return len(self.content.strip()) != 0

    def withdraw(self) -> None:
        """公開を取り下げ"""
        if self.publication_status != PublicationStatus.PUBLISHED:
            msg = "公開済みのエピソードのみ取り下げ可能です"
            raise ValueError(msg)

        self.publication_status = PublicationStatus.WITHDRAWN
        self.updated_at = project_now().datetime

    def update_plot_info(self, plot_info: dict[str, Any]) -> None:
        """プロット情報更新"""
        self.plot_info = plot_info.copy()
        self.updated_at = project_now().datetime

    def get_target_word_count(self) -> int:
        """目標文字数取得"""
        return self.plot_info.get("word_count_target", 3000)

    def get_completion_rate(self) -> float:
        """完成度計算(文字数ベース)"""
        target = self.get_target_word_count()
        if target == 0:
            return 0.0
        actual_count = self.word_count.value if self.word_count else 0
        return min(100.0, (actual_count / target) * 100.0)

    def is_over_target(self) -> bool:
        """目標文字数超過判定"""
        actual_count = self.word_count.value if self.word_count else 0
        return actual_count > self.get_target_word_count()

    def _calculate_actual_word_count(self) -> WordCount:
        """実際の小説部分の文字数を計算(メタ情報除外)"""
        if not self.content:
            return WordCount(0)

        lines = self.content.split("\n")
        novel_lines = []

        for line in lines:
            stripped_line = line.strip()
            # メタ情報行を除外
            if stripped_line.startswith(("#", "**", "---", "- ")) or stripped_line == "":
                continue
            novel_lines.append(stripped_line)

        novel_content = "".join(novel_lines)
        return WordCount(len(novel_content))

    def is_ready_to_publish(self) -> bool:
        """公開可能な状態かチェック(既存互換性維持)"""
        return self.can_publish()


@dataclass
class WritingRecord:
    """執筆記録エンティティ"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    episode_id: str = ""
    phase: WritingPhase = WritingPhase.DRAFT
    started_at: datetime = field(default_factory=lambda: project_now().datetime)
    ended_at: datetime | None = None
    duration: WritingDuration | None = None
    word_count_before: WordCount | None = None
    word_count_after: WordCount | None = None
    notes: str = ""

    def end_session(self, word_count_after: WordCount) -> None:
        """執筆セッションを終了"""
        if self.ended_at is not None:
            msg = "既に終了済みのセッションです"
            raise ValueError(msg)

        self.ended_at = project_now().datetime
        self.word_count_after = word_count_after

        # 執筆時間を計算
        duration_seconds = (self.ended_at - self.started_at).total_seconds()
        self.duration = WritingDuration(int(duration_seconds / 60))

    def get_words_written(self) -> int | None:
        """執筆した文字数を取得"""
        if self.word_count_before and self.word_count_after:
            return self.word_count_after.value - self.word_count_before.value
        return None

    def get_writing_speed(self) -> float | None:
        """執筆速度(文字/分)を取得"""
        words_written = self.get_words_written()
        if words_written is not None and self.duration and self.duration.minutes > 0:
            return words_written / self.duration.minutes
        return None


@dataclass
class WritingSession:
    """執筆セッション集約"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    episode_id: str = ""
    date: date = field(default_factory=lambda: project_now().datetime.date())
    records: list[WritingRecord] = field(default_factory=list)

    def add_record(self, record: WritingRecord) -> None:
        """記録を追加"""
        if record.episode_id != self.episode_id:
            msg = "異なるエピソードの記録は追加できません"
            raise ValueError(msg)
        self.records.append(record)

    def get_total_duration(self) -> WritingDuration:
        """合計執筆時間を取得"""
        total_minutes = sum(record.duration.minutes for record in self.records if record.duration)
        return WritingDuration(total_minutes)

    def get_total_words_written(self) -> int:
        """合計執筆文字数を取得"""
        total = 0
        for record in self.records:
            words = record.get_words_written()
            if words and words > 0:
                total += words
        return total

    def get_average_writing_speed(self) -> float | None:
        """平均執筆速度を取得"""
        total_words = self.get_total_words_written()
        total_duration = self.get_total_duration()

        if total_duration.minutes > 0:
            return total_words / total_duration.minutes
        return None


@dataclass
class AutoEpisodeCreator:
    """自動エピソード作成エンティティ."""

    project_root: Path
    _path_service: Any = field(init=False, repr=False)
    _plot_dir: Path = field(init=False, repr=False)
    _management_dir: Path = field(init=False, repr=False)
    _episode_manager: EpisodeManager = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """パスサービスとエピソード管理コンポーネントを初期化する."""
        self.project_root = Path(self.project_root)
        path_service_factory = EpisodeManager._resolve_path_service_factory()
        self._path_service = path_service_factory(project_root=self.project_root)
        self._plot_dir = self._resolve_to_project(self._path_service.get_plots_dir()) / "章別プロット"
        self._management_dir = self._resolve_to_project(self._path_service.get_management_dir())
        self._episode_manager = EpisodeManager(self.project_root)

    def create_next_episode(self) -> EpisodeCreationResult:
        """プロットから次の未執筆エピソードを生成し、関連情報を更新する."""
        next_episode = self._episode_manager.find_next_unwritten_episode()
        if not next_episode:
            return EpisodeCreationResult(success=False, error_message="未執筆エピソードが見つかりません")

        plot_info = self._get_plot_info(next_episode)
        if not plot_info:
            return EpisodeCreationResult(success=False, error_message="該当プロット情報が見つかりません")

        creation_result = self._episode_manager.create_episode_from_plot(plot_info)
        if not creation_result.success:
            return creation_result

        self._episode_manager.update_plot_status(next_episode, "執筆中")

        writing_record_created = self._create_writing_record(
            episode_number=creation_result.episode_number or next_episode,
            title=creation_result.title or self._episode_manager.extract_title_from_plot(plot_info.get("title", "")),
            manuscript_path=creation_result.file_path,
        )

        return EpisodeCreationResult(
            success=True,
            file_path=creation_result.file_path,
            episode_number=creation_result.episode_number or next_episode,
            title=creation_result.title or plot_info.get("title", ""),
            writing_record_created=writing_record_created,
        )

    def get_plot_status(self, episode_number: str) -> str | None:
        """指定話数の現在のプロットステータスを取得する."""
        entry = self._get_plot_info(episode_number)
        if entry is None:
            return None
        status = entry.get("status")
        return str(status) if status is not None else None

    # ---- internal helpers -------------------------------------------------

    def _resolve_to_project(self, maybe_relative: Path) -> Path:
        candidate = Path(maybe_relative)
        return candidate if candidate.is_absolute() else self.project_root / candidate

    def _get_plot_info(self, episode_number: str) -> dict[str, Any] | None:
        if not self._plot_dir.exists():
            return None

        target = self._normalize_episode_number(episode_number)
        for yaml_file in sorted(self._plot_dir.glob("*.yaml")):
            try:
                with yaml_file.open(encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
            except (OSError, yaml.YAMLError):
                continue

            episodes = data.get("episodes")
            if not isinstance(episodes, list):
                continue

            for entry in episodes:
                if self._normalize_episode_number(entry.get("episode_number", "")) == target:
                    return entry
        return None

    def _create_writing_record(
        self,
        episode_number: str,
        title: str,
        manuscript_path: Path | None,
    ) -> bool:
        try:
            record_dir = self._management_dir / "writing_records"
            record_dir.mkdir(parents=True, exist_ok=True)
            record_file = record_dir / "records.log"
            timestamp = datetime.now().isoformat(timespec="seconds")
            with record_file.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"{timestamp}\t第{episode_number}話\t{title}\t{(manuscript_path or '')}\n"
                )
            return True
        except OSError:
            return False

    @staticmethod
    def _normalize_episode_number(number: Any) -> str:
        digits = str(number).strip()
        if not digits:
            return "001"
        try:
            return f"{int(digits):03d}"
        except ValueError:
            cleaned = re.sub(r"\D", "", digits)
            return f"{int(cleaned or 1):03d}"


@dataclass
class ContentGenerator:
    """コンテンツ生成エンティティ."""

    def __init__(self) -> None:
        """初期化."""

    def generate_content(self, plot_summary: str, target_length: int) -> str:
        """プロットサマリーからコンテンツを生成.

        Args:
            plot_summary: プロットサマリー
            target_length: 目標文字数

        Returns:
            生成されたコンテンツ
        """
        # 簡単なテンプレート生成
        return f"""# {plot_summary}

## 導入

## 展開

## 結末

(目標文字数: {target_length}文字)
"""

    def generate_from_plot(self, plot_info: dict[str, Any]) -> str:
        """プロット情報からテンプレート化された原稿素案を生成する."""
        episode_number = self._normalize_episode_number(plot_info.get("episode_number", "1"))
        title = str(plot_info.get("title", "無題")).strip() or "無題"
        summary = str(plot_info.get("summary", "")).strip()
        word_target = int(plot_info.get("word_count_target", 3000))
        plot_points = [str(point) for point in (plot_info.get("plot_points") or [])]
        character_focus = [str(name) for name in (plot_info.get("character_focus") or [])]

        section_targets = self.calculate_section_targets(word_target)
        character_hint_block = self.generate_character_hints({"character_focus": character_focus})

        lines: list[str] = [
            f"# 第{episode_number}話 {title}",
            "",
            "## あらすじ",
            summary,
            "",
            f"**目標文字数:** {word_target}文字",
            "",
            "---",
            "",
            "## セクション配分",
            "",
        ]

        for section, target in section_targets.items():
            lines.append(f"- {section}: 約{target}文字")

        if plot_points:
            lines.extend(["", "## プロットポイント", ""])
            lines.extend(f"- {point}" for point in plot_points)

        if character_focus:
            lines.extend(["", "## キャラクターフォーカス", ""])
            lines.extend(f"- {name}" for name in character_focus)

        if character_hint_block:
            lines.extend(["", "---", "", character_hint_block])

        lines.append("")
        return "\n".join(lines)

    def calculate_section_targets(self, total_words: int) -> dict[str, int]:
        """セクションごとの目標文字数を算出する."""
        total = max(total_words, 0)
        distribution = {
            "introduction": 0.25,
            "development": 0.5,
            "climax": 0.2,
            "conclusion": 0.05,
        }

        targets: dict[str, int] = {}
        consumed = 0
        sections = list(distribution.items())
        for index, (section, ratio) in enumerate(sections, start=1):
            if index == len(sections):
                value = max(total - consumed, 0)
            else:
                value = round(total * ratio)
                consumed += value
            targets[section] = int(value)
        return targets

    def generate_character_hints(self, plot_info: dict[str, Any]) -> str:
        """キャラクターの描写ポイントを列挙するテキストを生成する."""
        characters = [str(name).strip() for name in (plot_info.get("character_focus") or []) if str(name).strip()]
        if not characters:
            return "キャラクターの描写に特別な指定はありません。"

        lines = ["キャラクター描写ヒント:", ""]
        lines.extend(f"- {name}の描写を重視" for name in characters)
        return "\n".join(lines)

    @staticmethod
    def _normalize_episode_number(number: Any) -> str:
        digits = str(number).strip()
        if not digits:
            return "001"
        try:
            return f"{int(digits):03d}"
        except ValueError:
            cleaned = re.sub(r"\D", "", digits)
            return f"{int(cleaned or 1):03d}"



@dataclass
class EpisodeCreationResult:
    """エピソード作成処理の結果を表現するデータ転送オブジェクト."""

    success: bool
    file_path: Path | None = None
    episode_number: str | None = None
    title: str | None = None
    error_message: str | None = None
    writing_record_created: bool = False


@dataclass
class EpisodeManager:
    """プロット情報と原稿の橋渡しを担うエピソード管理クラス."""

    project_root: Path
    episodes: list[Episode] = field(default_factory=list)
    _path_service: Any = field(init=False, repr=False)
    _plot_dir: Path = field(init=False, repr=False)
    _manuscript_dir: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """パスサービスを確立し、プロジェクト配下の基準ディレクトリを解決する."""
        self.project_root = Path(self.project_root)
        path_service_factory = self._resolve_path_service_factory()
        self._path_service = path_service_factory(project_root=self.project_root)
        plots_root = self._resolve_to_project(self._path_service.get_plots_dir())
        self._plot_dir = plots_root / "章別プロット"
        self._manuscript_dir = self._resolve_to_project(self._path_service.get_manuscript_dir())

    def add_episode(self, episode: Episode) -> None:
        """エピソードを追加.

        Args:
            episode: 追加するエピソード
        """
        self.episodes.append(episode)

    def get_episode(self, episode_number: int) -> Episode | None:
        """エピソード番号でエピソードを取得.

        Args:
            episode_number: エピソード番号

        Returns:
            エピソード、存在しない場合はNone
        """
        for episode in self.episodes:
            if episode.episode_number and episode.episode_number.value == episode_number:
                return episode
        return None

    def get_total_episodes(self) -> int:
        """総エピソード数を取得.

        Returns:
            エピソード数
        """
        return len(self.episodes)

    def get_published_episodes(self) -> list[Episode]:
        """公開済みエピソード一覧を取得.

        Returns:
            公開済みエピソードのリスト
        """
        return [ep for ep in self.episodes if ep.publication_status == PublicationStatus.PUBLISHED]

    def find_next_unwritten_episode(self) -> str | None:
        """章別プロットから次に執筆すべきエピソード番号を返す."""
        try:
            plot_entries = self._load_plot_entries()
        except FileNotFoundError:
            return None

        existing = self._collect_existing_episode_numbers()
        for entry in sorted(plot_entries, key=self._episode_sort_key):
            raw_number = str(entry.get("episode_number", "")).strip()
            if not raw_number:
                continue
            normalized = self._normalize_episode_number(raw_number)
            status = str(entry.get("status", "未執筆")).strip() or "未執筆"
            if status == "未執筆" and normalized not in existing:
                return normalized
        return None

    def extract_title_from_plot(self, plot_title: str) -> str:
        """プロット見出しからタイトル部分のみを抽出する."""
        title = str(plot_title or "").strip()
        if not title:
            return ""
        match = re.search(r"第\d+話[\s_:：-]*(.+)", title)
        if match:
            return match.group(1).strip()
        return title

    def create_episode_from_plot(self, plot_info: dict[str, Any]) -> EpisodeCreationResult:
        """プロット情報を基に原稿ファイルを生成する."""
        try:
            episode_number = self._normalize_episode_number(str(plot_info.get("episode_number", "001")))
            title = self.extract_title_from_plot(plot_info.get("title", "")) or "無題"
            summary = str(plot_info.get("summary", "")).strip()
            word_target = int(plot_info.get("word_count_target", 3000))
            plot_points = plot_info.get("plot_points", []) or []
            character_focus = plot_info.get("character_focus", []) or []

            manuscript_path = self._build_manuscript_path(episode_number, title)
            manuscript_path.parent.mkdir(parents=True, exist_ok=True)

            content = self._render_episode_skeleton(
                episode_number=episode_number,
                title=title,
                summary=summary,
                word_target=word_target,
                plot_points=plot_points,
                character_focus=character_focus,
            )
            manuscript_path.write_text(content, encoding="utf-8")

            return EpisodeCreationResult(
                success=True,
                file_path=manuscript_path,
                episode_number=episode_number,
                title=title,
            )
        except Exception as exc:  # noqa: BLE001
            return EpisodeCreationResult(success=False, error_message=str(exc))

    def update_plot_status(self, episode_number: str, status: str) -> bool:
        """章別プロットYAMLのステータスを更新する."""
        if not self._plot_dir.exists():
            return False

        normalized = self._normalize_episode_number(str(episode_number))
        updated = False

        for yaml_file in sorted(self._plot_dir.glob("*.yaml")):
            try:
                with yaml_file.open(encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
            except (OSError, yaml.YAMLError):
                continue

            episodes = data.get("episodes")
            if not isinstance(episodes, list):
                continue

            for entry in episodes:
                if self._normalize_episode_number(str(entry.get("episode_number", ""))) == normalized:
                    entry["status"] = status
                    try:
                        with yaml_file.open("w", encoding="utf-8") as handle:
                            yaml.dump(data, handle, allow_unicode=True, sort_keys=False)
                        updated = True
                    except OSError:
                        return False
                    break

            if updated:
                break

        return updated

    # === internal helpers ==================================================

    @staticmethod
    def _resolve_path_service_factory():
        try:
            module = importlib.import_module("noveler.presentation.shared.shared_utilities")
            getter = getattr(module, "get_common_path_service", None)
            if callable(getter):
                return getter
        except Exception:
            pass
        try:
            module = importlib.import_module("noveler.infrastructure.services.common_path_service")
            getter = getattr(module, "get_common_path_service", None)
            if callable(getter):
                return getter
        except Exception:
            pass

        def _fallback(project_root: Path | None = None):
            root = Path(project_root) if project_root else Path.cwd()

            class _FallbackPathService:
                def __init__(self, base: Path) -> None:
                    self._base = base

                def get_plots_dir(self) -> Path:
                    return get_default_plot_dir(self._base)

                def get_manuscript_dir(self) -> Path:
                    return get_default_manuscript_dir(self._base)

                def get_management_dir(self) -> Path:
                    return get_default_management_dir(self._base)

            return _FallbackPathService(root)

        return _fallback

    def _resolve_to_project(self, maybe_relative: Path) -> Path:
        candidate = Path(maybe_relative)
        if candidate.is_absolute():
            return candidate
        return self.project_root / candidate

    def _load_plot_entries(self) -> list[dict[str, Any]]:
        if not self._plot_dir.exists():
            raise FileNotFoundError(self._plot_dir)

        entries: list[dict[str, Any]] = []
        for yaml_file in sorted(self._plot_dir.glob("*.yaml")):
            try:
                with yaml_file.open(encoding="utf-8") as handle:
                    data = yaml.safe_load(handle) or {}
            except (OSError, yaml.YAMLError):
                continue

            block = data.get("episodes")
            if isinstance(block, list):
                entries.extend(block)
        return entries

    def _collect_existing_episode_numbers(self) -> set[str]:
        existing: set[str] = set()
        if not self._manuscript_dir.exists():
            return existing

        for manuscript in self._manuscript_dir.glob("第*話_*.md"):
            match = re.search(r"第(\d+)話", manuscript.name)
            if match:
                existing.add(self._normalize_episode_number(match.group(1)))
        return existing

    @staticmethod
    def _episode_sort_key(entry: dict[str, Any]) -> tuple[int, str]:
        raw = str(entry.get("episode_number", "")).strip()
        try:
            numeric = int(raw)
        except ValueError:
            numeric = 9999
        return numeric, raw

    @staticmethod
    def _normalize_episode_number(number: str) -> str:
        digits = str(number).strip()
        if not digits:
            return ""
        try:
            return f"{int(digits):03d}"
        except ValueError:
            cleaned = re.sub(r"\D", "", digits)
            return f"{int(cleaned or 0):03d}"

    def _build_manuscript_path(self, episode_number: str, title: str) -> Path:
        safe_title = self._sanitize_filename(title) or "無題"
        filename = f"第{episode_number}話_{safe_title}.md"
        return self._manuscript_dir / filename

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        sanitized = re.sub(r"[\\/:*?\"<>|]", "", name or "").strip()
        return sanitized.replace(" ", "_")

    def _render_episode_skeleton(
        self,
        episode_number: str,
        title: str,
        summary: str,
        word_target: int,
        plot_points: list[Any],
        character_focus: list[str],
    ) -> str:
        lines: list[str] = [
            f"# 第{episode_number}話 {title}",
            "",
            "## あらすじ",
            summary,
            "",
            f"**目標文字数:** {word_target}文字",
            "",
            "---",
            "",
            "## 導入部",
            "",
            "## 展開部",
            "",
            "## 転換部",
            "",
            "## 結末部",
            "",
            "---",
        ]

        if plot_points:
            lines.extend(["", "## プロットポイント", ""])
            for point in plot_points:
                lines.append(f"- {point}")

        if character_focus:
            lines.extend(["", "## キャラクターフォーカス", ""])
            for name in character_focus:
                lines.append(f"- {name} の描写を重視")

        lines.append("")
        return "\n".join(lines)
@dataclass
class ProgressTracker:
    """進捗追跡エンティティ."""

    sessions: list[WritingSession] = field(default_factory=list)

    def add_session(self, session: WritingSession) -> None:
        """セッションを追加.

        Args:
            session: 追加するセッション
        """
        self.sessions.append(session)

    def get_total_writing_time(self) -> WritingDuration:
        """総執筆時間を取得.

        Returns:
            総執筆時間
        """
        total_minutes = sum(session.get_total_duration().minutes for session in self.sessions)
        return WritingDuration(total_minutes)

    def get_daily_progress(self, date: datetime) -> WritingSession | None:
        """指定日の進捗を取得.

        Args:
            date: 対象日

        Returns:
            その日の進捗、存在しない場合はNone
        """
        target_date = date.date() if hasattr(date, "date") else date
        for session in self.sessions:
            session_date = session.date.date() if hasattr(session.date, "date") else session.date
            if session_date == target_date:
                return session
        return None

    def get_average_daily_words(self) -> float:
        """日平均執筆文字数を取得.

        Returns:
            日平均文字数
        """
        if not self.sessions:
            return 0.0

        total_words = sum(session.get_total_words_written() for session in self.sessions)
        return total_words / len(self.sessions)


    @dataclass
    class ProgressSummary:
        total_episodes: int
        written_episodes: int
        completion_rate: float

    def calculate_progress(self, plot_episodes: list[dict], written_files: list[str]) -> "ProgressSummary":
        total = len(plot_episodes or [])
        written_set = set(str(x) for x in (written_files or []))
        written = sum(1 for ep in (plot_episodes or []) if str(ep.get("episode_number", "")).zfill(3) in written_set)
        rate = round((written / total * 100.0) if total else 0.0, 1)
        return ProgressTracker.ProgressSummary(total, written, rate)

    def find_next_episode(self, plot_episodes: list[dict], written_files: list[str]) -> str | None:
        written_set = set(str(x) for x in (written_files or []))
        for ep in plot_episodes or []:
            num = str(ep.get("episode_number", "")).zfill(3)
            status = str(ep.get("status", "未執筆"))
            if status == "未執筆" and num not in written_set:
                return num
        return None

    def estimate_word_count(self, content: str) -> int:
        """Markdown原稿から実質的な本文文字数を推定する."""
        lines = content.splitlines()
        effective_fragments: list[str] = []
        skip_bullet_block = False

        for raw_line in lines:
            stripped = raw_line.strip()

            if not stripped:
                skip_bullet_block = False
                continue

            if stripped.startswith("#"):
                continue

            if stripped.startswith("**") and stripped.endswith("**"):
                skip_bullet_block = True
                continue

            if stripped.startswith("**"):
                skip_bullet_block = True
                continue

            if stripped.startswith("-") and skip_bullet_block:
                continue

            effective_fragments.append(stripped)

        joined = "".join(fragment.replace(" ", "") for fragment in effective_fragments)
        return len(joined)
