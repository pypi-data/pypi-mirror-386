# File: src/noveler/domain/services/validation/target_length_validator.py
# Purpose: Validate and normalize target_length configuration
# Context: Extracted from ProgressiveCheckManager._normalize_target_length_dict

from typing import Any

from noveler.domain.services.progressive_check_manager import ProjectConfigError


class TargetLengthValidator:
    """Target length validation and normalization (Domain layer - no I/O).

    Responsibilities:
    - Validate target_length dictionary structure
    - Normalize min/max values (type coercion)
    - Enforce business rules (min < max, both >= 1)

    Extracted from:
    - ProgressiveCheckManager._normalize_target_length_dict (lines 391-403)

    Business rules:
    - min and max must be integers
    - min >= 1, max >= 1
    - min < max (strict inequality)
    """

    @staticmethod
    def normalize_target_length(
        candidate: dict[str, Any],
        *,
        source: str,
    ) -> dict[str, Any]:
        """Validate and normalize target_length dictionary.

        Args:
            candidate: Raw target_length dict with "min" and "max" keys
            source: Source identifier for error messages (e.g., "project_config", "manifest")

        Returns:
            Normalized dict with:
            - min: int (>= 1)
            - max: int (>= 1, > min)
            - source: str (identifier)

        Raises:
            ProjectConfigError: QC-010 when validation fails
                - Not a dict
                - Missing min/max keys
                - Non-numeric values
                - Invalid range (min < 1, max < 1, min >= max)

        Example:
            >>> validator = TargetLengthValidator()
            >>> validator.normalize_target_length(
            ...     {"min": "3000", "max": "5000"},
            ...     source="test"
            ... )
            {"min": 3000, "max": 5000, "source": "test"}
        """
        # Validate structure
        if not isinstance(candidate, dict):
            raise ProjectConfigError(
                "QC-010",
                "target_length が辞書形式ではありません",
                details={"source": source},
            )

        # Extract and coerce min/max
        try:
            min_val = int(candidate["min"])
            max_val = int(candidate["max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProjectConfigError(
                "QC-010",
                "target_length に min/max が存在しないか数値ではありません",
                details={"source": source},
            ) from exc

        # Validate business rules
        if min_val < 1 or max_val < 1 or min_val >= max_val:
            raise ProjectConfigError(
                "QC-010",
                "target_length の min/max が不正です",
                details={
                    "source": source,
                    "min": min_val,
                    "max": max_val,
                },
            )

        return {
            "min": min_val,
            "max": max_val,
            "source": source,
        }
