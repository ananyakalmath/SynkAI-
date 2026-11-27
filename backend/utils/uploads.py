"""
Shared helpers for hashing an uploaded file's content.

/upload, /chat/upload, and /summarize each independently end up with the same file on
disk (the frontend posts a meeting once to /upload and once to /chat/upload, and
/summarize re-reads it by filename afterwards). A SHA-256 of the file's exact bytes is
the cache key FileParserService uses to recognize "this is content I've already
extracted/transcribed," so every caller needs the same hash for the same bytes.
"""

import hashlib
import os

from fastapi import UploadFile

from backend.config import settings


def workspace_uploads_dir(workspace_id: str) -> str:
    """
    Returns the uploads/ subdirectory for a workspace — files from different
    workspaces are kept in separate directories so two uploads with the same
    filename (from different companies) can never collide or be confused for
    each other.
    """
    return os.path.join(settings.UPLOADS_DIR, workspace_id)


def save_upload_and_hash(file: UploadFile, target_path: str, chunk_size: int = 1024 * 1024) -> str:
    """
    Streams `file` to `target_path` in chunks, returning a SHA-256 hex digest of its
    exact bytes. Hashing happens in the same pass as the disk write, so identifying a
    large video's content never needs a second read of the file or holding it fully
    in memory.

    Args:
        file: The incoming upload.
        target_path: Destination path to write the file to.
        chunk_size: Bytes read per iteration.

    Returns:
        Hex-encoded SHA-256 digest of the file's content.
    """
    hasher = hashlib.sha256()
    with open(target_path, "wb") as buffer:
        while True:
            chunk = file.file.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
            buffer.write(chunk)
    return hasher.hexdigest()


def hash_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """
    Returns a SHA-256 hex digest of a file already on disk — for callers (like
    /summarize) that only have a path, not the original upload stream.
    """
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
