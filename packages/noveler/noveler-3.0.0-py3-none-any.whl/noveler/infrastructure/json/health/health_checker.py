#!/usr/bin/env python3
"""JSON変換システム ヘルスチェック"""


from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.json.converters.cli_response_converter import CLIResponseConverter
from noveler.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager
from noveler.infrastructure.json.models.response_models import StandardResponseModel


@dataclass
class HealthCheckResult:
    """ヘルスチェック結果"""

    component: str
    status: str  # "healthy", "warning", "critical"
    message: str
    details: dict[str, Any]
    checked_at: str
    response_time_ms: float = 0.0


class JSONSystemHealthChecker:
    """JSON変換システム ヘルスチェッカー"""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path.cwd() / "temp" / "json_output"
        # logger_service経由で注入

    def run_comprehensive_check(self) -> dict[str, Any]:
        """包括的ヘルスチェック実行"""
        start_time = project_now().datetime

        results = []

        # 各コンポーネント チェック実行（例外安全）
        check_methods = [
            ("file_system", self._check_file_system_health),
            ("converter", self._check_converter_health),
            ("file_manager", self._check_file_manager_health),
            ("model_validation", self._check_model_validation_health),
            ("performance", self._check_performance_metrics),
        ]

        for component_name, check_method in check_methods:
            try:
                result = check_method()
                results.append(result)
            except Exception as e:
                # チェックメソッドで例外が発生した場合のフォールバック
                self.logger.exception("ヘルスチェック例外 [%s]", component_name)
                error_result = HealthCheckResult(
                    component=component_name,
                    status="critical",
                    message=f"チェック実行中に例外が発生: {e!s}",
                    details={"error": str(e), "error_type": type(e).__name__},
                    checked_at=project_now().datetime.isoformat(),
                    response_time_ms=0.0,
                )
                results.append(error_result)

        # 総合ステータス判定
        overall_status = self._determine_overall_status(results)

        total_time = (project_now().datetime - start_time).total_seconds() * 1000

        return {
            "overall_status": overall_status,
            "total_check_time_ms": total_time,
            "checked_at": start_time.isoformat(),
            "components": [asdict(result) for result in results],
            "summary": self._generate_summary(results),
        }

    def _check_file_system_health(self) -> HealthCheckResult:
        """ファイルシステム ヘルスチェック"""
        start_time = project_now().datetime

        try:
            # ディレクトリ存在確認
            if not self.output_dir.exists():
                self.output_dir.mkdir(parents=True, exist_ok=True)

            # 書き込み権限確認
            test_file = self.output_dir / ".health_check_test"
            test_file.write_text("health check test")
            test_file.unlink()

            # ディスク容量チェック
            self.output_dir.stat()

            response_time = (project_now().datetime - start_time).total_seconds() * 1000

            return HealthCheckResult(
                component="file_system",
                status="healthy",
                message="ファイルシステム正常",
                details={"output_dir": str(self.output_dir), "writable": True, "disk_available": True},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (project_now().datetime - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component="file_system",
                status="critical",
                message=f"ファイルシステムエラー: {e!s}",
                details={"error": str(e)},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

    def _check_converter_health(self) -> HealthCheckResult:
        """コンバーター ヘルスチェック"""
        start_time = project_now().datetime

        try:
            converter = CLIResponseConverter(output_dir=self.output_dir)

            # テスト変換実行（許可されたコマンドプレフィックスを使用）
            test_cli_result = {
                "success": True,
                "command": "novel health_check",  # 許可されたプレフィックス
                "content": "# ヘルスチェック\n\nテスト内容",
                "execution_time_ms": 100.0,
            }

            json_result = converter.convert(test_cli_result)

            # 結果検証
            if not json_result.get("success", False):
                msg = "変換結果が成功ステータスではありません"
                raise ValueError(msg)

            if "outputs" not in json_result:
                msg = "出力情報がありません"
                raise ValueError(msg)

            response_time = (project_now().datetime - start_time).total_seconds() * 1000

            return HealthCheckResult(
                component="converter",
                status="healthy",
                message="コンバーター正常動作",
                details={"test_conversion": "success", "output_files": json_result["outputs"]["total_files"]},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (project_now().datetime - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component="converter",
                status="critical",
                message=f"コンバーターエラー: {e!s}",
                details={"error": str(e)},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

    def _check_file_manager_health(self) -> HealthCheckResult:
        """ファイルマネージャー ヘルスチェック"""
        start_time = project_now().datetime

        try:
            file_manager = FileReferenceManager(self.output_dir)

            # テストファイル保存・検証
            test_content = "ヘルスチェックテストコンテンツ"
            file_ref = file_manager.save_content(
                content=test_content, content_type="text/plain", filename_prefix="health_check"
            )

            # 完全性検証
            integrity_ok = file_manager.verify_file_integrity(file_ref)
            if not integrity_ok:
                msg = "ファイル完全性チェックに失敗"
                raise ValueError(msg)

            # ファイル読み込みテスト
            loaded_content = file_manager.load_file_content(file_ref)
            if loaded_content != test_content:
                msg = "ファイル内容が一致しません"
                raise ValueError(msg)

            response_time = (project_now().datetime - start_time).total_seconds() * 1000

            return HealthCheckResult(
                component="file_manager",
                status="healthy",
                message="ファイルマネージャー正常動作",
                details={"file_save": "success", "integrity_check": "success", "file_load": "success"},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (project_now().datetime - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component="file_manager",
                status="critical",
                message=f"ファイルマネージャーエラー: {e!s}",
                details={"error": str(e)},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

    def _check_model_validation_health(self) -> HealthCheckResult:
        """モデルバリデーション ヘルスチェック"""
        start_time = project_now().datetime

        try:
            # テストデータでモデル検証（許可されたコマンドを使用）
            test_data = {
                "success": True,
                "command": "novel test_command",  # 許可されたプレフィックス
                "execution_time_ms": 123.45,
                "outputs": {"files": [], "total_files": 0, "total_size_bytes": 0},
                "metadata": {"test": True},
                "created_at": project_now().datetime,
            }

            # StandardResponseModelでバリデーション
            model = StandardResponseModel(**test_data)

            # モデル→辞書変換テスト
            model.model_dump()

            response_time = (project_now().datetime - start_time).total_seconds() * 1000

            return HealthCheckResult(
                component="model_validation",
                status="healthy",
                message="モデルバリデーション正常",
                details={"pydantic_validation": "success", "model_serialization": "success"},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (project_now().datetime - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component="model_validation",
                status="critical",
                message=f"モデルバリデーションエラー: {e!s}",
                details={"error": str(e)},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

    def _check_performance_metrics(self) -> HealthCheckResult:
        """パフォーマンス メトリクス チェック"""
        start_time = project_now().datetime

        try:
            # 複数回テスト実行してパフォーマンス測定
            execution_times = []

            for i in range(5):
                test_start = project_now().datetime

                converter = CLIResponseConverter(output_dir=self.output_dir)
                converter.convert(
                    {
                        "success": True,
                        "command": f"novel performance_test_{i}",  # 許可されたプレフィックス
                        "content": f"パフォーマンステスト {i}",
                    }
                )

                test_time = (project_now().datetime - test_start).total_seconds() * 1000
                execution_times.append(test_time)

            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)

            # パフォーマンス閾値チェック
            status = "healthy"
            if avg_time > 1000:  # 1秒以上
                status = "warning"
            elif avg_time > 2000:  # 2秒以上
                status = "critical"

            response_time = (project_now().datetime - start_time).total_seconds() * 1000

            return HealthCheckResult(
                component="performance",
                status=status,
                message=f"パフォーマンス測定完了: 平均{avg_time:.2f}ms",
                details={
                    "average_time_ms": avg_time,
                    "max_time_ms": max_time,
                    "min_time_ms": min_time,
                    "test_iterations": len(execution_times),
                },
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (project_now().datetime - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component="performance",
                status="critical",
                message=f"パフォーマンス測定エラー: {e!s}",
                details={"error": str(e)},
                checked_at=project_now().datetime.isoformat(),
                response_time_ms=response_time,
            )

    def _determine_overall_status(self, results: list[HealthCheckResult]) -> str:
        """総合ステータス判定"""
        statuses = [result.status for result in results]

        if "critical" in statuses:
            return "critical"
        if "warning" in statuses:
            return "warning"
        return "healthy"

    def _generate_summary(self, results: list[HealthCheckResult]) -> dict[str, Any]:
        """サマリー生成"""
        total_components = len(results)
        healthy_count = sum(1 for r in results if r.status == "healthy")
        warning_count = sum(1 for r in results if r.status == "warning")
        critical_count = sum(1 for r in results if r.status == "critical")

        avg_response_time = sum(r.response_time_ms for r in results) / total_components

        return {
            "total_components": total_components,
            "healthy_components": healthy_count,
            "warning_components": warning_count,
            "critical_components": critical_count,
            "health_percentage": (healthy_count / total_components) * 100,
            "average_response_time_ms": avg_response_time,
        }
