import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

OutputFormat = Literal["markdown", "html", "json"]


@dataclass
class OCRResult:
    content: str
    format: OutputFormat
    metadata: dict = field(default_factory=dict)


class OCREngine(ABC):
    name: str
    supported_formats: list[OutputFormat]

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def process(self, image: bytes, output_format: OutputFormat = "markdown") -> OCRResult:
        pass

    async def process_batch(self, images: list[bytes], output_format: OutputFormat = "markdown") -> list[OCRResult | Exception]:
        tasks = [self.process(img, output_format) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    async def cleanup(self) -> None:
        pass
