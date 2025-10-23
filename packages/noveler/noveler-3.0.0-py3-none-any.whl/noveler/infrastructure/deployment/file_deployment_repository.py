"""ファイルベースのデプロイメントリポジトリ

デプロイメント情報をJSONファイルで永続化
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentHistory,
    DeploymentMode,
    DeploymentStatus,
    DeploymentTarget,
)
from noveler.domain.deployment.repositories import DeploymentRepository
from noveler.domain.deployment.value_objects import CommitHash, ProjectPath


class FileDeploymentRepository(DeploymentRepository):
    """ファイルベースのデプロイメントリポジトリ"""

    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = Path.home() / storage_dir
        self.storage_dir.mkdir(exist_ok=True)

    def save(self, deployment: Deployment) -> None:
        """デプロイメント情報を保存"""
        deployment_file = self.storage_dir / f"deployment_{deployment.id}.json"

        deployment_data: dict[str, Any] = {
            "id": deployment.id,
            "target": {
                "project_path": deployment.target.project_path.value,
                "project_name": deployment.target.project_name,
            },
            "mode": deployment.mode.value,
            "source_commit": deployment.source_commit.value,
            "timestamp": deployment.timestamp.isoformat(),
            "status": deployment.status.value,
            "error_message": deployment.error_message,
            "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
        }

        with Path(deployment_file).open("w", encoding="utf-8") as f:
            json.dump(deployment_data, f, indent=2, ensure_ascii=False)

    def find_by_id(self, deployment_id: str) -> Deployment | None:
        """IDでデプロイメントを検索"""
        deployment_file = self.storage_dir / f"deployment_{deployment_id}.json"

        if not deployment_file.exists():
            return None

        with Path(deployment_file).open(encoding="utf-8") as f:
            data = json.load(f)

        return self._deserialize_deployment(data)

    def find_by_project(self, project_path: ProjectPath) -> list[Deployment]:
        """プロジェクトごとのデプロイメントを検索"""
        deployments = []

        for deployment_file in self.storage_dir.glob("deployment_*.json"):
            with Path(deployment_file).open(encoding="utf-8") as f:
                data = json.load(f)

            if data["target"]["project_path"] == project_path.value:
                deployment = self._deserialize_deployment(data)
                if deployment:
                    deployments.append(deployment)

        # 時刻順でソート
        deployments.sort(key=lambda d: d.timestamp, reverse=True)
        return deployments

    def get_history(self, project_path: ProjectPath) -> DeploymentHistory:
        """プロジェクトのデプロイメント履歴を取得"""
        deployments = self.find_by_project(project_path)
        return DeploymentHistory(project_path=project_path, deployments=deployments)

    def rollback(self, deployment: Deployment) -> None:
        """デプロイメントをロールバック"""
        # ロールバック実装(詳細は省略)
        deployment.status = DeploymentStatus.ROLLED_BACK
        self.save(deployment)

    def _deserialize_deployment(self, data: dict) -> Deployment | None:
        """JSONデータからDeploymentオブジェクトを復元"""
        try:
            target = DeploymentTarget(
                project_path=ProjectPath(data["target"]["project_path"]),
                project_name=data["target"]["project_name"],
            )

            deployment = Deployment(
                target=target,
                mode=DeploymentMode(data["mode"]),
                source_commit=CommitHash(data["source_commit"]),
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )

            deployment.id = data["id"]
            deployment.status = DeploymentStatus(data["status"])
            deployment.error_message = data.get("error_message")

            if data.get("completed_at"):
                deployment.completed_at = datetime.fromisoformat(data["completed_at"])

            return deployment
        except Exception:
            return None
