"""
RAG Chat API Routes for SynkAI.
Handles POST /chat/upload for uploading and indexing transcripts,
and POST /chat/query for Q&A retrieval.
"""

import asyncio
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from backend.dependencies import get_current_user
from backend.models.chat import (
    ChatUploadResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    SourceMetadata
)
from backend.services.auth_service import AuthContext
from backend.services.file_parser import FileParserService
from backend.services.chunking_service import ChunkingService
from backend.services.vector_service import VectorService
from backend.services.retrieval_service import RetrievalService
from backend.utils.logger import get_logger
from backend.utils.uploads import save_upload_and_hash, workspace_uploads_dir

logger = get_logger(__name__)
router = APIRouter()

# Instantiate services
chunking_service = ChunkingService()
vector_service = VectorService()
retrieval_service = RetrievalService(vector_service=vector_service)


@router.post(
    "/chat/upload",
    response_model=ChatUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index meeting transcript into ChromaDB"
)
async def index_transcript_for_chat(
    file: UploadFile = File(...),
    current: AuthContext = Depends(get_current_user),
) -> ChatUploadResponse:
    """
    Ingests an uploaded meeting transcript (.txt, .pdf, .docx) or a recorded video/audio
    meeting (transcribed locally with Whisper first), splits the resulting text into
    overlapping chunks, generates embeddings, and indexes into ChromaDB — tagged with
    the caller's workspace so it is never visible to another workspace.

    - **file**: UploadFile binary stream.
    """
    logger.info("Transcript uploaded event triggered via /chat/upload.")
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty."
        )

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    if ext not in FileParserService.SUPPORTED_EXTENSIONS:
        logger.warning(f"Rejected upload for unsupported extension '{ext}': {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats are: {', '.join(FileParserService.SUPPORTED_EXTENSIONS)}"
        )

    # Ensure the workspace's uploads subdirectory exists
    uploads_dir = workspace_uploads_dir(current.workspace_id)
    os.makedirs(uploads_dir, exist_ok=True)

    # Define destination path
    safe_filename = os.path.basename(file.filename)
    target_path = os.path.join(uploads_dir, safe_filename)

    logger.info(f"Saving uploaded file to '{target_path}'...")
    try:
        file_hash = save_upload_and_hash(file, target_path)
    except Exception as exc:
        logger.error(f"Failed to save uploaded file '{file.filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file on server: {str(exc)}"
        )

    # Check file size limit (video/audio recordings get a much higher ceiling)
    file_size = os.path.getsize(target_path)
    max_size_mb = FileParserService.max_size_mb(ext)
    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        os.remove(target_path)
        logger.warning(f"File size {file_size} bytes exceeds limit of {max_bytes} bytes.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {max_size_mb} MB."
        )

    # Parse extracted text using FileParserService, keyed by content hash so a file
    # already seen by /upload or /summarize isn't re-parsed (re-transcribed). Video/
    # audio transcription can take minutes, so this runs off the event loop like the
    # embedding work below.
    logger.info("Transcript parsed starting...")
    try:
        extracted_text = await asyncio.to_thread(FileParserService.parse_file, target_path, file_hash)
    except Exception as exc:
        logger.error(f"Text extraction failed for '{target_path}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse text from uploaded file: {str(exc)}"
        )

    # Chunk the parsed text
    logger.info("Chunks created starting...")
    chunks = chunking_service.chunk_text(extracted_text)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content yielded no valid text chunks."
        )

    # Generate document_id
    document_id = str(uuid.uuid4())

    # Generate embeddings and store in ChromaDB
    logger.info("Embeddings generated & vectors stored starting...")
    try:
        # Embedding generation is blocking and gated; keep it off the event loop.
        await asyncio.to_thread(
            vector_service.store_chunks,
            document_id,
            safe_filename,
            chunks,
            current.workspace_id
        )
    except ConnectionError as exc:
        logger.error(f"Ollama connection failure during vector storage: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"Failed to index vectors in ChromaDB: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(exc)}"
        )

    logger.info(f"Indexing completed for document '{document_id}' (filename: '{safe_filename}').")

    return ChatUploadResponse(
        document_id=document_id,
        filename=safe_filename,
        number_of_chunks=len(chunks)
    )


@router.post(
    "/chat/query",
    response_model=ChatQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query meeting transcript using RAG"
)
async def query_transcript_chat(
    request: ChatQueryRequest,
    current: AuthContext = Depends(get_current_user),
) -> ChatQueryResponse:
    """
    RAG chat endpoint to answer questions over a specific indexed document, scoped to
    the caller's workspace — a document_id from another workspace matches nothing.

    - **document_id**: Unique identifier returned by /chat/upload.
    - **question**: User question string.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question field cannot be empty."
        )
    if not request.document_id or not request.document_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID field cannot be empty."
        )

    logger.info(f"Query received for document_id '{request.document_id}'.")

    try:
        # Blocking retrieval + Ollama call: run off the event loop.
        rag_result = await asyncio.to_thread(
            retrieval_service.answer_question,
            request.document_id,
            request.question,
            current.workspace_id
        )
        logger.info("Retrieval completed and answer generated.")

        sources = [
            SourceMetadata(
                filename=src["filename"],
                chunk_number=src["chunk_number"]
            )
            for src in rag_result.get("sources", [])
        ]

        return ChatQueryResponse(
            answer=rag_result["answer"],
            sources=sources
        )

    except ConnectionError as exc:
        logger.error(f"Ollama connection error during RAG query: {exc}")
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
