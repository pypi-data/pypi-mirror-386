from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_cached_resource(
    cache_dir: str,
    resource: str,
    resource_id: str,
    resource_updated_at: str | None,
    format: str = "parquet",
) -> pd.DataFrame | None:
    key = _get_cache_key(resource, resource_id, resource_updated_at)
    filepath = _get_abs_file_path(cache_dir, f"{key}.{format}", resource)
    if not filepath.exists():
        return None
    try:
        return pd.read_parquet(filepath)
    except Exception as e:
        logger.warning(f"Failed to load cached resource from {filepath}: {e}")
        return None


def cache_resource(
    cache_dir: str,
    resource: str,
    resource_id: str,
    resource_updated_at: str | None,
    resource_data: pd.DataFrame,
    format: str = "parquet",
) -> None:
    key = _get_cache_key(resource, resource_id, resource_updated_at)
    filepath = _get_abs_file_path(cache_dir, f"{key}.{format}", resource)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    resource_data.to_parquet(filepath, index=False)
    logger.debug(f"Cached resource to {filepath}")


def _get_cache_key(
    resource: str,
    resource_id: str,
    resource_updated_at: str | None,
) -> str:
    # include updated_at if present to produce a new key when dataset changes
    key = f"{resource}_{resource_id}"
    if resource_updated_at:
        key += f"_{resource_updated_at}"
    return key


def _get_abs_file_path(
    directory: str,
    filename: str,
    subdirectory: str | None = None,
) -> Path:
    """
    Return an absolute path to a file located under `directory[/subdirectory]/filename`.
    Expands '~' and resolves relative components.
    """
    base = Path(directory).expanduser()
    if subdirectory:
        base = base / subdirectory
    return (base / filename).resolve()
