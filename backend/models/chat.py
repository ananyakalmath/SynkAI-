"""
Pydantic schemas for RAG chat indexing and querying in SynkAI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatUploadRequest(BaseModel):
    """
    Optional Pydantic model representing request metadata for transcript upload.
    (Endpoints may ingest via UploadFile form-data instead).
    """
    filename: str = Field(..., description="Name of the file to be processed/indexed")


class ChatUploadResponse(BaseModel):
    """
    Response model returned after transcript upload and RAG vector store indexing.
    """
    document_id: str = Field(..., description="Unique document identifier generated for the transcript")
    filename: str = Field(..., description="Name of the indexed transcript file")
    number_of_chunks: int = Field(..., description="Number of text chunks created and indexed in ChromaDB")


class ChatQueryRequest(BaseModel):
    """
    Request model for RAG question querying.
    """
    document_id: str = Field(..., description="The document ID to query against")
    question: str = Field(..., description="The question to ask about the meeting transcript")


class SourceMetadata(BaseModel):
    """
    Source citation metadata containing file origin and chunk index.
    """
    filename: str = Field(..., description="Name of the source transcript file")
    chunk_number: int = Field(..., description="Index of the source text chunk")


class ChatQueryResponse(BaseModel):
    """
    Response model containing generated answer and source citations.
    """
    answer: str = Field(..., description="AI synthesized answer from retrieved meeting context")
    sources: List[SourceMetadata] = Field(default_factory=list, description="List of source context chunk citations")
