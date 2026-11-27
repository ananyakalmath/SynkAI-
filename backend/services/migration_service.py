"""
One-time migration of pre-account (Sprint 1-4) data into the default workspace.

Before accounts existed, every upload and every indexed chunk was implicitly "global."
Now that ChromaDB queries and uploads/ paths are scoped by workspace_id, that old data
needs a home — the fixed-ID "legacy" workspace (see auth_service.DEFAULT_WORKSPACE_ID)
— or it would simply vanish from every workspace-scoped query. Both steps are
idempotent: re-running them after the first successful run is a no-op.
"""

import os
import shutil
from typing import Any, Dict, List

from backend.config import settings
from backend.services.auth_service import DEFAULT_WORKSPACE_ID
from backend.services.vector_service import VectorService
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def migrate_legacy_chroma_data(vector_service: VectorService) -> int:
    """Tags every chunk missing a workspace_id with the default workspace."""
    results = vector_service.collection.get(include=["metadatas"])
    ids: List[str] = results.get("ids") or []
    metadatas: List[Dict[str, Any]] = results.get("metadatas") or []

    stale_ids: List[str] = []
    stale_metadatas: List[Dict[str, Any]] = []

    for chunk_id, meta in zip(ids, metadatas):
        meta = dict(meta or {})
        if not meta.get("workspace_id"):
            meta["workspace_id"] = DEFAULT_WORKSPACE_ID
            stale_ids.append(chunk_id)
            stale_metadatas.append(meta)

    if stale_ids:
        vector_service.collection.update(ids=stale_ids, metadatas=stale_metadatas)
        logger.info(f"Migrated {len(stale_ids)} legacy vector chunk(s) into the default workspace.")

    return len(stale_ids)


def migrate_legacy_uploads() -> int:
    """Moves any file sitting directly in uploads/ into uploads/<default workspace>/."""
    uploads_dir = settings.UPLOADS_DIR
    if not os.path.isdir(uploads_dir):
        return 0

    legacy_dir = os.path.join(uploads_dir, DEFAULT_WORKSPACE_ID)
    moved = 0

    for name in os.listdir(uploads_dir):
        if name.startswith("."):
            continue  # .gitkeep and similar placeholders are not meeting uploads
        source = os.path.join(uploads_dir, name)
        if not os.path.isfile(source):
            continue
        os.makedirs(legacy_dir, exist_ok=True)
        shutil.move(source, os.path.join(legacy_dir, name))
        moved += 1

    if moved:
        logger.info(f"Migrated {moved} legacy upload(s) into '{legacy_dir}'.")

    return moved
