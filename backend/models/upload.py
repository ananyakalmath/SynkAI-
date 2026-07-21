"""
Pydantic schemas for file upload responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """
    Response model for file upload operation.
    """
    filename: str = Field(..., description="Original uploaded filename")
    file_path: str = Field(..., description="Saved relative file path on server")
    file_size_bytes: int = Field(..., description="Size of uploaded file in bytes")
    character_count: int = Field(..., description="Total characters extracted from document")
    sample_text: str = Field(..., description="Sample snippet of extracted transcript text")
    message: str = Field(default="File successfully uploaded and parsed.", description="Status message")
