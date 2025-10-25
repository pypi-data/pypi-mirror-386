from abc import ABC, abstractmethod
from typing import Optional

from beekeeper.core.observers.types import PayloadRecord
from beekeeper.core.prompts import PromptTemplate
from deprecated import deprecated


class BaseObserver(ABC):
    """An interface for observability."""

    @classmethod
    def class_name(cls) -> str:
        return "BaseObserver"


class PromptObserver(BaseObserver):
    """Abstract base class defining the interface for prompt observability."""

    def __init__(self, prompt_template: Optional[PromptTemplate] = None) -> None:
        self.prompt_template = prompt_template

    @classmethod
    def class_name(cls) -> str:
        return "PromptObserver"

    @abstractmethod
    def __call__(self, payload: PayloadRecord) -> None:
        """PromptObserver."""


@deprecated(
    reason="'ModelObserver()' is deprecated and will be removed in a future version. Use 'PromptObserver()' instead.",
    version="1.0.3",
    action="always",
)
class ModelObserver(PromptObserver):
    """DEPRECATED: This class is deprecated and kept only for backward compatibility."""


class TelemetryObserver(BaseObserver):
    """Abstract base class defining the interface for telemetry observability."""

    @classmethod
    def class_name(cls) -> str:
        return "TelemetryObserver"
