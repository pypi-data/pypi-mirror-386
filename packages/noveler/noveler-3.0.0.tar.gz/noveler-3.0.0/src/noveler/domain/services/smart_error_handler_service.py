"""Domain.services.smart_error_handler_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""スマートエラーハンドラーサービス

技術的なエラーをユーザーフレンドリーなメッセージに変換し、
具体的な解決策を提案するドメインサービス
"""


from typing import ClassVar

from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class SmartErrorHandlerService:
    """スマートエラーハンドラーサービス"""

    # ファイル名とテンプレートのマッピング定数
    FILE_MAPPINGS: ClassVar[dict[str, dict[str, str]]] = {
        "企画書.yaml": {
            "friendly_name": "企画書",
            "template": "企画書テンプレート.yaml",
        },
        "キャラクター.yaml": {
            "friendly_name": "キャラクター設定",
            "template": "キャラクター設定テンプレート.yaml",
        },
        "世界観.yaml": {
            "friendly_name": "世界観設定",
            "template": "世界観設定テンプレート.yaml",
        },
        "全体構成.yaml": {
            "friendly_name": "全体構成プロット",
            "template": "マスタープロットテンプレート.yaml",
        },
    }

    def __init__(self) -> None:
        self.error_message_templates: dict[str, str] = self._initialize_error_templates()
        self.genre_advice_map: dict[str, dict[str, str]] = self._initialize_genre_advice()

    def generate_smart_error_message(self, error_context: object) -> str:
        """文脈に応じたスマートなエラーメッセージを生成

        Args:
            error_context: エラーコンテキスト

        Returns:
            str: ユーザーフレンドリーなエラーメッセージ
        """
        experience_level = error_context.get_user_experience_level()
        project_type = error_context.get_project_type()

        # 基本メッセージの生成
        base_message = self._generate_base_message(error_context)

        # 経験レベル別の詳細度調整
        detailed_message = (
            self._add_beginner_details(base_message, error_context)
            if experience_level == "beginner"
            else self._add_expert_details(base_message, error_context)
        )

        # 解決コマンドの追加(テストで期待される)
        commands = self._get_quick_resolution_commands(error_context)
        if commands:
            detailed_message += f"\n\n🔧 実行コマンド:\n{commands}"

        # ジャンル別アドバイスの追加
        if project_type:
            genre_advice = self._get_genre_specific_advice(project_type, error_context)
            if genre_advice:
                detailed_message += f"\n\n💡 {project_type}ジャンルのアドバイス:\n{genre_advice}"

        # 解決時間の見積もり追加
        time_estimate = self._estimate_resolution_time(error_context)
        detailed_message += f"\n\n⏱️ 解決予想時間: {time_estimate}"

        return detailed_message

    def _generate_base_message(self, error_context: object) -> str:
        """基本メッセージの生成"""
        if error_context.error_type == "PREREQUISITE_MISSING":
            return self._generate_prerequisite_missing_message(error_context)
        if error_context.error_type == "FILE_ACCESS_ERROR":
            return "ファイルにアクセスできませんでした。"
        if error_context.error_type == "VALIDATION_ERROR":
            return "入力内容に問題があります。"
        return f"問題が発生しました: {error_context.error_type}"

    def _generate_prerequisite_missing_message(self, error_context: object) -> str:
        """前提条件不足メッセージの生成"""
        stage_name = self._get_stage_japanese_name(error_context.affected_stage)
        primary_file = error_context.get_primary_missing_file()

        if primary_file:
            file_name = self._get_friendly_file_name(primary_file)
            return f"{stage_name}を作成するには、まず{file_name}が必要です。"
        return f"{stage_name}を作成するために必要なファイルが不足しています。"

    def _add_beginner_details(self, base_message: str, error_context: object) -> str:
        """初心者向け詳細説明の追加"""
        detailed = base_message + "\n\n📚 詳細な手順:"

        if error_context.is_prerequisite_error():
            primary_file = error_context.get_primary_missing_file()
            if primary_file:
                steps = self._get_file_creation_steps(primary_file)
                for i, step in enumerate(steps, 1):
                    detailed += f"\n   {i}. {step}"

        detailed += "\n\n💭 初回でわからないことがあっても大丈夫です。一歩ずつ進めていきましょう。"

        return detailed

    def _add_expert_details(self, base_message: str, error_context: object) -> str:
        """熟練者向け簡潔な詳細の追加"""
        if error_context.is_prerequisite_error():
            commands = self._get_quick_resolution_commands(error_context)
            if commands:
                base_message += f"\n\n🔧 解決コマンド:\n{commands}"

        return base_message

    def _get_file_creation_steps(self, file_path: str) -> list[str]:
        """ファイル作成の詳細ステップ"""
        # file_pathが文字列でない場合のガード
        if not isinstance(file_path, str):
            return ["テンプレートをコピーする", "内容を編集する", "保存する"]
            
        if "企画書" in file_path:
            return [
                "プロジェクトのコンセプトを考える",
                "ターゲット読者を決める",
                "作品の魅力ポイントを整理する",
                "テンプレートをコピーして編集する",
            ]
        if "キャラクター" in file_path:
            return [
                "主人公の基本設定を決める",
                "性格・価値観を設定する",
                "目標と動機を明確にする",
                "テンプレートに入力する",
            ]
        if "世界観" in file_path:
            return [
                "物語の舞台設定を決める",
                "時代・場所を設定する",
                "特殊なルールがあれば整理する",
                "テンプレートに入力する",
            ]
        return ["テンプレートをコピーする", "内容を編集する", "保存する"]

    def _get_quick_resolution_commands(self, error_context: object) -> str:
        """素早い解決用のコマンド（セキュリティ強化版）"""
        commands = []

        if not hasattr(error_context, "missing_files"):
            return "# エラーコンテキスト情報が不足しています"

        # Handle missing_files safely
        try:
            missing_files_list = list(error_context.missing_files) if error_context.missing_files else []
        except (TypeError, AttributeError):
            return "# エラーコンテキスト情報が不足しています"

        for missing_file in missing_files_list:
            if isinstance(missing_file, str):
                if "企画書" in missing_file:
                    commands.append("novel init project")
                elif "キャラクター" in missing_file:
                    commands.append("novel create character")
                elif "世界観" in missing_file:
                    commands.append("novel create world")
                else:
                    commands.append(f"# ファイル作成が必要: {missing_file}")

        return "\n".join(f"   {cmd}" for cmd in commands)

    def _get_genre_specific_advice(self, project_type: str, error_context: object) -> str | None:
        """ジャンル別アドバイスの取得"""
        genre_advice = self.genre_advice_map.get(project_type.lower(), {})

        if error_context.is_prerequisite_error():
            primary_file = error_context.get_primary_missing_file()

            # primary_fileが文字列でない場合のガード
            if primary_file and isinstance(primary_file, str):
                if "世界観" in primary_file:
                    return genre_advice.get("world_building", "")
                if "キャラクター" in primary_file:
                    return genre_advice.get("character_development", "")
                if "企画書" in primary_file:
                    return genre_advice.get("concept_development", "")

        return genre_advice.get("general", "")

    def _estimate_resolution_time(self, error_context: object) -> str:
        """解決時間の見積もり"""
        if error_context.is_prerequisite_error():
            file_count = len(error_context.missing_files)

            if file_count == 1:
                primary_file = error_context.get_primary_missing_file()
                if "企画書" in primary_file:
                    return "30-60分"
                if "キャラクター" in primary_file:
                    return "45-90分"
                if "世界観" in primary_file:
                    return "60-120分"
                return "15-30分"
            base_time = file_count * 30
            return f"{base_time}-{base_time * 2}分"

        return "15-30分"

    def _get_friendly_file_name(self, file_path: str) -> str:
        """ユーザーフレンドリーなファイル名"""
        for pattern, mapping in self.FILE_MAPPINGS.items():
            if pattern in file_path:
                return mapping["friendly_name"]
        return file_path.split("/")[-1]

    def _get_template_name(self, file_path: str) -> str | None:
        """テンプレート名の取得"""
        for pattern, mapping in self.FILE_MAPPINGS.items():
            if pattern in file_path:
                return mapping["template"]
        return None

    def _get_stage_japanese_name(self, stage: WorkflowStageType) -> str:
        """段階の日本語名を取得"""
        stage_names = {
            WorkflowStageType.MASTER_PLOT: "全体構成プロット",
            WorkflowStageType.CHAPTER_PLOT: "章別プロット",
            WorkflowStageType.EPISODE_PLOT: "話数別プロット",
        }
        return stage_names.get(stage, str(stage.value))

    def _initialize_error_templates(self) -> dict[str, str]:
        """エラーメッセージテンプレートの初期化"""
        return {
            "PREREQUISITE_MISSING": "{stage_name}を作成するには、まず{missing_files}が必要です。",
            "FILE_ACCESS_ERROR": "ファイルにアクセスできませんでした。権限を確認してください。",
            "VALIDATION_ERROR": "入力内容に問題があります。形式を確認してください。",
            "NETWORK_ERROR": "ネットワーク接続に問題があります。",
        }

    def _initialize_genre_advice(self) -> dict[str, dict[str, str]]:
        """ジャンル別アドバイスの初期化"""
        return {
            "fantasy": {
                "world_building": "魔法システム、種族設定、地理設定が重要です。独自性を持たせつつ、読者にとって理解しやすいルールを作りましょう。",
                "character_development": "主人公の成長軌道と魔法や特殊能力の習得過程を明確にしましょう。",
                "concept_development": "既存作品との差別化要素を明確にし、魅力的な設定の組み合わせを考えましょう。",
                "general": "世界観の一貫性を保ち、読者が没入できる設定を心がけましょう。",
            },
            "sf": {
                "world_building": "科学的根拠に基づいた設定と、技術が社会に与える影響を考慮しましょう。",
                "character_development": "科学技術との関わり方や、技術進歩への人間の適応を描きましょう。",
                "concept_development": "現実の科学をベースに、想像力豊かな未来や技術を設計しましょう。",
                "general": "科学的整合性と物語性のバランスを取りましょう。",
            },
            "mystery": {
                "world_building": "事件の背景となる社会環境や制度を詳細に設定しましょう。",
                "character_development": "探偵役の推理力の根拠と、犯人の動機を丁寧に設計しましょう。",
                "concept_development": "トリックと動機の組み合わせで独自性を出しましょう。",
                "general": "手がかりの配置とミスリードのバランスが重要です。",
            },
            "romance": {
                "world_building": "恋愛が育まれる環境や社会背景を魅力的に設定しましょう。",
                "character_development": "お互いを惹かれ合う理由と成長要素を明確にしましょう。",
                "concept_development": "恋愛の障害と解決方法で読者の心を掴みましょう。",
                "general": "感情的な説得力と現実味のバランスを大切にしましょう。",
            },
        }
