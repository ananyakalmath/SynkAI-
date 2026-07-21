"""
RAG Chat API Endpoints for SynkAI.
Provides POST /chat/upload for vector indexing and POST /chat/query for Q&A.
"""

import os
from fastapi import APIRouter, HTTPException, status
from backend.config import settings
from backend.models.chat import (
    ChatUploadRequest,
    ChatUploadResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    SourceChunk
)
from backend.services.file_parser import FileParserService
from backend.services.chunking_service import ChunkingService
from backend.services.vector_service import VectorService
from backend.services.retrieval_service import RetrievalService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

chunking_service = ChunkingService()
vector_service = VectorService()
retrieval_service = RetrievalService(vector_service=vector_service)


@router.post(
    "/chat/upload",
    response_model=ChatUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Index uploaded transcript into ChromaDB vector store"
)
async def index_transcript_for_chat(request: ChatUploadRequest) -> ChatUploadResponse:
    """
    Parses, chunks, embeds, and indexes an uploaded transcript file into ChromaDB for RAG retrieval.

    - **filename**: Relative filename located in uploads/.
    """
    file_path = os.path.join(settings.UPLOADS_DIR, os.path.basename(request.filename))
    if not os.path.exists(file_path):
        logger.error(f"Cannot index file. Path does not exist: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{request.filename}' not found in uploads directory."
        )

    logger.info(f"Step 1/4: Parsing file '{request.filename}' for indexing...")
    try:
        extracted_text = FileParserService.parse_file(file_path)
    except Exception as exc:
        logger.error(f"Failed to parse text from '{file_path}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File parsing failed: {str(exc)}"
        )

    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{request.filename}' is empty."
        )

    logger.info(f"Step 2/4: Chunking text for '{request.filename}'...")
    chunks = chunking_service.chunk_text(extracted_text)

    logger.info(f"Step 3/4 & 4/4: Generating embeddings and storing vectors in ChromaDB...")
    try:
        stored_count = vector_service.store_chunks(
            filename=request.filename,
            chunks=chunks
        )
    except ConnectionError as exc:
        logger.error(f"Ollama embedding connection error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"Failed to store vectors in ChromaDB: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector storage failed: {str(exc)}"
        )

    return ChatUploadResponse(
        filename=request.filename,
        chunk_count=len(chunks),
        vectors_stored=stored_count,
        message=f"Successfully indexed {stored_count} vectors for '{request.filename}'."
    )


@router.post(
    "/chat/query",
    response_model=ChatQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query indexed transcripts using RAG"
)
async def query_transcript_chat(request: ChatQueryRequest) -> ChatQueryResponse:
    """
    RAG query endpoint to ask questions over indexed meeting transcripts.

    - **question**: User query string.
    - **filename**: Optional filename to restrict search scope.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question field cannot be empty."
        )

    logger.info(f"Querying transcript RAG engine with question: '{request.question}'...")

    try:
        rag_result = retrieval_service.answer_question(
            question=request.question,
            filename=request.filename
        )

        sources = [
            SourceChunk(
                filename=src["filename"],
                chunk_number=src["chunk_number"],
                text=src["text"]
            )
            for src in rag_result.get("sources", [])
        ]

        return ChatQueryResponse(
            answer=rag_result["answer"],
            sources=sources,
            model_used=rag_result["model_used"]
        )

    except ConnectionError as exc:
        logger.error(f"Ollama service error during RAG retrieval: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"RAG query processing failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(exc)}"
        )
