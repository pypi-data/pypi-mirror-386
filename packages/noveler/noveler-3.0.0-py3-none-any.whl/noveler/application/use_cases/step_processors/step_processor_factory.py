"""ステップ処理器ファクトリー

ステップ番号に応じた適切な処理器を提供
"""


from .base_step_processor import BaseStepProcessor


class MockStepProcessor(BaseStepProcessor):
    """モックステップ処理器（テスト用）"""

    async def execute(self, session, context=None):
        from noveler.domain.entities.interactive_writing_session import StepExecutionResult, StepStatus

        return StepExecutionResult(
            step=self.step_number,
            status=StepStatus.COMPLETED,
            output={"message": f"ステップ {self.step_number} 完了（モック）"},
            summary=f"ステップ {self.step_number}: {self.get_step_name()} が完了しました",
            user_prompt="処理が完了しました。続行しますか？"
        )

    def validate_prerequisites(self, session):
        return True


class StepProcessorFactory:
    """ステップ処理器ファクトリー"""

    def get_processor(self, step: int | float) -> BaseStepProcessor:
        """ステップ処理器を取得

        Args:
            step: ステップ番号（整数または浮動小数点数）

        Returns:
            ステップ処理器
        """
        # STEP 3: テーマ性・独自性検証（旧2.5）
        if step == 3:
            from .theme_uniqueness_step_processor import ThemeUniquenessStepProcessor
            return ThemeUniquenessStepProcessor()

        # 実際の実装では各ステップに応じた専用処理器を返す
        # 現在はモック処理器を返す
        return MockStepProcessor(step)
