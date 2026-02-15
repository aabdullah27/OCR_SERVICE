class OCRException(Exception):
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class EngineNotFoundError(OCRException):
    def __init__(self, engine_name: str):
        super().__init__(f"Engine '{engine_name}' not found", {"engine": engine_name})


class UnsupportedFormatError(OCRException):
    def __init__(self, format: str, engine: str, supported: list[str]):
        super().__init__(
            f"Format '{format}' not supported by engine '{engine}'",
            {"format": format, "engine": engine, "supported_formats": supported},
        )


class ImageProcessingError(OCRException):
    def __init__(self, reason: str):
        super().__init__(f"Failed to process image: {reason}")


class VLLMConnectionError(OCRException):
    def __init__(self, url: str, reason: str):
        super().__init__(f"Failed to connect to vLLM at {url}: {reason}", {"url": url})
