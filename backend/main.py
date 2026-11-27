"""
FastAPI application entry point for SynkAI backend.
Configures CORS middleware, health/upload/summary/chat routes, lifespan logging, and global exception handlers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db import init_db
from backend.routes.health import router as health_router
from backend.routes.upload import router as upload_router
from backend.routes.summary import router as summary_router
from backend.routes.chat import router as chat_router
from backend.routes.analysis import router as analysis_router
from backend.routes.meetings import router as meetings_router
from backend.routes.auth import router as auth_router
from backend.routes.workspace import router as workspace_router
from backend.routes.scheduled_meetings import router as scheduled_meetings_router
from backend.routes.google_calendar import router as google_calendar_router
from backend.services import auth_service
from backend.services.meeting_schedule_service import send_due_reminders
from backend.services.migration_service import migrate_legacy_chroma_data, migrate_legacy_uploads
from backend.services.vector_service import VectorService
from backend.utils.logger import get_logger


logger = get_logger(__name__)


async def _reminder_loop() -> None:
    """
    Periodically checks every workspace's scheduled meetings for a due 24h/1h
    reminder. A plain asyncio background task rather than a new scheduler dependency —
    send_due_reminders() is itself a one-shot, idempotent, directly-testable function;
    this loop is just what calls it repeatedly in a real running server.
    """
    while True:
        try:
            sent = await asyncio.to_thread(send_due_reminders)
            if sent:
                logger.info(f"Sent {sent} meeting reminder email(s).")
        except Exception as exc:
            logger.error(f"Reminder check failed (will retry): {exc}", exc_info=True)
        await asyncio.sleep(settings.REMINDER_CHECK_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager handling application startup and shutdown events:
    starts the reminder background loop, and stops it cleanly on shutdown.
    """
    logger.info(f"=== Starting {settings.APP_NAME} Backend (Environment: {settings.ENVIRONMENT}) ===")
    reminder_task = asyncio.create_task(_reminder_loop())
    yield
    reminder_task.cancel()
    logger.info(f"=== Shutting down {settings.APP_NAME} Backend ===")


def _init_accounts_and_migrate_legacy_data() -> None:
    """
    Creates the accounts database and the fixed-ID "legacy" workspace, then migrates
    any pre-account uploads/ files and ChromaDB chunks into it. Runs at import time
    (not inside the async lifespan) so it happens reliably for the real server and for
    TestClient(app), which doesn't always trigger ASGI lifespan events.
    """
    init_db()
    auth_service.ensure_default_workspace()

    try:
        vector_service = VectorService()
        migrate_legacy_chroma_data(vector_service)
    except Exception as exc:
        logger.error(f"Legacy ChromaDB migration failed (continuing startup): {exc}", exc_info=True)

    try:
        migrate_legacy_uploads()
    except Exception as exc:
        logger.error(f"Legacy uploads migration failed (continuing startup): {exc}", exc_info=True)


def create_app() -> FastAPI:
    """
    Initializes and configures the FastAPI application instance.

    Returns:
        FastAPI: Fully configured FastAPI app.
    """
    _init_accounts_and_migrate_legacy_data()

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
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(workspace_router, tags=["Workspace"])
    app.include_router(upload_router, tags=["Upload"])
    app.include_router(summary_router, tags=["Summarization"])
    app.include_router(chat_router, tags=["RAG Chat"])
    app.include_router(analysis_router, tags=["Analysis"])
    app.include_router(meetings_router, tags=["Meetings"])
    app.include_router(scheduled_meetings_router, tags=["Scheduled Meetings"])
    app.include_router(google_calendar_router, tags=["Google Calendar"])

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
