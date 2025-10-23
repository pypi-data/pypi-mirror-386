"""
File: tests/fixtures/domain/value_objects/immutable_vo_example.py
Purpose: Immutable Value Object with @dataclass(frozen=True)
Context: Should pass detection (dataclass auto-generates __eq__)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ImmutableEpisodeNumber:
    """
    Immutable Value Object - Should pass

    @dataclass(frozen=True) で不変性を保証
    __eq__ は自動生成される
    """
    value: int

    def __post_init__(self):
        """バリデーション"""
        if not 1 <= self.value <= 9999:
            raise ValueError(f"Invalid episode number: {self.value}")


@dataclass(eq=True, frozen=True)
class StrictImmutableValue:
    """
    Explicit eq=True - Should pass

    eq=True を明示的に指定
    """
    data: str

    def __post_init__(self):
        if not self.data:
            raise ValueError("Data cannot be empty")


@dataclass(eq=False)
class NoEqValue:
    """
    eq=False specified - Should fail

    __eq__ が生成されない
    __post_init__ もない
    """
    value: int
