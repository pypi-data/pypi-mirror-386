"""ProfileId 値オブジェクト

SPEC-CONFIGURATION-001準拠
"""


class ProfileId:
    """プロファイルID値オブジェクト"""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            msg = "ProfileID cannot be empty"
            raise ValueError(msg)
        self.value = value.strip()

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProfileId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
