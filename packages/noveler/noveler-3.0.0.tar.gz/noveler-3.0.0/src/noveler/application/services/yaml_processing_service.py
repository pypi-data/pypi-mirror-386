"""YAML processing application services.

Provides application-level adapters that wrap the domain YAML processors in accordance with SPEC-YAML-001.
"""

from typing import Any

from noveler.domain.interfaces.yaml_processor import IYamlContentProcessor, IYamlProcessor
from noveler.domain.value_objects.project_time import project_now


class YamlProcessingService:
    """Expose YAML processing use cases at the application layer.

    The service adapts domain-level processors so business validation and metadata enrichment can
    happen before persisting YAML artifacts.
    """

    def __init__(self, yaml_processor: IYamlProcessor) -> None:
        """Initialize the service.

        Args:
            yaml_processor: Concrete YAML processor injected from the infrastructure layer.
        """
        self._yaml_processor = yaml_processor

    def process_episode_content(self, content: str) -> dict[str, Any]:
        """Transform raw episode content into a YAML-ready structure.

        Args:
            content: Episode body text to process.

        Returns:
            dict[str, Any]: Serializable dictionary prepared for YAML output.

        Raises:
            ValueError: If the content is empty or only whitespace.
        """
        if not content or not content.strip():
            msg = "Episode content cannot be empty"
            raise ValueError(msg)

        # マルチライン文字列オブジェクトを生成
        multiline_content = self._yaml_processor.create_multiline_string(content)

        # 処理結果構造を作成
        result = {
            "content": multiline_content,
            "processed_at": project_now().datetime.isoformat(),
            "content_length": len(content),
            "line_count": content.count("\\n") + 1,
            "processing_metadata": {"processor_version": "1.0", "spec_compliance": "SPEC-YAML-001"},
        }

        return self._yaml_processor.process_content_to_dict(result)

    def create_episode_yaml_structure(
        self,
        episode_number: int,
        title: str,
        content: str,
        template_version: str = "1.0",
        generation_mode: str = "enhanced",
        quality_level: str = "detailed",
        additional_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the canonical YAML payload for a single episode.

        Args:
            episode_number: Numerical identifier of the episode.
            title: Episode title.
            content: Episode content text.
            template_version: Version identifier of the YAML template.
            generation_mode: Mode that generated the episode content.
            quality_level: Quality level classification.
            additional_metadata: Optional metadata to merge into the payload.

        Returns:
            dict[str, Any]: YAML-ready structure enriched with metadata and validation info.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        # 入力検証
        if episode_number <= 0:
            msg = "Episode number must be positive"
            raise ValueError(msg)

        if not title or not title.strip():
            msg = "Episode title cannot be empty"
            raise ValueError(msg)

        if not content or not content.strip():
            msg = "Episode content cannot be empty"
            raise ValueError(msg)

        if len(content) < 100:
            msg = "Episode content too short (minimum 100 characters)"
            raise ValueError(msg)

        # マルチライン処理
        multiline_content = self._yaml_processor.create_multiline_string(content)

        # 基本構造作成
        yaml_structure = {
            "metadata": {
                "spec_id": "SPEC-PROMPT-SAVE-001",
                "episode_number": episode_number,
                "title": title,
                "generation_timestamp": project_now().datetime.isoformat(),
                "template_version": template_version,
                "generation_mode": generation_mode,
                "quality_level": quality_level,
            },
            "prompt_content": multiline_content,
            "content_sections": additional_metadata.get("content_sections", {}) if additional_metadata else {},
            "validation": {
                "content_length": len(content),
                "sections_count": len(additional_metadata.get("content_sections", {}) if additional_metadata else {}),
                "quality_validated": True,
                "processing_timestamp": project_now().datetime.isoformat(),
            },
        }

        # 追加メタデータのマージ
        if additional_metadata:
            # content_sectionsは上で処理済みなので除外
            filtered_metadata = {k: v for k, v in additional_metadata.items() if k != "content_sections"}
            if filtered_metadata:
                yaml_structure["additional_metadata"] = filtered_metadata

        return self._yaml_processor.process_content_to_dict(yaml_structure)

    def validate_and_process_bulk_content(self, content_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate and convert multiple content items in a single batch.

        Args:
            content_list: Items to validate and transform.

        Returns:
            dict[str, Any]: Summary containing processed items and validation errors.

        Raises:
            ValueError: If the content list is empty.
        """
        if not content_list:
            msg = "Content list cannot be empty"
            raise ValueError(msg)

        processed_items = []
        validation_errors = []

        for idx, content_item in enumerate(content_list):
            try:
                # 各アイテムを検証・処理
                if "content" not in content_item:
                    msg = f"Item {idx}: 'content' field is required"
                    raise ValueError(msg)

                # マルチラインフィールド特定
                multiline_fields = ["content", "description", "summary"]  # 標準的なマルチラインフィールド

                processed_item = self._yaml_processor.create_safe_yaml_dict(content_item, multiline_fields)

                # YAML serializable 検証
                if not self._yaml_processor.validate_yaml_serializable(processed_item):
                    msg = f"Item {idx}: Not YAML serializable"
                    raise ValueError(msg)

                processed_items.append(processed_item)

            except Exception as e:
                validation_errors.append(
                    {
                        "index": idx,
                        "error": str(e),
                        "content_preview": str(content_item).get("title", f"Item {idx}")[:50],
                    }
                )

        return {
            "processed_items": processed_items,
            "total_count": len(content_list),
            "success_count": len(processed_items),
            "error_count": len(validation_errors),
            "validation_errors": validation_errors,
            "processing_summary": {
                "processed_at": project_now().datetime.isoformat(),
                "processor_version": "1.0",
                "spec_compliance": "SPEC-YAML-001",
            },
        }


class YamlContentOrchestrator:
    """Coordinate YAML processing workflows across multiple services.

    The orchestrator combines the core service with optional content processors to address complex flows.
    """

    def __init__(
        self, yaml_processing_service: YamlProcessingService, content_processor: IYamlContentProcessor | None = None
    ) -> None:
        """Initialize the orchestrator.

        Args:
            yaml_processing_service: Core YAML processing service.
            content_processor: Optional content-specific processor to augment the workflow.
        """
        self._yaml_processing_service = yaml_processing_service
        self._content_processor = content_processor

    def orchestrate_episode_creation_workflow(self, episode_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the end-to-end workflow for creating an episode YAML artifact.

        Args:
            episode_data: Source data describing the episode.

        Returns:
            dict[str, Any]: Resulting YAML structure and workflow metadata.

        Raises:
            ValueError: If required episode fields are missing or invalid.
        """
        # 必須フィールド検証
        required_fields = ["episode_number", "title", "content"]
        missing_fields = [field for field in required_fields if field not in episode_data]

        if missing_fields:
            msg = f"Missing required fields: {missing_fields}"
            raise ValueError(msg)

        # YAML構造生成
        yaml_structure = self._yaml_processing_service.create_episode_yaml_structure(
            episode_number=episode_data["episode_number"],
            title=episode_data["title"],
            content=episode_data["content"],
            template_version=episode_data.get("template_version", "1.0"),
            generation_mode=episode_data.get("generation_mode", "enhanced"),
            quality_level=episode_data.get("quality_level", "detailed"),
            additional_metadata=episode_data.get("metadata", {}),
        )

        # 専用プロセッサがある場合は追加処理
        if self._content_processor:
            enhanced_structure = self._content_processor.create_episode_yaml_structure(
                episode_data["episode_number"],
                episode_data["title"],
                episode_data["content"],
                episode_data.get("metadata", {}),
            )

            # 結果をマージ（専用プロセッサの結果を優先）
            yaml_structure.update(enhanced_structure)

        return {
            "yaml_structure": yaml_structure,
            "workflow_metadata": {
                "completed_at": project_now().datetime.isoformat(),
                "workflow_version": "1.0",
                "orchestrator_spec": "SPEC-YAML-001",
            },
        }
