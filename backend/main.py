"""
FastAPI application entry point for SynkAI backend.
Configures CORS middleware, health/upload/summary/chat routes, lifespan logging, and global exception handlers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routes.health import router as health_router
from backend.routes.upload import router as upload_router
from backend.routes.summary import router as summary_router
from backend.routes.chat import router as chat_router
from backend.routes.analysis import router as analysis_router
from backend.routes.meetings import router as meetings_router
from backend.routes.auth import router as auth_router
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
        version="0.3.0",
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

    # Mount API routes
    app.include_router(health_router, tags=["Health"])
    app.include_router(upload_router, tags=["Upload"])
    app.include_router(summary_router, tags=["Summarization"])
    app.include_router(chat_router, tags=["RAG Chat"])
    app.include_router(analysis_router, tags=["Analysis"])
    app.include_router(meetings_router, tags=["Meetings"])
    app.include_router(auth_router, tags=["Authentication"])


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
