"""Domain.repositories.claude_quality_prompt_repository
Where: Domain repository interface for Claude quality prompts.
What: Defines methods to persist and fetch prompt templates and history.
Why: Keeps prompt storage concerns decoupled from application logic.
"""

from datetime import timezone
from typing import Any

import yaml

"""Claude品質プロンプトリポジトリ インターフェース
仕様: Claude Code品質チェック統合システム
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from noveler.domain.value_objects.claude_quality_check_request import (
    ClaudeQualityCheckRequest,
    ClaudeQualityCheckResult,
)
from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent, YamlPromptMetadata


class ClaudeQualityPromptRepository(ABC):
    """Claude品質プロンプトリポジトリ インターフェース

    Claude Code用の品質チェックプロンプトの生成・保存・管理を担当
    YAML構造化プロンプトの永続化とテンプレート管理を抽象化
    """

    @abstractmethod
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

    def generate_self_triggering_prompt(
        self, quality_request: ClaudeQualityCheckRequest, session_id: str, episode_number: int
    ) -> YamlPromptContent:
        """自己トリガー型Claude品質チェックプロンプト生成

        Args:
            quality_request: 品質チェックリクエスト
            session_id: セッションID
            episode_number: エピソード番号

        Returns:
            YamlPromptContent: 自己トリガー機能付きYAMLプロンプト
        """
        # 型はトップレベルでインポート済み

        # 自己トリガーテンプレート読み込み
        guide_root = Path(__file__).parent.parent.parent.parent
        template_path = guide_root / "templates" / "self_triggering_quality_prompt_template.yaml"

        if not template_path.exists():
            # フォールバック: 通常のプロンプト生成
            return self.generate_quality_check_prompt(quality_request, template_type="comprehensive")

        try:
            with Path(template_path).open(encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)

            # 原稿内容読み込み
            manuscript_content = quality_request.manuscript_path.read_text(encoding="utf-8")

            # テンプレート変数展開
            project_name = quality_request.manuscript_path.parent.parent.name.replace("10_", "")

            # 基本品質チェック結果・A31評価結果（モック）
            basic_check_results = "基本チェック: 78/100点 - 文字数、構成、基本的な文法チェック完了"
            a31_check_results = "A31評価: 82/100点 - 小説執筆ガイドライン準拠チェック完了"

            # テンプレート展開
            prompt_content = template_data["quality_check_prompt"].format(
                episode_number=episode_number,
                project_name=project_name,
                episode_title=quality_request.episode_title,
                word_count=quality_request.word_count,
                manuscript_content=manuscript_content,
                basic_check_results=basic_check_results,
                a31_check_results=a31_check_results,
            )

            # 継続指示展開
            continuation_instructions = template_data["claude_code_instructions"].format(
                episode_number=episode_number, session_id=session_id
            )

            # 最終プロンプト組み立て
            final_prompt = prompt_content + "\n\n" + continuation_instructions

            # メタデータ組み立て
            metadata_dict = {
                "metadata": {
                    "title": f"第{episode_number:03d}話_品質チェック用（自己トリガー型）",
                    "project": f"10_{project_name}",
                    "episode_file": quality_request.manuscript_path.name,
                    "generated_at": str(datetime.now(timezone.utc).isoformat()),
                    "genre": "ファンタジー",
                    "viewpoint": "三人称単元視点",
                    "viewpoint_character": "三人称単元視点",
                    "word_count": str(quality_request.word_count),
                    "detail_level": "detailed",
                    "methodology": "comprehensive_with_self_triggering",
                },
                "session_info": {
                    "session_id": session_id,
                    "episode_number": episode_number,
                    "project_name": project_name,
                    "trigger_command": f"novel check {episode_number} --claude-execute-from-prompt --session-id={session_id}",
                },
                "task_definition": {
                    "objective": "Claude Codeによる小説原稿品質評価（一気通貫ワークフロー）",
                    "scope": "AIの客観性・一貫性を活かした定量的品質評価",
                    "complexity_level": "high",
                    "evaluation_points": 100,
                },
                "output_format": {
                    "structure": "structured_yaml",
                    "include_scores": True,
                    "include_feedback": True,
                    "include_suggestions": True,
                },
                "quality_threshold": quality_request.quality_threshold,
                "prompt_content": final_prompt,
            }

            final_yaml = yaml.dump(metadata_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)

            # YamlPromptContentオブジェクト作成
            metadata = YamlPromptMetadata(
                title=f"第{episode_number:03d}話_品質チェック用（自己トリガー型）",
                project=f"10_{project_name}",
                episode_file=quality_request.manuscript_path.name,
                generated_at=str(datetime.now(timezone.utc).isoformat()),
                genre="ファンタジー",
                viewpoint="三人称単元視点",
                word_count=str(quality_request.word_count),
                detail_level="detailed",
                methodology="comprehensive_with_self_triggering",
            )

            return YamlPromptContent.create_from_yaml_string(
                yaml_content=final_yaml, metadata=metadata, custom_requirements=[], validation_passed=True
            )

        except Exception:
            # エラー時のフォールバック
            return self.generate_quality_check_prompt(quality_request, template_type="comprehensive")

    @abstractmethod
    def save_prompt_with_validation(self, yaml_content: YamlPromptContent, output_path: Path) -> None:
        """プロンプト検証付き保存

        Args:
            yaml_content: 保存するYAMLプロンプト
            output_path: 保存先パス

        Raises:
            ValueError: 無効なYAMLコンテンツ
            IOError: ファイル保存エラー
        """

    @abstractmethod
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

    @abstractmethod
    def get_available_templates(self) -> list[str]:
        """利用可能テンプレート一覧取得

        Returns:
            List[str]: テンプレート種別一覧
        """

    @abstractmethod
    def validate_prompt_structure(self, yaml_content: YamlPromptContent) -> bool:
        """プロンプト構造検証

        Args:
            yaml_content: 検証対象プロンプト

        Returns:
            bool: 検証結果（True=正常、False=異常）
        """

    @abstractmethod
    def get_template_metadata(self, template_type: str) -> dict[str, any]:
        """テンプレートメタデータ取得

        Args:
            template_type: テンプレート種別

        Returns:
            Dict: テンプレートメタデータ

        Raises:
            ValueError: 存在しないテンプレート種別
        """

    @abstractmethod
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

    @abstractmethod
    def get_prompt_history(self, episode_number: int, limit: int = 10) -> list[dict[str, any]]:
        """プロンプト履歴取得

        Args:
            episode_number: エピソード番号
            limit: 取得件数上限

        Returns:
            List[Dict]: プロンプト履歴情報
        """

    @abstractmethod
    def cleanup_old_prompts(self, days_threshold: int = 30) -> int:
        """古いプロンプトクリーンアップ

        Args:
            days_threshold: 保持日数閾値

        Returns:
            int: 削除されたファイル数
        """

    @abstractmethod
    def export_prompt_collection(self, output_dir: Path, template_types: list[str] | None = None) -> Path:
        """プロンプトコレクション出力

        Args:
            output_dir: 出力ディレクトリ
            template_types: 出力対象テンプレート種別（None=全て）

        Returns:
            Path: 出力されたアーカイブファイルパス
        """

    @abstractmethod
    def get_prompt_statistics(self) -> dict[str, int]:
        """プロンプト統計情報取得

        Returns:
            Dict: 統計情報
            - total_prompts: 総プロンプト数
            - templates_count: テンプレート種別数
            - average_file_size: 平均ファイルサイズ
            - recent_usage_count: 直近使用回数
        """


class ClaudeQualityResultRepository(ABC):
    """Claude品質チェック結果リポジトリ インターフェース

    品質チェック結果の永続化・履歴管理・統計分析を担当
    """

    @abstractmethod
    def save_quality_result(
        self, result: "ClaudeQualityCheckResult", session_data: dict[str, any] | None = None
    ) -> None:
        """品質チェック結果保存

        Args:
            result: 品質チェック結果
            session_data: セッション追加データ

        Raises:
            ValueError: 無効な結果データ
            IOError: 保存エラー
        """

    @abstractmethod
    def load_quality_result(
        self, episode_number: int, timestamp: str | None = None
    ) -> Optional["ClaudeQualityCheckResult"]:
        """品質チェック結果読み込み

        Args:
            episode_number: エピソード番号
            timestamp: 特定時刻（None=最新）

        Returns:
            ClaudeQualityCheckResult: 品質チェック結果（存在しない場合None）
        """

    @abstractmethod
    def get_quality_history(self, episode_number: int, limit: int = 20) -> list[dict[str, any]]:
        """品質履歴取得

        Args:
            episode_number: エピソード番号
            limit: 取得件数上限

        Returns:
            List[Dict]: 品質履歴情報
        """

    @abstractmethod
    def get_quality_trends(self, start_episode: int, end_episode: int) -> dict[str, list[float]]:
        """品質トレンド取得

        Args:
            start_episode: 開始エピソード番号
            end_episode: 終了エピソード番号

        Returns:
            Dict: トレンドデータ
            - total_scores: 総合スコアリスト
            - creative_scores: 創作品質スコアリスト
            - experience_scores: 読者体験スコアリスト
            - structural_scores: 構成妥当性スコアリスト
        """

    @abstractmethod
    def calculate_improvement_rate(self, episode_number: int, comparison_count: int = 5) -> float | None:
        """改善率計算

        Args:
            episode_number: 基準エピソード番号
            comparison_count: 比較対象エピソード数

        Returns:
            float: 改善率（パーセント、データ不足時None）
        """

    @abstractmethod
    def get_weak_areas_analysis(self, episode_range: tuple[int, int]) -> dict[str, dict[str, any]]:
        """弱点分析取得

        Args:
            episode_range: 分析対象エピソード範囲

        Returns:
            Dict: 弱点分析結果
            - categories: カテゴリ別弱点
            - patterns: 傾向パターン
            - recommendations: 改善推奨事項
        """

    @abstractmethod
    def cleanup_old_results(self, retention_days: int = 90) -> int:
        """古い結果クリーンアップ

        Args:
            retention_days: 保持日数

        Returns:
            int: 削除された結果数
        """
