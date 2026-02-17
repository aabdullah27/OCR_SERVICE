from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import router
from app.core.config import settings
from app.core.exceptions import OCRException
from app.engines.registry import EngineRegistry

import app.engines.dolphin.engine  # noqa: F401
import app.engines.gemini.engine  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Startup] Initializing engine: {settings.DEFAULT_ENGINE}")
    await EngineRegistry.initialize_engine(settings.DEFAULT_ENGINE)
    print(f"[Startup] Engine ready: {settings.DEFAULT_ENGINE}")
    yield
    print("[Shutdown] Cleaning up engines...")
    await EngineRegistry.cleanup_all()


app = FastAPI(
    title="OCR Service",
    description="OCR microservice",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OCRException)
async def ocr_exception_handler(request: Request, exc: OCRException):
    return JSONResponse(status_code=400, content={"detail": exc.message, "error_type": type(exc).__name__})


app.include_router(router)
