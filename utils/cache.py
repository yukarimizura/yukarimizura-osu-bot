import os
from utils.logger import get_logger
from config import MAX_BEATMAP_CACHE, MAX_DELETE_BATCH

logger = get_logger(__name__)

MAX_CACHE_FILES = MAX_BEATMAP_CACHE
CACHE_DELETE_BATCH = MAX_DELETE_BATCH


def cleanup_cache(cache_directory: str, extension: str = ".osu") -> None:
    """
    Keeps the cache size within MAX_CACHE_FILES.
    Frees enough room so that the upcoming file will not exceed capacity.
    """
    if not os.path.exists(cache_directory):
        return

    # Gather files and their modification times safely
    cached_files = []
    try:
        for file in os.listdir(cache_directory):
            if file.endswith(extension):
                full_path = os.path.join(cache_directory, file)
                try:
                    cached_files.append((full_path, os.path.getmtime(full_path)))
                except OSError:
                    continue  # File was removed or inaccessible
    except OSError as error:
        logger.warning(f"Failed to scan cache directory {cache_directory}: {error}")
        return

    # Nothing to clean if under threshold
    if len(cached_files) < MAX_CACHE_FILES:
        return

    # Sort by mtime ascending (oldest files first)
    cached_files.sort(key=lambda item: item[1])

    # Calculate overflow: at least enough to get back under MAX_CACHE_FILES,
    # or capped by CACHE_DELETE_BATCH if purging in bulk.
    overflow = len(cached_files) - MAX_CACHE_FILES + 1
    files_to_delete_count = max(overflow, min(CACHE_DELETE_BATCH, len(cached_files)))

    for file_path, _ in cached_files[:files_to_delete_count]:
        try:
            os.remove(file_path)
            logger.debug(f"Cache evicted: {os.path.basename(file_path)}")
        except OSError as error:
            logger.warning(f"Failed to delete cached file {os.path.basename(file_path)}: {error}")


def touch(path: str) -> None:
    """
    Refresh the modification time of a cached file.
    Frequently-used beatmaps remain newer than unused ones.
    """
    try:
        os.utime(path, None)
    except OSError:
        pass