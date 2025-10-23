#!/usr/bin/env python3
"""
Ten Stage Writing Process MCP Adapter

Purpose: 10段階執筆プロセス専用MCPアダプター
Architecture: Presentation Layer (DDD準拠)
Responsibility: 10段階執筆システムとMCPプロトコル間の変換
"""

from noveler.infrastructure.logging.unified_logger import get_logger
from datetime import datetime, timezone
from typing import Any, ClassVar
import importlib

from noveler.domain.interfaces.di_container_factory import IDIContainerFactory
from noveler.infrastructure.di.domain_di_container_factory import get_domain_di_factory


class TenStageWritingMCPAdapter:
    """10段階執筆プロセス専用MCPアダプター

    10段階執筆システムのMCPプロトコル変換を担当。
    各段階の実行、進捗管理、結果フォーマットを行う。

    DDD原則:
    - 10段階執筆ドメインロジックとMCPプロトコルの分離
    - Application層への依存のみ（UseCase経由）
    - 段階固有の変換ロジック集約
    """

    # 10段階執筆ステップ定義
    TEN_STAGES: ClassVar[list[str]] = [
        "context_extraction",  # 文脈抽出
        "plot_analysis",  # プロット分析
        "character_consistency",  # キャラクター一貫性
        "scene_design",  # シーン設計
        "dialogue_design",  # 対話設計
        "narrative_structure",  # 物語構造
        "emotion_curve_design",  # 感情曲線設計
        "sensory_design",  # 感覚描写設計
        "manuscript_generation",  # 原稿生成
        "quality_certification",  # 品質認証
    ]

    def __init__(self, di_factory: IDIContainerFactory | None = None) -> None:
        """10段階執筆MCPアダプター初期化

        Args:
            di_factory: 依存性注入ファクトリー
        """
        self.di_factory = di_factory or get_domain_di_factory()
        self.logger = get_logger(__name__)

    async def execute_stage(self, stage_name: str, stage_number: int, options: dict[str, Any]) -> dict[str, Any]:
        """指定された段階の実行

        Args:
            stage_name: 段階名
            stage_number: 段階番号（1-10）
            options: 実行オプション

        Returns:
            Dict[str, Any]: MCP準拠の実行結果
        """
        try:
            self.logger.info("🎯 10段階執筆 Stage %s: %s 開始", stage_number, stage_name)

            # 1. ステージバリデーション
            validated_request = self._validate_stage_request(stage_name, stage_number, options)

            # 2. UseCase実行
            result = await self._execute_stage_use_case(validated_request)

            # 3. MCPレスポンス形式変換
            return self._format_stage_response(stage_name, stage_number, result)

        except Exception as e:
            self.logger.exception("❌ Stage %s 実行エラー", stage_number)
            return self._format_stage_error(stage_name, stage_number, str(e))

    async def get_progress_status(self, _project_root: str | None = None) -> dict[str, Any]:
        """10段階執筆の進捗状況取得

        Args:
            project_root: プロジェクトルート

        Returns:
            Dict[str, Any]: 進捗状況
        """
        try:
            # Application層の進捗管理UseCaseを使用（未実装）
            raise NotImplementedError(
                "TenStageProgressUseCase is not implemented yet (see ISSUE-TENSTAGE-001)"
            )
        except NotImplementedError as e:
            # 仕様上は未提供。呼び出し側で適切に分岐させるため、明示的にエラーを返す
            return {
                "jsonrpc": "2.0",
                "result": {
                    "success": False,
                    "error": str(e),
                    "operation": "progress_status",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        except Exception as e:  # pragma: no cover - 予期せぬ例外の保険
            self.logger.exception("進捗状況取得エラー")
            return self._format_progress_error(str(e))

    def _validate_stage_request(self, stage_name: str, stage_number: int, options: dict[str, Any]) -> dict[str, Any]:
        """ステージリクエストのバリデーション

        Args:
            stage_name: ステージ名
            stage_number: ステージ番号
            options: オプション

        Returns:
            Dict[str, Any]: バリデーション済みリクエスト

        Raises:
            ValueError: バリデーションエラー時
        """
        # ステージ番号の範囲チェック
        if not (1 <= stage_number <= 10):
            msg = f"ステージ番号は1-10の範囲で指定してください: {stage_number}"
            raise ValueError(msg)

        # ステージ名の妥当性チェック
        if stage_name not in self.TEN_STAGES:
            msg = f"無効なステージ名: {stage_name}"
            raise ValueError(msg)

        # ステージ番号と名前の整合性チェック
        expected_stage_name = self.TEN_STAGES[stage_number - 1]
        if stage_name != expected_stage_name:
            msg = f"ステージ番号 {stage_number} には '{expected_stage_name}' が期待されますが、'{stage_name}' が指定されました"
            raise ValueError(msg)

        return {
            "stage_name": stage_name,
            "stage_number": stage_number,
            "options": options,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _execute_stage_use_case(self, request: dict[str, Any]) -> dict[str, Any]:
        """ステージ対応UseCaseの実行

        Args:
            request: バリデーション済みリクエスト

        Returns:
            Dict[str, Any]: UseCase実行結果
        """
        stage_number = request["stage_number"]

        try:
            # 現在は10段階執筆UseCaseを使用
            mod_ts = importlib.import_module('noveler.application.use_cases.ten_stage_episode_writing_use_case')
            TenStageEpisodeWritingUseCase = getattr(mod_ts, 'TenStageEpisodeWritingUseCase')

            use_case = self.di_factory.resolve(TenStageEpisodeWritingUseCase)

            # ステージ固有のリクエスト変換
            use_case_request = self._convert_stage_request(request)

            # UseCase実行
            result = await use_case.execute_stage(stage_number, use_case_request)

            return {
                "stage_execution": "success",
                "stage_output": result,
                "execution_time": datetime.now(timezone.utc).isoformat(),
            }

        except ImportError:
            # UseCaseが存在しない場合のフォールバック
            self.logger.warning("TenStageEpisodeWritingUseCase が見つかりません。モック実行します。")
            return await self._mock_stage_execution(request)

        except Exception:
            self.logger.exception("UseCase実行エラー")
            raise

    async def _mock_stage_execution(self, request: dict[str, Any]) -> dict[str, Any]:
        """ステージ実行のモック処理（開発用）

        Args:
            request: ステージリクエスト

        Returns:
            Dict[str, Any]: モック実行結果
        """
        stage_name = request["stage_name"]
        stage_number = request["stage_number"]

        # 段階別のモック処理
        mock_outputs = {
            "context_extraction": {
                "extracted_context": "前話から抽出されたコンテキスト",
                "key_elements": ["キャラクター状態", "場面設定", "進行中の出来事"],
            },
            "plot_analysis": {
                "plot_structure": "3幕構成の第2幕",
                "tension_level": "上昇中",
                "key_conflicts": ["内的葛藤", "外的障害"],
            },
            "character_consistency": {
                "consistency_score": 0.95,
                "inconsistencies": [],
                "character_states": ["主人公：成長段階", "ヒロイン：信頼構築段階"],
            },
        }

        return {
            "stage_execution": "mock_success",
            "stage_output": mock_outputs.get(
                stage_name, {"stage_name": stage_name, "message": f"ステージ {stage_number} のモック実行完了"}
            ),
            "execution_time": datetime.now(timezone.utc).isoformat(),
            "note": "これはモック実行結果です",
        }

    def _convert_stage_request(self, stage_request: dict[str, Any]) -> dict[str, Any]:
        """ステージリクエスト → UseCase形式変換

        Args:
            stage_request: ステージリクエスト

        Returns:
            Dict[str, Any]: UseCase用リクエスト
        """
        options = stage_request.get("options", {})

        return {
            "episode_number": options.get("episode_number", 1),
            "project_root": options.get("project_root"),
            "stage_config": options.get("stage_config", {}),
            "previous_stage_output": options.get("previous_stage_output"),
        }

    def _format_stage_response(self, stage_name: str, stage_number: int, result: dict[str, Any]) -> dict[str, Any]:
        """ステージ実行結果のMCPレスポンス形式変換

        Args:
            stage_name: ステージ名
            stage_number: ステージ番号
            result: 実行結果

        Returns:
            Dict[str, Any]: MCP準拠レスポンス
        """
        return {
            "jsonrpc": "2.0",
            "result": {
                "success": True,
                "data": {
                    "operation": "ten_stage_execution",
                    "stage_info": {
                        "stage_number": stage_number,
                        "stage_name": stage_name,
                        "total_stages": len(self.TEN_STAGES),
                    },
                    "execution_result": result,
                    "adapter_info": {"name": "TenStageWritingMCPAdapter", "version": "1.0.0", "ddd_compliant": True},
                },
            },
        }

    def _format_stage_error(self, stage_name: str, stage_number: int, error_message: str) -> dict[str, Any]:
        """ステージ実行エラーのMCPレスポンス形式変換

        Args:
            stage_name: ステージ名
            stage_number: ステージ番号
            error_message: エラーメッセージ

        Returns:
            Dict[str, Any]: MCP準拠エラーレスポンス
        """
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"10段階執筆 Stage {stage_number} 実行エラー",
                "data": {
                    "stage_name": stage_name,
                    "stage_number": stage_number,
                    "error_message": error_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        }

    def _format_progress_error(self, error_message: str) -> dict[str, Any]:
        """進捗状況取得エラーのMCPレスポンス形式変換

        Args:
            error_message: エラーメッセージ

        Returns:
            Dict[str, Any]: MCP準拠エラーレスポンス
        """
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "10段階執筆進捗取得エラー",
                "data": {"error_message": error_message, "timestamp": datetime.now(timezone.utc).isoformat()},
            },
        }
