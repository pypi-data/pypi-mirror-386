from abc import ABC, abstractmethod
from typing import Any


class TemplaterInterface(ABC):
    @abstractmethod
    def render(self, template: str, **kwargs: dict[str, Any]) -> str:
        raise NotImplementedError
