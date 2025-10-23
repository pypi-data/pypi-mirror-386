"""STEP 17: 公開準備サービス

A38執筆プロンプトガイドのSTEP17「公開準備」を実装するサービス。
品質認定を通過した原稿の最終的な公開準備を行い、
各種プラットフォームでの公開に必要な形式と要件を満たします。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.application.services.stepwise_execution_service import BaseWritingStep
from noveler.domain.models.project_model import ProjectModel
from noveler.domain.services.configuration_manager_service import ConfigurationManagerService


class PublishingPlatform(Enum):
    """公開プラットフォーム"""
    NAROU = "narou"  # 小説家になろう
    KAKUYOMU = "kakuyomu"  # カクヨム
    ALPHAPOLARIS = "alphapolaris"  # アルファポリス
    NOVEL_DAYS = "novel_days"  # ノベルデイズ
    PIXIV = "pixiv"  # pixiv小説
    MAGNET_MACROMILL = "magnet_macromill"  # マグネットマクロミル
    CUSTOM = "custom"  # カスタムプラットフォーム


class ContentFormat(Enum):
    """コンテンツ形式"""
    PLAIN_TEXT = "plain_text"  # プレーンテキスト
    HTML = "html"  # HTML形式
    MARKDOWN = "markdown"  # Markdown形式
    RICH_TEXT = "rich_text"  # リッチテキスト
    EPUB = "epub"  # EPUB形式


class PublishingStatus(Enum):
    """公開ステータス"""
    DRAFT = "draft"  # 下書き
    SCHEDULED = "scheduled"  # 予約投稿
    PUBLISHED = "published"  # 公開済み
    UPDATED = "updated"  # 更新済み
    SUSPENDED = "suspended"  # 一時停止
    DELETED = "deleted"  # 削除済み


class MetadataType(Enum):
    """メタデータタイプ"""
    BASIC_INFO = "basic_info"  # 基本情報
    SEO_DATA = "seo_data"  # SEO関連データ
    PLATFORM_SPECIFIC = "platform_specific"  # プラットフォーム固有
    ANALYTICS = "analytics"  # 分析用データ
    COPYRIGHT = "copyright"  # 著作権情報


@dataclass
class PlatformRequirements:
    """プラットフォーム要件"""
    platform: PublishingPlatform
    max_title_length: int
    max_summary_length: int
    max_content_length: int
    supported_formats: list[ContentFormat]
    required_metadata: list[str]
    optional_metadata: list[str]
    content_guidelines: list[str]
    submission_rules: list[str]
    update_frequency_limit: str | None  # 更新頻度制限


@dataclass
class ContentMetadata:
    """コンテンツメタデータ"""
    metadata_id: str
    metadata_type: MetadataType
    title: str
    summary: str
    author: str
    tags: list[str]
    genre: str
    target_audience: str
    content_warning: list[str]  # 内容警告
    language: str
    created_at: datetime
    updated_at: datetime
    version: str
    word_count: int
    estimated_reading_time: int  # 推定読了時間（分）
    series_info: dict[str, Any] | None = None
    custom_fields: dict[str, Any] = None


@dataclass
class PublishingConfiguration:
    """公開設定"""
    config_id: str
    target_platforms: list[PublishingPlatform]
    preferred_format: ContentFormat
    publishing_schedule: datetime | None
    auto_publish: bool
    content_visibility: str  # public, private, unlisted
    enable_comments: bool
    enable_ratings: bool
    monetization_enabled: bool
    backup_enabled: bool


@dataclass
class FormattedContent:
    """フォーマット済みコンテンツ"""
    content_id: str
    platform: PublishingPlatform
    format: ContentFormat
    title: str
    content: str
    metadata: ContentMetadata
    formatting_notes: list[str]
    validation_status: bool
    warnings: list[str]
    file_size: int  # バイトサイズ
    checksum: str  # チェックサム


@dataclass
class PublishingValidation:
    """公開検証"""
    validation_id: str
    platform: PublishingPlatform
    validation_timestamp: datetime
    passed_checks: list[str]
    failed_checks: list[str]
    warnings: list[str]
    compliance_score: float  # コンプライアンススコア (0-1)
    ready_for_publishing: bool
    blocking_issues: list[str]  # 公開阻害要因


@dataclass
class PublishingReport:
    """公開準備レポート"""
    report_id: str
    episode_number: int
    preparation_timestamp: datetime
    source_content: str
    target_platforms: list[PublishingPlatform]
    formatted_contents: list[FormattedContent]
    platform_validations: list[PublishingValidation]
    publishing_configuration: PublishingConfiguration
    overall_readiness_score: float  # 総合準備完了スコア (0-1)
    estimated_publication_date: datetime | None
    preparation_summary: str
    next_actions: list[str]
    backup_locations: list[str]
    preparation_metadata: dict[str, Any]


@dataclass
class PublishingPreparationConfig:
    """公開準備設定"""
    default_platforms: list[PublishingPlatform] = None
    preferred_format: ContentFormat = ContentFormat.PLAIN_TEXT
    enable_auto_formatting: bool = True
    enable_validation: bool = True
    create_backups: bool = True
    enable_seo_optimization: bool = True
    enable_content_warnings: bool = True
    enable_scheduling: bool = True
    max_preparation_time: int = 3600  # 秒
    quality_threshold: float = 0.8  # 品質閾値


class PublishingPreparationService(BaseWritingStep):
    """STEP 17: 公開準備サービス

    品質認定を通過した原稿の最終的な公開準備を行い、
    各種プラットフォームでの公開に必要な形式と要件を満たすサービス。
    A38ガイドのSTEP17「公開準備」を実装。
    """

    def __init__(
        self,
        config_manager: ConfigurationManagerService | None = None,
        path_service: Any | None = None,
        file_system_service: Any | None = None
    ) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._path_service = path_service
        self._file_system = file_system_service

        # デフォルト設定
        self._prep_config = PublishingPreparationConfig()
        if self._prep_config.default_platforms is None:
            self._prep_config.default_platforms = [
                PublishingPlatform.NAROU,
                PublishingPlatform.KAKUYOMU
            ]

        # プラットフォーム要件とフォーマッターの初期化
        self._platform_requirements = self._initialize_platform_requirements()
        self._content_formatters = self._initialize_content_formatters()
        self._validation_rules = self._initialize_validation_rules()

    @abstractmethod
    def get_step_name(self) -> str:
        """ステップ名を取得"""
        return "公開準備"

    @abstractmethod
    def get_step_description(self) -> str:
        """ステップの説明を取得"""
        return "品質認定を通過した原稿の最終的な公開準備を行い、各種プラットフォームでの公開に必要な形式と要件を満たします"

    @abstractmethod
    def execute_step(self, context: dict[str, Any]) -> dict[str, Any]:
        """STEP 17: 公開準備の実行

        Args:
            context: 実行コンテキスト

        Returns:
            公開準備結果を含むコンテキスト
        """
        try:
            episode_number = context.get("episode_number")
            project = context.get("project")

            if not episode_number or not project:
                msg = "episode_numberまたはprojectが指定されていません"
                raise ValueError(msg)

            # 品質認定結果の確認
            certification_status = context.get("certification_status")
            if not self._is_ready_for_publishing(certification_status):
                msg = "品質認定を通過していないため公開準備を実行できません"
                raise ValueError(msg)

            # 公開準備の実行
            publishing_report = self._execute_publishing_preparation(
                episode_number=episode_number,
                project=project,
                context=context
            )

            # 結果をコンテキストに追加
            context["publishing_preparation"] = publishing_report
            context["formatted_contents"] = publishing_report.formatted_contents
            context["publishing_readiness"] = publishing_report.overall_readiness_score
            context["publishing_preparation_completed"] = True

            return context

        except Exception as e:
            context["publishing_preparation_error"] = str(e)
            raise

    def _is_ready_for_publishing(self, certification_status) -> bool:
        """公開準備可能かどうかの判定"""
        from .quality_certification_service import CertificationStatus

        ready_statuses = [
            CertificationStatus.PASSED,
            CertificationStatus.CONDITIONAL
        ]

        return certification_status in ready_statuses

    def _execute_publishing_preparation(
        self,
        episode_number: int,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> PublishingReport:
        """公開準備の実行"""

        # 最終原稿の取得
        final_content = self._get_final_content(context)

        # 公開設定の構築
        publishing_config = self._build_publishing_configuration(project, context)

        # メタデータの生成
        content_metadata = self._generate_content_metadata(
            final_content, project, episode_number, context
        )

        # プラットフォーム別フォーマット処理
        formatted_contents = self._format_content_for_platforms(
            final_content, content_metadata, publishing_config
        )

        # プラットフォーム検証
        platform_validations = self._validate_platform_requirements(
            formatted_contents, publishing_config
        )

        # バックアップの作成
        backup_locations = []
        if self._prep_config.create_backups:
            backup_locations = self._create_content_backups(
                formatted_contents, content_metadata
            )

        # 準備完了度の評価
        readiness_score = self._calculate_readiness_score(
            formatted_contents, platform_validations
        )

        # 公開予定日の推定
        estimated_publication_date = self._estimate_publication_date(
            publishing_config, readiness_score
        )

        # レポート生成
        return self._generate_publishing_report(
            episode_number=episode_number,
            source_content=final_content,
            formatted_contents=formatted_contents,
            platform_validations=platform_validations,
            publishing_configuration=publishing_config,
            overall_readiness_score=readiness_score,
            estimated_publication_date=estimated_publication_date,
            backup_locations=backup_locations
        )

    def _get_final_content(self, context: dict[str, Any]) -> str:
        """最終コンテンツの取得"""

        # 可読性最適化後のテキストが最優先
        if "optimized_readable_text" in context:
            return context["optimized_readable_text"]

        # 文字数最適化後のテキスト
        if "optimized_text" in context:
            return context["optimized_text"]

        # その他のソース
        text_sources = [
            "final_manuscript",
            "manuscript_text",
            "generated_manuscript"
        ]

        for source in text_sources:
            text = context.get(source)
            if text and isinstance(text, str):
                return text

        return ""

    def _build_publishing_configuration(
        self,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> PublishingConfiguration:
        """公開設定の構築"""

        # プロジェクト設定から取得
        project_platforms = getattr(project, "target_platforms", None)
        target_platforms = project_platforms or self._prep_config.default_platforms

        # コンテキストから設定を取得
        user_config = context.get("publishing_config", {})

        return PublishingConfiguration(
            config_id=f"pub_config_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            target_platforms=target_platforms,
            preferred_format=user_config.get("format", self._prep_config.preferred_format),
            publishing_schedule=user_config.get("schedule"),
            auto_publish=user_config.get("auto_publish", False),
            content_visibility=user_config.get("visibility", "public"),
            enable_comments=user_config.get("enable_comments", True),
            enable_ratings=user_config.get("enable_ratings", True),
            monetization_enabled=user_config.get("monetization", False),
            backup_enabled=self._prep_config.create_backups
        )

    def _generate_content_metadata(
        self,
        content: str,
        project: ProjectModel,
        episode_number: int,
        context: dict[str, Any]
    ) -> ContentMetadata:
        """コンテンツメタデータの生成"""

        # 基本情報の抽出
        title = f"{project.project_name} 第{episode_number}話"
        author = getattr(project, "author", "Unknown")

        # サマリーの生成
        summary = self._generate_summary(content, context)

        # タグの生成
        tags = self._generate_tags(content, project, context)

        # ジャンルの推定
        genre = self._estimate_genre(content, project, context)

        # 読了時間の推定（1分間に400文字として計算）
        reading_time = max(1, len(content) // 400)

        # 内容警告の生成
        content_warnings = self._generate_content_warnings(content)

        return ContentMetadata(
            metadata_id=f"meta_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            metadata_type=MetadataType.BASIC_INFO,
            title=title,
            summary=summary,
            author=author,
            tags=tags,
            genre=genre,
            target_audience="一般",
            content_warning=content_warnings,
            language="ja",
            created_at=datetime.now(tz=datetime.timezone.utc),
            updated_at=datetime.now(tz=datetime.timezone.utc),
            version="1.0",
            word_count=len(content),
            estimated_reading_time=reading_time,
            series_info={
                "series_title": project.project_name,
                "episode_number": episode_number,
                "total_episodes": "未定"
            }
        )

    def _format_content_for_platforms(
        self,
        content: str,
        metadata: ContentMetadata,
        config: PublishingConfiguration
    ) -> list[FormattedContent]:
        """プラットフォーム別コンテンツフォーマット"""

        formatted_contents = []

        for platform in config.target_platforms:
            requirements = self._platform_requirements.get(platform)
            if not requirements:
                continue

            # プラットフォーム固有フォーマット処理
            formatted_content = self._format_for_platform(
                content, metadata, platform, requirements
            )

            formatted_contents.append(formatted_content)

        return formatted_contents

    def _format_for_platform(
        self,
        content: str,
        metadata: ContentMetadata,
        platform: PublishingPlatform,
        requirements: PlatformRequirements
    ) -> FormattedContent:
        """特定プラットフォーム向けフォーマット"""

        # タイトルの長さ調整
        adjusted_title = self._adjust_title_length(metadata.title, requirements.max_title_length)

        # コンテンツの長さ調整
        adjusted_content = self._adjust_content_length(content, requirements.max_content_length)

        # フォーマット適用
        if ContentFormat.HTML in requirements.supported_formats:
            formatted_content = self._format_as_html(adjusted_content)
            format_used = ContentFormat.HTML
        elif ContentFormat.MARKDOWN in requirements.supported_formats:
            formatted_content = self._format_as_markdown(adjusted_content)
            format_used = ContentFormat.MARKDOWN
        else:
            formatted_content = adjusted_content
            format_used = ContentFormat.PLAIN_TEXT

        # 検証実行
        validation_status, warnings = self._validate_formatted_content(
            formatted_content, requirements
        )

        # チェックサムの生成
        import hashlib
        checksum = hashlib.sha256(formatted_content.encode()).hexdigest()

        return FormattedContent(
            content_id=f"formatted_{platform.value}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            platform=platform,
            format=format_used,
            title=adjusted_title,
            content=formatted_content,
            metadata=metadata,
            formatting_notes=self._generate_formatting_notes(platform, format_used),
            validation_status=validation_status,
            warnings=warnings,
            file_size=len(formatted_content.encode()),
            checksum=checksum
        )

    def _validate_platform_requirements(
        self,
        formatted_contents: list[FormattedContent],
        config: PublishingConfiguration
    ) -> list[PublishingValidation]:
        """プラットフォーム要件の検証"""

        validations = []

        for content in formatted_contents:
            requirements = self._platform_requirements.get(content.platform)
            if not requirements:
                continue

            validation = self._validate_single_platform(content, requirements)
            validations.append(validation)

        return validations

    def _validate_single_platform(
        self,
        content: FormattedContent,
        requirements: PlatformRequirements
    ) -> PublishingValidation:
        """単一プラットフォームの検証"""

        passed_checks = []
        failed_checks = []
        warnings = []
        blocking_issues = []

        # タイトル長チェック
        if len(content.title) <= requirements.max_title_length:
            passed_checks.append("タイトル長要件")
        else:
            failed_checks.append("タイトル長超過")
            blocking_issues.append(f"タイトルが{requirements.max_title_length}文字を超過")

        # コンテンツ長チェック
        if len(content.content) <= requirements.max_content_length:
            passed_checks.append("コンテンツ長要件")
        else:
            failed_checks.append("コンテンツ長超過")
            blocking_issues.append(f"コンテンツが{requirements.max_content_length}文字を超過")

        # フォーマットサポートチェック
        if content.format in requirements.supported_formats:
            passed_checks.append("フォーマットサポート")
        else:
            failed_checks.append("フォーマット未サポート")
            blocking_issues.append(f"{content.format.value}形式は未サポート")

        # ガイドライン準拠チェック
        guideline_compliance = self._check_content_guidelines(
            content, requirements.content_guidelines
        )

        if guideline_compliance["passed"]:
            passed_checks.extend(guideline_compliance["passed"])

        if guideline_compliance["failed"]:
            failed_checks.extend(guideline_compliance["failed"])
            blocking_issues.extend(guideline_compliance["blocking"])

        if guideline_compliance["warnings"]:
            warnings.extend(guideline_compliance["warnings"])

        # コンプライアンススコアの計算
        total_checks = len(passed_checks) + len(failed_checks)
        compliance_score = len(passed_checks) / total_checks if total_checks > 0 else 0.0

        # 公開準備完了判定
        ready_for_publishing = len(blocking_issues) == 0 and compliance_score >= self._prep_config.quality_threshold

        return PublishingValidation(
            validation_id=f"val_{content.platform.value}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            platform=content.platform,
            validation_timestamp=datetime.now(tz=datetime.timezone.utc),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            compliance_score=compliance_score,
            ready_for_publishing=ready_for_publishing,
            blocking_issues=blocking_issues
        )

    def _create_content_backups(
        self,
        formatted_contents: list[FormattedContent],
        metadata: ContentMetadata
    ) -> list[str]:
        """コンテンツバックアップの作成"""

        backup_locations = []

        # バックアップディレクトリの作成
        backup_dir = None
        if self._path_service is not None:
            get_backup_directory = getattr(self._path_service, "get_backup_directory", None)
            if callable(get_backup_directory):
                backup_dir = get_backup_directory()
            else:
                get_backup_dir = getattr(self._path_service, "get_backup_dir", None)
                if callable(get_backup_dir):
                    backup_dir = get_backup_dir()

        if backup_dir is None:
            backup_dir = Path.cwd() / "backups"

        if not isinstance(backup_dir, Path):
            backup_dir = Path(backup_dir)

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

        for content in formatted_contents:
            # ファイル名の生成
            filename = f"{metadata.title}_{content.platform.value}_{timestamp}.txt"
            backup_path = backup_dir / filename

            try:
                # ファイルへの保存
                if self._file_system is None:
                    continue

                write_file = getattr(self._file_system, "write_file", None)
                if not callable(write_file):
                    continue

                write_file(backup_path, content.content)
                backup_locations.append(str(backup_path))
            except Exception:
                # バックアップ失敗は警告に留める
                continue

        return backup_locations

    def _calculate_readiness_score(
        self,
        formatted_contents: list[FormattedContent],
        validations: list[PublishingValidation]
    ) -> float:
        """準備完了スコアの計算"""

        if not validations:
            return 0.0

        # 各プラットフォームのコンプライアンススコアの平均
        compliance_scores = [v.compliance_score for v in validations]
        avg_compliance = sum(compliance_scores) / len(compliance_scores)

        # 公開準備完了プラットフォームの割合
        ready_platforms = len([v for v in validations if v.ready_for_publishing])
        readiness_ratio = ready_platforms / len(validations)

        # フォーマット品質スコア
        format_scores = [
            1.0 if c.validation_status else 0.5 for c in formatted_contents
        ]
        avg_format_quality = sum(format_scores) / len(format_scores) if format_scores else 0.0

        # 総合スコア計算
        overall_score = (avg_compliance * 0.5 + readiness_ratio * 0.3 + avg_format_quality * 0.2)

        return min(1.0, max(0.0, overall_score))

    def _estimate_publication_date(
        self,
        config: PublishingConfiguration,
        readiness_score: float
    ) -> datetime | None:
        """公開予定日の推定"""

        # 予約投稿が設定されている場合
        if config.publishing_schedule:
            return config.publishing_schedule

        # 準備完了度に基づく推定
        if readiness_score >= 0.9:
            # 即座に公開可能
            return datetime.now(tz=datetime.timezone.utc) + timedelta(hours=1)
        if readiness_score >= 0.7:
            # 軽微な調整後に公開
            return datetime.now(tz=datetime.timezone.utc) + timedelta(hours=6)
        if readiness_score >= 0.5:
            # 追加作業が必要
            return datetime.now(tz=datetime.timezone.utc) + timedelta(days=1)
        # 大幅な修正が必要
        return datetime.now(tz=datetime.timezone.utc) + timedelta(days=3)

    def _generate_publishing_report(
        self,
        episode_number: int,
        source_content: str,
        formatted_contents: list[FormattedContent],
        platform_validations: list[PublishingValidation],
        publishing_configuration: PublishingConfiguration,
        overall_readiness_score: float,
        estimated_publication_date: datetime | None,
        backup_locations: list[str]
    ) -> PublishingReport:
        """公開準備レポートの生成"""

        # サマリーの生成
        preparation_summary = self._generate_preparation_summary(
            formatted_contents, platform_validations, overall_readiness_score
        )

        # 次のアクションの生成
        next_actions = self._generate_next_actions(
            platform_validations, overall_readiness_score
        )

        return PublishingReport(
            report_id=f"pub_report_{episode_number}_{datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            episode_number=episode_number,
            preparation_timestamp=datetime.now(tz=datetime.timezone.utc),
            source_content=source_content,
            target_platforms=publishing_configuration.target_platforms,
            formatted_contents=formatted_contents,
            platform_validations=platform_validations,
            publishing_configuration=publishing_configuration,
            overall_readiness_score=overall_readiness_score,
            estimated_publication_date=estimated_publication_date,
            preparation_summary=preparation_summary,
            next_actions=next_actions,
            backup_locations=backup_locations,
            preparation_metadata={
                "config": self._prep_config.__dict__,
                "preparation_timestamp": datetime.now(tz=datetime.timezone.utc),
                "total_platforms": len(publishing_configuration.target_platforms),
                "ready_platforms": len([v for v in platform_validations if v.ready_for_publishing]),
                "total_file_size": sum(c.file_size for c in formatted_contents),
                "backup_count": len(backup_locations)
            }
        )

    # 初期化メソッドの実装

    def _initialize_platform_requirements(self) -> dict[PublishingPlatform, PlatformRequirements]:
        """プラットフォーム要件の初期化"""
        requirements = {}

        # 小説家になろう
        requirements[PublishingPlatform.NAROU] = PlatformRequirements(
            platform=PublishingPlatform.NAROU,
            max_title_length=50,
            max_summary_length=500,
            max_content_length=50000,
            supported_formats=[ContentFormat.PLAIN_TEXT],
            required_metadata=["title", "summary", "genre"],
            optional_metadata=["tags", "content_warning"],
            content_guidelines=[
                "性的表現の制限",
                "暴力表現の適切な警告",
                "著作権遵守"
            ],
            submission_rules=[
                "1日1回まで投稿可能",
                "連載は定期更新推奨"
            ],
            update_frequency_limit="1日1回"
        )

        # カクヨム
        requirements[PublishingPlatform.KAKUYOMU] = PlatformRequirements(
            platform=PublishingPlatform.KAKUYOMU,
            max_title_length=60,
            max_summary_length=600,
            max_content_length=60000,
            supported_formats=[ContentFormat.PLAIN_TEXT, ContentFormat.RICH_TEXT],
            required_metadata=["title", "summary", "genre", "tags"],
            optional_metadata=["content_warning", "target_audience"],
            content_guidelines=[
                "表現の自由重視",
                "適切なタグ付け必須",
                "読者への配慮"
            ],
            submission_rules=[
                "制限なし",
                "品質重視"
            ],
            update_frequency_limit=None
        )

        return requirements

    def _initialize_content_formatters(self) -> dict[ContentFormat, Any]:
        """コンテンツフォーマッターの初期化"""
        return {
            ContentFormat.PLAIN_TEXT: self._format_as_plain_text,
            ContentFormat.HTML: self._format_as_html,
            ContentFormat.MARKDOWN: self._format_as_markdown
        }

    def _initialize_validation_rules(self) -> dict[str, Any]:
        """検証ルールの初期化"""
        return {
            "content_guidelines": {
                "性的表現の制限": self._check_adult_content,
                "暴力表現の適切な警告": self._check_violence_content,
                "著作権遵守": self._check_copyright_compliance
            }
        }

    # ヘルパーメソッドの実装

    def _generate_summary(self, content: str, context: dict[str, Any]) -> str:
        """サマリーの生成"""
        # プロットデータからサマリーを生成
        plot_data = context.get("plot_data", {})
        if plot_data and "summary" in plot_data:
            return plot_data["summary"][:200]  # 200文字以内

        # コンテンツから自動生成
        sentences = content.split("。")
        if len(sentences) >= 3:
            return "。".join(sentences[:3]) + "。"
        return content[:200] + "..." if len(content) > 200 else content

    def _generate_tags(
        self,
        content: str,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> list[str]:
        """タグの生成"""
        tags = []

        # プロジェクトから基本タグ
        if hasattr(project, "genre"):
            tags.append(project.genre)

        # コンテンツから自動タグ生成
        common_words = ["恋愛", "冒険", "ファンタジー", "現代", "学園", "異世界"]
        for word in common_words:
            if word in content:
                tags.append(word)

        return tags[:10]  # 最大10個

    def _estimate_genre(
        self,
        content: str,
        project: ProjectModel,
        context: dict[str, Any]
    ) -> str:
        """ジャンルの推定"""
        # プロジェクトにジャンル設定がある場合
        if hasattr(project, "genre"):
            return project.genre

        # コンテンツから推定
        if any(word in content for word in ["魔法", "魔王", "勇者", "異世界"]):
            return "ファンタジー"
        if any(word in content for word in ["恋", "愛", "好き"]):
            return "恋愛"
        if any(word in content for word in ["学校", "学園", "部活"]):
            return "学園"
        return "その他"

    def _generate_content_warnings(self, content: str) -> list[str]:
        """内容警告の生成"""
        warnings = []

        # 暴力表現のチェック
        violence_words = ["血", "戦い", "殺", "暴力"]
        if any(word in content for word in violence_words):
            warnings.append("暴力表現あり")

        # 性的表現のチェック
        adult_words = ["キス", "恋人", "抱擁"]
        if any(word in content for word in adult_words):
            warnings.append("恋愛表現あり")

        return warnings

    def _adjust_title_length(self, title: str, max_length: int) -> str:
        """タイトル長の調整"""
        if len(title) <= max_length:
            return title
        return title[:max_length-3] + "..."

    def _adjust_content_length(self, content: str, max_length: int) -> str:
        """コンテンツ長の調整"""
        if len(content) <= max_length:
            return content
        # 段落単位で切り詰め
        paragraphs = content.split("\n\n")
        adjusted = ""
        for paragraph in paragraphs:
            if len(adjusted) + len(paragraph) <= max_length - 100:  # 余裕を持つ
                adjusted += paragraph + "\n\n"
            else:
                break
        return adjusted + "[続きは次回...]"

    def _format_as_plain_text(self, content: str) -> str:
        """プレーンテキストフォーマット"""
        return content

    def _format_as_html(self, content: str) -> str:
        """HTMLフォーマット"""
        # 簡易HTML変換
        paragraphs = content.split("\n\n")
        html_content = []

        for paragraph in paragraphs:
            if paragraph.strip():
                html_content.append(f"<p>{paragraph.strip()}</p>")

        return "\n".join(html_content)

    def _format_as_markdown(self, content: str) -> str:
        """Markdownフォーマット"""
        # 簡易Markdown変換
        lines = content.split("\n")
        markdown_content = []

        for line in lines:
            if line.strip():
                markdown_content.append(line)
            else:
                markdown_content.append("")

        return "\n".join(markdown_content)

    def _validate_formatted_content(
        self,
        content: str,
        requirements: PlatformRequirements
    ) -> tuple[bool, list[str]]:
        """フォーマット済みコンテンツの検証"""
        warnings = []

        # 基本的な検証
        if len(content) == 0:
            return False, ["コンテンツが空です"]

        # 文字エンコーディングチェック
        try:
            content.encode("utf-8")
        except UnicodeEncodeError:
            warnings.append("文字エンコーディングに問題があります")

        # 改行コードの統一チェック
        if "\r\n" in content:
            warnings.append("改行コードの統一が推奨されます")

        return True, warnings

    def _generate_formatting_notes(
        self,
        platform: PublishingPlatform,
        format: ContentFormat
    ) -> list[str]:
        """フォーマット注意事項の生成"""
        notes = []

        if platform == PublishingPlatform.NAROU:
            notes.append("小説家になろう形式でフォーマット済み")
            if format == ContentFormat.PLAIN_TEXT:
                notes.append("プレーンテキスト形式を使用")

        elif platform == PublishingPlatform.KAKUYOMU:
            notes.append("カクヨム形式でフォーマット済み")
            if format == ContentFormat.HTML:
                notes.append("HTMLフォーマットを適用")

        return notes

    def _check_content_guidelines(
        self,
        content: FormattedContent,
        guidelines: list[str]
    ) -> dict[str, list[str]]:
        """コンテンツガイドライン準拠チェック"""

        result = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "blocking": []
        }

        for guideline in guidelines:
            if guideline == "性的表現の制限":
                if self._check_adult_content(content.content):
                    result["warnings"].append("性的表現が含まれています")
                else:
                    result["passed"].append("性的表現チェック通過")

            elif guideline == "暴力表現の適切な警告":
                if self._check_violence_content(content.content):
                    if "暴力表現あり" in content.metadata.content_warning:
                        result["passed"].append("暴力表現警告適切")
                    else:
                        result["warnings"].append("暴力表現の警告が推奨されます")
                else:
                    result["passed"].append("暴力表現なし")

            elif guideline == "著作権遵守":
                if self._check_copyright_compliance(content.content):
                    result["passed"].append("著作権問題なし")
                else:
                    result["failed"].append("著作権問題の可能性")
                    result["blocking"].append("著作権問題要確認")

        return result

    def _check_adult_content(self, content: str) -> bool:
        """成人向けコンテンツのチェック"""
        adult_indicators = ["性的", "アダルト", "18禁"]
        return any(indicator in content for indicator in adult_indicators)

    def _check_violence_content(self, content: str) -> bool:
        """暴力表現のチェック"""
        violence_indicators = ["血", "殺", "暴力", "戦闘"]
        return any(indicator in content for indicator in violence_indicators)

    def _check_copyright_compliance(self, content: str) -> bool:
        """著作権遵守のチェック"""
        # 簡易実装：特定のキーワードをチェック
        copyright_violations = ["コピー", "転載", "無断使用"]
        return not any(violation in content for violation in copyright_violations)

    def _generate_preparation_summary(
        self,
        formatted_contents: list[FormattedContent],
        validations: list[PublishingValidation],
        readiness_score: float
    ) -> str:
        """準備サマリーの生成"""

        total_platforms = len(formatted_contents)
        ready_platforms = len([v for v in validations if v.ready_for_publishing])

        summary_parts = [
            f"対象プラットフォーム: {total_platforms}個",
            f"公開準備完了: {ready_platforms}個",
            f"準備完了率: {readiness_score:.1%}"
        ]

        if readiness_score >= 0.9:
            summary_parts.append("即座に公開可能です")
        elif readiness_score >= 0.7:
            summary_parts.append("軽微な調整後に公開可能です")
        elif readiness_score >= 0.5:
            summary_parts.append("追加作業が必要です")
        else:
            summary_parts.append("大幅な修正が必要です")

        return " | ".join(summary_parts)

    def _generate_next_actions(
        self,
        validations: list[PublishingValidation],
        readiness_score: float
    ) -> list[str]:
        """次のアクションの生成"""

        actions = []

        if readiness_score >= 0.9:
            actions.append("✅ 公開実行準備完了")
            actions.append("📅 公開スケジュールの確認")
            actions.append("🔄 最終確認チェックリスト実行")

        elif readiness_score >= 0.7:
            actions.append("🔧 軽微な修正の実行")
            for validation in validations:
                if not validation.ready_for_publishing and validation.warnings:
                    actions.append(f"⚠️ {validation.platform.value}: {validation.warnings[0]}")
            actions.append("🔄 修正後の再検証")

        else:
            actions.append("🚨 重要な問題の解決が必要")
            for validation in validations:
                if validation.blocking_issues:
                    for issue in validation.blocking_issues[:2]:  # 最大2個まで表示
                        actions.append(f"❗ {validation.platform.value}: {issue}")
            actions.append("📋 品質改善計画の策定")

        return actions
