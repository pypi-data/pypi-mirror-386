"""Infrastructure.tools.design_review_manager
Where: Infrastructure tool managing design review data.
What: Aggregates design review input and produces output reports.
Why: Simplifies processing of design reviews within infrastructure workflows.
"""

#!/usr/bin/env python3
from __future__ import annotations

from noveler.presentation.shared.shared_utilities import console


"""
設計レビュー管理システム: 既存システム調査義務化

このシステムは新規実装開始前に設計レビューを強制し、
既存システムの調査を義務化することでNIH症候群を防ぎます。
"""


import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ReviewStatus(Enum):
    """レビュー状態"""

    PENDING = "pending"  # レビュー待ち
    IN_PROGRESS = "in_progress"  # レビュー中
    APPROVED = "approved"  # 承認済み
    REJECTED = "rejected"  # 要修正
    EXPIRED = "expired"  # 期限切れ


class ReviewType(Enum):
    """レビュータイプ"""

    NEW_FEATURE = "new_feature"  # 新機能設計
    REFACTORING = "refactoring"  # リファクタリング
    BUG_FIX = "bug_fix"  # バグ修正
    ARCHITECTURE = "architecture"  # アーキテクチャ変更
    INTEGRATION = "integration"  # システム統合


@dataclass
class ExistingSystemAnalysis:
    """既存システム分析結果"""

    analyzed_components: list[str]
    similar_implementations: list[str]
    reusable_patterns: list[str]
    potential_conflicts: list[str]
    integration_points: list[str]
    analysis_summary: str
    analyzer_name: str
    analysis_date: datetime


@dataclass
class DesignReviewRequest:
    """設計レビューリクエスト"""

    request_id: str
    feature_name: str
    feature_description: str
    review_type: ReviewType
    requester: str
    created_at: datetime
    target_files: list[Path]
    existing_analysis: ExistingSystemAnalysis | None
    status: ReviewStatus
    reviewer_comments: list[str]
    approval_date: datetime | None
    expires_at: datetime


class DesignReviewManager:
    """
    設計レビュー管理システム

    機能:
    - 新規実装前の設計レビュー強制化
    - 既存システム分析の義務化
    - レビュー状態の追跡・管理
    - 承認済み設計の有効期限管理
    """

    def __init__(self, project_root: Path, logger_service=None, console_service=None) -> None:
        """
        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root
        self.reviews_dir = project_root / ".design_reviews"
        self.reviews_dir.mkdir(exist_ok=True)

        self.pending_reviews: dict[str, DesignReviewRequest] = {}
        self.approved_reviews: dict[str, DesignReviewRequest] = {}

        self._load_existing_reviews()

        self.logger_service = logger_service
        self.console_service = console_service
    def create_review_request(
        self,
        feature_name: str,
        feature_description: str,
        review_type: ReviewType,
        requester: str,
        target_files: list[Path],
    ) -> str:
        """
        設計レビューリクエストを作成

        Args:
            feature_name: 機能名
            feature_description: 機能詳細説明
            review_type: レビュータイプ
            requester: 要求者
            target_files: 対象ファイルリスト

        Returns:
            作成されたレビューID
        """
        # リクエストID生成（内容のハッシュベース）
        content_hash = hashlib.md5(f"{feature_name}_{feature_description}_{requester}".encode()).hexdigest()[:8]
        request_id = f"DR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{content_hash}"

        # 有効期限設定（作成から30日後）
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        review_request = DesignReviewRequest(
            request_id=request_id,
            feature_name=feature_name,
            feature_description=feature_description,
            review_type=review_type,
            requester=requester,
            created_at=datetime.now(timezone.utc),
            target_files=target_files,
            existing_analysis=None,  # 後で分析結果を設定
            status=ReviewStatus.PENDING,
            reviewer_comments=[],
            approval_date=None,
            expires_at=expires_at,
        )

        self.pending_reviews[request_id] = review_request
        self._save_review(review_request)

        return request_id

    def analyze_existing_systems(self, request_id: str, analyzer_name: str) -> ExistingSystemAnalysis:
        """
        既存システム分析の実行（義務化）

        Args:
            request_id: レビューID
            analyzer_name: 分析者名

        Returns:
            分析結果

        Raises:
            ValueError: レビューが見つからない場合
        """
        if request_id not in self.pending_reviews:
            msg = f"レビューID {request_id} が見つかりません"
            raise ValueError(msg)

        request = self.pending_reviews[request_id]

        # 既存システムの自動分析
        analyzed_components = self._analyze_existing_components(request.feature_name)
        similar_implementations = self._find_similar_implementations(request.feature_description)
        reusable_patterns = self._identify_reusable_patterns(request.target_files)
        potential_conflicts = self._detect_potential_conflicts(request.target_files)
        integration_points = self._find_integration_points(request.feature_name)

        analysis_summary = self._generate_analysis_summary(
            analyzed_components, similar_implementations, reusable_patterns, potential_conflicts, integration_points
        )

        analysis = ExistingSystemAnalysis(
            analyzed_components=analyzed_components,
            similar_implementations=similar_implementations,
            reusable_patterns=reusable_patterns,
            potential_conflicts=potential_conflicts,
            integration_points=integration_points,
            analysis_summary=analysis_summary,
            analyzer_name=analyzer_name,
            analysis_date=datetime.now(timezone.utc),
        )

        # レビューリクエストに分析結果を設定
        request.existing_analysis = analysis
        request.status = ReviewStatus.IN_PROGRESS
        self._save_review(request)

        return analysis

    def approve_review(self, request_id: str, reviewer_name: str, comments: list[str] | None = None) -> bool:
        """
        設計レビューの承認

        Args:
            request_id: レビューID
            reviewer_name: レビュアー名
            comments: レビューコメント

        Returns:
            承認成功の可否
        """
        if request_id not in self.pending_reviews:
            return False

        request = self.pending_reviews.pop(request_id)

        # 既存システム分析が実施されているかチェック
        if not request.existing_analysis:
            console.print(f"❌ レビューID {request_id}: 既存システム分析が未実施です")
            return False

        # 承認処理
        request.status = ReviewStatus.APPROVED
        request.approval_date = datetime.now(timezone.utc)
        request.reviewer_comments.extend(comments or [])
        request.reviewer_comments.append(f"承認者: {reviewer_name}")

        self.approved_reviews[request_id] = request
        self._save_review(request)

        console.print(f"✅ レビューID {request_id} が承認されました")
        return True

    def reject_review(self, request_id: str, reviewer_name: str, rejection_reason: str) -> bool:
        """
        設計レビューの差し戻し

        Args:
            request_id: レビューID
            reviewer_name: レビュアー名
            rejection_reason: 差し戻し理由

        Returns:
            差し戻し成功の可否
        """
        if request_id not in self.pending_reviews:
            return False

        request = self.pending_reviews[request_id]
        request.status = ReviewStatus.REJECTED
        request.reviewer_comments.append(f"差し戻し ({reviewer_name}): {rejection_reason}")

        self._save_review(request)

        console.print(f"🔄 レビューID {request_id} が差し戻されました: {rejection_reason}")
        return True

    def check_implementation_permission(self, target_files: list[Path]) -> tuple[bool, str]:
        """
        実装許可チェック（承認済みレビューの確認）

        Args:
            target_files: 実装対象ファイル

        Returns:
            (許可有無, メッセージ)
        """
        for file_path in target_files:
            # 該当ファイルの承認済みレビューを検索
            matching_reviews = [
                review
                for review in self.approved_reviews.values()
                if any(target in review.target_files for target in [file_path])
            ]

            if not matching_reviews:
                return False, f"ファイル {file_path} の設計レビューが承認されていません"

            # 有効期限チェック
            for review in matching_reviews:
                if datetime.now(timezone.utc) > review.expires_at:
                    return False, f"レビューID {review.request_id} の承認期限が切れています"

        return True, "実装許可されています"

    def _analyze_existing_components(self, feature_name: str) -> list[str]:
        """既存コンポーネント分析"""
        components = []

        # scriptsディレクトリを検索
        for py_file in self.project_root.glob("noveler/**/*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                # 機能名に関連するクラス・関数を検索
                if feature_name.lower() in content.lower():
                    components.append(str(py_file.relative_to(self.project_root)))
            except Exception:
                continue

        return components

    def _find_similar_implementations(self, feature_description: str) -> list[str]:
        """類似実装の検索"""
        similar = []
        keywords = feature_description.lower().split()

        for py_file in self.project_root.glob("noveler/**/*.py"):
            try:
                content = py_file.read_text(encoding="utf-8").lower()
                # キーワードマッチング
                matches = sum(1 for keyword in keywords if keyword in content)
                if matches >= 2:  # 2個以上のキーワードが一致:
                    similar.append(str(py_file.relative_to(self.project_root)))
            except Exception:
                continue

        return similar

    def _identify_reusable_patterns(self, target_files: list[Path]) -> list[str]:
        """再利用可能パターンの特定"""
        patterns = []

        # 共通的なパターンを検索
        common_patterns = ["Repository", "Service", "Manager", "Factory", "Builder", "Strategy", "Observer"]

        for py_file in self.project_root.glob("noveler/**/*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern in common_patterns:
                    if pattern in content:
                        patterns.append(f"{pattern}パターン in {py_file.relative_to(self.project_root)}")
            except Exception:
                continue

        return list(set(patterns))  # 重複除去

    def _detect_potential_conflicts(self, target_files: list[Path]) -> list[str]:
        """潜在的な競合の検出"""
        conflicts = []

        for target_file in target_files:
            if target_file.exists():
                conflicts.append(f"ファイル {target_file} は既に存在します")

            # 同名クラス・関数の競合チェック
            target_name = target_file.stem
            for py_file in self.project_root.glob("noveler/**/*.py"):
                if py_file.stem == target_name and py_file != target_file:
                    conflicts.append(f"同名ファイル競合: {py_file.relative_to(self.project_root)}")

        return conflicts

    def _find_integration_points(self, feature_name: str) -> list[str]:
        """統合ポイントの特定"""
        integration_points = []

        # 設定ファイルでの統合ポイント
        config_files = ["CLAUDE.md", "docs/guides/developer_guide.md"]
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                integration_points.append(f"設定更新必要: {config_file}")

        # 共通インターフェースでの統合ポイント
        interface_patterns = ["UseCase", "Repository", "Service"]
        for pattern in interface_patterns:
            if pattern.lower() in feature_name.lower():
                integration_points.append(f"{pattern}インターフェース統合が必要")

        return integration_points

    def _generate_analysis_summary(
        self,
        analyzed_components: list[str],
        similar_implementations: list[str],
        reusable_patterns: list[str],
        potential_conflicts: list[str],
        integration_points: list[str],
    ) -> str:
        """分析結果サマリー生成"""
        summary_parts = []

        if analyzed_components:
            summary_parts.append(f"関連コンポーネント {len(analyzed_components)}個を特定")

        if similar_implementations:
            summary_parts.append(f"類似実装 {len(similar_implementations)}個を発見")

        if reusable_patterns:
            summary_parts.append(f"再利用可能パターン {len(reusable_patterns)}個を特定")

        if potential_conflicts:
            summary_parts.append(f"潜在的競合 {len(potential_conflicts)}個を検出")

        if integration_points:
            summary_parts.append(f"統合ポイント {len(integration_points)}個を特定")

        if not summary_parts:
            return "新規機能として独立実装が可能です"

        return "。".join(summary_parts) + "。"

    def _load_existing_reviews(self) -> None:
        """既存レビューファイルの読み込み"""
        for review_file in self.reviews_dir.glob("DR-*.yaml"):
            try:
                f_content = review_file.read_text(encoding="utf-8")
                review_data: dict[str, Any] = yaml.safe_load(f_content)

                # データクラス復元
                review = self._deserialize_review(review_data)

                if review.status in [ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS, ReviewStatus.REJECTED]:
                    self.pending_reviews[review.request_id] = review
                elif review.status == ReviewStatus.APPROVED:
                    self.approved_reviews[review.request_id] = review

            except Exception as e:
                console.print(f"⚠️ レビューファイル {review_file} の読み込みエラー: {e}")

    def _save_review(self, review: DesignReviewRequest) -> None:
        """レビューの保存"""
        review_file = self.reviews_dir / f"{review.request_id}.yaml"

        review_data: dict[str, Any] = self._serialize_review(review)

        with review_file.Path("w").open(encoding="utf-8") as f:
            yaml.dump(review_data, f, allow_unicode=True, sort_keys=False)

    def _serialize_review(self, review: DesignReviewRequest) -> dict[str, Any]:
        """レビューオブジェクトのシリアライズ"""
        data = {
            "request_id": review.request_id,
            "feature_name": review.feature_name,
            "feature_description": review.feature_description,
            "review_type": review.review_type.value,
            "requester": review.requester,
            "created_at": review.created_at.isoformat(),
            "target_files": [str(f) for f in review.target_files],
            "status": review.status.value,
            "reviewer_comments": review.reviewer_comments,
            "approval_date": review.approval_date.isoformat() if review.approval_date else None,
            "expires_at": review.expires_at.isoformat(),
        }

        if review.existing_analysis:
            data["existing_analysis"] = {
                "analyzed_components": review.existing_analysis.analyzed_components,
                "similar_implementations": review.existing_analysis.similar_implementations,
                "reusable_patterns": review.existing_analysis.reusable_patterns,
                "potential_conflicts": review.existing_analysis.potential_conflicts,
                "integration_points": review.existing_analysis.integration_points,
                "analysis_summary": review.existing_analysis.analysis_summary,
                "analyzer_name": review.existing_analysis.analyzer_name,
                "analysis_date": review.existing_analysis.analysis_date.isoformat(),
            }

        return data

    def _deserialize_review(self, data: dict[str, Any]) -> DesignReviewRequest:
        """レビューオブジェクトのデシリアライズ"""
        existing_analysis = None
        if "existing_analysis" in data:
            analysis_data: dict[str, Any] = data["existing_analysis"]
            existing_analysis = ExistingSystemAnalysis(
                analyzed_components=analysis_data["analyzed_components"],
                similar_implementations=analysis_data["similar_implementations"],
                reusable_patterns=analysis_data["reusable_patterns"],
                potential_conflicts=analysis_data["potential_conflicts"],
                integration_points=analysis_data["integration_points"],
                analysis_summary=analysis_data["analysis_summary"],
                analyzer_name=analysis_data["analyzer_name"],
                analysis_date=datetime.fromisoformat(analysis_data["analysis_date"]),
            )

        return DesignReviewRequest(
            request_id=data["request_id"],
            feature_name=data["feature_name"],
            feature_description=data["feature_description"],
            review_type=ReviewType(data["review_type"]),
            requester=data["requester"],
            created_at=datetime.fromisoformat(data["created_at"]),
            target_files=[Path(f) for f in data["target_files"]],
            existing_analysis=existing_analysis,
            status=ReviewStatus(data["status"]),
            reviewer_comments=data["reviewer_comments"],
            approval_date=datetime.fromisoformat(data["approval_date"]) if data["approval_date"] else None,
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )

    def list_pending_reviews(self) -> list[DesignReviewRequest]:
        """承認待ちレビュー一覧"""
        return list(self.pending_reviews.values())

    def list_approved_reviews(self) -> list[DesignReviewRequest]:
        """承認済みレビュー一覧"""
        return list(self.approved_reviews.values())

    def generate_review_report(self) -> dict[str, Any]:
        """レビュー状況レポートの生成"""
        return {
            "total_reviews": len(self.pending_reviews) + len(self.approved_reviews),
            "pending_reviews": len(self.pending_reviews),
            "approved_reviews": len(self.approved_reviews),
            "expired_reviews": len(
                [r for r in self.approved_reviews.values() if datetime.now(timezone.utc) > r.expires_at]
            ),
            "review_types_distribution": {
                review_type.value: len(
                    [
                        r
                        for r in {**self.pending_reviews, **self.approved_reviews}.values()
                        if r.review_type == review_type
                    ]
                )
                for review_type in ReviewType
            },
        }


def main() -> None:
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="設計レビュー管理システム")
    parser.add_argument("--project-root", type=Path, default=Path(), help="プロジェクトルートディレクトリ")

    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")

    # レビューリクエスト作成
    create_parser = subparsers.add_parser("create", help="設計レビューリクエスト作成")
    create_parser.add_argument("--feature", required=True, help="機能名")
    create_parser.add_argument("--description", required=True, help="機能説明")
    create_parser.add_argument(
        "--type", choices=[t.value for t in ReviewType], default="new_feature", help="レビュータイプ"
    )
    create_parser.add_argument("--requester", required=True, help="要求者名")
    create_parser.add_argument("--files", nargs="+", help="対象ファイルリスト")

    # 分析実行
    analyze_parser = subparsers.add_parser("analyze", help="既存システム分析実行")
    analyze_parser.add_argument("--review-id", required=True, help="レビューID")
    analyze_parser.add_argument("--analyzer", required=True, help="分析者名")

    # 承認/差し戻し
    approve_parser = subparsers.add_parser("approve", help="レビュー承認")
    approve_parser.add_argument("--review-id", required=True, help="レビューID")
    approve_parser.add_argument("--reviewer", required=True, help="レビュアー名")
    approve_parser.add_argument("--comments", nargs="*", help="コメント")

    reject_parser = subparsers.add_parser("reject", help="レビュー差し戻し")
    reject_parser.add_argument("--review-id", required=True, help="レビューID")
    reject_parser.add_argument("--reviewer", required=True, help="レビュアー名")
    reject_parser.add_argument("--reason", required=True, help="差し戻し理由")

    # 実装許可チェック
    check_parser = subparsers.add_parser("check", help="実装許可チェック")
    check_parser.add_argument("--files", nargs="+", required=True, help="実装対象ファイル")

    # 一覧表示
    subparsers.add_parser("list", help="レビュー一覧表示")
    subparsers.add_parser("report", help="レビュー状況レポート")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = DesignReviewManager(args.project_root)

    if args.command == "create":
        target_files = [Path(f) for f in (args.files or [])]
        review_id = manager.create_review_request(
            args.feature, args.description, ReviewType(args.type), args.requester, target_files
        )

        console.print(f"✅ レビューリクエストを作成しました: {review_id}")

    elif args.command == "analyze":
        try:
            analysis = manager.analyze_existing_systems(args.review_id, args.analyzer)
            console.print(f"🔍 既存システム分析完了: {analysis.analysis_summary}")
        except ValueError as e:
            console.print(f"❌ エラー: {e}")

    elif args.command == "approve":
        success = manager.approve_review(args.review_id, args.reviewer, args.comments)
        if not success:
            console.print("❌ レビューの承認に失敗しました")

    elif args.command == "reject":
        success = manager.reject_review(args.review_id, args.reviewer, args.reason)
        if not success:
            console.print("❌ レビューの差し戻しに失敗しました")

    elif args.command == "check":
        target_files = [Path(f) for f in args.files]
        permitted, message = manager.check_implementation_permission(target_files)
        console.print(f"{'✅' if permitted else '❌'} {message}")

    elif args.command == "list":
        console.print("📋 承認待ちレビュー:")
        for review in manager.list_pending_reviews():
            console.print(f"  - {review.request_id}: {review.feature_name} ({review.status.value})")

        console.print("\n✅ 承認済みレビュー:")
        for review in manager.list_approved_reviews():
            expires_str = review.expires_at.strftime("%Y-%m-%d")
            console.print(f"  - {review.request_id}: {review.feature_name} (期限: {expires_str})")

    elif args.command == "report":
        report = manager.generate_review_report()
        console.print("📊 レビュー状況レポート:")
        console.print(f"  総レビュー数: {report['total_reviews']}")
        console.print(f"  承認待ち: {report['pending_reviews']}")
        console.print(f"  承認済み: {report['approved_reviews']}")
        console.print(f"  期限切れ: {report['expired_reviews']}")


if __name__ == "__main__":
    main()
