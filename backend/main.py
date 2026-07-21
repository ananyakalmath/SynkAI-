"""
FastAPI application entry point for SynkAI backend.
Configures CORS middleware, health routes, lifespan logging, and global exception handlers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routes.health import router as health_router
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager handling application startup and shutdown events.
    Configures startup and shutdown logging.
    """
    logger.info(f"=== Starting {settings.APP_NAME} Backend (Environment: {settings.ENVIRONMENT}) ===")
    yield
    logger.info(f"=== Shutting down {settings.APP_NAME} Backend ===")


def create_app() -> FastAPI:
    """
    Initializes and configures the FastAPI application instance.

    Returns:
        FastAPI: Fully configured FastAPI app.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Agentic AI Meeting Assistant powered by LangGraph, RAG, Ollama, and ChromaDB.",
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include health routes
    app.include_router(health_router)

    # Global unhandled exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected internal server error occurred."}
        )

    return app


app = create_app()

if __name__ == "__main__":
    logger.info(f"Launching Uvicorn server at {settings.HOST}:{settings.PORT}...")
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
