"""Application.use_cases.enhanced_plot_generation_use_case
Where: Application use case handling enhanced plot generation requests.
What: Drives domain services to synthesize plot structures, evaluate quality, and persist outputs.
Why: Streamlines plot creation workflows while ensuring quality controls stay consistent.
"""

from __future__ import annotations


from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.repository_factory_protocol import IRepositoryFactory
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.contextual_plot_generation import ContextualPlotResult, PlotGenerationConfig
from noveler.domain.services.enhanced_plot_generation_service import EnhancedPlotGenerationService
from noveler.domain.value_objects.chapter_number import ChapterNumber
from noveler.domain.value_objects.episode_number import EpisodeNumber

# DDD準拠: Infrastructure層への直接依存を除去
# from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory

# DDD Clean Architecture準拠:
# - Infrastructure/Presentationレイヤーへの直接依存を除去
# - 依存性注入パターンでインターフェース経由のアクセスを実現


if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.repository_factory import IRepositoryFactory
    from noveler.infrastructure.unit_of_work import IUnitOfWork

@dataclass
class EnhancedPlotGenerationResult:
    """拡張プロット生成結果"""

    success: bool
    episode_number: int
    generated_plot: str = ""
    plot_file_path: str = ""
    execution_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)
    error_message: str = ""
    execution_mode: str = ""
    prompt_content: str = ""
    saved_file_path: str = ""
    quality_score: float = 0.0

    @property
    def is_manual_execution_required(self) -> bool:
        """手動実行が必要かどうかを判定"""
        return self.execution_mode in ["prompt_only", "fallback"] or self.metadata.get(
            "requires_manual_execution", False
        )

    def get_execution_summary(self) -> str:
        """実行サマリー取得"""
        if self.success:
            return f"第{self.episode_number}話プロット生成成功 ({self.execution_time_ms:.1f}ms)"
        return f"第{self.episode_number}話プロット生成失敗: {self.error_message}"


class EnhancedPlotGenerationUseCase(AbstractUseCase[dict, ContextualPlotResult]):
    """拡張プロット生成ユースケース

    責務:
        - 章プロット情報に基づく文脈考慮型エピソードプロット生成
        - 品質評価指標の計算と改善レコメンデーション提供
        - バッチ処理と再生成による品質向上サポート

    設計原則:
        - SPEC-PLOT-004準拠のコンテキスト駆動プロット生成
        - DDD層分離: Application層としてDomain/Infrastructureを協調
        - B30品質作業指示書準拠: DI/Repository Pattern完全適用

    依存関係:
        - EnhancedPlotGenerationService（Domain層）
        - IRepositoryFactory（DI経由で注入）
        - Configuration Manager（環境変数アクセス）
    """

    def __init__(self,
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        enhanced_service: EnhancedPlotGenerationService | None = None,
        repository_factory: IRepositoryFactory | None = None,
        **kwargs) -> None:
        """ユースケース初期化（DDD準拠）

        Args:
            enhanced_service: 拡張プロット生成サービス(DI)
            repository_factory: 統合リポジトリファクトリー（DI対応）
            **kwargs: AbstractUseCaseの引数

        Raises:
            ValueError: Repository Factoryが注入されていない場合
        """
        # 基底クラス初期化
        super().__init__(**kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work


        # DDD原則：Repository Factory Interface経由の依存注入
        self._repository_factory = repository_factory or self._create_default_factory()

        # ドメインサービス（DI または デフォルト作成）
        self._enhanced_service = enhanced_service or EnhancedPlotGenerationService()

        # DDD準拠：統合ファクトリー経由でリポジトリ作成
        self._chapter_repository = self._repository_factory.create_yaml_chapter_plot_repository()
        self._result_repository = self._repository_factory.create_enhanced_plot_result_repository()

    def _get_configuration_manager(self) -> Any:
        """Configuration Managerの遅延初期化"""
        # DDD準拠: AbstractUseCaseの基底プロパティを使用
        return self.config_service

    def _create_default_factory(self) -> None:
        """デフォルトファクトリー作成（後方互換性維持）

        Note:
            DI Container実装後は削除予定。
            Application Factory Interface経由での注入に移行。
        """
        # TODO: DI - Remove Infrastructure DI import
        # Should use Application Factory Interface instead
        # DDD準拠: AbstractUseCaseの基底プロパティを使用
        return self.repository_factory

    def generate_enhanced_episode_plot(
        self,
        episode_number: int,
        config: PlotGenerationConfig | None = None,
        save_result: bool = True,
        project_root: Path | None = None,
    ) -> ContextualPlotResult:
        """拡張エピソードプロット生成の完全実行

        処理フロー:
            1. 入力検証とパラメータ正規化
            2. プロジェクトルート検出・設定
            3. 章プロット情報取得（推定/フォールバック含む）
            4. コンテキスト考慮型プロット生成
            5. 結果保存と品質評価レポート生成

        Args:
            episode_number: 対象エピソード番号（1以上の整数）
            config: プロット生成設定（省略時はデフォルト使用）
            save_result: 結果保存フラグ（デフォルト: True）
            project_root: プロジェクトルートパス（省略時は自動検出）

        Returns:
            ContextualPlotResult: 品質評価付き拡張プロット結果

        Raises:
            ValueError: 無効なエピソード番号
            ChapterPlotNotFoundError: 章プロット情報が見つからない
            PlotGenerationError: プロット生成処理エラー
        """
        # 1. 入力検証
        if episode_number <= 0:
            msg = f"Invalid episode number: {episode_number}"
            raise ValueError(msg)

        episode_num = EpisodeNumber(episode_number)
        generation_config: dict[str, Any] = config or self._create_default_config()

        # 2. プロジェクトルートの設定
        effective_project_root = project_root or self._detect_project_root()
        self._chapter_repository.set_project_root(effective_project_root)
        self._result_repository.set_project_root(effective_project_root)

        try:
            # 3. 章プロット情報の取得
            chapter_plot = self._get_chapter_plot_for_episode(episode_num)

            # 4. 拡張プロット生成の実行
            result = self._enhanced_service.generate_contextual_plot(
                episode_number=episode_num, chapter_plot=chapter_plot, config=generation_config
            )

            # 5. 生成結果の保存
            if save_result:
                self._save_generation_result(result, effective_project_root)

            # 6. 品質評価レポートの生成
            quality_report = self._generate_quality_report(result)
            result.metadata.update({"quality_report": quality_report})

            return result

        except Exception as e:
            # エラーログ記録とユーザーフレンドリーなエラーメッセージ
            self._log_generation_error(episode_number, str(e))
            raise

    def batch_generate_enhanced_plots(
        self, episode_numbers: list[int], config: PlotGenerationConfig | None = None, project_root: Path | None = None
    ) -> dict[int, ContextualPlotResult]:
        """複数エピソードの一括拡張プロット生成

        特徴:
            - 並列処理なし（順次処理で安定性優先）
            - エラー時も継続処理
            - 処理サマリー自動出力

        Args:
            episode_numbers: 対象エピソード番号リスト
            config: プロット生成設定（全エピソード共通）
            project_root: プロジェクトルートパス

        Returns:
            Dict[int, ContextualPlotResult]: エピソード番号をキーとした生成結果マップ
        """
        results: dict[str, Any] = {}
        failed_episodes = []

        for episode_num in episode_numbers:
            try:
                result = self.generate_enhanced_episode_plot(
                    episode_number=episode_num, config=config, save_result=True, project_root=project_root
                )

                results[episode_num] = result

            except Exception as e:
                failed_episodes.append((episode_num, str(e)))
                self.logger.exception(f"Episode {episode_num} generation failed: {e}")

        # バッチ処理結果のサマリー
        self.logger.info(f"Batch generation completed: {len(results)} succeeded, {len(failed_episodes)} failed")
        if failed_episodes:
            self.logger.warning(f"Failed episodes: {failed_episodes}")

        return results

    def get_generation_history(self, episode_number: int | None = None, limit: int = 10) -> list[ContextualPlotResult]:
        """生成履歴の取得

        Args:
            episode_number: 特定エピソード番号（省略時は全エピソード）
            limit: 取得件数制限（デフォルト: 10）

        Returns:
            list[ContextualPlotResult]: 生成履歴リスト（新しい順）
        """
        return self._result_repository.get_generation_history(episode_number=episode_number, limit=limit)

    def regenerate_with_improved_quality(
        self, episode_number: int, quality_threshold: float = 85.0, max_attempts: int = 3
    ) -> ContextualPlotResult:
        """品質向上を目指した再生成

        アルゴリズム:
            - 指定閾値達成まで最大N回試行
            - 試行ごとに設定を段階的に調整
            - 最良結果を保存して返却

        Args:
            episode_number: 対象エピソード番号
            quality_threshold: 品質閾値（0-100）
            max_attempts: 最大試行回数

        Returns:
            ContextualPlotResult: 品質改善された生成結果
        """
        best_result = None
        best_score = 0.0

        for attempt in range(max_attempts):
            try:
                # 試行ごとに少しずつ設定を調整
                config = self._create_quality_focused_config(attempt)

                result = self.generate_enhanced_episode_plot(
                    episode_number=episode_number,
                    config=config,
                    save_result=False,  # 最終結果のみ保存
                )

                current_score = result.quality_indicators.overall_score or 0.0

                if current_score >= quality_threshold:
                    # 閾値達成時は即座に返す
                    self._save_generation_result(result, self._detect_project_root())
                    return result

                if current_score > best_score:
                    best_result = result
                    best_score = current_score

            except Exception as e:
                self.logger.warning(f"Regeneration attempt {attempt + 1} failed: {e}")
                continue

        # 最良の結果を保存して返す
        if best_result:
            self._save_generation_result(best_result, self._detect_project_root())
            return best_result
        # 全て失敗した場合はデフォルト設定で最後の試行
        return self.generate_enhanced_episode_plot(episode_number)

    def _get_chapter_plot_for_episode(self, episode_number: EpisodeNumber) -> ChapterPlot:
        """エピソードに対応する章プロット情報の取得

        取得戦略:
            1. エピソード番号から章番号を推定
            2. リポジトリから章プロット取得試行
            3. 失敗時はフォールバック章プロット生成

        Args:
            episode_number: エピソード番号

        Returns:
            ChapterPlot: 対応章プロット情報
        """
        # 章番号の推定(エピソード番号から章を推定)
        estimated_chapter_number = self._estimate_chapter_number(episode_number)

        try:
            chapter_plot = self._chapter_repository.find_by_chapter_number(estimated_chapter_number)
        except Exception:
            # 章プロットが見つからない場合のフォールバック
            chapter_plot = self._create_fallback_chapter_plot(estimated_chapter_number, episode_number)

        return chapter_plot

    def _estimate_chapter_number(self, episode_number: EpisodeNumber) -> ChapterNumber:
        """エピソード番号から章番号を正確に推定

        推定ロジック:
            1. ChapterStructureService経由で正確な章構成取得（未実装）
            2. フォールバック: 既知の章構成に基づく推定
            3. 緊急フォールバック: 20話単位の基本推定

        Args:
            episode_number: エピソード番号

        Returns:
            ChapterNumber: 推定章番号
        """
        from noveler.domain.value_objects.chapter_number import ChapterNumber

        try:
            # ChapterStructureServiceを使用して正確な章情報を取得
            # TODO: DI - IChapterStructureService injection required
            # 基本実装: エピソード番号から章番号を推定（1章10話想定）
            estimated_chapter = (episode_number - 1) // 10 + 1
            return ChapterNumber(estimated_chapter)

        except Exception:
            # フォールバック: 従来の推定ロジック（ただしより正確に）
            pass

        # 緊急フォールバック: 既知の構成に基づく推定

        if 1 <= episode_number.value <= 20:
            return ChapterNumber(1)  # 第1章: DEBUGログ覚醒編
        if 21 <= episode_number.value <= 80:
            return ChapterNumber(2)  # 第2章: The Architects謎解き編
        if 81 <= episode_number.value <= 100:
            return ChapterNumber(3)  # 第3章: 新生The Architects編
        # 想定外の範囲: 基本推定ロジック
        estimated_number = ((episode_number.value - 1) // 20) + 1
        return ChapterNumber(min(estimated_number, 3))  # 最大3章まで  # 最大3章まで

    def _create_fallback_chapter_plot(
        self, chapter_number: ChapterNumber, episode_number: EpisodeNumber
    ) -> ChapterPlot:
        """フォールバック章プロット作成

        用途:
            章プロット情報が取得できない場合の緊急対応
            最小限の情報で処理継続を保証

        Args:
            chapter_number: 章番号
            episode_number: エピソード番号

        Returns:
            ChapterPlot: フォールバック章プロット
        """
        return ChapterPlot(
            chapter_number=chapter_number,
            title=f"chapter{chapter_number.value:02d}",
            summary=f"chapter{chapter_number.value:02d}の概要(自動生成)",
            key_events=[f"episode{episode_number.value:03d}の主要イベント"],
            episodes=[
                {
                    "episode_number": episode_number.value,
                    "title": f"episode{episode_number.value:03d}",
                    "summary": "エピソード概要(自動推定)",
                }
            ],
            central_theme="物語の展開",
            viewpoint_management={"primary": "主人公視点"},
        )

    def _create_default_config(self) -> PlotGenerationConfig:
        """デフォルト設定の作成

        設定値:
            - 目標文字数: 6000文字
            - 技術精度チェック: 有効
            - キャラクター一貫性: 有効
            - シーン構造強化: 有効

        Returns:
            PlotGenerationConfig: デフォルト設定
        """
        return PlotGenerationConfig(
            target_word_count=6000,
            technical_accuracy_required=True,
            character_consistency_check=True,
            scene_structure_enhanced=True,
        )

    def _create_quality_focused_config(self, attempt: int) -> PlotGenerationConfig:
        """品質重視設定の作成

        調整戦略:
            - 試行回数に応じて詳細度を段階的に向上
            - 最大8000文字まで拡張可能

        Args:
            attempt: 試行回数（0から開始）

        Returns:
            PlotGenerationConfig: 品質重視設定
        """
        base_word_count = 6000
        word_count_adjustment = attempt * 500  # 試行ごとに詳細度を上げる

        return PlotGenerationConfig(
            target_word_count=min(base_word_count + word_count_adjustment, 8000),
            technical_accuracy_required=True,
            character_consistency_check=True,
            scene_structure_enhanced=True,
        )

    def _save_generation_result(self, result: ContextualPlotResult, project_root: Path) -> None:
        """生成結果の保存

        エラーハンドリング:
            保存失敗時もプロセス継続（ログ出力のみ）

        Args:
            result: 生成結果
            project_root: プロジェクトルートパス
        """
        try:
            self._result_repository.save_result(result)
            self.logger.info(f"Enhanced plot for episode {result.episode_number.value} saved successfully")

        except Exception as e:
            self.logger.exception(f"Failed to save generation result: {e}")
            # 保存に失敗してもプロセスは継続

    def _generate_quality_report(self, result: ContextualPlotResult) -> dict[str, Any]:
        """品質評価レポートの生成

        レポート内容:
            - 総合スコアと個別指標
            - 品質グレード（A+〜D）
            - 改善推奨事項リスト

        Args:
            result: 生成結果

        Returns:
            Dict[str, Any]: 品質評価レポート
        """
        indicators = result.quality_indicators

        return {
            "overall_score": indicators.overall_score,
            "technical_accuracy": indicators.technical_accuracy,
            "character_consistency": indicators.character_consistency,
            "plot_coherence": indicators.plot_coherence,
            "quality_grade": self._calculate_quality_grade(indicators.overall_score or 0.0),
            "recommendations": self._generate_quality_recommendations(indicators),
        }

    def _calculate_quality_grade(self, overall_score: float) -> str:
        """品質グレードの計算

        グレード基準:
            - A+: 95以上（最高品質）
            - A: 90-94（優秀）
            - B+: 85-89（良好）
            - B: 80-84（標準）
            - C+: 75-79（改善余地あり）
            - C: 70-74（要改善）
            - D: 70未満（大幅改善必要）

        Args:
            overall_score: 総合スコア（0-100）

        Returns:
            str: 品質グレード
        """
        if overall_score >= 95.0:
            return "A+"
        if overall_score >= 90.0:
            return "A"
        if overall_score >= 85.0:
            return "B+"
        if overall_score >= 80.0:
            return "B"
        if overall_score >= 75.0:
            return "C+"
        if overall_score >= 70.0:
            return "C"
        return "D"

    def _generate_quality_recommendations(self, indicators: Any) -> list[str]:
        """品質改善推奨事項の生成

        判定基準:
            - 技術精度: 85未満で改善推奨
            - キャラクター一貫性: 80未満で改善推奨
            - プロット連結性: 75未満で改善推奨

        Args:
            indicators: 品質指標

        Returns:
            list[str]: 改善推奨事項リスト
        """
        recommendations = []

        if indicators.technical_accuracy < 85.0:
            recommendations.append("技術要素の精度向上が必要です")

        if indicators.character_consistency < 80.0:
            recommendations.append("キャラクター一貫性の改善が推奨されます")

        if indicators.plot_coherence < 75.0:
            recommendations.append("プロット連結性の強化を検討してください")

        if not recommendations:
            recommendations.append("高品質なプロットが生成されました")

        return recommendations

    def _detect_project_root(self) -> Path:
        """プロジェクトルートの自動検出

        検出戦略:
            1. Configuration Manager経由で環境設定取得
            2. プロジェクト構造に基づく探索
            3. カレントディレクトリへのフォールバック

        Returns:
            Path: 検出されたプロジェクトルートパス
        """
        # B30準拠: Configuration Manager経由で取得（遅延初期化）
        config_manager = self._get_configuration_manager()

        # ConfigurationManager API修正: get_system_settingを使用
        try:
            project_root = config_manager.get_system_setting("project_root")
            if project_root:
                return Path(project_root)
        except Exception:
            # 設定取得失敗時はフォールバック処理へ
            pass

        # B30品質作業指示書遵守: テスト環境フォールバック対応
        # 実運用時は DI Container経由でIPathServiceを注入
        # テスト時は現在ディレクトリをフォールバックとして使用
        try:
            # DI Container実装後は以下に置き換え:
            # path_service: IPathService = self._path_service
            # return path_service.detect_project_root()
            # フォールバック: 現在のディレクトリから上位にプロジェクトルートを探索
            current_path = Path.cwd()
            while current_path != current_path.parent:
                if (current_path / "pyproject.toml").exists() or (current_path / "scripts").exists():
                    return current_path
                current_path = current_path.parent

            # 最終フォールバック
            return Path.cwd()

        except Exception:
            # エラー時のフォールバック
            return Path.cwd()

    def _log_generation_error(self, episode_number: int, error_message: str) -> None:
        """生成エラーのログ記録

        Note:
            現在は標準出力のみ。将来的には統一ロガー経由に移行。

        Args:
            episode_number: エピソード番号
            error_message: エラーメッセージ
        """
        self.logger.error("Enhanced plot generation error for episode %s: %s", episode_number, error_message)

    async def execute(self, request: dict) -> ContextualPlotResult:
        """ユースケース実行 (AbstractUseCaseインターフェース実装)

        Args:
            request: リクエスト辞書 (episode_number, config等)

        Returns:
            ContextualPlotResult: 生成結果
        """
        episode_number = request.get("episode_number")
        config = request.get("config")
        save_result = request.get("save_result", True)
        project_root = request.get("project_root")

        return self.generate_enhanced_episode_plot(
            episode_number=episode_number, config=config, save_result=save_result, project_root=project_root
        )
