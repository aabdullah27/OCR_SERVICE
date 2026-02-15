from typing import TYPE_CHECKING

from app.core.exceptions import EngineNotFoundError

if TYPE_CHECKING:
    from app.engines.base import OCREngine


class EngineRegistry:
    _engines: dict[str, type["OCREngine"]] = {}
    _instances: dict[str, "OCREngine"] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(engine_cls: type["OCREngine"]):
            cls._engines[name] = engine_cls
            return engine_cls
        return decorator

    @classmethod
    def get_class(cls, name: str) -> type["OCREngine"]:
        if name not in cls._engines:
            raise EngineNotFoundError(name)
        return cls._engines[name]

    @classmethod
    def get_instance(cls, name: str) -> "OCREngine":
        if name not in cls._instances:
            raise EngineNotFoundError(name)
        return cls._instances[name]

    @classmethod
    async def initialize_engine(cls, name: str, **kwargs) -> "OCREngine":
        engine_cls = cls.get_class(name)
        engine = engine_cls(**kwargs)
        await engine.initialize()
        cls._instances[name] = engine
        return engine

    @classmethod
    async def cleanup_all(cls) -> None:
        for engine in cls._instances.values():
            await engine.cleanup()
        cls._instances.clear()

    @classmethod
    def list_engines(cls) -> list[str]:
        return list(cls._engines.keys())

    @classmethod
    def list_initialized(cls) -> list[str]:
        return list(cls._instances.keys())
