"""Claude品質プロンプトリポジトリ YAML実装
仕様: Claude Code品質チェック統合システム
"""

import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML

from noveler.domain.repositories.claude_quality_prompt_repository import (
    ClaudeQualityPromptRepository,
    ClaudeQualityResultRepository,
)
from noveler.domain.value_objects.claude_quality_check_request import (
    ClaudeQualityCheckRequest,
    ClaudeQualityCheckResult,
)
from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent, YamlPromptMetadata
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

# パフォーマンス監視インポート（フォールバック付き）
try:
    from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor
except ImportError:

    def performance_monitor(name: str):
        """パフォーマンス監視デコレータ（フォールバック）"""

        def decorator(func):
            return func

        return decorator


class YamlClaudeQualityPromptRepository(ClaudeQualityPromptRepository):
    """Claude品質プロンプトリポジトリ YAML実装

    Claude Code用の品質チェックプロンプトをYAML形式で生成・保存・管理
    構造化プロンプトの永続化とテンプレート管理を提供
    """

    def __init__(self, guide_root: Path) -> None:
        """初期化

        Args:
            guide_root: ガイドルートパス
        """
        self.guide_root = guide_root
        self.templates_dir = guide_root / "templates"
        self.prompts_cache_dir = guide_root / "cache" / "claude_prompts"

        # ディレクトリ作成
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_cache_dir.mkdir(parents=True, exist_ok=True)

        # YAML設定
        self.yaml_processor = YAML()
        self.yaml_processor.preserve_quotes = True
        self.yaml_processor.width = 4096

    @performance_monitor("YamlClaudeQualityPromptRepository.generate_quality_check_prompt")
    def generate_quality_check_prompt(
        self, request: ClaudeQualityCheckRequest, template_type: str = "comprehensive"
    ) -> YamlPromptContent:
        """品質チェックプロンプト生成

        Args:
            request: 品質チェックリクエスト
            template_type: プロンプトテンプレート種別

        Returns:
            YamlPromptContent: 生成されたYAMLプロンプト

        Raises:
            ValueError: 無効なリクエストまたはテンプレート種別
            RuntimeError: プロンプト生成エラー
        """
        if template_type not in self.get_available_templates():
            msg = f"無効なテンプレート種別: {template_type}"
            raise ValueError(msg)

        try:
            # メタデータ作成
            metadata = self._create_prompt_metadata(request, template_type)

            # カスタム要件抽出
            custom_requirements = self._extract_custom_requirements(request)

            # YAMLコンテンツ生成
            yaml_content = self._generate_yaml_structure(metadata, request, template_type, custom_requirements)

            # 検証
            validation_passed = self.validate_prompt_structure(
                YamlPromptContent.create_from_yaml_string(yaml_content, metadata, custom_requirements, False)
            )

            return YamlPromptContent.create_from_yaml_string(
                yaml_content, metadata, custom_requirements, validation_passed
            )

        except Exception as e:
            msg = f"プロンプト生成エラー: {e!s}"
            raise RuntimeError(msg) from e

    @performance_monitor("YamlClaudeQualityPromptRepository.save_prompt_with_validation")
    def save_prompt_with_validation(self, yaml_content: YamlPromptContent, output_path: Path) -> None:
        """プロンプト検証付き保存

        Args:
            yaml_content: 保存するYAMLプロンプト
            output_path: 保存先パス

        Raises:
            ValueError: 無効なYAMLコンテンツ
            IOError: ファイル保存エラー
        """
        if not yaml_content.is_validated():
            msg = "YAMLコンテンツの検証が失敗しています"
            raise ValueError(msg)

        try:
            # ディレクトリ作成
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイル保存
            output_path.write_text(yaml_content.raw_yaml_content, encoding="utf-8")

            # キャッシュ更新
            self._update_prompt_cache(yaml_content, output_path)

        except Exception as e:
            msg = f"ファイル保存エラー: {e!s}"
            raise OSError(msg) from e

    @performance_monitor("YamlClaudeQualityPromptRepository.load_prompt_from_file")
    def load_prompt_from_file(self, file_path: Path) -> YamlPromptContent:
        """ファイルからプロンプト読み込み

        Args:
            file_path: プロンプトファイルパス

        Returns:
            YamlPromptContent: 読み込まれたプロンプト

        Raises:
            FileNotFoundError: ファイルが存在しない
            ValueError: 無効なYAML形式
        """
        if not file_path.exists():
            msg = f"プロンプトファイルが存在しません: {file_path}"
            raise FileNotFoundError(msg)

        try:
            yaml_content = file_path.read_text(encoding="utf-8")
            yaml_data: dict[str, Any] = yaml.safe_load(yaml_content)

            # メタデータ抽出
            metadata_dict = yaml_data.get("metadata", {})
            metadata = YamlPromptMetadata(
                title=metadata_dict.get("title", "Unknown"),
                project=metadata_dict.get("project", "Unknown"),
                episode_file=metadata_dict.get("episode_file", "Unknown"),
                genre=metadata_dict.get("genre", "ファンタジー"),
                word_count=str(metadata_dict.get("word_count", "4000")),
                viewpoint=metadata_dict.get("viewpoint", "三人称単元視点"),
                viewpoint_character=metadata_dict.get("viewpoint_character", "Unknown"),
                detail_level=metadata_dict.get("detail_level", "detailed"),
                methodology=metadata_dict.get("methodology", "stepwise"),
                generated_at=metadata_dict.get("generated_at", datetime.now(timezone.utc).isoformat()),
            )

            # カスタム要件抽出
            custom_requirements = yaml_data.get("custom_requirements", [])

            return YamlPromptContent.create_from_yaml_string(
                yaml_content, metadata, custom_requirements, validation_passed=True
            )

        except Exception as e:
            msg = f"無効なYAML形式: {e!s}"
            raise ValueError(msg) from e

    def get_available_templates(self) -> list[str]:
        """利用可能テンプレート一覧取得

        Returns:
            List[str]: テンプレート種別一覧
        """
        return [
            "comprehensive",  # AI特化総合品質チェック（改良済み）
            "creative_focus",  # 創作品質重点
            "reader_experience",  # なろう系読者体験特化（改良済み）
            "structural",  # 構成重点
            "quick",  # 簡易チェック
            "debug",  # デバッグ用
            "consistency_analysis",  # AI特化一貫性分析（新規）
            "emotional_depth_analyzer",  # 感情表現深度AI分析（新規）
        ]

    def validate_prompt_structure(self, yaml_content: YamlPromptContent) -> bool:
        """プロンプト構造検証

        Args:
            yaml_content: 検証対象プロンプト

        Returns:
            bool: 検証結果（True=正常、False=異常）
        """
        try:
            yaml_data: dict[str, Any] = yaml.safe_load(yaml_content.raw_yaml_content)

            # 必須セクション確認
            required_sections = ["metadata", "task_definition", "evaluation_criteria", "custom_requirements"]

            for section in required_sections:
                if section not in yaml_data:
                    return False

            # メタデータ詳細確認
            metadata = yaml_data["metadata"]
            required_metadata = ["title", "project", "generated_at"]

            for field in required_metadata:
                if field not in metadata:
                    return False

            # 評価基準の存在確認
            criteria = yaml_data["evaluation_criteria"]
            return not (not isinstance(criteria, dict) or len(criteria) == 0)

        except Exception:
            return False

    def get_template_metadata(self, template_type: str) -> dict[str, any]:
        """テンプレートメタデータ取得

        Args:
            template_type: テンプレート種別

        Returns:
            Dict: テンプレートメタデータ

        Raises:
            ValueError: 存在しないテンプレート種別
            FileNotFoundError: テンプレートファイルが見つからない
        """
        if template_type not in self.get_available_templates():
            msg = f"存在しないテンプレート種別: {template_type}"
            raise ValueError(msg)

        # 外部YAMLテンプレートファイルから読み取り
        template_file = self.templates_dir / f"{template_type}.yaml"

        if not template_file.exists():
            msg = f"テンプレートファイルが見つかりません: {template_file}"
            raise FileNotFoundError(msg)

        try:
            with open(template_file, encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)

            # メタデータ部分を抽出
            if "metadata" not in template_data:
                msg = f"テンプレートファイルにmetadataセクションがありません: {template_file}"
                raise ValueError(msg)

            return template_data["metadata"]

        except yaml.YAMLError as e:
            msg = f"テンプレートファイルの解析エラー: {template_file}, {e!s}"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"テンプレートファイル読み取りエラー: {template_file}, {e!s}"
            raise ValueError(msg) from e

    def create_custom_template(self, template_name: str, base_template: str, customizations: dict[str, any]) -> str:
        """カスタムテンプレート作成

        Args:
            template_name: 新テンプレート名
            base_template: ベーステンプレート
            customizations: カスタマイズ内容

        Returns:
            str: 作成されたテンプレート種別

        Raises:
            ValueError: 無効なベーステンプレートまたはカスタマイズ内容
        """
        if base_template not in self.get_available_templates():
            msg = f"無効なベーステンプレート: {base_template}"
            raise ValueError(msg)

        # カスタマイズ検証
        valid_customizations = [
            "evaluation_criteria",
            "focus_areas",
            "word_count_range",
            "quality_threshold",
            "additional_requirements",
        ]

        for key in customizations:
            if key not in valid_customizations:
                msg = f"無効なカスタマイズキー: {key}"
                raise ValueError(msg)

        # カスタムテンプレート保存
        custom_template_path = self.templates_dir / f"{template_name}.yaml"

        try:
            base_metadata = self.get_template_metadata(base_template)

            # ベーステンプレートとカスタマイズのマージ
            custom_metadata = {
                **base_metadata,
                "name": template_name,
                "base_template": base_template,
                "customizations": customizations,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # YAML保存
            custom_template_path.write_text(
                yaml.dump(custom_metadata, allow_unicode=True, default_flow_style=False), encoding="utf-8"
            )

            return template_name

        except Exception as e:
            msg = f"カスタムテンプレート作成エラー: {e!s}"
            raise ValueError(msg) from e

    def get_prompt_history(self, episode_number: int, limit: int = 10) -> list[dict[str, any]]:
        """プロンプト履歴取得

        Args:
            episode_number: エピソード番号
            limit: 取得件数上限

        Returns:
            List[Dict]: プロンプト履歴情報
        """
        history_pattern = f"*{episode_number:03d}*.yaml"
        prompt_files = list(self.prompts_cache_dir.glob(history_pattern))

        # 更新日時でソート
        prompt_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        history = []
        for prompt_file in prompt_files[:limit]:
            try:
                stat_info = prompt_file.stat()
                yaml_content = self.load_prompt_from_file(prompt_file)

                history.append(
                    {
                        "file_path": str(prompt_file),
                        "episode_number": episode_number,
                        "template_type": yaml_content.metadata.methodology,
                        "created_at": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "file_size_kb": yaml_content.get_file_size_kb(),
                        "custom_requirements_count": len(yaml_content.custom_requirements),
                        "validation_passed": yaml_content.is_validated(),
                    }
                )

            except Exception:
                # 読み込みエラーは無視して続行
                continue

        return history

    def cleanup_old_prompts(self, days_threshold: int = 30) -> int:
        """古いプロンプトクリーンアップ

        Args:
            days_threshold: 保持日数閾値

        Returns:
            int: 削除されたファイル数
        """
        cutoff_time = time.time() - (days_threshold * 24 * 60 * 60)
        deleted_count = 0

        for prompt_file in self.prompts_cache_dir.glob("*.yaml"):
            try:
                if prompt_file.stat().st_mtime < cutoff_time:
                    prompt_file.unlink()
                    deleted_count += 1
            except Exception:
                # 削除エラーは無視して続行
                continue

        return deleted_count

    def _get_template_mapping(self) -> dict[str, str]:
        """動的にテンプレートマッピングを生成"""
        mapping = {}

        # 新ディレクトリ構造マッピング
        structure_map = {
            "writing": ["write_step*.yaml"],
            "quality/checks": ["check_step*.yaml"],
            "quality/analysis": ["comprehensive", "consistency_analysis",
                                "creative_focus", "emotional_depth_analyzer",
                                "quick", "reader_experience", "structural"],
            "plot": ["chapter_plot", "*プロット*"],
            "special": ["stage5_*", "self_triggering_*", "執筆品質*"],
            "legacy": ["debug", "step00_scope_definition"]
        }

        for subdir, patterns in structure_map.items():
            dir_path = self.templates_dir / subdir
            if dir_path.exists():
                for pattern in patterns:
                    if "*" in pattern:
                        # ワイルドカード処理：既に.yamlが含まれている場合は重複を避ける
                        search_pattern = pattern if pattern.endswith(".yaml") else f"{pattern}.yaml"
                        for file in dir_path.glob(search_pattern):
                            if file.is_file():
                                mapping[file.stem] = f"{subdir}/{file.name}"
                    else:
                        file_path = dir_path / f"{pattern}.yaml"
                        if file_path.exists():
                            mapping[pattern] = f"{subdir}/{pattern}.yaml"

        return mapping

    def export_prompt_collection(self, output_dir: Path, template_types: list[str] | None = None) -> Path:
        """プロンプトコレクション出力

        Args:
            output_dir: 出力ディレクトリ
            template_types: 出力対象テンプレート種別（None=全て）

        Returns:
            Path: 出力されたアーカイブファイルパス
        """
        if template_types is None:
            template_types = self.get_available_templates()

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_path = output_dir / f"claude_quality_prompts_{timestamp}.zip"

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # テンプレートファイル追加（新構造対応）
            template_mapping = self._get_template_mapping()
            for template_type in template_types:
                try:
                    if template_type in template_mapping:
                        rel_path = template_mapping[template_type]
                        template_path = self.templates_dir / rel_path
                        if template_path.exists():
                            zipf.write(template_path, f"templates/{rel_path}")
                    else:
                        # フォールバック：旧構造
                        template_path = self.templates_dir / f"{template_type}.yaml"
                        if template_path.exists():
                            zipf.write(template_path, f"templates/{template_type}.yaml")
                except Exception:
                    continue

            # キャッシュされたプロンプト追加
            for prompt_file in self.prompts_cache_dir.glob("*.yaml"):
                try:
                    relative_path = f"cache/{prompt_file.name}"
                    zipf.write(prompt_file, relative_path)
                except Exception:
                    continue

            # メタデータファイル追加
            metadata = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "template_types": template_types,
                "total_templates": len(template_types),
                "cache_files_count": len(list(self.prompts_cache_dir.glob("*.yaml"))),
                "generator": "YamlClaudeQualityPromptRepository",
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
                yaml.dump(metadata, tmp, allow_unicode=True, default_flow_style=False)
                tmp.flush()
                zipf.write(tmp.name, "metadata.yaml")

        return archive_path

    def get_prompt_statistics(self) -> dict[str, int]:
        """プロンプト統計情報取得

        Returns:
            Dict: 統計情報
        """
        template_files = list(self.templates_dir.glob("*.yaml"))
        cache_files = list(self.prompts_cache_dir.glob("*.yaml"))

        total_size = sum(f.stat().st_size for f in cache_files if f.exists())
        average_size = total_size // len(cache_files) if cache_files else 0

        # 最近の使用状況
        recent_cutoff = time.time() - (7 * 24 * 60 * 60)  # 7日以内
        recent_usage = sum(1 for f in cache_files if f.exists() and f.stat().st_mtime > recent_cutoff)

        return {
            "total_prompts": len(cache_files),
            "templates_count": len(template_files),
            "average_file_size": average_size,
            "recent_usage_count": recent_usage,
            "total_cache_size_mb": total_size // (1024 * 1024),
        }

    def _create_prompt_metadata(self, request: ClaudeQualityCheckRequest, template_type: str) -> YamlPromptMetadata:
        """プロンプトメタデータ作成"""
        # 新しいファイル名形式: 第000話_タイトル_品質チェック用
        request.episode_title.replace("第", "").replace("話", "")
        if "_" in request.episode_title:
            episode_part, title_part = request.episode_title.split("_", 1)
            formatted_title = f"{episode_part}_品質チェック用"
        else:
            formatted_title = f"{request.episode_title}_品質チェック用"

        return YamlPromptMetadata(
            title=formatted_title,
            project=request.manuscript_path.parent.parent.name,
            episode_file=request.manuscript_path.name,
            genre=request.genre,
            word_count=str(request.word_count),
            viewpoint=request.viewpoint,
            viewpoint_character=request.viewpoint or "主人公",
            detail_level="detailed",
            methodology=template_type,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _extract_custom_requirements(self, request: ClaudeQualityCheckRequest) -> list[str]:
        """カスタム要件抽出"""
        requirements = request.custom_focus_areas.copy()

        # 高優先度エピソード用の追加要件
        if request.is_high_priority_episode():
            requirements.extend(["離脱防止効果の重点評価", "引きの強さを詳細分析", "読者の継続意欲向上提案"])

        # 品質期待値に基づく要件
        expectations = request.get_quality_expectations()
        if expectations["creative_quality"] > 40:
            requirements.append("創作品質の厳格評価")

        return requirements

    def _generate_yaml_structure(
        self,
        metadata: YamlPromptMetadata,
        request: ClaudeQualityCheckRequest,
        template_type: str,
        custom_requirements: list[str],
    ) -> str:
        """YAML構造生成"""
        template_metadata = self.get_template_metadata(template_type)

        yaml_structure = {
            "metadata": {
                "title": metadata.title,
                "project": metadata.project,
                "episode_file": metadata.episode_file,
                "genre": metadata.genre,
                "word_count": metadata.word_count,
                "viewpoint": metadata.viewpoint,
                "viewpoint_character": metadata.viewpoint_character,
                "detail_level": metadata.detail_level,
                "methodology": metadata.methodology,
                "generated_at": metadata.generated_at,
            },
            "task_definition": {
                "objective": "Claude Codeによる小説原稿品質評価",
                "scope": template_metadata["description"],
                "evaluation_points": template_metadata["evaluation_points"],
                "complexity_level": template_metadata["complexity"],
            },
            "evaluation_criteria": self._generate_evaluation_criteria(template_type),
            "custom_requirements": custom_requirements,
            "quality_threshold": request.quality_threshold,
            "analysis_instructions": self._generate_analysis_instructions(template_type),
            "output_format": {
                "structure": "structured_json",
                "include_scores": True,
                "include_feedback": True,
                "include_suggestions": True,
            },
        }

        return yaml.dump(yaml_structure, allow_unicode=True, default_flow_style=False)

    def _generate_evaluation_criteria(self, template_type: str) -> dict[str, any]:
        """評価基準生成（外部テンプレートファイルから取得）"""
        template_file = self.templates_dir / f"{template_type}.yaml"

        if not template_file.exists():
            msg = f"テンプレートファイルが見つかりません: {template_file}"
            raise FileNotFoundError(msg)

        try:
            with open(template_file, encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)

            # evaluation_criteria部分を抽出
            if "evaluation_criteria" not in template_data:
                msg = f"テンプレートファイルにevaluation_criteriaセクションがありません: {template_file}"
                raise ValueError(msg)

            return template_data["evaluation_criteria"]

        except yaml.YAMLError as e:
            msg = f"テンプレートファイルの解析エラー: {template_file}, {e!s}"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"評価基準読み取りエラー: {template_file}, {e!s}"
            raise ValueError(msg) from e

    def _generate_analysis_instructions(self, template_type: str) -> list[str]:
        """分析指示生成（外部テンプレートファイルから取得）"""
        template_file = self.templates_dir / f"{template_type}.yaml"

        if not template_file.exists():
            msg = f"テンプレートファイルが見つかりません: {template_file}"
            raise FileNotFoundError(msg)

        try:
            with open(template_file, encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)

            # analysis_instructions部分を抽出
            if "analysis_instructions" not in template_data:
                msg = f"テンプレートファイルにanalysis_instructionsセクションがありません: {template_file}"
                raise ValueError(msg)

            return template_data["analysis_instructions"]

        except yaml.YAMLError as e:
            msg = f"テンプレートファイルの解析エラー: {template_file}, {e!s}"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"分析指示読み取りエラー: {template_file}, {e!s}"
            raise ValueError(msg) from e

    def _update_prompt_cache(self, yaml_content: YamlPromptContent, output_path: Path) -> None:
        """プロンプトキャッシュ更新"""
        cache_file = self.prompts_cache_dir / output_path.name

        try:
            # キャッシュファイル作成
            cache_file.write_text(yaml_content.raw_yaml_content, encoding="utf-8")

            # メタデータファイル作成
            metadata_file = cache_file.with_suffix(".meta.yaml")
            cache_metadata = {
                "original_path": str(output_path),
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "file_size_bytes": yaml_content.file_size_bytes,
                "validation_passed": yaml_content.validation_passed,
                "custom_requirements_count": len(yaml_content.custom_requirements),
            }

            metadata_file.write_text(
                yaml.dump(cache_metadata, allow_unicode=True, default_flow_style=False), encoding="utf-8"
            )

        except Exception:
            # キャッシュ更新エラーは無視（メイン処理に影響しない）
            pass


class YamlClaudeQualityResultRepository(ClaudeQualityResultRepository):
    """Claude品質チェック結果リポジトリ YAML実装

    品質チェック結果の永続化・履歴管理・統計分析を提供
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root

        # CommonPathServiceを使用してパス管理
        path_service = create_path_service(project_root)
        self.results_dir = path_service.get_management_dir() / "claude_quality_results"
        self.history_dir = self.results_dir / "history"
        self.stats_dir = self.results_dir / "statistics"

        # ディレクトリ作成
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.stats_dir.mkdir(parents=True, exist_ok=True)

    def save_quality_result(self, result: ClaudeQualityCheckResult, session_data: dict[str, any] | None = None) -> None:
        """品質チェック結果保存

        Args:
            result: 品質チェック結果
            session_data: セッション追加データ

        Raises:
            ValueError: 無効な結果データ
            IOError: 保存エラー
        """
        if not result.is_success:
            msg = "失敗した結果は保存できません"
            raise ValueError(msg)

        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            episode_num = result.request.episode_number.value

            # メイン結果ファイル
            result_file = self.results_dir / f"episode_{episode_num:03d}_{timestamp}.yaml"

            result_data: dict[str, Any] = {
                "metadata": {
                    "episode_number": episode_num,
                    "episode_title": result.request.episode_title,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                    "word_count": result.request.word_count,
                    "genre": result.request.genre,
                    "viewpoint": result.request.viewpoint,
                },
                "scores": {
                    "total_score": result.total_score,
                    "creative_quality_score": result.creative_quality_score,
                    "reader_experience_score": result.reader_experience_score,
                    "structural_coherence_score": result.structural_coherence_score,
                    "quality_grade": result.get_quality_grade(),
                    "meets_threshold": result.meets_quality_threshold(),
                },
                "feedback": {
                    "detailed_feedback": result.detailed_feedback,
                    "improvement_suggestions": result.improvement_suggestions,
                    "priority_improvements": result.get_priority_improvements(),
                },
                "execution_info": {
                    "execution_time_ms": result.execution_time_ms,
                    "custom_focus_areas": result.request.custom_focus_areas,
                    "quality_threshold": result.request.quality_threshold,
                },
            }

            # セッションデータ追加
            if session_data:
                result_data["session_data"] = session_data

            # YAML保存
            result_file.write_text(
                yaml.dump(result_data, allow_unicode=True, default_flow_style=False), encoding="utf-8"
            )

            # 履歴更新
            self._update_history(result, timestamp)

            # 統計更新
            self._update_statistics(result)

        except Exception as e:
            msg = f"結果保存エラー: {e!s}"
            raise OSError(msg) from e

    def load_quality_result(self, episode_number: int, timestamp: str | None = None) -> ClaudeQualityCheckResult | None:
        """品質チェック結果読み込み

        Args:
            episode_number: エピソード番号
            timestamp: 特定時刻（None=最新）

        Returns:
            ClaudeQualityCheckResult: 品質チェック結果（存在しない場合None）
        """
        try:
            if timestamp:
                result_file = self.results_dir / f"episode_{episode_number:03d}_{timestamp}.yaml"
                if not result_file.exists():
                    return None
            else:
                # 最新ファイル検索
                pattern = f"episode_{episode_number:03d}_*.yaml"
                result_files = list(self.results_dir.glob(pattern))
                if not result_files:
                    return None

                # 最新ファイル選択
                result_file = max(result_files, key=lambda f: f.stat().st_mtime)

            # YAML読み込み
            yaml.safe_load(result_file.read_text(encoding="utf-8"))

            # ClaudeQualityCheckResult再構築（簡略化実装）
            # 実際の実装では完全な再構築が必要
            return None  # TODO: 完全実装時に修正

        except Exception:
            return None

    def get_quality_history(self, episode_number: int, limit: int = 20) -> list[dict[str, any]]:
        """品質履歴取得

        Args:
            episode_number: エピソード番号
            limit: 取得件数上限

        Returns:
            List[Dict]: 品質履歴情報
        """
        pattern = f"episode_{episode_number:03d}_*.yaml"
        result_files = list(self.results_dir.glob(pattern))

        # 更新日時でソート
        result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        history = []
        for result_file in result_files[:limit]:
            try:
                result_data: dict[str, Any] = yaml.safe_load(result_file.read_text(encoding="utf-8"))

                history.append(
                    {
                        "timestamp": result_file.stem.split("_")[-1],
                        "total_score": result_data["scores"]["total_score"],
                        "quality_grade": result_data["scores"]["quality_grade"],
                        "meets_threshold": result_data["scores"]["meets_threshold"],
                        "execution_time_ms": result_data["execution_info"]["execution_time_ms"],
                        "improvement_count": len(result_data["feedback"]["improvement_suggestions"]),
                    }
                )

            except Exception:
                continue

        return history

    def get_quality_trends(self, start_episode: int, end_episode: int) -> dict[str, list[float]]:
        """品質トレンド取得

        Args:
            start_episode: 開始エピソード番号
            end_episode: 終了エピソード番号

        Returns:
            Dict: トレンドデータ
        """
        trends = {"total_scores": [], "creative_scores": [], "experience_scores": [], "structural_scores": []}

        for episode_num in range(start_episode, end_episode + 1):
            latest_result = self.load_quality_result(episode_num)
            if latest_result:
                trends["total_scores"].append(float(latest_result.total_score))
                trends["creative_scores"].append(float(latest_result.creative_quality_score))
                trends["experience_scores"].append(float(latest_result.reader_experience_score))
                trends["structural_scores"].append(float(latest_result.structural_coherence_score))

        return trends

    def calculate_improvement_rate(self, episode_number: int, comparison_count: int = 5) -> float | None:
        """改善率計算

        Args:
            episode_number: 基準エピソード番号
            comparison_count: 比較対象エピソード数

        Returns:
            float: 改善率（パーセント、データ不足時None）
        """
        if episode_number <= comparison_count:
            return None

        try:
            # 現在エピソードのスコア
            current_result = self.load_quality_result(episode_number)
            if not current_result:
                return None

            # 過去エピソードの平均スコア計算
            past_scores = []
            for past_episode in range(episode_number - comparison_count, episode_number):
                past_result = self.load_quality_result(past_episode)
                if past_result:
                    past_scores.append(past_result.total_score)

            if not past_scores:
                return None

            past_average = sum(past_scores) / len(past_scores)
            return ((current_result.total_score - past_average) / past_average) * 100

        except Exception:
            return None

    def get_weak_areas_analysis(self, episode_range: tuple[int, int]) -> dict[str, dict[str, any]]:
        """弱点分析取得

        Args:
            episode_range: 分析対象エピソード範囲

        Returns:
            Dict: 弱点分析結果
        """
        start_episode, end_episode = episode_range

        # カテゴリ別スコア収集
        category_scores = {"creative_quality": [], "reader_experience": [], "structural_coherence": []}

        for episode_num in range(start_episode, end_episode + 1):
            result = self.load_quality_result(episode_num)
            if result:
                category_scores["creative_quality"].append(result.creative_quality_score)
                category_scores["reader_experience"].append(result.reader_experience_score)
                category_scores["structural_coherence"].append(result.structural_coherence_score)

        # 弱点分析
        analysis = {"categories": {}, "patterns": {}, "recommendations": []}

        for category, scores in category_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                max_possible = {"creative_quality": 40, "reader_experience": 35, "structural_coherence": 25}

                analysis["categories"][category] = {
                    "average_score": avg_score,
                    "max_possible": max_possible[category],
                    "achievement_rate": (avg_score / max_possible[category]) * 100,
                    "is_weak_area": avg_score < (max_possible[category] * 0.7),
                }

        # 改善推奨事項生成
        for category, stats in analysis["categories"].items():
            if stats["is_weak_area"]:
                recommendations = {
                    "creative_quality": "感情表現の身体感覚化とキャラクター個性の強化",
                    "reader_experience": "段落の短縮化とメタ発言の削除",
                    "structural_coherence": "シーン目的の明確化と接続詞の適切な使用",
                }
                analysis["recommendations"].append(recommendations[category])

        return analysis

    def cleanup_old_results(self, retention_days: int = 90) -> int:
        """古い結果クリーンアップ

        Args:
            retention_days: 保持日数

        Returns:
            int: 削除された結果数
        """
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        deleted_count = 0

        for result_file in self.results_dir.glob("*.yaml"):
            try:
                if result_file.stat().st_mtime < cutoff_time:
                    result_file.unlink()
                    deleted_count += 1
            except Exception:
                continue

        return deleted_count

    def _update_history(self, result: ClaudeQualityCheckResult, timestamp: str) -> None:
        """履歴更新"""
        episode_num = result.request.episode_number.value
        history_file = self.history_dir / f"episode_{episode_num:03d}_history.yaml"

        try:
            # 既存履歴読み込み
            if history_file.exists():
                history_data: dict[str, Any] = yaml.safe_load(history_file.read_text(encoding="utf-8"))
            else:
                history_data: dict[str, Any] = {"episode_number": episode_num, "entries": []}

            # 新エントリ追加
            new_entry = {
                "timestamp": timestamp,
                "total_score": result.total_score,
                "quality_grade": result.get_quality_grade(),
                "execution_time_ms": result.execution_time_ms,
            }

            history_data["entries"].append(new_entry)

            # 履歴保存（最新50件まで保持）
            history_data["entries"] = history_data["entries"][-50:]

            history_file.write_text(
                yaml.dump(history_data, allow_unicode=True, default_flow_style=False), encoding="utf-8"
            )

        except Exception:
            # 履歴更新エラーは無視
            pass

    def _update_statistics(self, result: ClaudeQualityCheckResult) -> None:
        """統計更新"""
        stats_file = self.stats_dir / "overall_statistics.yaml"

        try:
            # 既存統計読み込み
            if stats_file.exists():
                stats_data: dict[str, Any] = yaml.safe_load(stats_file.read_text(encoding="utf-8"))
            else:
                stats_data: dict[str, Any] = {
                    "total_evaluations": 0,
                    "average_scores": {"total": 0.0, "creative": 0.0, "experience": 0.0, "structural": 0.0},
                    "quality_distribution": {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0},
                    "last_updated": None,
                }

            # 統計更新
            total_count = stats_data["total_evaluations"]

            # 平均スコア更新（重み付き平均）
            stats_data["average_scores"]["total"] = (
                stats_data["average_scores"]["total"] * total_count + result.total_score
            ) / (total_count + 1)

            stats_data["average_scores"]["creative"] = (
                stats_data["average_scores"]["creative"] * total_count + result.creative_quality_score
            ) / (total_count + 1)

            stats_data["average_scores"]["experience"] = (
                stats_data["average_scores"]["experience"] * total_count + result.reader_experience_score
            ) / (total_count + 1)

            stats_data["average_scores"]["structural"] = (
                stats_data["average_scores"]["structural"] * total_count + result.structural_coherence_score
            ) / (total_count + 1)

            # 品質分布更新
            grade = result.get_quality_grade()[0]  # "S（出版レベル）" -> "S"
            stats_data["quality_distribution"][grade] += 1

            stats_data["total_evaluations"] += 1
            stats_data["last_updated"] = datetime.now(timezone.utc).isoformat()

            # 統計保存
            stats_file.write_text(yaml.dump(stats_data, allow_unicode=True, default_flow_style=False), encoding="utf-8")

        except Exception:
            # 統計更新エラーは無視
            pass
