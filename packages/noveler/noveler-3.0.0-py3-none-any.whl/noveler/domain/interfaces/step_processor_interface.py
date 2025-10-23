# File: src/noveler/domain/interfaces/step_processor_interface.py
# Purpose: Define the step processor interface used by domain orchestrators.
# Context: Allows application services to inject step processors without binding to concrete implementations.

"""Purpose: Provide an interface for asynchronous step processors used in domain workflows.
Context: Supports dependency inversion between domain orchestrators and infrastructure processors.
Side Effects: None within the interface definition.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class IStepProcessor(ABC):
    """Purpose: Describe the contract for processing workflow steps.

    Side Effects:
        Implementations may perform I/O or mutate provided context dictionaries.
    """

    @abstractmethod
    async def process(self, context: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Purpose: Execute the step logic using the supplied context.

        Args:
            context: Mutable processing context shared across steps.
            **kwargs: Additional parameters or overrides for the step execution.

        Returns:
            Updated processing context dictionary.

        Side Effects:
            Implementation defined; may perform network requests or filesystem writes.
        """

    @abstractmethod
    def get_step_number(self) -> float:
        """Purpose: Identify the numeric step position handled by this processor.

        Returns:
            Step number as a float (e.g., 1.0, 2.5).

        Side Effects:
            None.
        """

    @abstractmethod
    def get_step_name(self) -> str:
        """Purpose: Provide a human-readable name for the step.

        Returns:
            Step name string.

        Side Effects:
            None.
        """
