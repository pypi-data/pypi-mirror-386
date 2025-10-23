#!/usr/bin/env python3
"""
YAML執筆ガイド処理ユーティリティ

A30_執筆ガイド.yamlを動的に処理し、
Claude Code執筆依頼用のプロンプトを生成する
"""

import io
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML


@dataclass
class WritingRequest:
    """執筆リクエスト設定"""

    genre: str = "fantasy"
    word_count: str = "4000-6000"
    viewpoint: str = "三人称単元視点"
    viewpoint_character: str = "主人公"
    difficulty: str = "beginner"
    priority: str = "critical"
    detail_level: str = "standard"  # minimal, standard, detailed
    project_path: str = None  # プロジェクトルート（設定ファイル参照用）
    episode_file: str = None  # 話別プロットファイル名
    custom_requirements: list[str] = None


class YamlGuideProcessor:
    """YAML執筆ガイド処理クラス"""

    def __init__(self, guide_path: Path | None = None, logger_service=None, console_service=None) -> None:
        """
        初期化

        Args:
            guide_path: A30_執筆ガイド.yamlのパス
        """
        if guide_path is None:
            # デフォルトパスを設定
            current_dir = Path(__file__).parent
            guide_path = current_dir.parent.parent / "docs" / "A30_執筆ガイド.yaml"

        self.guide_path = guide_path
        self.guide_data = self._load_guide()

        self.logger_service = logger_service
        self.console_service = console_service
    def _load_guide(self) -> dict[str, Any]:
        """YAMLガイドを読み込む"""
        try:
            with open(self.guide_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            msg = f"ガイドファイルが見つかりません: {self.guide_path}"
            raise FileNotFoundError(msg)
        except yaml.YAMLError as e:
            msg = f"YAML解析エラー: {e}"
            raise ValueError(msg)

    def get_basic_prompt(self, request: WritingRequest) -> str:
        """
        基本的な執筆プロンプトを生成

        Args:
            request: 執筆リクエスト設定

        Returns:
            Claude Code用の実行可能プロンプト
        """
        template = self.guide_data["prompt_templates"]["basic_writing_request"]["template"]
        variables = self.guide_data["prompt_templates"]["basic_writing_request"]["variables"]

        # ジャンル別の要件を取得
        genre_requirements = self._get_genre_requirements(request.genre)

        # 禁止・推奨表現を取得
        forbidden_expressions = self._format_list(variables["forbidden_expressions"])
        recommended_expressions = self._format_list(variables["recommended_expressions"])

        # テンプレート変数を置換
        return template.format(
            word_count=request.word_count,
            viewpoint=request.viewpoint,
            viewpoint_character=request.viewpoint_character,
            genre=request.genre,
            project_path=request.project_path or "{PROJECT_ROOT}",
            episode_file=request.episode_file or "{EPISODE_FILE}",
            forbidden_expressions=forbidden_expressions,
            recommended_expressions=recommended_expressions,
            genre_specific_requirements=genre_requirements,
        )

    def _get_genre_requirements(self, genre: str) -> str:
        """ジャンル特有の要件を取得"""
        genre_specs = self.guide_data.get("genre_specifications", {})

        if genre not in genre_specs:
            return ""

        spec = genre_specs[genre]
        requirements = []

        # 特化ルールを追加
        if "specific_rules" in spec:
            for rule in spec["specific_rules"]:
                requirements.append(f"- {rule['rule']}: {rule['method']}")

        # テンプレート追加事項
        if "template_additions" in spec:
            requirements.extend([f"- {addition}" for addition in spec["template_additions"]])

        return "\n".join(requirements)

    def _format_list(self, items: list[str]) -> str:
        """リストを文字列形式にフォーマット"""
        return "\n".join([f"- {item}" for item in items])

    def get_quality_checklist(self, priority: str = "critical") -> list[dict[str, Any]]:
        """
        品質チェックリストを取得

        Args:
            priority: 優先度 (critical, high, medium)

        Returns:
            チェック項目のリスト
        """
        quality_standards = self.guide_data.get("quality_standards", {})

        if priority not in quality_standards:
            return []

        return list(quality_standards[priority].values())

    def get_validation_checklist(self, check_type: str = "mandatory") -> list[dict[str, Any]]:
        """
        バリデーションチェックリストを取得

        Args:
            check_type: チェック種別 (mandatory, recommended)

        Returns:
            チェック項目のリスト
        """
        validation = self.guide_data.get("validation_checklist", {})
        key = f"{check_type}_checks"

        return validation.get(key, [])

    def get_genre_example(self, genre: str) -> str | None:
        """
        ジャンル別の使用例を取得

        Args:
            genre: ジャンル名

        Returns:
            使用例のプロンプト
        """
        examples = self.guide_data.get("usage_examples", {})

        # ジャンルに対応する例を検索
        for key, example in examples.items():
            if genre.lower() in key.lower():
                return example.get("prompt", "")

        return None

    def get_troubleshooting(self, problem_key: str) -> dict[str, Any] | None:
        """
        トラブルシューティング情報を取得

        Args:
            problem_key: 問題のキー（例: explanatory_writing）

        Returns:
            問題解決情報
        """
        troubleshooting = self.guide_data.get("troubleshooting", {})
        common_problems = troubleshooting.get("common_problems", {})

        return common_problems.get(problem_key)

    def generate_custom_prompt(
        self, request: WritingRequest, include_examples: bool = True, include_troubleshooting: bool = False
    ) -> str:
        """
        カスタム執筆プロンプトを生成

        Args:
            request: 執筆リクエスト設定
            include_examples: 使用例を含めるか
            include_troubleshooting: トラブルシューティングを含めるか

        Returns:
            カスタマイズされたプロンプト
        """
        # detail_levelに応じて生成方法を切り替え
        if request.detail_level == "minimal":
            return self._generate_minimal_prompt(request)
        if request.detail_level == "stepwise":
            return self._generate_stepwise_prompt(request, include_examples, include_troubleshooting)
        if request.detail_level == "detailed":
            return self._generate_detailed_prompt(request, include_examples, include_troubleshooting)
        # standard
        return self._generate_standard_prompt(request, include_examples, include_troubleshooting)

    def _generate_standard_prompt(
        self, request: WritingRequest, include_examples: bool = True, include_troubleshooting: bool = False
    ) -> str:
        """標準版プロンプト生成（現在の方式）"""
        prompt_parts = []

        # 基本プロンプト
        basic_prompt = self.get_basic_prompt(request)
        prompt_parts.append(basic_prompt)

        # ジャンル別例の追加
        if include_examples:
            example = self.get_genre_example(request.genre)
            if example:
                prompt_parts.append(f"\n\n【参考例】\n{example}")

        # トラブルシューティングの追加
        if include_troubleshooting:
            ts_info = self._get_common_troubleshooting()
            if ts_info:
                prompt_parts.append(f"\n\n【注意点】\n{ts_info}")

        # カスタム要件の追加
        if request.custom_requirements:
            custom_reqs = "\n".join([f"- {req}" for req in request.custom_requirements])
            prompt_parts.append(f"\n\n【追加要件】\n{custom_reqs}")

        return "\n".join(prompt_parts)

    def _generate_stepwise_prompt(
        self, request: WritingRequest, include_examples: bool = True, include_troubleshooting: bool = False
    ) -> str:
        """段階的執筆プロンプト生成（YAML構造化方式）"""
        prompt_parts = []

        # YAML構造化データから段階的執筆システムを取得
        stepwise_system = self.guide_data.get("stepwise_writing_system", {})

        if not stepwise_system:
            # フォールバック: 従来のテンプレート方式
            return self._generate_stepwise_prompt_legacy(request, include_examples, include_troubleshooting)

        # ヘッダー部分
        methodology = stepwise_system.get("methodology", "A30準拠10段階構造化執筆プロセス")
        prompt_parts.append(f"【📝 段階的執筆指示】{methodology}")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")

        # 禁止・推奨表現を取得
        variables = self.guide_data["prompt_templates"]["basic_writing_request"]["variables"]
        forbidden_expressions = self._format_list(variables["forbidden_expressions"])
        recommended_expressions = self._format_list(variables["recommended_expressions"])

        # 各段階の詳細を構築
        stages = stepwise_system.get("stages", {})
        for stage_data in stages.values():
            stage_name = stage_data.get("name", "未定義段階")
            objective = stage_data.get("objective", "")

            prompt_parts.append("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
            prompt_parts.append(f"┃ 🎯 {stage_name}")
            prompt_parts.append(f"┃ 目的: {objective}")
            prompt_parts.append("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
            prompt_parts.append("")

            # 必須ファイル情報（Stage 1のみ）
            if "required_files" in stage_data:
                prompt_parts.append("📁 必須参照ファイル:")
                for file_info in stage_data["required_files"]:
                    file_path = file_info["path"].format(
                        project_path=request.project_path or "{PROJECT_ROOT}",
                        episode_file=request.episode_file or "{EPISODE_FILE}",
                    )

                    prompt_parts.append(f"  ├─ {file_info['type']}: {file_path}")
                prompt_parts.append("")

            # タスク詳細
            tasks = stage_data.get("tasks", [])
            if tasks:
                prompt_parts.append("✅ 実行タスク:")
                for task in tasks:
                    task_name = task.get("name", "")
                    task_details = task.get("details", "")

                    prompt_parts.append(f"  {task_name}")
                    if task_details:
                        prompt_parts.append(f"    └─ {task_details}")

                    # サブタスクの処理
                    if "subtasks" in task:
                        for subtask in task["subtasks"]:
                            prompt_parts.append(f"    • {subtask}")

                    # 特別な処理（禁止表現など）
                    if task.get("id") == "expression_cleanup":
                        prompt_parts.append(f"    禁止表現: {forbidden_expressions}")
                    elif task.get("id") == "recommended_expressions":
                        prompt_parts.append(f"    推奨表現: {recommended_expressions}")
                    elif task.get("id") == "viewpoint_character":
                        task_details_formatted = task_details.format(viewpoint_character=request.viewpoint_character)
                        prompt_parts[-1] = f"    └─ {task_details_formatted}"
                    elif task.get("id") == "format_rules":
                        # 詳細なフォーマットルールを展開
                        format_rules = task.get("rules", [])
                        for rule in format_rules:
                            prompt_parts.append(f"    • {rule}")
                    elif task.get("id") == "narou_10_rules":
                        # なろう執筆10箇条を展開
                        narou_rules = task.get("rules", [])
                        for rule in narou_rules:
                            prompt_parts.append(f"    • {rule}")
                    elif task.get("id") == "opening_golden_rule":
                        # 冒頭3行の黄金律を展開
                        golden_rules = task.get("rules", [])
                        for rule in golden_rules:
                            prompt_parts.append(f"    • {rule}")

            # 完了マーカー
            completion_marker = stage_data.get("completion_marker", f"■ {stage_name} 完了")
            prompt_parts.append(f"\n⚠️ 完了時は必ず「{completion_marker}」と明記してください")
            prompt_parts.append("")

        # 最終出力要件
        final_output = stepwise_system.get("final_output", {})
        if final_output:
            prompt_parts.append("🎯 最終目標:")
            requirements = final_output.get("requirements", [])
            for req in requirements:
                formatted_req = req.format(
                    word_count=request.word_count,
                    viewpoint=request.viewpoint,
                    viewpoint_character=request.viewpoint_character,
                    genre=request.genre,
                )

                prompt_parts.append(f"  • {formatted_req}")

            completion_instruction = final_output.get("completion_instruction", "")
            if completion_instruction:
                prompt_parts.append(f"\n📝 {completion_instruction}")

        # カスタム要件の追加
        if request.custom_requirements:
            custom_reqs = "\n".join([f"  • {req}" for req in request.custom_requirements])
            prompt_parts.append(f"\n🔧 追加要件（各段階で考慮）:\n{custom_reqs}")

        return "\n".join(prompt_parts)

    def _generate_stepwise_prompt_legacy(
        self, request: WritingRequest, include_examples: bool = True, include_troubleshooting: bool = False
    ) -> str:
        """段階的執筆プロンプト生成（従来のテンプレート方式）"""
        prompt_parts = []

        # 段階的執筆プロンプト
        stepwise_template = self.guide_data["prompt_templates"]["stepwise_writing_request"]["template"]

        # ジャンル別の要件を取得
        genre_requirements = self._get_genre_requirements(request.genre)

        # 禁止・推奨表現を取得
        variables = self.guide_data["prompt_templates"]["basic_writing_request"]["variables"]
        forbidden_expressions = self._format_list(variables["forbidden_expressions"])
        recommended_expressions = self._format_list(variables["recommended_expressions"])

        # テンプレート変数を置換
        prompt = stepwise_template.format(
            word_count=request.word_count,
            viewpoint=request.viewpoint,
            viewpoint_character=request.viewpoint_character,
            genre=request.genre,
            project_path=request.project_path or "{PROJECT_ROOT}",
            episode_file=request.episode_file or "{EPISODE_FILE}",
            forbidden_expressions=forbidden_expressions,
            recommended_expressions=recommended_expressions,
            genre_specific_requirements=genre_requirements,
        )

        prompt_parts.append(prompt)

        # ジャンル別例の追加
        if include_examples:
            example = self.get_genre_example(request.genre)
            if example:
                prompt_parts.append(f"\n\n【段階的執筆の参考例】\n{example}")

        # トラブルシューティングの追加
        if include_troubleshooting:
            ts_info = self._get_common_troubleshooting()
            if ts_info:
                prompt_parts.append(f"\n\n【段階的執筆の注意点】\n{ts_info}")

        # カスタム要件の追加
        if request.custom_requirements:
            custom_reqs = "\n".join([f"- {req}" for req in request.custom_requirements])
            prompt_parts.append(f"\n\n【追加要件（各段階で考慮）】\n{custom_reqs}")

        return "\n".join(prompt_parts)

    def _generate_minimal_prompt(self, request: WritingRequest) -> str:
        """最小版プロンプト生成（核心ルールのみ ~1500文字）"""
        prompt_parts = []

        # 核心条件のみ
        core_template = """以下の条件で小説を執筆してください：

【基本条件】
- 字数：{word_count}字
- 視点：{viewpoint}（{viewpoint_character}視点）
- ジャンル：{genre}

【必須ルール】
- 段落設計：一塊一意義（1段落 = 1意味）、2-4行以内
- 禁止表現：「〜と思った」「〜という気持ち」「〜を感じた」
- 推奨：感情→身体反応で表現、説明→体験として表現"""

        core_prompt = core_template.format(
            word_count=request.word_count,
            viewpoint=request.viewpoint,
            viewpoint_character=request.viewpoint_character,
            genre=request.genre,
        )

        prompt_parts.append(core_prompt)

        # 最重要なカスタム要件のみ（最大3個）
        if request.custom_requirements:
            top_requirements = request.custom_requirements[:3]
            custom_reqs = "\n".join([f"- {req}" for req in top_requirements])
            prompt_parts.append(f"\n\n【重要条件】\n{custom_reqs}")

        return "\n".join(prompt_parts)

    def _generate_detailed_prompt(
        self, request: WritingRequest, include_examples: bool = True, include_troubleshooting: bool = False
    ) -> str:
        """詳細版プロンプト生成（全制約適用 ~5500文字）"""
        # 標準版をベースに詳細制約を追加
        standard_prompt = self._generate_standard_prompt(request, include_examples, include_troubleshooting)

        # 詳細制約を追加
        detailed_additions = []

        # 品質基準詳細
        quality_checklist = self.get_quality_checklist("critical")
        if quality_checklist:
            quality_items = [f"- {item.get('name', 'Unknown')}" for item in quality_checklist[:5]]
            detailed_additions.append("\n\n【品質基準】\n" + "\n".join(quality_items))

        # バリデーション詳細
        validation_items = self.get_validation_checklist("mandatory")
        if validation_items:
            val_summary = [f"- {item.get('check', 'Unknown')}" for item in validation_items[:3]]
            detailed_additions.append("\n\n【必須チェック】\n" + "\n".join(val_summary))

        return standard_prompt + "\n".join(detailed_additions)

    def _get_common_troubleshooting(self) -> str:
        """よくある問題のまとめを取得"""
        troubleshooting = self.guide_data.get("troubleshooting", {})
        common_problems = troubleshooting.get("common_problems", {})

        tips = []
        for problem_info in common_problems.values():
            problem = problem_info.get("problem", "")
            solution = problem_info.get("solution", [])

            solution_text = "\n  ".join(solution) if isinstance(solution, list) else str(solution)

            tips.append(f"【{problem}】\n  {solution_text}")

        return "\n\n".join(tips)

    def validate_content(self, content: str) -> dict[str, Any]:
        """
        執筆内容を検証

        Args:
            content: 検証対象の文章

        Returns:
            検証結果
        """
        results: dict[str, Any] = {"issues": [], "warnings": [], "score": 100, "recommendations": []}

        # 禁止表現チェック
        forbidden = self.guide_data["prompt_templates"]["basic_writing_request"]["variables"]["forbidden_expressions"]
        for expr in forbidden:
            pattern = expr.replace("〜", r"[^」]*?")  # 「〜」を任意文字に置換
            if re.search(pattern, content):
                results["issues"].append(f"禁止表現が含まれています: {expr}")
                results["score"] -= 10

        # 連続短文チェック
        sentences = re.split(r"[。！？]", content)
        max_consecutive = 0
        current_consecutive = 0

        for sentence in sentences:
            if len(sentence.strip()) < 30:  # 短文の基準:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        if max_consecutive >= 8:
            results["issues"].append(f"連続短文問題: {max_consecutive}文連続")
            results["score"] -= 15
        elif max_consecutive >= 5:
            results["warnings"].append(f"連続短文注意: {max_consecutive}文連続")
            results["score"] -= 5

        # 段落長チェック
        paragraphs = content.split("\n\n")
        long_paragraphs = [p for p in paragraphs if len(p.split("\n")) > 4]

        if long_paragraphs:
            results["warnings"].append(f"長い段落が{len(long_paragraphs)}個あります（4行超）")
            results["score"] -= 5

        return results

    def get_version_info(self) -> dict[str, Any]:
        """バージョン情報を取得"""
        return self.guide_data.get("metadata", {})

    def generate_yaml_prompt(self, request: WritingRequest) -> str:
        """
        YAML構造化形式でプロンプトを生成（ruamel.yaml使用でyamllint準拠）

        Args:
            request: 執筆リクエスト設定

        Returns:
            YAML形式のプロンプト
        """


        # YAML構造化データから段階的執筆システムを取得
        stepwise_system = self.guide_data.get("stepwise_writing_system", {})
        variables = self.guide_data["prompt_templates"]["basic_writing_request"]["variables"]

        # YAML構造化プロンプトデータを構築
        yaml_prompt_data: dict[str, Any] = {
            "metadata": {
                "title": f"段階的執筆プロンプト: {request.episode_file or '新規エピソード'}",
                "project": request.project_path or "Novel Project",
                "episode_file": request.episode_file or "new_episode.md",
                "genre": request.genre,
                "word_count": request.word_count,
                "viewpoint": request.viewpoint,
                "viewpoint_character": request.viewpoint_character,
                "detail_level": request.detail_level,
                "methodology": stepwise_system.get("methodology", "A30準拠10段階構造化執筆プロセス"),
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            },
            "instructions": {
                "overview": "以下のA30準拠10段階で小説を執筆してください。各段階を順次実行し、段階的に品質を向上させます。",
                "completion_rule": "各段階完了時に「■ Stage X 完了」と明記してください",
            },
            "required_files": {
                "description": "執筆前に必ず読み込むファイル",
                "files": [
                    {
                        "type": "plot",
                        "path": f"{request.project_path or '{PROJECT_ROOT}'}/20_プロット/{request.episode_file or '{EPISODE_FILE}'}",
                        "priority": "mandatory",
                    },
                    {
                        "type": "world_setting",
                        "path": f"{request.project_path or '{PROJECT_ROOT}'}/30_設定集/世界観.yaml",
                        "priority": "mandatory",
                    },
                    {
                        "type": "character_setting",
                        "path": f"{request.project_path or '{PROJECT_ROOT}'}/30_設定集/キャラクター.yaml",
                        "priority": "mandatory",
                    },
                ],
            },
            "stages": {},
        }

        # 各段階のデータを構築
        stages = stepwise_system.get("stages", {})
        for stage_key, stage_data in stages.items():
            stage_info = {
                "name": stage_data.get("name", "未定義段階"),
                "objective": stage_data.get("objective", ""),
                "completion_marker": stage_data.get("completion_marker", f"■ {stage_data.get('name', 'Stage')} 完了"),
                "tasks": [],
            }

            # タスク情報を構築
            tasks = stage_data.get("tasks", [])
            for task in tasks:
                task_info = {
                    "name": task.get("name", ""),
                    "details": task.get("details", ""),
                    "subtasks": task.get("subtasks", []),
                }

                # 特別なタスクの処理
                if task.get("id") == "expression_cleanup":
                    task_info["forbidden_expressions"] = variables.get("forbidden_expressions", [])
                elif task.get("id") == "recommended_expressions":
                    task_info["recommended_expressions"] = variables.get("recommended_expressions", [])
                elif task.get("id") == "format_rules":
                    task_info["format_rules"] = task.get("rules", [])
                elif task.get("id") == "narou_10_rules":
                    task_info["narou_rules"] = task.get("rules", [])
                elif task.get("id") == "opening_golden_rule":
                    task_info["golden_rules"] = task.get("rules", [])

                stage_info["tasks"].append(task_info)

            yaml_prompt_data["stages"][stage_key] = stage_info

        # 最終目標
        final_output = stepwise_system.get("final_output", {})
        yaml_prompt_data["final_output"] = {
            "word_count": request.word_count,
            "viewpoint": f"{request.viewpoint}（{request.viewpoint_character}視点）",
            "genre": request.genre,
            "completion_instruction": final_output.get(
                "completion_instruction", "全段階を統合した完成原稿を出力してください"
            ),
        }

        # カスタム要件
        if request.custom_requirements:
            yaml_prompt_data["custom_requirements"] = {
                "description": "各段階で考慮すべき追加要件",
                "requirements": request.custom_requirements,
            }

        # ruamel.yamlでyamllint準拠の厳格なフォーマット出力
        yaml = YAML()
        yaml.indent(mapping=4, sequence=4, offset=2)
        yaml.preserve_quotes = True
        yaml.width = 4096
        yaml.map_indent = 2
        yaml.sequence_indent = 4

        stream = io.StringIO()
        yaml.dump(yaml_prompt_data, stream)

        return stream.getvalue()

    def save_yaml_prompt(self, request: WritingRequest, output_dir: str | None = None) -> str:
        """
        YAML形式でプロンプトを生成し、ファイルに保存

        Args:
            request: 執筆リクエスト設定
            output_dir: 出力ディレクトリ（省略時は現在のディレクトリ）

        Returns:
            保存されたファイルのパス
        """

        # YAML形式プロンプトを生成
        yaml_prompt = self.generate_yaml_prompt(request)

        # 出力ファイル名を決定
        if request.episode_file:
            # エピソードファイル名から拡張子を除去してyamlに変更
            base_name = Path(request.episode_file).stem
            output_filename = f"{base_name}.yaml"
        else:
            output_filename = "stepwise_writing_prompt.yaml"

        # 出力ディレクトリを決定
        output_dir = Path.cwd() if output_dir is None else Path(output_dir)

        output_path = output_dir / output_filename

        # YAMLファイルに保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(yaml_prompt)

        return str(output_path)

    def validate_yaml_format(self, yaml_file_path: str) -> dict:
        """
        生成されたYAMLファイルの形式をチェック

        Args:
            yaml_file_path: 検証するYAMLファイルのパス

        Returns:
            検証結果の辞書 {is_valid: bool, errors: list, warnings: list}
        """


        result = {"is_valid": True, "errors": [], "warnings": [], "yaml_syntax_valid": False, "yamllint_passed": False}

        yaml_path = Path(yaml_file_path)
        if not yaml_path.exists():
            result["is_valid"] = False
            result["errors"].append(f"ファイルが存在しません: {yaml_file_path}")
            return result

        # 1. YAML構文チェック（PyYAMLによる）
        try:
            with open(yaml_path, encoding="utf-8") as f:
                yaml.safe_load(f)
            result["yaml_syntax_valid"] = True
        except yaml.YAMLError as e:
            result["is_valid"] = False
            result["errors"].append(f"YAML構文エラー: {e!s}")

        # 2. yamllintによるフォーマットチェック
        try:
            cmd_result = subprocess.run(
                ["yamllint", yaml_file_path], check=False, capture_output=True, text=True, timeout=30
            )

            if cmd_result.returncode == 0:
                result["yamllint_passed"] = True
            else:
                # yamllintの出力を解析
                output_lines = cmd_result.stdout.strip().split("\n") if cmd_result.stdout else []
                for line in output_lines:
                    if "error" in line.lower():
                        result["errors"].append(f"yamllint: {line}")
                        result["is_valid"] = False
                    elif "warning" in line.lower():
                        result["warnings"].append(f"yamllint: {line}")

        except subprocess.TimeoutExpired:
            result["warnings"].append("yamllintの実行がタイムアウトしました")
        except FileNotFoundError:
            result["warnings"].append("yamllintが見つかりません（インストールされていない可能性があります）")
        except Exception as e:
            result["warnings"].append(f"yamllint実行エラー: {e!s}")

        return result

    def save_yaml_prompt_with_validation(self, request: WritingRequest, output_dir: str | None = None) -> dict:
        """
        YAML形式でプロンプトを生成、保存し、検証も実行

        Args:
            request: 執筆リクエスト設定
            output_dir: 出力ディレクトリ（省略時は現在のディレクトリ）

        Returns:
            結果辞書 {file_path: str, validation: dict}
        """
        # YAMLファイル保存
        file_path = self.save_yaml_prompt(request, output_dir)

        # 検証実行
        validation_result = self.validate_yaml_format(file_path)

        return {"file_path": file_path, "validation": validation_result}

    def generate_yaml_prompt_legacy(self, request: WritingRequest) -> str:
        """
        YAML構造化形式でプロンプトを生成（レガシー版）

        Args:
            request: 執筆リクエスト設定

        Returns:
            YAML形式のプロンプト
        """

        # YAML構造化プロンプトデータを構築
        yaml_prompt_data: dict[str, Any] = {
            "metadata": {
                "title": f"執筆プロンプト: {request.episode_file}",
                "genre": request.genre,
                "word_count": request.word_count,
                "viewpoint": f"{request.viewpoint}（{request.viewpoint_character}視点）",
                "detail_level": request.detail_level,
                "generated_at": "2025-08-05",
            },
            "required_files": {
                "description": "執筆前に必ず読み込むファイル",
                "files": [
                    {
                        "type": "plot",
                        "description": "話別プロット",
                        "path": f"{request.project_path}/20_プロット/{request.episode_file}",
                    },
                    {
                        "type": "worldview",
                        "description": "世界観設定",
                        "path": f"{request.project_path}/30_設定集/世界観.yaml",
                    },
                    {
                        "type": "characters",
                        "description": "キャラクター設定",
                        "path": f"{request.project_path}/30_設定集/キャラクター.yaml",
                    },
                    {
                        "type": "terminology",
                        "description": "用語集",
                        "path": f"{request.project_path}/30_設定集/用語集.yaml",
                    },
                ],
            },
            "writing_conditions": {
                "basic": {
                    "word_count": request.word_count,
                    "viewpoint": request.viewpoint,
                    "viewpoint_character": request.viewpoint_character,
                    "genre": request.genre,
                },
                "paragraph_design": {
                    "principle": "一塊一意義（1段落 = 1意味）",
                    "length": "2-4行以内（スマホ最適化）",
                    "line_break_triggers": ["視点変化", "感情変化", "行動変化"],
                    "text_separation": ["地の文", "会話文", "描写文は段落分け"],
                },
                "forbidden_expressions": ["〜と思った", "〜という気持ち", "〜を感じた", "〜な雰囲気"],
                "recommended_expressions": [
                    "感情 → 身体反応で表現",
                    "抽象 → 具体的描写で表現",
                    "説明 → 体験として表現",
                ],
            },
            "genre_specifications": self._get_genre_yaml_specs(request.genre),
            "custom_requirements": request.custom_requirements or [],
            "quality_standards": {
                "critical_checks": [
                    "段落設計の原則遵守",
                    "視点統一の維持",
                    "禁止表現の排除",
                    "リズム管理（連続短文回避）",
                ],
                "recommended_checks": ["感情の身体反応表現", "ジャンル特化技法の適用", "世界観の体験的提示"],
            },
            "troubleshooting": {
                "common_issues": [
                    {"problem": "説明的文章", "solution": "「〜と思った」→身体反応、「〜という気持ち」→具体的行動"},
                    {"problem": "単調なリズム", "solution": "連続短文チェック、文章統合、五感描写拡張"},
                    {"problem": "会話文の羅列", "solution": "感情的反応挿入、身体的描写追加、内面描写補完"},
                ]
            },
        }

        # YAML形式で出力
        return yaml.dump(yaml_prompt_data, allow_unicode=True, default_flow_style=False, indent=2)

    def _get_genre_yaml_specs(self, genre: str) -> dict:
        """ジャンル特化仕様をYAML形式で取得"""
        genre_specs = self.guide_data.get("genre_specifications", {})

        if genre not in genre_specs:
            return {}

        spec = genre_specs[genre]
        return {
            "name": spec.get("name", genre),
            "specific_rules": spec.get("specific_rules", []),
            "template_additions": spec.get("template_additions", []),
        }


def main() -> None:
    """使用例のデモンストレーション"""
    from noveler.presentation.shared.shared_utilities import console  # noqa: PLC0415


    processor = YamlGuideProcessor()

    # ファンタジー小説の執筆依頼例
    fantasy_request = WritingRequest(
        genre="fantasy",
        word_count="5000",
        viewpoint="一人称（主人公）",
        custom_requirements=["魔法学園設定", "主人公は初心者魔法使い"],
    )

    console.print("=== ファンタジー小説執筆プロンプト ===")
    prompt = processor.generate_custom_prompt(fantasy_request, include_examples=True)
    console.print(prompt)

    console.print("\n=== 品質チェックリスト ===")
    checklist = processor.get_quality_checklist("critical")
    for item in checklist:
        console.print(f"- {item.get('name', 'Unknown')}")

    console.print("\n=== バージョン情報 ===")
    version_info = processor.get_version_info()
    console.print(f"Version: {version_info.get('version', 'Unknown')}")
    console.print(f"Last Updated: {version_info.get('last_updated', 'Unknown')}")


if __name__ == "__main__":
    main()
