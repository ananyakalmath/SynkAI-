"""
Pydantic schemas for RAG chat indexing and question querying.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatUploadRequest(BaseModel):
    """
    Request payload to trigger vector indexing for an existing uploaded file.
    """
    filename: str = Field(..., description="Target uploaded file in uploads/ to index into ChromaDB")


class ChatUploadResponse(BaseModel):
    """
    Response payload after transcript text chunking and vector indexing.
    """
    filename: str = Field(..., description="Name of indexed transcript file")
    chunk_count: int = Field(..., description="Total text chunks generated")
    vectors_stored: int = Field(..., description="Total vector embeddings stored in ChromaDB")
    message: str = Field(default="Transcript successfully chunked and indexed in ChromaDB.", description="Status message")


class ChatQueryRequest(BaseModel):
    """
    Request payload for asking questions over indexed transcripts.
    """
    question: str = Field(..., description="User question about meeting transcript content")
    filename: Optional[str] = Field(default=None, description="Optional filename filter to narrow retrieval scope")


class SourceChunk(BaseModel):
    """
    Metadata citation schema for context chunk sources.
    """
    filename: str = Field(..., description="Source transcript filename")
    chunk_number: int = Field(..., description="Chunk sequence index")
    text: str = Field(..., description="Retrieved raw snippet text")


class ChatQueryResponse(BaseModel):
    """
    Response payload containing AI generated RAG answer and source citations.
    """
    answer: str = Field(..., description="Generated AI answer based on retrieved context")
    sources: List[SourceChunk] = Field(default_factory=list, description="List of source context chunks used for answer synthesis")
    model_used: str = Field(..., description="Model used for response generation")
