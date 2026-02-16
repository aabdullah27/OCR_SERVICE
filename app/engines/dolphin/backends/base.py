from abc import ABC, abstractmethod
from PIL import Image


class DolphinBackend(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def chat(self, prompt: str, image: Image.Image) -> str:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    async def cleanup(self) -> None:
        pass
